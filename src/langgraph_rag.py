"""
LangGraph & LangChain Educational Agentic RAG Workflow
Demonstrates stateful agent loops, document grading, and self-correction.
"""

from typing import Dict, Any, List, Optional, TypedDict
from src.jd_parser import HeuristicJDParser, ParsedJobDescription
from src.store import VectorStore
from src.generator import CareerRAGGenerator


class AgenticState(TypedDict):
    """
    State object passed between LangGraph nodes.
    Maintains workflow context across steps.
    """
    jd_text: str
    parsed_jd: Optional[ParsedJobDescription]
    search_query: str
    retrieved_chunks: List[Dict[str, Any]]
    relevance_score: float
    retry_count: int
    final_output: str


class LangGraphCareerAgent:
    """
    Educational LangGraph-style Agentic RAG Pipeline.
    Implements: Node 1 (JD Parse) -> Node 2 (Vector Search) -> Node 3 (Grade & Check) -> Conditional Self-Correction Loop -> Node 4 (LLM Synthesis).
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.jd_parser = HeuristicJDParser()
        self.generator = CareerRAGGenerator()

    def node_analyze_jd(self, state: AgenticState) -> AgenticState:
        print("\n🔵 [LangGraph Node 1: Analyze JD Requirements]")
        parsed_jd = self.jd_parser.parse(state["jd_text"])
        state["parsed_jd"] = parsed_jd
        state["search_query"] = f"{parsed_jd.title} requiring {', '.join(parsed_jd.required_skills[:5])}"
        print(f" -> Extracted Target Skills: {parsed_jd.required_skills}")
        return state

    def node_retrieve_chunks(self, state: AgenticState) -> AgenticState:
        print(f"\n🔵 [LangGraph Node 2: Vector Store Search (Query: '{state['search_query']}')]")
        results = self.vector_store.search(state["search_query"], top_k=4)
        state["retrieved_chunks"] = results
        print(f" -> Retrieved {len(results)} chunks.")
        return state

    def node_grade_documents(self, state: AgenticState) -> AgenticState:
        print("\n🔵 [LangGraph Node 3: Grading Retrieved Context Relevance]")
        chunks = state["retrieved_chunks"]
        if not chunks:
            state["relevance_score"] = 0.0
            return state

        avg_score = sum(c["similarity_score"] for c in chunks) / len(chunks)
        state["relevance_score"] = round(avg_score, 4)
        print(f" -> Context Relevance Score: {state['relevance_score']}")
        return state

    def node_rewrite_query(self, state: AgenticState) -> AgenticState:
        print("\n🔄 [LangGraph Self-Correction Node: Rewriting Search Query]")
        state["retry_count"] += 1
        parsed_jd = state["parsed_jd"]
        # Expand search query with fallback terms
        state["search_query"] = f"experience building scalable software with {', '.join(parsed_jd.required_skills[-3:]) if parsed_jd else 'Python'}"
        print(f" -> New Rewritten Query (Attempt #{state['retry_count']}): '{state['search_query']}'")
        return state

    def node_generate_synthesis(self, state: AgenticState) -> AgenticState:
        print("\n🔵 [LangGraph Node 4: LLM Synthesis Engine]")
        out = self.generator.generate_tailored_content(state["parsed_jd"], state["retrieved_chunks"])
        state["final_output"] = out
        return state

    def execute(self, jd_text: str) -> AgenticState:
        """
        Executes the LangGraph Agentic Loop.
        """
        print("\n================ STARTING LANGGRAPH AGENTIC RAG FLOW ================")
        state: AgenticState = {
            "jd_text": jd_text,
            "parsed_jd": None,
            "search_query": "",
            "retrieved_chunks": [],
            "relevance_score": 0.0,
            "retry_count": 0,
            "final_output": ""
        }

        # Step 1: Analyze JD
        state = self.node_analyze_jd(state)

        # Step 2: Retrieve
        state = self.node_retrieve_chunks(state)

        # Step 3: Grade Documents
        state = self.node_grade_documents(state)

        # Conditional Edge: Self-Correction loop if relevance is too low (< 0.25)
        MAX_RETRIES = 2
        while state["relevance_score"] < 0.25 and state["retry_count"] < MAX_RETRIES:
            state = self.node_rewrite_query(state)
            state = self.node_retrieve_chunks(state)
            state = self.node_grade_documents(state)

        # Step 4: Final Synthesis
        state = self.node_generate_synthesis(state)

        print("\n================ LANGGRAPH AGENTIC RAG FLOW COMPLETED ================")
        return state
