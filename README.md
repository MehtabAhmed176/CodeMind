# CodeMind 🧠

> **Status: Active Development** — Core GraphRAG engine working. Agent memory, evaluation pipeline, and API layer in progress.

A GraphRAG-powered codebase intelligence engine. Ask natural language questions about any Python codebase and get accurate, relationship-aware answers — backed by a knowledge graph, not just vector similarity.

---

## The Problem With Plain RAG on Code

Standard RAG splits code into chunks and finds semantically similar ones. It has no concept of relationships.

Ask *"what breaks if I delete UserRepository?"* and it returns random chunks mentioning the word "user". It misses the fact that `AuthService` calls `UserRepository` which queries the database — because that's a **graph problem**, not a text similarity problem.

CodeMind solves this with GraphRAG: graph traversal first, semantic retrieval second.

---

## How It Works

```
Codebase ingested
    → AST parser extracts classes, functions, imports
    → Knowledge graph built in Neo4j
    → Nodes: Repository, File, Class, Function, Dependency
    → Edges: CONTAINS, DEFINES, CALLS, IMPORTS

User asks a question
    → Keywords extracted
    → Neo4j graph traversed for relevant nodes + relationships
    → Structured context built from graph data
    → Injected into Ollama LLM prompt
    → Answer grounded in real codebase structure
```

---

## Features

- **Knowledge Graph** — Neo4j graph of entire codebase structure
- **AST Parsing** — extracts classes, functions, call graphs, and imports automatically
- **GraphRAG Engine** — graph traversal drives context retrieval, not just vector similarity
- **Session Memory** — Redis-backed conversation history, agent remembers what you explored
- **Fully Local** — runs entirely on machine via Ollama and Docker, no API costs
- **CLI Interface** — interactive chat loop with `--reingest` flag to rebuild the graph

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   CodeMind                      │
├──────────────┬──────────────────┬───────────────┤
│  Ingestion   │   Query Engine   │    Memory     │
│              │                  │               │
│  AST Parser  │  Graph Traversal │  Redis        │
│      ↓       │       ↓          │  Session      │
│  Neo4j Graph │  Context Builder │  History      │
│              │       ↓          │               │
│  CONTAINS    │  Ollama LLM      │               │
│  DEFINES     │                  │               │
│  CALLS       │                  │               │
│  IMPORTS     │                  │               │
└──────────────┴──────────────────┴───────────────┘
```

---

## Tech Stack


| Layer           | Technology          |
| --------------- | ------------------- |
| Knowledge Graph | Neo4j 5             |
| LLM             | Ollama (llama3.2)   |
| Session Memory  | Redis 7             |
| AST Parsing     | Python `ast` module |
| Infrastructure  | Docker Compose      |
| Language        | Python 3.11         |


---

## Getting Started

**Prerequisites:** Docker, Python 3.11+, Ollama

```bash
# 1. Clone the repo
git clone https://github.com/MehtabAhmed176/CodeMind.git
cd codemind

# 2. Start Neo4j and Redis
docker-compose up -d

# 3. Pull the LLM
ollama pull llama3.2

# 4. Set up Python environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 5. Install dependencies
pip install -r requirements.txt

# 6. Configure environment
cp .env.example .env
# Edit .env with your Neo4j credentials

# 7. Ingest your codebase and start chatting
python main.py --reingest
```

---

## Usage

```bash
# Start with existing graph
python main.py

# Rebuild graph from scratch
python main.py --reingest
```

**Example questions:**

```
You: What does AuthService do?
You: Which functions does login call?
You: What does db.py depend on?
You: What breaks if I remove neo4j?
You: Summarize what we discussed so far
```

---

## Roadmap

- Knowledge graph ontology design
- AST ingestion pipeline
- GraphRAG query engine
- Session memory with Redis
- IMPORTS edge detection
- Qdrant vector store for semantic search
- Long term persistent memory across sessions
- Context engineering improvements
- Retrieval evaluation pipeline (Ragas)
- FastAPI REST layer
- Multi-language support (JavaScript/TypeScript)
- Next.js graph visualizer frontend

---

## Project Structure

```
codemind/
├── src/
│   ├── auth.py          # example codebase for testing
│   ├── db.py            # Neo4j connection layer
│   ├── ingest.py        # AST parser + graph ingestion
│   ├── llm.py           # Ollama integration
│   ├── memory.py        # Redis session memory
│   └── query.py         # GraphRAG query engine
├── docker-compose.yml   # Neo4j + Redis
├── main.py              # CLI entry point
├── .env.example         # environment template
└── requirements.txt     # Python dependencies
```

---

## Background

Built to master: Knowledge Graphs · GraphRAG · Agent Memory · Context Engineering · Ontology Design · Retrieval Evaluation

Inspired by the insight that code is fundamentally a graph of relationships — and that treating it as a bag of text chunks throws away the most valuable information.

---

## Author

**Mehtab Ahmed** — Backend & Cloud Engineer
[GitHub](https://github.com/MehtabAhmed176) · [LinkedIn](https://www.linkedin.com/in/mehtabahmed1993/)