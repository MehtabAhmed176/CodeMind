import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import db
from src.query import extract_keywords, build_context
from src.llm import ask
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.run_config import RunConfig
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from datasets import Dataset

# Configure Ragas to use Ollama
ollama_llm = LangchainLLMWrapper(Ollama(model="mistral"))
ollama_embeddings = LangchainEmbeddingsWrapper(OllamaEmbeddings(model="nomic-embed-text"))

# Configure metrics to use Ollama
faithfulness.llm = ollama_llm
faithfulness.embeddings = ollama_embeddings
answer_relevancy.llm = ollama_llm
answer_relevancy.embeddings = ollama_embeddings
context_recall.llm = ollama_llm
context_recall.embeddings = ollama_embeddings

# Run sequentially to avoid overwhelming local Ollama
run_config = RunConfig(
    timeout=120,
    max_retries=3,
    max_workers=1
)

# Load test set
with open("eval/test_set.json", "r") as f:
    test_set = json.load(f)

print(f"Running evaluation on {len(test_set)} questions...\n")

questions = []
answers = []
contexts = []
ground_truths = []

for item in test_set:
    question = item["question"]
    ground_truth = item["ground_truth"]

    print(f"Q: {question}")

    # Get keywords and context from graph
    keywords = extract_keywords(question)
    context = build_context(keywords)

    # Get answer from LLM
    answer = ask(context, question)

    print(f"A: {answer[:100]}...")
    print("-" * 40)

    questions.append(question)
    answers.append(answer)
    contexts.append([context])
    ground_truths.append(ground_truth)

# Build Ragas dataset
dataset = Dataset.from_dict({
    "question": questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truth": ground_truths
})

print("\nRunning Ragas metrics...")

results = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_recall],
    run_config=run_config
)

print("\n--- Evaluation Results ---")
print(results)

# Save report
report = {
    "faithfulness": results["faithfulness"],
    "answer_relevancy": results["answer_relevancy"],
    "context_recall": results["context_recall"],
    "overall": (
        results["faithfulness"] +
        results["answer_relevancy"] +
        results["context_recall"]
    ) / 3
}

with open("eval/report.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"\nOverall Score: {report['overall']:.2f}")
print("Report saved to eval/report.json")

db.close()