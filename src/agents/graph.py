from langgraph.graph import END, StateGraph
from .nodes import router_node, retriever_node, grader_node, generator_node, web_search_node
from .state import GraphState

def build_workflow():
    workflow = StateGraph(GraphState)

    # 1. Add All Nodes
    workflow.add_node("router", router_node)
    workflow.add_node("retrieve", retriever_node)
    workflow.add_node("grade_documents", grader_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("generate", generator_node)

    # 2. Define Routing Logic Functions (CRITICAL FIX)
    def select_next_node(state):
        # This function MUST return a string, never a dict.
        return state.get("web_search", "chat")

    def decide_to_verify(state):
        # This function MUST return a string, never a dict.
        return state.get("web_search", "no")

    # 3. Build Logic
    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        select_next_node, # No lambda, just the function name
        {
            "resume_search": "retrieve",
            "web_search": "web_search",
            "chat": "generate",
        },
    )

    workflow.add_edge("retrieve", "grade_documents")

    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_verify,
        {
            "yes": "generate",
            "no": "web_search",
        },
    )

    workflow.add_edge("web_search", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()