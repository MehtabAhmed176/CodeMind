import ast
import os
from src.db import db
from src.vector_store import embed_graph_nodes

def get_called_functions(func_node):
    """Extract all function calls inside a function body"""
    calls = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
    return calls


def ingest_file(repo_name: str, file_path: str):
    """First pass — create all nodes only, no CALLS edges yet"""
    with open(file_path, "r") as f:
        source_code = f.read()

    tree = ast.parse(source_code)

    db.query(
        """
        MERGE (r:Repository {name: $repo_name})
        MERGE (f:File {path: $file_path})
        MERGE (r)-[:CONTAINS]->(f)
        """,
        {"repo_name": repo_name, "file_path": file_path},
    )

    # Extract import statements
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                db.query(
                    """
                    MATCH (f:File {path: $file_path})
                    MERGE (d:Dependency {name: $name})
                    MERGE (f)-[:IMPORTS]->(d)
                    """,
                    {"file_path": file_path, "name": alias.name},
                )

        if isinstance(node, ast.ImportFrom):
            module = node.module or "unknown"
            db.query(
                """
                MATCH (f:File {path: $file_path})
                MERGE (d:Dependency {name: $module})
                MERGE (f)-[:IMPORTS]->(d)
                """,
                {"file_path": file_path, "module": module},
            )

    # Extract classes and functions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            db.query(
                """
                MATCH (f:File {path: $file_path})
                MERGE (c:Class {name: $name, file: $file_path})
                MERGE (f)-[:DEFINES]->(c)
                """,
                {"file_path": file_path, "name": class_name},
            )

            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.FunctionDef):
                    db.query(
                        """
                        MATCH (c:Class {name: $class_name, file: $file_path})
                        MERGE (fn:Function {name: $func_name, file: $file_path, parent: $class_name})
                        MERGE (c)-[:DEFINES]->(fn)
                        """,
                        {
                            "file_path": file_path,
                            "class_name": class_name,
                            "func_name": child.name,
                        },
                    )

        elif isinstance(node, ast.FunctionDef):
            db.query(
                """
                MATCH (f:File {path: $file_path})
                MERGE (fn:Function {name: $func_name, file: $file_path, parent: 'module'})
                MERGE (f)-[:DEFINES]->(fn)
                """,
                {"file_path": file_path, "func_name": node.name},
            )

    print(f"Ingested nodes: {file_path}")


def ingest_calls(file_path: str):
    """Second pass — create CALLS edges after all nodes exist"""
    with open(file_path, "r") as f:
        source_code = f.read()

    tree = ast.parse(source_code)

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.FunctionDef):
                    calls = get_called_functions(child)
                    for called in calls:
                        db.query(
                            """
                            MATCH (caller:Function {name: $caller, file: $file_path})
                            MATCH (callee:Function {name: $called})
                            MERGE (caller)-[:CALLS]->(callee)
                            """,
                            {
                                "caller": child.name,
                                "called": called,
                                "file_path": file_path,
                            },
                        )

        elif isinstance(node, ast.FunctionDef):
            calls = get_called_functions(node)
            for called in calls:
                db.query(
                    """
                    MATCH (caller:Function {name: $caller, file: $file_path})
                    MATCH (callee:Function {name: $called})
                    MERGE (caller)-[:CALLS]->(callee)
                    """,
                    {
                        "caller": node.name,
                        "called": called,
                        "file_path": file_path,
                    },
                )

    print(f"Ingested calls: {file_path}")


def ingest_directory(repo_name: str, dir_path: str):
    """Walk entire directory, two passes — nodes first, edges second"""
    python_files = []

    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [
            d
            for d in dirs
            if d not in ["venv", ".git", "__pycache__", "node_modules"]
        ]
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    print(f"Found {len(python_files)} Python files")

    # Pass 1 — all nodes
    for file_path in python_files:
        try:
            ingest_file(repo_name, file_path)
        except Exception as e:
            print(f"Skipped {file_path}: {e}")

    # Pass 2 — all CALLS edges
    for file_path in python_files:
        try:
            ingest_calls(file_path)
        except Exception as e:
            print(f"Skipped calls {file_path}: {e}")
     # Pass 3 — embed all nodes into Qdrant
    embed_graph_nodes()
    print(f"\nDone. Ingested {len(python_files)} files into graph.")