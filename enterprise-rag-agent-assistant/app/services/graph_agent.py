from typing import Any, TypedDict

from sqlalchemy.orm import Session

from app.services.agent_router import AgentRouter
from app.services.tool_executor import ToolExecutor
from app.utils.logger import get_logger


logger = get_logger(__name__)

# Experimental only. The mainline Agent flow lives in app.services.agent_service.


class AgentState(TypedDict, total=False):
    """
    Agent workflow state.

    You can understand it as a task sheet passed between nodes.
    """

    question: str
    top_k: int | None
    db: Session

    intent: str | None
    reason: str | None

    tool_used: str | None
    tool_result: dict[str, Any] | None

    answer: str | None
    sources: list[dict[str, Any]]
    error: str | None

class GraphAgent:
    """
    A minimal graph-style Agent.

    This is not LangGraph yet.
    It simulates the core idea of LangGraph:

    State -> router_node -> conditional branch -> tool_node -> final_node
    """

    def __init__(self) -> None:
        self.router = AgentRouter()
        self.executor = ToolExecutor()

    def run(
        self,
        question: str,
        db: Session,
        top_k: int | None = None,
    ) -> AgentState:
        """
        Run the graph-style Agent workflow.
        """
        state: AgentState = {
            "question": question,
            "top_k": top_k,
            "db": db,
            "intent": None,
            "reason": None,
            "tool_used": None,
            "tool_result": None,
            "answer": None,
            "sources": [],
            "error": None,
        }

        state = self.router_node(state)

        next_node = self.route_by_intent(state)

        if next_node == "rag_node":
            state = self.rag_node(state)
        elif next_node == "summary_node":
            state = self.summary_node(state)
        elif next_node == "writing_node":
            state = self.writing_node(state)
        elif next_node == "chat_node":
            state = self.chat_node(state)
        else:
            state["error"] = f"Unknown next node: {next_node}"

        state = self.final_node(state)

        return state
    
    def router_node(self, state: AgentState) -> AgentState:
        """
        Decide user intent.
        """
        question = state.get("question", "")

        try:
            route_result = self.router.route(question)

            state["intent"] = route_result.get("intent", "general_chat")
            state["reason"] = route_result.get("reason", "")

            logger.info(
                "graph router_node completed | intent=%s | reason=%s",
                state["intent"],
                state["reason"],
            )

        except Exception as exc:
            logger.exception("graph router_node failed | error=%s", str(exc))

            state["intent"] = "general_chat"
            state["reason"] = "Router failed. Fallback to general_chat."
            state["error"] = f"router_node failed: {str(exc)}"

        return state
    
    def route_by_intent(self, state: AgentState) -> str:
        """
        Conditional edge.

        Decide which node should run next according to intent.
        """
        intent = state.get("intent")

        if intent == "document_qa":
            return "rag_node"

        if intent == "summary":
            return "summary_node"

        if intent == "writing":
            return "writing_node"

        if intent == "general_chat":
            return "chat_node"

        logger.warning(
            "Unknown intent in graph route_by_intent | intent=%s",
            intent,
        )

        return "chat_node"
    
    def rag_node(self, state: AgentState) -> AgentState:
        """
        Execute RAG tool.
        """
        return self._execute_tool_node(state, expected_intent="document_qa")

    def summary_node(self, state: AgentState) -> AgentState:
        """
        Execute summary tool.
        """
        return self._execute_tool_node(state, expected_intent="summary")

    def writing_node(self, state: AgentState) -> AgentState:
        """
        Execute writing tool.
        """
        return self._execute_tool_node(state, expected_intent="writing")

    def chat_node(self, state: AgentState) -> AgentState:
        """
        Execute general chat tool.
        """
        return self._execute_tool_node(state, expected_intent="general_chat")
    
    def _execute_tool_node(
        self,
        state: AgentState,
        expected_intent: str,
    ) -> AgentState:
        """
        Execute tool by intent and update state.
        """
        question = state.get("question", "")
        db = state.get("db")
        top_k = state.get("top_k")

        try:
            if db is None:
                state["error"] = "Database session is required."
                return state

            tool_result = self.executor.execute(
                intent=expected_intent,
                question=question,
                db=db,
                top_k=top_k,
            )

            state["tool_result"] = tool_result
            state["tool_used"] = tool_result.get("tool_used")
            state["answer"] = tool_result.get("answer", "")
            state["sources"] = tool_result.get("sources", [])
            state["error"] = tool_result.get("error")

            logger.info(
                "graph tool node completed | intent=%s | tool_used=%s | error=%s",
                expected_intent,
                state["tool_used"],
                state["error"],
            )

        except Exception as exc:
            logger.exception(
                "graph tool node failed | intent=%s | error=%s",
                expected_intent,
                str(exc),
            )

            state["tool_used"] = None
            state["answer"] = ""
            state["sources"] = []
            state["error"] = f"{expected_intent} node failed: {str(exc)}"

        return state
        
    def final_node(self, state: AgentState) -> AgentState:
        """
        Final formatting node.

        This node is responsible for normalizing the final output.

        In a more complex Agent, this node could:
        - normalize answer format
        - add citations
        - rewrite final response
        - handle fallback messages
        - clean empty fields
        """
        if not state.get("answer") and state.get("error"):
            state["answer"] = ""

        if state.get("sources") is None:
            state["sources"] = []

        logger.info(
            "graph final_node completed | intent=%s | tool_used=%s | error=%s",
            state.get("intent"),
            state.get("tool_used"),
            state.get("error"),
        )

        return state
