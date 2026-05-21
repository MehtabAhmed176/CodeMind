import ollama


def ask(context: str, question: str, history: str = "") -> str:
    """Send graph context + history + question to Ollama"""

    prompt = f"""You are a codebase assistant.
You have been given information extracted from a knowledge graph about a codebase.
Use ONLY this information to answer the question.
Do not make anything up.

CONVERSATION HISTORY:
{history if history else "No previous conversation."}

CODEBASE CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response["message"]["content"]