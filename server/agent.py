import asyncio
import logging
import re
from typing import Sequence, TypedDict, Annotated, List, Any, Dict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from tools import create_search_tool

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
        self.tools = [create_search_tool()]

        self.think_prompt = """
You are an expert tutor for Math and Coding in PHASE 1: PLANNING.

Output reasoning inside <THINK></THINK> tags.
At the end of the THINK block include:
NEED_SEARCH: yes|no
SEARCH_QUERY: <best short query or empty>

Conversation History:
{chat_history}
"""

        self.answer_prompt = """
You are an expert tutor for Math and Coding in PHASE 2: FINAL ANSWER.

Generate the final solution based on your plan and the conversation history.

Guidelines:
- For Math: step-by-step derivations, formulas, units.
- For Coding: clean code, explain logic, time/space complexity.

Plan from Phase 1:
{plan}

Conversation History:
{chat_history}

Output only inside <ANSWER> tags.
"""

        self.graph = self._build_graph()
        logger.info("✅ TutorAgent initialized successfully.")

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
        logger.info("🔍 Running search tool...")
        plan = self._extract_plan(state)
        query = self._parse_search_query(plan) or next(
            (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
            ""
        )
        try:
            results = self.tools[0].invoke({"query": query})
            results_text = results if isinstance(results, str) else str(results)
        except Exception as e:
            logger.exception("❌ Search tool failed")
            results_text = f"[Search Error] {e}"
        return {"messages": [SystemMessage(content=f"<SEARCH_RESULTS>\nQuery: {query}\n{results_text}\n</SEARCH_RESULTS>")]}

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
