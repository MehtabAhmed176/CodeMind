from src.db import db
from src.ingest import ingest_directory
from src.query import query_codebase
from src.memory import clear_session
import sys
import uuid

# Parse flags
reingest = "--reingest" in sys.argv
no_chat = "--no-chat" in sys.argv

# Generate unique session id for this run
session_id = str(uuid.uuid4())
clear_session(session_id)

if reingest:
    print("Reingesting codebase...")
    db.query("MATCH (n) DETACH DELETE n")
    ingest_directory("codemind", "src")
else:
    node_count = db.query("MATCH (n) RETURN count(n) AS count")[0]["count"]
    if node_count == 0:
        print("Graph is empty — reingesting automatically...")
        ingest_directory("codemind", "src")
    else:
        print("Using existing graph. Run with --reingest to rebuild.")

if no_chat:
    print("CI mode — skipping chat loop")
    db.close()
else:
    print("\n--- CodeMind is ready. Ask anything about your codebase ---")
    print("--- Type 'exit' to quit ---\n")

    while True:
        question = input("You: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            continue

        answer = query_codebase(question, session_id)
        print(f"\nCodeMind: {answer}\n")
        print("-" * 50)

    db.close()