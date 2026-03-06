from database import search_vtt_lines, semantic_search_vtt_lines
from models import SearchResult
from sentence_transformers import SentenceTransformer

if __name__ == "__main__":
    query = "etwas ist parallel zur antenned"

    # --- Fuzzy search (pg_trgm) ---
    print("=== Fuzzy Search ===")
    results: list[SearchResult] = search_vtt_lines(query=query, limit=5)
    for r in results:
        print(f"[{r.similarity:.3f}] Lecture {r.lecture_id}, Line {r.line_number}: {r.content}")

    # --- Semantic search (pgvector) ---
    print("\n=== Semantic Search ===")
    model = SentenceTransformer("BAAI/bge-m3")
    query_embedding = model.encode(query).tolist()
    results = semantic_search_vtt_lines(query_embedding=query_embedding, limit=5)
    for r in results:
        print(f"[{r.similarity:.3f}] Lecture {r.lecture_id}, Line {r.line_number}: {r.content}")
        if r.context:
            print(f"  Context: {r.context}")
        print()