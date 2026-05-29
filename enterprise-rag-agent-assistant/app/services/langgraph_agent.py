from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.services.agent_router import AgentRouter
from app.services.tool_executor import ToolExecutor
from app.utils.logger import get_logger


logger = get_logger(__name__)

# Experimental only. The mainline Agent flow lives in app.services.agent_service.


class LangGraphAgentState(TypedDict, total=False):
    """
    LangGraph Agent workflow state.

    This state is passed between all graph nodes.
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


class LangGraphAgent:
    """
    Minimal LangGraph-based Agent.

    Flow:
        router_node
            -> conditional edge
            -> rag_node / summary_node / writing_node / chat_node
            -> final_node
            -> END
    """

    def __init__(self) -> None:
        self.router = AgentRouter()
        self.executor = ToolExecutor()
        self.graph = self._build_graph()

    def _build_graph(self):
        """
        Build and compile the LangGraph workflow.
        """
        workflow = StateGraph(LangGraphAgentState)

        workflow.add_node("router", self.router_node)
        workflow.add_node("rag", self.rag_node)
        workflow.add_node("summary", self.summary_node)
        workflow.add_node("writing", self.writing_node)
        workflow.add_node("chat", self.chat_node)
        workflow.add_node("final", self.final_node)

        workflow.set_entry_point("router")

        workflow.add_conditional_edges(
            "router",
            self.route_by_intent,
            {
                "rag": "rag",
                "summary": "summary",
                "writing": "writing",
                "chat": "chat",
            },
        )

        workflow.add_edge("rag", "final")
        workflow.add_edge("summary", "final")
        workflow.add_edge("writing", "final")
        workflow.add_edge("chat", "final")
        workflow.add_edge("final", END)

        return workflow.compile()

    def run(
        self,
        question: str,
        db: Session,
        top_k: int | None = None,
    ) -> LangGraphAgentState:
        """
        Run the compiled LangGraph workflow.
        """
        initial_state: LangGraphAgentState = {
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

        final_state = self.graph.invoke(initial_state)

        return final_state

    def router_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """
        Router node.

        Decide user intent and update state.
        """
        question = state.get("question", "")

        try:
            route_result = self.router.route(question)

            state["intent"] = route_result.get("intent", "general_chat")
            state["reason"] = route_result.get("reason", "")

            logger.info(
                "langgraph router_node completed | intent=%s | reason=%s",
                state["intent"],
                state["reason"],
            )

        except Exception as exc:
            logger.exception(
                "langgraph router_node failed | error=%s",
                str(exc),
            )

            state["intent"] = "general_chat"
            state["reason"] = "Router failed. Fallback to general_chat."
            state["error"] = f"router_node failed: {str(exc)}"

        return state

    def route_by_intent(self, state: LangGraphAgentState) -> str:
        """
        LangGraph conditional edge.

        Return the next route key according to intent.
        """
        intent = state.get("intent")

        if intent == "document_qa":
            next_route = "rag"
        elif intent == "summary":
            next_route = "summary"
        elif intent == "writing":
            next_route = "writing"
        elif intent == "general_chat":
            next_route = "chat"
        else:
            logger.warning(
                "Unknown intent in langgraph route_by_intent | intent=%s",
                intent,
            )
            next_route = "chat"

        logger.info(
            "langgraph conditional edge selected | intent=%s | next_route=%s",
            intent,
            next_route,
        )

        return next_route

    def rag_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """
        Execute RAG tool.
        """
        return self._execute_tool_node(state, expected_intent="document_qa")

    def summary_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """
        Execute summary tool.
        """
        return self._execute_tool_node(state, expected_intent="summary")

    def writing_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """
        Execute writing tool.
        """
        return self._execute_tool_node(state, expected_intent="writing")

    def chat_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """
        Execute general chat tool.
        """
        return self._execute_tool_node(state, expected_intent="general_chat")

    def _execute_tool_node(
        self,
        state: LangGraphAgentState,
        expected_intent: str,
    ) -> LangGraphAgentState:
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
                "langgraph tool node completed | intent=%s | tool_used=%s | error=%s",
                expected_intent,
                state["tool_used"],
                state["error"],
            )

        except Exception as exc:
            logger.exception(
                "langgraph tool node failed | intent=%s | error=%s",
                expected_intent,
                str(exc),
            )

            state["tool_used"] = None
            state["answer"] = ""
            state["sources"] = []
            state["error"] = f"{expected_intent} node failed: {str(exc)}"

        return state

    def final_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """
        Final formatting node.
        """
        if not state.get("answer") and state.get("error"):
            state["answer"] = ""

        if state.get("sources") is None:
            state["sources"] = []

        logger.info(
            "langgraph final_node completed | intent=%s | tool_used=%s | error=%s",
            state.get("intent"),
            state.get("tool_used"),
            state.get("error"),
        )

        return state
