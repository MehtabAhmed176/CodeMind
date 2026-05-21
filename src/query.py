from src.db import db
from src.llm import ask
from src.memory import save_message, get_context_summary


def query_codebase(question: str, session_id: str) -> str:
    """Main entry point — takes a question, returns an answer"""

    # Step 1 — get conversation history from Redis
    history = get_context_summary(session_id)

    # Step 2 — extract keywords from question
    keywords = extract_keywords(question)

    # Step 3 — find relevant nodes in graph
    context = build_context(keywords)

    # Step 4 — send history + context + question to Ollama
    answer = ask(context, question, history)

    # Step 5 — save question and answer to Redis
    save_message(session_id, "user", question)
    save_message(session_id, "assistant", answer)

    return answer


def extract_keywords(question: str) -> list:
    """Extract meaningful words from the question"""
    stopwords = ["what", "how", "does", "is", "the", "a", "an",
                 "in", "of", "to", "and", "or", "it", "this",
                 "do", "did", "can", "where", "which", "who",
                 "define", "defined", "about", "tell", "me",
                 "show", "list", "give", "explain"]

    words = question.lower().replace("?", "").split()
    keywords = [w for w in words if w not in stopwords]

    return keywords


def build_context(keywords: list) -> str:
    """Query Neo4j graph and build context string for LLM"""
    context_parts = []

    for keyword in keywords:
        results = db.query("""
            MATCH (n)
            WHERE toLower(n.name) CONTAINS toLower($keyword)
               OR toLower(n.path) CONTAINS toLower($keyword)
            OPTIONAL MATCH (n)-[r]->(related)
            OPTIONAL MATCH (parent)-[r2]->(n)
            RETURN labels(n) AS type,
                   n.name AS name,
                   n.path AS path,
                   type(r) AS relationship,
                   related.name AS related_name,
                   labels(related) AS related_type,
                   labels(parent) AS parent_type,
                   parent.name AS parent_name,
                   type(r2) AS parent_relationship
            LIMIT 20
        """, {"keyword": keyword})

        for row in results:
            node_type = row["type"][0] if row["type"] else "Unknown"
            name = row["name"] or row["path"] or "unnamed"

            line = f"{node_type}: {name}"

            if row["relationship"] and row["related_name"]:
                related_type = row["related_type"][0] if row["related_type"] else ""
                line += f" → {row['relationship']} → {related_type}: {row['related_name']}"

            if row["parent_relationship"] and row["parent_name"]:
                parent_type = row["parent_type"][0] if row["parent_type"] else ""
                line = f"{parent_type}: {row['parent_name']} → {row['parent_relationship']} → {line}"

            context_parts.append(line)

    unique_parts = list(set(context_parts))

    if not unique_parts:
        return "No relevant code found for this question."

    return "\n".join(unique_parts)