from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from src.db import db
import uuid

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)

# Local embedding model — no API needed
model = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME = "codemind"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output size


def create_collection():
    """Create Qdrant collection if it doesn't exist"""
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        print(f"Created Qdrant collection: {COLLECTION_NAME}")
    else:
        print(f"Collection already exists: {COLLECTION_NAME}")


def embed_graph_nodes():
    """Embed all nodes from Neo4j into Qdrant"""
    create_collection()

    # Fetch all nodes from Neo4j
    nodes = db.query("""
        MATCH (n)
        WHERE n.name IS NOT NULL OR n.path IS NOT NULL
        RETURN labels(n)[0] AS type,
               n.name AS name,
               n.path AS path,
               n.file AS file
    """)

    points = []

    for node in nodes:
        node_type = node["type"] or "Unknown"
        name = node["name"] or node["path"] or "unnamed"
        file = node["file"] or ""

        # Build text representation of node
        text = f"{node_type}: {name}"
        if file:
            text += f" in {file}"

        # Generate embedding
        vector = model.encode(text).tolist()

        # Create Qdrant point
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "type": node_type,
                "name": name,
                "path": node["path"] or "",
                "file": file,
                "text": text
            }
        )
        points.append(point)

    # Upload all points to Qdrant
    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"Embedded {len(points)} nodes into Qdrant")

def semantic_search(query: str, limit: int = 5) -> list:
    """Find semantically similar nodes for a query"""
    query_vector = model.encode(query).tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit
    ).points

    return [
        {
            "type": r.payload["type"],
            "name": r.payload["name"],
            "file": r.payload["file"],
            "score": r.score
        }
        for r in results
    ]