# In state.py, define what the agent carries from node to node.

# Keys needed: question, generation, web_search (boolean), documents (list), and your trust_score_breakdown (dictionary).
from typing import List, TypedDict

class GraphState(TypedDict):
    """
    Represents the state of our professional investigator.
    """
    question: str            # User's query
    generation: str          # Final LLM response
    web_search: str          # Binary: "yes" or "no"
    documents: List[str]     # Retrieved resume chunks
    trust_score: dict        # { "score": 85, "reasoning": "..." }
