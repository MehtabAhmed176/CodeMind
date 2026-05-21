from src.db import db
from src.ingest import ingest_directory
from src.query import query_codebase
from src.memory import clear_session
import sys
import uuid

# Generate unique session id for this run
session_id = str(uuid.uuid4())
clear_session(session_id)

# Check if --reingest flag was passed
reingest = "--reingest" in sys.argv

if reingest:
    print("Reingesting codebase...")
    db.query("MATCH (n) DETACH DELETE n")
    ingest_directory("codemind", "src")
else:
    print("Using existing graph. Run with --reingest to rebuild.")

print(f"\n--- CodeMind is ready. Session: {session_id[:8]} ---")
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