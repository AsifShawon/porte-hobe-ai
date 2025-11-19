import asyncio
import logging
import re
from typing import Sequence, TypedDict, Annotated, List, Any, Dict, AsyncGenerator, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from tools import create_search_tool
from prompts import THINK_PROMPT, ANSWER_PROMPT, get_think_prompt, get_answer_prompt
# NEW IMPORTS FOR MCP INTEGRATION
import subprocess, sys, json, threading, queue, uuid, time as _time
from pathlib import Path
from contextlib import suppress
# MEMORI INTEGRATION
from memori_engine import MemoriEngine
# PHASE 3: INTENT CLASSIFICATION & DYNAMIC PROMPTS
from intent_classifier import IntentClassifier, IntentResult, IntentType, ThinkingLevel
from dynamic_prompts import DynamicPromptManager

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("TutorAgent")


# --- Agent State ---
class AgentState(TypedDict):
    """The state that flows through the graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    final_answer: str
    intent_result: Optional[IntentResult]  # PHASE 3: Store detected intent


# --- Tutor Agent ---
class TutorAgent:
    """Two-phase reasoning tutor with tool-calling and streaming answers."""

    def __init__(self, model_name: str = "qwen2.5:3b-instruct-q5_K_M", enable_memori: bool = True, enable_dynamic_prompts: bool = True) -> None:
        logger.info(f"🚀 Initializing TutorAgent with model: {model_name}")

        self.llm = ChatOllama(model=model_name, temperature=0.1, stream=True)  # enable streaming
        self.tools = [create_search_tool()]  # legacy direct search tool
        # Initialize MCP client (for web_search, time, weather)
        self.mcp_client = MCPClient(start=True)

        # Initialize Memori for long-term memory management
        self.memori_engine = None
        if enable_memori:
            try:
                self.memori_engine = MemoriEngine(
                    ollama_model=model_name,
                    verbose=False  # Set to True for debugging
                )
                logger.info("✅ Memori long-term memory enabled")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize Memori: {e}")
                logger.info("Continuing without Memori integration")

        # PHASE 3: Initialize intent classification and dynamic prompts
        self.enable_dynamic_prompts = enable_dynamic_prompts
        self.intent_classifier = None
        self.prompt_manager = None

        if enable_dynamic_prompts:
            try:
                self.intent_classifier = IntentClassifier(model_name=model_name)
                self.prompt_manager = DynamicPromptManager()
                logger.info("✅ Dynamic prompts enabled (Phase 3)")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize dynamic prompts: {e}")
                logger.info("Falling back to static prompts")
                self.enable_dynamic_prompts = False

        # Load prompts from prompts.py
        self.think_prompt = THINK_PROMPT
        self.answer_prompt = ANSWER_PROMPT

        # Optional: Allow dynamic prompt selection
        self.subject_focus = None  # Can be set to "math", "coding", etc.
        self.complexity_level = "standard"  # Can be "simple" or "standard"

        self.graph = self._build_graph()
        logger.info("✅ TutorAgent initialized successfully.")

    # --- Prompt Configuration ---
    def set_subject_focus(self, subject: str) -> None:
        """Set the subject focus for specialized prompts (math, coding, etc.)"""
        self.subject_focus = subject
        self.answer_prompt = get_answer_prompt(subject, self.complexity_level)
        logger.info(f"🎯 Set subject focus to: {subject}")

    def set_complexity_level(self, level: str) -> None:
        """Set the complexity level (simple, standard)"""
        if level in ["simple", "standard"]:
            self.complexity_level = level
            self.think_prompt = get_think_prompt(level)
            if self.subject_focus:
                self.answer_prompt = get_answer_prompt(self.subject_focus, level)
            logger.info(f"📊 Set complexity level to: {level}")

    def reset_prompts(self) -> None:
        """Reset to default prompts"""
        self.think_prompt = THINK_PROMPT
        self.answer_prompt = ANSWER_PROMPT
        self.subject_focus = None
        self.complexity_level = "standard"
        logger.info("🔄 Reset to default prompts")

    # --- Graph Setup ---
    def _build_graph(self) -> StateGraph:
        graph = StateGraph(AgentState)

        graph.add_node("think", self._think_node)
        graph.add_node("tools", self._tools_node)
        graph.add_node("answer", self._answer_node)

        graph.set_entry_point("think")
        graph.add_conditional_edges("think", self._should_call_tools,
                                    {"continue": "tools", "end": "answer"})
        graph.add_edge("tools", "answer")
        graph.add_edge("answer", END)

        return graph.compile()

    # --- Helpers ---
    @staticmethod
    def _get_history_string(state: AgentState) -> str:
        return "\n".join(
            f"{'User' if isinstance(m, HumanMessage) else 'Tutor'}: {m.content}"
            for m in state.get("messages", [])
        )

    @staticmethod
    def _extract_plan(state: AgentState) -> str:
        for msg in reversed(state.get("messages", [])):
            if isinstance(msg, (AIMessage, SystemMessage)) and "<THINK>" in msg.content:
                return msg.content
        return state["messages"][-1].content if state.get("messages") else ""

    @staticmethod
    def _parse_need_search(content: str) -> bool:
        return bool(re.search(r"NEED_SEARCH:\s*yes", content, re.IGNORECASE))

    @staticmethod
    def _parse_search_query(content: str) -> str:
        m = re.search(r"SEARCH_QUERY:\s*(.*)", content, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    # --- Node Handlers ---
    def _think_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("🧠 Phase 1: Thinking...")
        history = self._get_history_string(state)
        user_message = state["messages"][-1]
        prompt = self.think_prompt.format(chat_history=history)
        response = self.llm.invoke([SystemMessage(content=prompt), user_message])
        logger.info(f"📋 Plan:\n{response.content}\n")
        return {"messages": [response]}

    def _tools_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("🔍 Running tools (MCP + search)...")
        plan = self._extract_plan(state)
        # Prefer MCP tools for external tasks
        need_search = self._parse_need_search(plan)
        query = self._parse_search_query(plan) or next(
            (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
            ""
        )
        # New tool flags
        need_time = bool(re.search(r"NEED_TIME:\s*yes", plan, re.IGNORECASE))
        need_weather = bool(re.search(r"NEED_WEATHER:\s*yes", plan, re.IGNORECASE))
        timezone_match = re.search(r"TIMEZONE:\s*([^\n]+)", plan, re.IGNORECASE)
        weather_loc_match = re.search(r"WEATHER_LOCATION:\s*([^\n]+)", plan, re.IGNORECASE)
        timezone = timezone_match.group(1).strip() if timezone_match else None
        weather_location = weather_loc_match.group(1).strip() if weather_loc_match else None

        blocks: List[str] = []
        # SEARCH via MCP (alias 'search')
        if need_search:
            try:
                results = self._call_mcp_tool("search", {"query": query, "max_results": 5})
                results_text = results if isinstance(results, str) else json.dumps(results, ensure_ascii=False)[:4000]
            except Exception as e:
                logger.exception("❌ Search tool failed")
                results_text = f"[Search Error] {e}"
            blocks.append(f"<SEARCH_RESULTS>\nQuery: {query}\n{results_text}\n</SEARCH_RESULTS>")
        # MEMORY via MCP (both scopes)
        try:
            mem = self._call_mcp_tool("memory_search", {"query": query, "k": 5, "scope": "both"})
            blocks.append(f"<MEMORY_RESULTS>\n{json.dumps(mem, ensure_ascii=False)[:4000]}\n</MEMORY_RESULTS>")
        except Exception as e:
            blocks.append(f"<MEMORY_RESULTS_ERROR>{e}</MEMORY_RESULTS_ERROR>")
        # TIME via MCP
        if need_time:
            try:
                res = self._call_mcp_tool("time", {"timezone": timezone} if timezone else {})
                blocks.append(f"<TIME_RESULT>\n{json.dumps(res, ensure_ascii=False)}\n</TIME_RESULT>")
            except Exception as e:
                blocks.append(f"<TIME_RESULT_ERROR>{e}</TIME_RESULT_ERROR>")
        # WEATHER via MCP
        if need_weather:
            try:
                res = self._call_mcp_tool("weather", {"location": weather_location or query})
                blocks.append(f"<WEATHER_RESULT>\n{json.dumps(res, ensure_ascii=False)[:4000]}\n</WEATHER_RESULT>")
            except Exception as e:
                blocks.append(f"<WEATHER_RESULT_ERROR>{e}</WEATHER_RESULT_ERROR>")

        if not blocks:
            logger.info("ℹ️ No tools triggered; skipping tool node.")
            return {"messages": []}

        return {"messages": [SystemMessage(content="\n".join(blocks))]}

    def _answer_node(self, state: AgentState) -> Dict[str, Any]:
        logger.info("✍️ Phase 2: Answering...")
        history = self._get_history_string(state)
        plan = self._extract_plan(state)
        prompt = self.answer_prompt.format(plan=plan, chat_history=history)

        # streaming response here
        print("\nTutor: ", end="", flush=True)
        chunks: List[str] = []
        for event in self.llm.stream([SystemMessage(content=prompt)]):
            if hasattr(event, "content") and event.content:
                print(event.content, end="", flush=True)
                chunks.append(event.content)
        print("\n" + "-" * 50)

        return {"final_answer": "".join(chunks)}

    def _should_call_tools(self, state: AgentState) -> str:
        last_msg = state["messages"][-1]
        if self._parse_need_search(last_msg.content):
            logger.info("🛠️ Tools required (per plan).")
            return "continue"
        logger.info("✅ No tools needed.")
        return "end"

    # --- Public Run ---
    async def run(self, query: str, history: List[BaseMessage]) -> Dict[str, Any]:
        """Run the agent and return the final state"""
        messages = history + [HumanMessage(content=query)]
        final_state = await self.graph.ainvoke({"messages": messages})
        return final_state
    
    async def run_with_streaming(self, query: str, history: List[BaseMessage]) -> None:
        """Run the agent with streaming output for console use"""
        messages = history + [HumanMessage(content=query)]
        async for event in self.graph.astream({"messages": messages}):
            if "think" in event:
                print(f"\n🤔 Plan:\n{event['think']['messages'][-1].content}\n")

    async def stream_phases(self, query: str, history: List[BaseMessage], user_id: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Yield structured streaming events for frontend consumption.
        Event types:
          intent_detected, thinking_start, thinking_delta, thinking_complete,
          answer_start, answer_delta, answer_complete
        """
        # Build history text and conversation list for intent classification
        history_lines = []
        conversation_history = []
        for m in history:
            role = "User" if isinstance(m, HumanMessage) else "Tutor"
            history_lines.append(f"{role}: {m.content}")
            conversation_history.append({
                "role": "user" if isinstance(m, HumanMessage) else "assistant",
                "content": m.content
            })
        history_text = "\n".join(history_lines)

        # ---- PHASE 3: INTENT CLASSIFICATION ----
        intent_result = None
        thinking_prompt_text = self.think_prompt
        answer_prompt_text = self.answer_prompt
        user_context = {}

        if self.enable_dynamic_prompts and self.intent_classifier and self.prompt_manager:
            try:
                logger.info("🎯 Classifying user intent...")
                intent_result = await self.intent_classifier.classify(query, conversation_history)

                # Yield intent detection event
                yield {
                    "type": "intent_detected",
                    "intent": str(intent_result.intent),
                    "confidence": intent_result.confidence,
                    "domain": str(intent_result.domain),
                    "thinking_level": str(intent_result.thinking_level)
                }

                # Get user context from Memori if available
                if self.memori_engine and user_id:
                    try:
                        # TODO: Add method to get user context from Memori
                        # For now, use empty context
                        user_context = {
                            "learning_history": [],
                            "preferences": {}
                        }
                    except Exception as e:
                        logger.warning(f"Could not fetch user context from Memori: {e}")

                # Get dynamic prompts based on intent
                thinking_prompt_text, answer_prompt_text = self.prompt_manager.get_prompts(
                    intent_result,
                    query,
                    user_context
                )

                logger.info(f"✅ Using dynamic prompts for intent: {intent_result.intent.name}")

            except Exception as e:
                logger.error(f"❌ Intent classification failed: {e}")
                logger.info("Falling back to static prompts")
                intent_result = None

        # Determine if we should skip thinking phase
        skip_thinking = (
            intent_result and
            intent_result.thinking_level == ThinkingLevel.NONE and
            thinking_prompt_text == ""  # Dynamic prompt returned empty thinking prompt
        )

        # ---- THINKING PHASE ----
        think_prompt_text = thinking_prompt_text if isinstance(thinking_prompt_text, str) else self.think_prompt.format(chat_history=history_text)
        system_msg = SystemMessage(content=think_prompt_text)
        user_msg = HumanMessage(content=query)

        # Skip thinking phase for quick answers (ThinkingLevel.NONE)
        think_accum = ""
        if skip_thinking:
            logger.info("⚡ Skipping thinking phase (quick answer mode)")
            yield {"type": "thinking_start"}
            yield {"type": "thinking_complete", "thinking_content": ""}
            plan_full = ""
        else:
            yield {"type": "thinking_start"}
            inside_think = False
            try:
                async for chunk in self.llm.astream([system_msg, user_msg]):
                    token = getattr(chunk, "content", "")
                    if not token:
                        continue
                    think_accum += token
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
            except Exception as e:
                logger.exception("Thinking phase streaming failed: %s", e)

            match = re.search(r"<THINK>(.*?)</THINK>", think_accum, re.DOTALL)
            plan_core = match.group(1).strip() if match else think_accum.strip()

            # Optional tool use (expanded for MCP tools)
            need_search = bool(re.search(r"NEED_SEARCH:\s*yes", think_accum, re.IGNORECASE))
            need_time = bool(re.search(r"NEED_TIME:\s*yes", think_accum, re.IGNORECASE))
            need_weather = bool(re.search(r"NEED_WEATHER:\s*yes", think_accum, re.IGNORECASE))
            search_block = ""
            extra_blocks: List[str] = []
            if need_search:
                search_query_match = re.search(r"SEARCH_QUERY:\s*(.*)", think_accum, re.IGNORECASE)
                search_query = (search_query_match.group(1).strip() if search_query_match else query) or query
                try:
                    tool_res = self._call_mcp_tool("search", {"query": search_query, "max_results": 5})
                    if not isinstance(tool_res, str):
                        tool_res = json.dumps(tool_res, ensure_ascii=False)[:4000]
                except Exception as e:
                    tool_res = f"[Search Error] {e}"
                search_block = f"\n\n<SEARCH_RESULTS>\nQuery: {search_query}\n{tool_res}\n</SEARCH_RESULTS>"
            # memory block
            with suppress(Exception):
                mem = self._call_mcp_tool("memory_search", {"query": query, "k": 5, "scope": "both"})
                extra_blocks.append(f"<MEMORY_RESULTS>\n{json.dumps(mem, ensure_ascii=False)[:4000]}\n</MEMORY_RESULTS>")
            if need_time:
                timezone_match = re.search(r"TIMEZONE:\s*([^\n]+)", think_accum, re.IGNORECASE)
                timezone = timezone_match.group(1).strip() if timezone_match else None
                with suppress(Exception):
                    res = self._call_mcp_tool("time", {"timezone": timezone} if timezone else {})
                    extra_blocks.append(f"<TIME_RESULT>\n{json.dumps(res, ensure_ascii=False)}\n</TIME_RESULT>")
            if need_weather:
                weather_loc_match = re.search(r"WEATHER_LOCATION:\s*([^\n]+)", think_accum, re.IGNORECASE)
                weather_loc = weather_loc_match.group(1).strip() if weather_loc_match else query
                with suppress(Exception):
                    res = self._call_mcp_tool("weather", {"location": weather_loc})
                    extra_blocks.append(f"<WEATHER_RESULT>\n{json.dumps(res, ensure_ascii=False)[:4000]}\n</WEATHER_RESULT>")
            search_block += ("\n" + "\n".join(extra_blocks)) if extra_blocks else ""
            plan_full = plan_core + search_block
            yield {"type": "thinking_complete", "thinking_content": plan_full}

        # ---- ANSWER PHASE ----
        # Use dynamic answer prompt if available, otherwise use static prompt
        if answer_prompt_text and answer_prompt_text != self.answer_prompt:
            # Dynamic prompt (doesn't need plan parameter since it's already embedded)
            final_answer_prompt = answer_prompt_text
        else:
            # Static prompt (needs plan and chat_history parameters)
            final_answer_prompt = self.answer_prompt.format(plan=plan_full, chat_history=history_text)

        answer_system = SystemMessage(content=final_answer_prompt)
        yield {"type": "answer_start"}
        answer_accum = ""
        inside_answer = False
        try:
            async for chunk in self.llm.astream([answer_system]):
                token = getattr(chunk, "content", "")
                if not token:
                    continue
                answer_accum += token
                if "<ANSWER>" in token:
                    inside_answer = True
                    token = token.split("<ANSWER>", 1)[-1]
                if "</ANSWER>" in token:
                    before_close, _ = token.split("</ANSWER>", 1)
                    if inside_answer and before_close:
                        yield {"type": "answer_delta", "delta": before_close}
                    inside_answer = False
                    continue
                if inside_answer and token:
                    yield {"type": "answer_delta", "delta": token}
        except Exception as e:
            logger.exception("Answer phase streaming failed: %s", e)

        ans_match = re.search(r"<ANSWER>(.*?)</ANSWER>", answer_accum, re.DOTALL)
        final_answer = ans_match.group(1).strip() if ans_match else answer_accum.strip()
        yield {"type": "answer_complete", "response": final_answer, "thinking_content": plan_full}

    # NEW: helper to call MCP tools
    def _call_mcp_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        if not self.mcp_client or not self.mcp_client.alive:
            raise RuntimeError("MCP client not running")
        return self.mcp_client.call_tool(name, arguments)

    # MEMORI INTEGRATION METHODS
    def store_conversation_memory(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a conversation in Memori for long-term memory extraction.

        Memori will automatically:
        - Extract facts, preferences, and skills from the conversation
        - Build entity relationships
        - Make memories available for future context injection

        Args:
            user_id: User identifier
            user_message: User's message
            assistant_response: AI tutor's response
            metadata: Optional metadata (topic_id, timestamp, etc.)

        Returns:
            Storage confirmation
        """
        if not self.memori_engine:
            logger.debug("Memori not enabled, skipping memory storage")
            return {"status": "skipped", "reason": "memori_disabled"}

        try:
            result = self.memori_engine.store_conversation(
                user_id=user_id,
                user_message=user_message,
                assistant_response=assistant_response,
                metadata=metadata
            )
            logger.debug(f"✅ Stored conversation in Memori for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to store in Memori: {e}")
            return {"status": "error", "error": str(e)}

    def add_user_learning_preference(
        self,
        user_id: str,
        preference: str,
        category: str = "learning_preference"
    ) -> Dict[str, Any]:
        """
        Explicitly store a user's learning preference in Memori.

        Args:
            user_id: User identifier
            preference: Preference description
            category: Category of preference

        Returns:
            Storage confirmation
        """
        if not self.memori_engine:
            return {"status": "skipped", "reason": "memori_disabled"}

        try:
            result = self.memori_engine.add_user_preference(
                user_id=user_id,
                preference=preference,
                category=category
            )
            logger.info(f"✅ Added learning preference for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to add preference: {e}")
            return {"status": "error", "error": str(e)}


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
