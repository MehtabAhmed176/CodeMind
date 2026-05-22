import json
import ollama
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
    """Use Ollama to extract relevant code entity names from the question"""

    prompt = f"""Extract code search terms from this question about a Python codebase.
Return a JSON array of strings. Always return at least 3 terms.
Include class names, function names, file names, and concept words.

Question: "{question}"

Examples:
"How does the database connection get initialized?" -> ["Neo4jConnection", "__init__", "db", "database", "connect", "driver"]
"What does AuthService do?" -> ["AuthService", "auth", "login", "token"]
"Which files deal with memory?" -> ["memory", "redis", "session", "cache"]
"What breaks if I remove neo4j?" -> ["neo4j", "Neo4jConnection", "db", "driver"]

Return ONLY the JSON array, nothing else:"""

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response["message"]["content"].strip()
    # Strip markdown code blocks if present
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        keywords = json.loads(raw)
        if isinstance(keywords, list) and len(keywords) > 0:
            return [str(k) for k in keywords]
    except json.JSONDecodeError:
        pass

    # Fallback
    words = question.lower().replace("?", "").split()
    stopwords = ["what", "how", "does", "is", "the", "a", "an",
                 "in", "of", "to", "and", "or", "it", "this",
                 "do", "did", "can", "where", "which", "who",
                 "define", "defined", "about", "tell", "me",
                 "show", "list", "give", "explain"]
    return [w for w in words if w not in stopwords]

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