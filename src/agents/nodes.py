from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.tools.search import get_web_search_tool

# 1. Local Setup
llm = ChatOllama(model="mistral", temperature=0)
llm_json = ChatOllama(model="mistral", format="json", temperature=0) # Specific for JSON routing
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings, collection_name="veritas_resumes")

# 2. The Router Node (The Decision Maker)
def router_node(state):
    print("--- ROUTING QUERY ---")
    question = state["question"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a precise recruitment router. 
        Your goal is to decide the next step. 
        Return ONLY a JSON with the key 'route_to' and one of these values:
        - 'resume_search' (for skills, stats, experience)
        - 'web_search' (for verification or online search)
        - 'chat' (for greetings)"""),
        ("human", "{question}")
    ])
    
    # Ensure you are using the JSON-enabled LLM
    chain = prompt | llm_json | JsonOutputParser()
    
    try:
        result = chain.invoke({"question": question})
        # We extract the STRING value from the LLM's JSON response
        decision = result.get("route_to", "chat")
    except Exception:
        decision = "chat"
        
    # We update the state with a string value
    return {"web_search": decision}

# 3. The Retriever Node
def retriever_node(state):
    print("--- RETRIEVING FROM RESUME ---")
    question = state["question"]
    documents = vectorstore.similarity_search(question, k=6)
    return {"documents": [d.page_content for d in documents]}

# 4. The Grader Node
def grader_node(state):
    print("--- CHECKING DOCUMENT RELEVANCE ---")
    docs = state["documents"]
    # Logic: If no relevant docs found in resume, set web_search to 'no' to trigger fallback
    return {"web_search": "yes" if docs else "no"}

# 5. The Detective Node
# Inside src/agents/nodes.py

def web_search_node(state):
    print("--- VERIFYING CLAIMS ON THE WEB ---")
    question = state["question"]
    docs = state.get("documents", []) # Information from the resume

    search = get_web_search_tool()
    
    # 1. We ask the LLM to generate a "Verification Query"
    # It uses the resume data to create a targeted search
    verification_prompt = f"""
    Based on this resume data: {docs}
    The user wants to know: {question}
    Generate a search query to find proof (GitHub, Portfolio, LinkedIn) that this candidate actually built these projects.
    """
    
    search_query = llm.invoke(verification_prompt).content
    
    # 2. Execute the targeted search
    search_result = search.invoke(search_query)
    
    docs.append(f"EXTERNAL VERIFICATION RESULT: {search_result}")
    return {"documents": docs, "web_search": "done"}

# 6. The Generator Node
def generator_node(state):
    print("--- GENERATING AUDIT REPORT ---")
    question = state["question"]
    docs = state.get("documents", [])
    has_web_data = state.get("web_search") == "done"
    
    # 1. Verification Logic
    # We look for 'EXTERNAL VERIFICATION RESULT' in the docs to see if web search was hit
    web_results = [d for d in docs if "EXTERNAL VERIFICATION RESULT" in d]
    resume_content = [d for d in docs if "EXTERNAL VERIFICATION RESULT" not in d]

    # Simple logic: If we have a project claim but web search returned 'no results' or generic info
    is_verified = False
    if has_web_data and web_results:
        # If the web result contains the candidate's name or specific project keywords
        if "Nishita" in str(web_results) or "GitHub" in str(web_results):
            is_verified = True

    # 2. Assigning the 'Fishy' Score
    if has_web_data and not is_verified:
        score = 40
        label = "⚠️ Unverified / Suspicious"
        reasoning = "Candidate claims this project/skill, but no external digital footprint or source code was found. Links are missing from the resume."
    elif is_verified:
        score = 95
        label = "✅ Verified"
        reasoning = "Project claims match external records or public profiles."
    else:
        score = 80
        label = "Internal Match"
        reasoning = "Information exists in resume but external verification was not performed."

    # 3. Prompting for a 'Summary' style answer
    prompt = f"""Context: {docs}
    Answer the HR: {question}
    If there are missing links for projects or skills like JavaScript mentioned without projects, point it out explicitly."""
    
    response = llm.invoke(prompt)
    
    return {
        "generation": response.content,
        "trust_score": {"score": score, "label": label, "reasoning": reasoning}
    }