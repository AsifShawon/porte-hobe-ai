import asyncio
import logging
import re
from typing import Sequence, TypedDict, Annotated, List, Any, Dict, AsyncGenerator
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

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("TutorAgent")


# --- Agent State ---
class AgentState(TypedDict):
    """The state that flows through the graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    final_answer: str


# --- Tutor Agent ---
class TutorAgent:
    """Two-phase reasoning tutor with tool-calling and streaming answers."""

    def __init__(self, model_name: str = "qwen2.5:3b-instruct-q5_K_M") -> None:
        logger.info(f"🚀 Initializing TutorAgent with model: {model_name}")

        self.llm = ChatOllama(model=model_name, temperature=0.1, stream=True)  # enable streaming
        self.tools = [create_search_tool()]  # legacy direct search tool
        # Initialize MCP client (for web_search, time, weather)
        self.mcp_client = MCPClient(start=True)

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
        # Always attempt legacy search if needed
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
        # SEARCH
        if need_search:
            try:
                results = self.tools[0].invoke({"query": query})
                results_text = results if isinstance(results, str) else json.dumps(results, ensure_ascii=False)[:4000]
            except Exception as e:
                logger.exception("❌ Search tool failed")
                results_text = f"[Search Error] {e}"
            blocks.append(f"<SEARCH_RESULTS>\nQuery: {query}\n{results_text}\n</SEARCH_RESULTS>")
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

    async def stream_phases(self, query: str, history: List[BaseMessage]) -> AsyncGenerator[Dict[str, Any], None]:
        """Yield structured streaming events for frontend consumption.
        Event types:
          thinking_start, thinking_delta, thinking_complete,
          answer_start, answer_delta, answer_complete
        """
        # Build history text
        history_lines = []
        for m in history:
            role = "User" if isinstance(m, HumanMessage) else "Tutor"
            history_lines.append(f"{role}: {m.content}")
        history_text = "\n".join(history_lines)

        # ---- THINKING PHASE ----
        think_prompt_text = self.think_prompt.format(chat_history=history_text)
        system_msg = SystemMessage(content=think_prompt_text)
        user_msg = HumanMessage(content=query)

        yield {"type": "thinking_start"}
        think_accum = ""
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
                tool_res = self.tools[0].invoke({"query": search_query})
                if not isinstance(tool_res, str):
                    tool_res = json.dumps(tool_res, ensure_ascii=False)[:4000]
            except Exception as e:
                tool_res = f"[Search Error] {e}"
            search_block = f"\n\n<SEARCH_RESULTS>\nQuery: {search_query}\n{tool_res}\n</SEARCH_RESULTS>"
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
        answer_prompt_text = self.answer_prompt.format(plan=plan_full, chat_history=history_text)
        answer_system = SystemMessage(content=answer_prompt_text)
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
