from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.db import db
from src.ingest import ingest_directory
from src.query import query_codebase
from src.memory import clear_session
import uuid

app = FastAPI(
    title="CodeMind API",
    description="GraphRAG-powered codebase intelligence engine",
    version="1.0.0"
)


# ── Request models ──

class IngestRequest(BaseModel):
    repo_name: str
    path: str
    clear_existing: bool = True


class QueryRequest(BaseModel):
    question: str
    session_id: str = None


# ── Routes ──

@app.get("/health")
def health():
    """Check if everything is running"""
    try:
        count = db.query("MATCH (n) RETURN count(n) AS count")[0]["count"]
        return {
            "status": "healthy",
            "neo4j": "connected",
            "graph_nodes": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {str(e)}")


@app.post("/ingest")
def ingest(request: IngestRequest):
    """Ingest a codebase into the knowledge graph"""
    try:
        if request.clear_existing:
            db.query("MATCH (n) DETACH DELETE n")

        ingest_directory(request.repo_name, request.path)

        count = db.query("MATCH (n) RETURN count(n) AS count")[0]["count"]

        return {
            "status": "success",
            "repo_name": request.repo_name,
            "path": request.path,
            "nodes_created": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
def query(request: QueryRequest):
    """Ask a question about the ingested codebase"""
    try:
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())

        answer = query_codebase(request.question, session_id)

        return {
            "question": request.question,
            "answer": answer,
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph")
def graph_stats():
    """Return knowledge graph statistics"""
    try:
        stats = db.query("""
            MATCH (n)
            RETURN labels(n)[0] AS type, count(n) AS count
            ORDER BY count DESC
        """)

        edges = db.query("""
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(r) AS count
            ORDER BY count DESC
        """)

        return {
            "nodes": stats,
            "edges": edges
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))