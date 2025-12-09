import asyncio
import logging
import re
from typing import Sequence, TypedDict, Annotated, List, Any, Dict, AsyncGenerator, Optional, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from tools import create_search_tool
from config import get_supabase_client
from prompts import THINK_PROMPT, ANSWER_PROMPT, get_think_prompt, get_answer_prompt
# NEW IMPORTS FOR MCP INTEGRATION
import subprocess, sys, json, threading, queue, uuid, time as _time
from pathlib import Path
from contextlib import suppress
# MEMORI INTEGRATION
from memori_engine import MemoriEngine
# PHASE 3: INTENT CLASSIFICATION & DYNAMIC PROMPTS
from intent_classifier import IntentClassifier, IntentResult, IntentType, ThinkingLevel, Domain
from dynamic_prompts import DynamicPromptManager
from config import (
    ROUTE_CONFIDENCE_MIN,
    VERIFY_CONFIDENCE_MAX,
    CACHE_TTL_SEC,
    MCP_TOOL_TIMEOUT_SEC,
    ENABLE_GRAPH_ADAPTIVE,
    ENABLE_STREAM_ADAPTIVE,
    MATH_VERIFY_LEVELS,
    CODE_VERIFY_LEVELS,
)

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("TutorAgent")


# --- Agent State ---
class AgentState(TypedDict):
    """The state that flows through the graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    final_answer: str
    plan: str
    route: str
    specialist_output: str
    specialist_model: str
    verified_answer: str
    tool_context: str
    intent_result: Optional[IntentResult]  # PHASE 3: Store detected intent


# --- Tutor Agent ---

class TutorAgent:
    """Multi-stage tutor agent with planner, specialist routing, and verifier."""

    def __init__(
        self,
        model_name: str = "qwen2.5:3b-instruct-q5_K_M",
        math_model: str = "mathstral:latest",
        code_model: str = "qwen2.5-coder:7b",
        verifier_model: str = "gemma3:4b",
        enable_memori: bool = True,
        enable_dynamic_prompts: bool = True,
        # Adaptive routing configuration
        enable_adaptive: bool = True,
        planner_confidence_threshold: float = ROUTE_CONFIDENCE_MIN,
        specialist_min_difficulty: str = "medium",  # easy|medium|hard
        verifier_confidence_threshold: float = VERIFY_CONFIDENCE_MAX,
        max_cache_size: int = 128,
        cache_ttl_seconds: int = CACHE_TTL_SEC,
    ) -> None:
        logger.info(
            "🚀 Initializing TutorAgent pipeline (planner=%s, math=%s, code=%s, verifier=%s)",
            model_name,
            math_model,
            code_model,
            verifier_model,
        )

        self.planner_model_name = model_name
        self.math_model_name = math_model
        self.code_model_name = code_model
        self.general_model_name = model_name
        self.verifier_model_name = verifier_model

        self.planner_llm = ChatOllama(model=self.planner_model_name, temperature=0.1, stream=True)
        self.math_llm = ChatOllama(model=self.math_model_name, temperature=0.05, stream=False)
        self.code_llm = ChatOllama(model=self.code_model_name, temperature=0.1, stream=False)
        self.general_llm = ChatOllama(model=self.general_model_name, temperature=0.1, stream=False)
        self.verifier_llm = ChatOllama(model=self.verifier_model_name, temperature=0.05, stream=True)

        try:
            self.tools = [create_search_tool()]
        except Exception as exc:
            logger.warning("⚠️  Search tool unavailable: %s", exc)
            self.tools = []
        self.mcp_client = MCPClient(start=True, timeout=float(MCP_TOOL_TIMEOUT_SEC))

        self.memori_engine = None
        if enable_memori:
            try:
                self.memori_engine = MemoriEngine(ollama_model=self.planner_model_name, verbose=False)
                logger.info("✅ Memori long-term memory enabled")
            except Exception as exc:
                logger.warning("⚠️  Failed to initialize Memori: %s", exc)
                logger.info("Continuing without Memori integration")

        self.intent_classifier: Optional[IntentClassifier] = None
        try:
            self.intent_classifier = IntentClassifier(model_name=self.planner_model_name)
            logger.info("✅ Intent classifier ready")
        except Exception as exc:
            logger.warning("⚠️  Failed to initialize intent classifier: %s", exc)

        self.enable_dynamic_prompts = enable_dynamic_prompts and self.intent_classifier is not None
        self.prompt_manager: Optional[DynamicPromptManager] = None
        if self.enable_dynamic_prompts:
            try:
                self.prompt_manager = DynamicPromptManager()
                logger.info("✅ Dynamic prompts enabled (Phase 3)")
            except Exception as exc:
                logger.warning("⚠️  Failed to initialize dynamic prompts: %s", exc)
                logger.info("Falling back to static prompts")
                self.enable_dynamic_prompts = False

        self.think_prompt = THINK_PROMPT
        self.answer_prompt = ANSWER_PROMPT

        self.subject_focus: Optional[str] = None
        self.complexity_level = "standard"

        self.graph = self._build_graph()
        logger.info("✅ TutorAgent initialized successfully.")

        # Adaptive and cache configuration
        self.enable_adaptive = enable_adaptive and ENABLE_GRAPH_ADAPTIVE
        self.enable_stream_adaptive = ENABLE_STREAM_ADAPTIVE
        self.planner_conf_threshold = planner_confidence_threshold
        self.verifier_conf_threshold = verifier_confidence_threshold
        self.cache_ttl_seconds = cache_ttl_seconds
        self._max_cache_size = max_cache_size
        self._answer_cache: Dict[str, Tuple[float, str]] = {}
        self.math_verify_levels = set(MATH_VERIFY_LEVELS)
        self.code_verify_levels = set(CODE_VERIFY_LEVELS)

    def set_subject_focus(self, subject: str) -> None:
        self.subject_focus = subject
        self.answer_prompt = get_answer_prompt(subject, self.complexity_level)
        logger.info("🎯 Set subject focus to: %s", subject)

    def set_complexity_level(self, level: str) -> None:
        if level in ["simple", "standard"]:
            self.complexity_level = level
            self.think_prompt = get_think_prompt(level)
            if self.subject_focus:
                self.answer_prompt = get_answer_prompt(self.subject_focus, level)
            logger.info("📊 Set complexity level to: %s", level)

    def reset_prompts(self) -> None:
        self.think_prompt = THINK_PROMPT
        self.answer_prompt = ANSWER_PROMPT
        self.subject_focus = None
        self.complexity_level = "standard"
        logger.info("🔄 Reset to default prompts")

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(AgentState)

        graph.add_node("plan", self._plan_node)
        graph.add_node("tools", self._tools_node)
        graph.add_node("solve", self._solve_node)
        graph.add_node("verify", self._verify_node)

        graph.set_entry_point("plan")
        graph.add_conditional_edges("plan", self._should_call_tools, {"tools": "tools", "solve": "solve"})
        graph.add_edge("tools", "solve")
        graph.add_edge("solve", "verify")
        graph.add_edge("verify", END)

        return graph.compile()

    @staticmethod
    def _get_history_string(state: AgentState) -> str:
        return "\n".join(
            f"{'User' if isinstance(m, HumanMessage) else 'Tutor'}: {m.content}"
            for m in state.get("messages", [])
        )

    @staticmethod
    def _get_conversation_history(messages: Sequence[BaseMessage]) -> List[Dict[str, str]]:
        history: List[Dict[str, str]] = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            else:
                history.append({"role": "assistant", "content": msg.content})
        return history

    @staticmethod
    def _get_last_user_message(state: AgentState) -> str:
        for msg in reversed(state.get("messages", [])):
            if isinstance(msg, HumanMessage):
                return msg.content
        return ""

    @staticmethod
    def _augment_planner_prompt(prompt: str) -> str:
        if "ROUTE_MODEL" in prompt and "DOMAIN" in prompt:
            return prompt
        extra = (
            "\nEnsure the <THINK> block ends with these metadata lines:\n"
            "DOMAIN: math|coding|general|mixed\n"
            "ROUTE_MODEL: mathstral|qwen-coder|generalist\n"
            "ROUTE_REASON: <one short sentence>\n"
            "NEED_SEARCH: yes|no\n"
            "SEARCH_QUERY: <best query or empty>\n"
        )
        return prompt.rstrip() + extra

    @staticmethod
    def _extract_plan(state: AgentState) -> str:
        if state.get("plan"):
            return state["plan"]
        for msg in reversed(state.get("messages", [])):
            if isinstance(msg, (AIMessage, SystemMessage)) and "<THINK>" in msg.content:
                return msg.content
        return ""

    @staticmethod
    def _extract_tag_content(text: str, tag: str) -> Optional[str]:
        if not text:
            return None
        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def _parse_need_search(content: str) -> bool:
        return bool(re.search(r"NEED_SEARCH:\s*yes", content or "", re.IGNORECASE))

    @staticmethod
    def _parse_search_query(content: str) -> str:
        match = re.search(r"SEARCH_QUERY:\s*(.*)", content or "", re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _collect_tool_blocks(self, plan: str, query: str) -> str:
        plan = plan or ""
        need_search = self._parse_need_search(plan)
        need_time = bool(re.search(r"NEED_TIME:\s*yes", plan, re.IGNORECASE))
        need_weather = bool(re.search(r"NEED_WEATHER:\s*yes", plan, re.IGNORECASE))
        timezone_match = re.search(r"TIMEZONE:\s*([^\n]+)", plan, re.IGNORECASE)
        weather_loc_match = re.search(r"WEATHER_LOCATION:\s*([^\n]+)", plan, re.IGNORECASE)
        timezone = timezone_match.group(1).strip() if timezone_match else None
        weather_location = weather_loc_match.group(1).strip() if weather_loc_match else None

        blocks: List[str] = []

        if need_search:
            try:
                results = self._call_mcp_tool("search", {"query": query, "max_results": 5})
                results_text = results if isinstance(results, str) else json.dumps(results, ensure_ascii=False)[:4000]
            except Exception as exc:
                logger.exception("❌ Search tool failed")
                results_text = f"[Search Error] {exc}"
            blocks.append(f"<SEARCH_RESULTS>\nQuery: {query}\n{results_text}\n</SEARCH_RESULTS>")

        try:
            mem = self._call_mcp_tool("memory_search", {"query": query, "k": 5, "scope": "both"})
            if mem:
                blocks.append(f"<MEMORY_RESULTS>\n{json.dumps(mem, ensure_ascii=False)[:4000]}\n</MEMORY_RESULTS>")
        except Exception as exc:
            blocks.append(f"<MEMORY_RESULTS_ERROR>{exc}</MEMORY_RESULTS_ERROR>")

        if need_time:
            try:
                res = self._call_mcp_tool("time", {"timezone": timezone} if timezone else {})
                blocks.append(f"<TIME_RESULT>\n{json.dumps(res, ensure_ascii=False)}\n</TIME_RESULT>")
            except Exception as exc:
                blocks.append(f"<TIME_RESULT_ERROR>{exc}</TIME_RESULT_ERROR>")

        if need_weather:
            try:
                res = self._call_mcp_tool("weather", {"location": weather_location or query})
                blocks.append(f"<WEATHER_RESULT>\n{json.dumps(res, ensure_ascii=False)[:4000]}\n</WEATHER_RESULT>")
            except Exception as exc:
                blocks.append(f"<WEATHER_RESULT_ERROR>{exc}</WEATHER_RESULT_ERROR>")

        return "\n".join(blocks)

    @staticmethod
    def _parse_route_from_plan(plan: str) -> Tuple[Optional[str], Optional[str]]:
        if not plan:
            return None, None
        route: Optional[str] = None
        domain_token: Optional[str] = None

        domain_match = re.search(r"DOMAIN:\s*([a-zA-Z]+)", plan, re.IGNORECASE)
        if domain_match:
            domain_raw = domain_match.group(1).lower()
            if domain_raw.startswith("math"):
                domain_token = "math"
            elif domain_raw in ("coding", "programming", "code"):
                domain_token = "code"
            elif domain_raw == "mixed":
                domain_token = "mixed"
            else:
                domain_token = "general"

        route_match = re.search(r"ROUTE_MODEL:\s*([^\s\n]+)", plan, re.IGNORECASE)
        if route_match:
            route_raw = route_match.group(1).lower()
            if "math" in route_raw:
                route = "math"
            elif "coder" in route_raw or "code" in route_raw:
                route = "code"
            elif "general" in route_raw or "planner" in route_raw:
                route = "general"

        if not route and domain_token:
            if domain_token == "math":
                route = "math"
            elif domain_token == "code":
                route = "code"
            elif domain_token == "mixed":
                route = "general"
            else:
                route = "general"

        return route, domain_token

    @staticmethod
    def _extract_difficulty(plan: str) -> Optional[str]:
        if not plan:
            return None
        m = re.search(r"difficulty\s*[:=-]\s*(easy|medium|hard)", plan, re.IGNORECASE)
        if m:
            return m.group(1).lower()
        m2 = re.search(r"expected_difficulty\s*[:=-]\s*(easy|medium|hard)", plan, re.IGNORECASE)
        if m2:
            return m2.group(1).lower()
        # heuristic based on steps count
        steps = re.findall(r"step", plan, re.IGNORECASE)
        if len(steps) >= 6:
            return "hard"
        if len(steps) >= 3:
            return "medium"
        if len(steps) > 0:
            return "easy"
        return None

    def _decide_usage(
        self,
        route: str,
        difficulty: Optional[str],
        intent_result: Optional[IntentResult],
        plan_text: str,
    ) -> Tuple[bool, bool, str]:
        """Return (use_specialist, use_verifier, rationale)."""
        if not self.enable_adaptive:
            return True, True, "adaptive_disabled"
        # default difficulty
        diff = difficulty or "medium"
        # intent influence
        high_conf = intent_result and intent_result.confidence >= self.planner_conf_threshold
        quick_intent = intent_result and intent_result.thinking_level == ThinkingLevel.NONE
        rationale_parts: List[str] = []
        # Decide specialist usage
        use_specialist = False
        if route in {"math", "code"}:
            if diff in {"hard", "medium"}:
                use_specialist = True
                rationale_parts.append(f"route={route} diff={diff} specialist")
            elif not high_conf:
                use_specialist = True
                rationale_parts.append("low_confidence_force_specialist")
        # quick intent overrides
        if quick_intent and diff == "easy" and high_conf:
            use_specialist = False
            rationale_parts.append("quick_intent_skip_specialist")
        # Decide verifier usage
        use_verifier = False
        if use_specialist:
            if route == "math" and diff in self.math_verify_levels:
                use_verifier = True
                rationale_parts.append("math_medium_or_hard_verify")
            elif route == "code" and diff in self.code_verify_levels:
                use_verifier = True
                rationale_parts.append("code_hard_verify")
            elif not high_conf and diff != "easy":
                use_verifier = True
                rationale_parts.append("low_confidence_verify")
        # If plan explicitly requests verification keyword
        if re.search(r"verify", plan_text, re.IGNORECASE) and use_specialist:
            use_verifier = True
            rationale_parts.append("plan_requests_verify")
        if not use_specialist:
            use_verifier = False
        rationale = ";".join(rationale_parts) or "default"
        return use_specialist, use_verifier, rationale

    def _cache_key(self, query: str, route: str) -> str:
        return f"{route}:{query.strip().lower()}"

    def _lookup_cache(self, key: str) -> Optional[str]:
        item = self._answer_cache.get(key)
        if not item:
            return None
        ts, answer = item
        if _time.time() - ts > self.cache_ttl_seconds:
            self._answer_cache.pop(key, None)
            return None
        return answer

    def _store_cache(self, key: str, answer: str) -> None:
        if len(self._answer_cache) >= self._max_cache_size:
            # simple eviction: remove oldest
            oldest_key = min(self._answer_cache.items(), key=lambda kv: kv[1][0])[0]
            self._answer_cache.pop(oldest_key, None)
        self._answer_cache[key] = (_time.time(), answer)

    @staticmethod
    def _route_from_intent(intent_result: Optional[IntentResult]) -> Optional[str]:
        if not intent_result:
            return None
        if intent_result.domain == Domain.MATHEMATICS:
            return "math"
        if intent_result.domain == Domain.PROGRAMMING:
            return "code"
        if intent_result.domain == Domain.MIXED:
            return "general"
        return "general"

    @staticmethod
    def _heuristic_route(query: str) -> str:
        if not query:
            return "general"
        if re.search(r"\b(integral|derivative|equation|solve|limit|matrix|algebra|calculus)\b", query, re.IGNORECASE):
            return "math"
        if re.search(r"\b(code|program|algorithm|debug|python|javascript|function|class|loop)\b", query, re.IGNORECASE):
            return "code"
        if re.search(r"[=+\-*/^]", query):
            return "math"
        return "general"

    def _determine_route(self, plan: str, intent_result: Optional[IntentResult], query: str) -> str:
        plan_route, plan_domain = self._parse_route_from_plan(plan)
        route = plan_route
        if plan_domain == "mixed" and (not route or route == "general"):
            route = self._heuristic_route(query)
        if not route and intent_result:
            route = self._route_from_intent(intent_result)
        if not route:
            route = self._heuristic_route(query)
        if route not in {"math", "code"}:
            route = "general"
        logger.info("🔀 Routing decision: %s", route)
        return route

    def _select_specialist_model(self, route: str) -> Tuple[ChatOllama, str]:
        if route == "math":
            return self.math_llm, self.math_model_name
        if route == "code":
            return self.code_llm, self.code_model_name
        return self.general_llm, self.general_model_name

    def _build_specialist_prompt(self, route: str, model_name: str) -> str:
        if route == "math":
            return (
                "You are the Mathstral specialist model. Use the plan and context to produce a rigorous, "
                "step-by-step mathematical solution. Show every transformation clearly, justify reasoning, "
                "and compute the final answer. Wrap the output inside <SPECIALIST_SOLUTION> with sections:\n"
                "### Step-by-Step Solution\n### Final Answer\n### Verification\n"
            )
        if route == "code":
            return (
                "You are the Qwen coding specialist. Use the plan and context to craft a high-quality programming "
                "solution. Describe the algorithm, present clean well-commented code, discuss complexity, and cover edge cases. "
                "Wrap the output inside <SPECIALIST_SOLUTION> with sections:\n"
                "### Approach\n### Code\n### Validation & Edge Cases\n"
            )
        return (
            "You are the general tutor specialist. Provide a thorough educational answer that follows the plan, "
            "captures key reasoning, and double-checks the result. Wrap the output inside <SPECIALIST_SOLUTION> with sections:\n"
            "### Key Reasoning\n### Final Answer\n### Checks\n"
        )

    def _build_specialist_payload(
        self,
        question: str,
        plan: str,
        history_text: str,
        tool_context: str,
    ) -> str:
        sections = [
            f"<QUESTION>\n{question}\n</QUESTION>",
            f"<PLAN>\n{plan.strip() or 'No plan provided'}\n</PLAN>",
        ]
        if tool_context:
            sections.append(f"<SUPPORTING_CONTEXT>\n{tool_context}\n</SUPPORTING_CONTEXT>")
        if history_text:
            sections.append(f"<CONVERSATION_HISTORY>\n{history_text}\n</CONVERSATION_HISTORY>")
        return "\n".join(sections)

    def _build_verifier_prompt(
        self,
        route: str,
        specialist_model: str,
        style_hint: Optional[str],
    ) -> str:
        style_section = f"\nStyle preferences:\n{style_hint}\n" if style_hint else ""
        return (
            "You are Gemma3 4B acting as the final verifier. Review the specialist solution, check every step, "
            "and correct any mistakes. Recompute any portion that is doubtful. Return the authoritative response inside "
            "<FINAL_ANSWER> with these sections:\n"
            "### Final Answer\n### Reasoning Summary\n### Confidence\n"
            "Confidence must be a number between 0 and 1 inclusive."
            f"\nSpecialist model: {specialist_model}\n"
            f"{style_section}"
        )

    def _build_verifier_payload(
        self,
        question: str,
        plan: str,
        specialist_output: str,
        tool_context: str,
        specialist_model: str,
    ) -> str:
        sections = [
            f"<QUESTION>\n{question}\n</QUESTION>",
            f"<PLAN>\n{plan.strip() or 'No plan provided'}\n</PLAN>",
            f"<SPECIALIST_SOLUTION>\n{specialist_output}\n</SPECIALIST_SOLUTION>",
            f"<SPECIALIST_MODEL>{specialist_model}</SPECIALIST_MODEL>",
        ]
        if tool_context:
            sections.append(f"<SUPPORTING_CONTEXT>\n{tool_context}\n</SUPPORTING_CONTEXT>")
        return "\n".join(sections)

    @staticmethod
    def _sanitize_stream_token(token: str, tag: str) -> str:
        token = re.sub(rf"<{tag}>", "", token, flags=re.IGNORECASE)
        token = re.sub(rf"</{tag}>", "", token, flags=re.IGNORECASE)
        return token

    async def _run_specialist_stage(
        self,
        route: str,
        question: str,
        plan: str,
        history_text: str,
        tool_context: str,
    ) -> Tuple[str, str, AIMessage]:
        solver_llm, solver_model = self._select_specialist_model(route)
        system_prompt = self._build_specialist_prompt(route, solver_model)
        payload = self._build_specialist_payload(question, plan, history_text, tool_context)
        response = await solver_llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=payload)])
        return response.content, solver_model, response

    async def _run_verifier_stage(
        self,
        route: str,
        specialist_model: str,
        question: str,
        plan: str,
        specialist_output: str,
        tool_context: str,
        style_hint: Optional[str],
    ) -> Tuple[str, AIMessage]:
        system_prompt = self._build_verifier_prompt(route, specialist_model, style_hint)
        payload = self._build_verifier_payload(question, plan, specialist_output, tool_context, specialist_model)
        response = await self.verifier_llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=payload)])
        final_answer = self._extract_tag_content(response.content, "FINAL_ANSWER") or response.content
        return final_answer.strip(), response

    async def _plan_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("🧠 Stage 1: Planner & Router")
        history_text = self._get_history_string(state)
        user_message = state["messages"][-1]
        conversation_history = self._get_conversation_history(state.get("messages", [])[:-1])
        intent_result: Optional[IntentResult] = None
        if self.intent_classifier:
            try:
                intent_result = await self.intent_classifier.classify(user_message.content, conversation_history)
                logger.info(
                    "🎯 Intent classified as %s (domain=%s, confidence=%.2f)",
                    intent_result.intent.value,
                    intent_result.domain.value,
                    intent_result.confidence,
                )
            except Exception as exc:
                logger.warning("⚠️  Intent classification failed: %s", exc)
                intent_result = None
        prompt_template = self.think_prompt
        try:
            prompt_formatted = prompt_template.format(chat_history=history_text)
        except KeyError:
            prompt_formatted = prompt_template
        planner_prompt = self._augment_planner_prompt(prompt_formatted)
        response = await self.planner_llm.ainvoke([SystemMessage(content=planner_prompt), user_message])
        plan_text = response.content
        route = self._determine_route(plan_text, intent_result, user_message.content)
        return {
            "messages": [response],
            "plan": plan_text,
            "route": route,
            "intent_result": intent_result,
        }

    async def _tools_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("🔍 Stage 1.5: Tool context gathering")
        plan = state.get("plan") or self._extract_plan(state)
        query = self._parse_search_query(plan) or self._get_last_user_message(state)
        tool_context = self._collect_tool_blocks(plan, query)
        if not tool_context:
            logger.info("ℹ️ No external tools required.")
            return {"messages": []}
        return {"messages": [SystemMessage(content=tool_context)], "tool_context": tool_context}

    async def _solve_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("🛠️ Stage 2: Specialist solving (graph mode)")
        t0 = _time.time()
        route = state.get("route", "general")
        plan = state.get("plan", "")
        tool_context = state.get("tool_context", "")
        history_text = self._get_history_string(state)
        question = self._get_last_user_message(state)
        intent_result = state.get("intent_result")
        difficulty = self._extract_difficulty(plan)
        use_specialist, use_verifier, rationale = self._decide_usage(route, difficulty, intent_result, plan)
        logger.info("📌 Decision: route=%s diff=%s specialist=%s verifier=%s rationale=%s",
                route, difficulty or "unknown", use_specialist, use_verifier, rationale)
        route_for_solve = route if use_specialist else "general"
        # Cache fast path
        cache_key = self._cache_key(question, route_for_solve)
        cached = self._lookup_cache(cache_key)
        if cached and not use_verifier:
            logger.info("⚡ Cache hit for route=%s; skipping verify", route_for_solve)
            t1 = _time.time()
            logger.info("⏱️ Solve stage (cached) took %.0f ms", (t1 - t0) * 1000)
            return {
                "messages": [],
                "specialist_output": cached,
                "specialist_model": self.math_model_name if route_for_solve == "math" else (
                    self.code_model_name if route_for_solve == "code" else self.general_model_name
                ),
                "use_verifier": False,
                "decision_rationale": rationale,
            }

        solution_text, specialist_model, response = await self._run_specialist_stage(
            route_for_solve, question, plan, history_text, tool_context
        )
        t1 = _time.time()
        logger.info("⏱️ Solve stage took %.0f ms", (t1 - t0) * 1000)
        return {
            "messages": [response],
            "specialist_output": solution_text,
            "specialist_model": specialist_model,
            "use_verifier": use_verifier,
            "decision_rationale": rationale,
        }

    async def _verify_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("✅ Stage 3: Verification & finalization")
        t0 = _time.time()
        route = state.get("route", "general")
        plan = state.get("plan", "")
        tool_context = state.get("tool_context", "")
        specialist_output = state.get("specialist_output", "")
        specialist_model = state.get("specialist_model", self.general_model_name)
        question = self._get_last_user_message(state)
        use_verifier = state.get("use_verifier", True)
        if not use_verifier:
            # Pass through specialist output
            self._store_cache(self._cache_key(question, route if route in {"math", "code"} else "general"), specialist_output)
            t1 = _time.time()
            logger.info("⏱️ Verify stage skipped; total %.0f ms", (t1 - t0) * 1000)
            return {
                "messages": [],
                "final_answer": specialist_output,
                "verified_answer": specialist_output,
            }

        final_answer, response = await self._run_verifier_stage(
            route,
            specialist_model,
            question,
            plan,
            specialist_output,
            tool_context,
            None,
        )
        self._store_cache(self._cache_key(question, route if route in {"math", "code"} else "general"), final_answer)
        t1 = _time.time()
        logger.info("⏱️ Verify stage took %.0f ms", (t1 - t0) * 1000)
        return {
            "messages": [response],
            "final_answer": final_answer,
            "verified_answer": response.content,
        }

    def _should_call_tools(self, state: AgentState) -> str:
        plan = state.get("plan") or self._extract_plan(state)
        if plan and (
            self._parse_need_search(plan)
            or re.search(r"NEED_TIME:\s*yes", plan, re.IGNORECASE)
            or re.search(r"NEED_WEATHER:\s*yes", plan, re.IGNORECASE)
        ):
            return "tools"
        return "solve"

    async def run(self, query: str, history: List[BaseMessage]) -> Dict[str, Any]:
        messages = history + [HumanMessage(content=query)]
        return await self.graph.ainvoke({"messages": messages})

    async def run_with_streaming(self, query: str, history: List[BaseMessage]) -> None:
        async for event in self.stream_phases(query, history):
            if event["type"] == "thinking_delta":
                print(event["delta"], end="", flush=True)
            if event["type"] == "answer_delta":
                print(event["delta"], end="", flush=True)
            if event["type"] == "thinking_complete":
                print(f"\n--- Plan complete ---\n{event['thinking_content']}\n")
            if event["type"] == "answer_complete":
                print(f"\n--- Final Answer ---\n{event['response']}\n")

    # removed older simple stream_phases to avoid duplicate definitions

    async def stream_phases(self, query: str, history: List[BaseMessage], user_id: Optional[str] = None, conversation_id: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Yield structured streaming events for frontend consumption.
        Event types:
          intent_detected, thinking_start, thinking_delta, thinking_complete,
          answer_start, answer_delta, answer_complete, roadmap_trigger
        """
        # Build history text and conversation list for intent classification
        history_lines = []
        conversation_history = []
        for m in history:
            role = "User" if isinstance(m, HumanMessage) else "Tutor"
            history_lines.append(f"{role}: {m.content}")
            conversation_history.append({
                "role": "user" if isinstance(m, HumanMessage) else "assistant",
                "content": m.content,
            })
        history_text = "\n".join(history_lines)

        intent_result: Optional[IntentResult] = None
        thinking_prompt_template = self.think_prompt
        answer_prompt_text = self.answer_prompt
        user_context: Dict[str, Any] = {}

        if self.intent_classifier:
            try:
                intent_result = await self.intent_classifier.classify(query, conversation_history)
                yield {
                    "type": "intent_detected",
                    "intent": str(intent_result.intent),
                    "confidence": intent_result.confidence,
                    "domain": str(intent_result.domain),
                    "thinking_level": str(intent_result.thinking_level),
                }
            except Exception as exc:
                logger.warning("⚠️  Intent classification failed: %s", exc)
                intent_result = None

        if self.enable_dynamic_prompts and self.prompt_manager and intent_result:
            try:
                # Get user context from Memori if available (optional)
                if self.memori_engine and user_id:
                    try:
                        user_context = {
                            "learning_history": [],
                            "preferences": {}
                        }
                    except Exception as e:
                        logger.warning(f"Could not fetch user context from Memori: {e}")

                # Get dynamic prompts based on intent
                thinking_prompt_template, answer_prompt_text = self.prompt_manager.get_prompts(
                    intent_result,
                    query,
                    user_context,
                )

                # ---- ROADMAP GENERATION TRIGGER ----
                if intent_result.intent in [IntentType.ROADMAP_REQUEST, IntentType.LEARNING_NEW_TOPIC]:
                    if intent_result.confidence > 0.6:
                        should_trigger = True
                        if user_id and conversation_id:
                            try:
                                supabase = get_supabase_client()
                                existing = supabase.table("learning_roadmaps") \
                                    .select("id") \
                                    .eq("user_id", user_id) \
                                    .eq("conversation_id", conversation_id) \
                                    .not_.eq("status", "abandoned") \
                                    .limit(1) \
                                    .execute()
                                if existing.data:
                                    should_trigger = False
                                    logger.info(f"🔁 Roadmap already exists for conversation {conversation_id}; suppressing trigger.")
                            except Exception as e:
                                logger.warning(f"Roadmap existence check failed: {e}; proceeding with trigger.")
                        if should_trigger:
                            yield {
                                "type": "roadmap_trigger",
                                "intent": str(intent_result.intent),
                                "topic": intent_result.topic,
                                "domain": str(intent_result.domain),
                                "user_level": intent_result.user_level or "beginner",
                                "query": query,
                                "conversation_id": conversation_id,
                                "user_id": user_id
                            }
                            logger.info(f"🗺️ Triggered roadmap generation for topic: {intent_result.topic}")

                # ---- QUIZ OFFER DISABLED ----
                # Quizzes will be milestone-based, not triggered by practice requests
            except Exception as exc:
                logger.warning("⚠️  Dynamic prompt generation failed: %s", exc)
                thinking_prompt_template = self.think_prompt
                answer_prompt_text = self.answer_prompt

        skip_thinking = (
            intent_result
            and intent_result.thinking_level == ThinkingLevel.NONE
            and not thinking_prompt_template
        )

        plan_raw = ""
        plan_for_specialist = ""
        plan_display = ""
        tool_context = ""
        route_guess = self._route_from_intent(intent_result) or self._heuristic_route(query)

        if skip_thinking:
            logger.info("⚡ Skipping planner stream (quick answer mode)")
            route = route_guess or "general"
            model_token = "mathstral" if route == "math" else "qwen-coder" if route == "code" else "generalist"
            plan_for_specialist = (
                "Quick response mode. Minimal planning applied.\n"
                f"DOMAIN: {route}\n"
                f"ROUTE_MODEL: {model_token}\n"
                "ROUTE_REASON: Quick answer requested by intent classifier.\n"
                "NEED_SEARCH: no\n"
                "SEARCH_QUERY:\n"
            )
            plan_display = plan_for_specialist
            yield {"type": "thinking_start"}
            yield {"type": "thinking_complete", "thinking_content": plan_display}
        else:
            prompt_template = thinking_prompt_template or self.think_prompt
            try:
                prompt_formatted = prompt_template.format(chat_history=history_text)
            except KeyError:
                prompt_formatted = prompt_template
            planner_prompt = self._augment_planner_prompt(prompt_formatted)
            system_msg = SystemMessage(content=planner_prompt)
            user_msg = HumanMessage(content=query)
            yield {"type": "thinking_start"}
            inside_think = False
            try:
                async for chunk in self.planner_llm.astream([system_msg, user_msg]):
                    token = getattr(chunk, "content", "")
                    if not token:
                        continue
                    plan_raw += token
                    if "<THINK>" in token:
                        inside_think = True
                        token = token.split("<THINK>", 1)[-1]
                    if "</THINK>" in token:
                        before_close, _ = token.split("</THINK>", 1)
                        if inside_think and before_close:
                            yield {"type": "thinking_delta", "delta": before_close}
                        inside_think = False
                        continue
                    if inside_think and token:
                        yield {"type": "thinking_delta", "delta": token}
            except Exception as exc:
                logger.exception("Thinking phase streaming failed: %s", exc)

            plan_for_specialist = self._extract_tag_content(plan_raw, "THINK") or plan_raw.strip()
            route = self._determine_route(plan_raw, intent_result, query)
            tool_context = self._collect_tool_blocks(plan_raw, query)
            plan_display = plan_for_specialist
            if tool_context:
                plan_display = f"{plan_display}\n{tool_context}"
            yield {"type": "thinking_complete", "thinking_content": plan_display}

        if not plan_for_specialist:
            plan_for_specialist = plan_display or ""

        if not tool_context:
            tool_context = ""

        final_route = route if not skip_thinking else (route_guess or "general")

        # Adaptive decisions for streaming path
        difficulty = self._extract_difficulty(plan_for_specialist)
        use_specialist, use_verifier, rationale = self._decide_usage(
            final_route,
            difficulty,
            intent_result,
            plan_for_specialist,
        )
        route_for_solve = final_route if (self.enable_stream_adaptive and use_specialist) else "general"

        # Cache fast path
        cache_key = self._cache_key(query, route_for_solve)
        cached = self._lookup_cache(cache_key)
        if self.enable_stream_adaptive and cached and not use_verifier:
            yield {"type": "answer_start"}
            yield {"type": "answer_delta", "delta": cached}
            yield {
                "type": "answer_complete",
                "response": cached,
                "thinking_content": plan_display,
                "specialist_model": self.math_model_name if route_for_solve == "math" else (
                    self.code_model_name if route_for_solve == "code" else self.general_model_name
                ),
            }
            return

        solution_text, specialist_model, _ = await self._run_specialist_stage(
            route_for_solve,
            query,
            plan_for_specialist,
            history_text,
            tool_context,
        )

        if not (self.enable_stream_adaptive and use_verifier):
            # Bypass verifier; stream specialist as final
            yield {"type": "answer_start"}
            yield {"type": "answer_delta", "delta": solution_text}
            self._store_cache(cache_key, solution_text)
            yield {
                "type": "answer_complete",
                "response": solution_text,
                "thinking_content": plan_display,
                "specialist_model": specialist_model,
            }
            return

        style_hint = answer_prompt_text if answer_prompt_text != self.answer_prompt else None
        verifier_system = SystemMessage(
            content=self._build_verifier_prompt(route_for_solve, specialist_model, style_hint)
        )
        verifier_payload = self._build_verifier_payload(
            query,
            plan_for_specialist,
            solution_text,
            tool_context,
            specialist_model,
        )
        verifier_human = HumanMessage(content=verifier_payload)

        yield {"type": "answer_start"}
        answer_accum = ""
        try:
            async for chunk in self.verifier_llm.astream([verifier_system, verifier_human]):
                token = getattr(chunk, "content", "")
                if not token:
                    continue
                answer_accum += token
                cleaned = self._sanitize_stream_token(token, "FINAL_ANSWER")
                if cleaned:
                    yield {"type": "answer_delta", "delta": cleaned}
        except Exception as exc:
            logger.exception("Answer phase streaming failed: %s", exc)

        final_answer = self._extract_tag_content(answer_accum, "FINAL_ANSWER") or self._sanitize_stream_token(
            answer_accum, "FINAL_ANSWER"
        ).strip()
        self._store_cache(cache_key, final_answer)
        yield {
            "type": "answer_complete",
            "response": final_answer,
            "thinking_content": plan_display,
            "specialist_model": specialist_model,
        }

        # ---- QUIZ OFFER DISABLED ----
        # Quiz offers will be triggered from milestone completion, not after every explanation
        # This prevents quiz spam on every single question

    # NEW: helper to call MCP tools
    def _call_mcp_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        if not self.mcp_client or not self.mcp_client.alive:
            raise RuntimeError("MCP client not running")
        return self.mcp_client.call_tool(name, arguments)

    def store_conversation_memory(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.memori_engine:
            logger.debug("Memori not enabled, skipping memory storage")
            return {"status": "skipped", "reason": "memori_disabled"}

        try:
            result = self.memori_engine.store_conversation(
                user_id=user_id,
                user_message=user_message,
                assistant_response=assistant_response,
                metadata=metadata,
            )
            logger.debug("✅ Stored conversation in Memori for user %s", user_id)
            return result
        except Exception as exc:
            logger.error("❌ Failed to store in Memori: %s", exc)
            return {"status": "error", "error": str(exc)}

    def add_user_learning_preference(
        self,
        user_id: str,
        preference: str,
        category: str = "learning_preference",
    ) -> Dict[str, Any]:
        if not self.memori_engine:
            return {"status": "skipped", "reason": "memori_disabled"}

        try:
            result = self.memori_engine.add_user_preference(
                user_id=user_id,
                preference=preference,
                category=category,
            )
            logger.info("✅ Added learning preference for user %s", user_id)
            return result
        except Exception as exc:
            logger.error("❌ Failed to add preference: %s", exc)
            return {"status": "error", "error": str(exc)}


# MCP CLIENT IMPLEMENTATION
class MCPClient:
    """Lightweight JSON-RPC stdio client for the local mcp_server."""
    def __init__(self, start: bool = False, timeout: float = 8.0):
        self.proc: subprocess.Popen | None = None
        self.q: "queue.Queue[str]" = queue.Queue()
        self.lock = threading.Lock()
        self.timeout = timeout
        self.alive = False
        if start:
            self.start()

    def start(self) -> None:
        if self.proc and self.alive:
            return
        script_path = Path(__file__).with_name("mcp_server.py")
        if not script_path.exists():
            logger.warning("mcp_server.py not found; MCP tools disabled")
            return
        self.proc = subprocess.Popen([sys.executable, "-u", str(script_path)],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, bufsize=1)
        self.alive = True
        threading.Thread(target=self._reader, daemon=True).start()
        threading.Thread(target=self._stderr_logger, daemon=True).start()

    def _reader(self):
        if not self.proc or not self.proc.stdout:
            return
        for line in self.proc.stdout:
            self.q.put(line.rstrip("\n"))
        self.alive = False

    def _stderr_logger(self):
        if not self.proc or not self.proc.stderr:
            return
        for line in self.proc.stderr:
            logger.debug(f"[MCP STDERR] {line.rstrip()}")

    def _send(self, obj: Dict[str, Any]):
        if not self.proc or not self.proc.stdin:
            raise RuntimeError("MCP process not started")
        line = json.dumps(obj)
        with self.lock:
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()

    def call_tool(self, name: str, arguments: Dict[str, Any] | None = None) -> Any:
        if not self.alive:
            raise RuntimeError("MCP server not alive")
        _id = str(uuid.uuid4())
        req = {"jsonrpc": "2.0", "id": _id, "method": "tools/call", "params": {"name": name, "arguments": arguments or {}}}
        self._send(req)
        deadline = _time.time() + self.timeout
        buf: List[str] = []
        while _time.time() < deadline:
            try:
                line = self.q.get(timeout=0.1)
            except queue.Empty:
                continue
            buf.append(line)
            with suppress(json.JSONDecodeError):
                msg = json.loads(line)
                if msg.get("id") == _id:
                    if "result" in msg:
                        return msg["result"]
                    if "error" in msg:
                        raise RuntimeError(msg["error"].get("message"))
        raise TimeoutError(f"Timeout waiting for MCP tool '{name}' response. Buffer: {buf[-5:]}")

    def list_tools(self) -> List[Dict[str, Any]]:
        if not self.alive:
            raise RuntimeError("MCP server not alive")
        _id = str(uuid.uuid4())
        self._send({"jsonrpc": "2.0", "id": _id, "method": "tools/list"})
        deadline = _time.time() + self.timeout
        while _time.time() < deadline:
            try:
                line = self.q.get(timeout=0.1)
            except queue.Empty:
                continue
            with suppress(json.JSONDecodeError):
                msg = json.loads(line)
                if msg.get("id") == _id and "result" in msg:
                    return msg["result"].get("tools", [])
        raise TimeoutError("Timeout listing tools")

    def close(self):  # optional
        if self.proc and self.alive:
            with suppress(Exception):
                self.proc.terminate()
        self.alive = False


# --- Example Interactive Loop ---
async def main() -> None:
    agent = TutorAgent()
    history: List[BaseMessage] = []

    print("Welcome to the Tutor Bot! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            break

        final_state = await agent.graph.ainvoke({"messages": history + [HumanMessage(content=user_input)]})
        ai_answer = final_state.get("final_answer", "⚠️ Could not process that.")

        history.extend([HumanMessage(content=user_input), AIMessage(content=ai_answer)])


if __name__ == "__main__":
    asyncio.run(main())
