import os
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable
from groq import Groq

from src.evaluation.faithfulness import check_faithfulness
from src.evaluation.relevance_precision import check_answer_relevance, check_context_precision

@dataclass
class EvalExample:
    question: str
    reference_answer: str = ""

@dataclass
class Evaluator:
    rag_fn: Callable[[str], tuple[str, List[Any]]]
    judge_model: str = "openai/gpt-oss-120b"
    client: Groq = field(default_factory=lambda: Groq(api_key=os.getenv("GROQ_API_KEY")))

    def evaluate_single(self, example: EvalExample) -> Dict[str, Any]:
        answer, chunks = self.rag_fn(example.question)

        faith = check_faithfulness(answer, chunks, client=self.client, model=self.judge_model)
        is_rel = check_answer_relevance(example.question, answer, client=self.client, model=self.judge_model)
        precision = check_context_precision(example.question, chunks, client=self.client, model=self.judge_model)

        return {
            "question": example.question,
            "answer": answer,
            "faithfulness": round(faith, 2),
            "relevance": 1.0 if is_rel else 0.0,
            "context_precision": round(precision, 2),
        }

    def run(self, test_set: List[EvalExample]) -> List[Dict[str, Any]]:
        """Chạy đánh giá cho toàn bộ test set."""
        return [self.evaluate_single(ex) for ex in test_set]

    def aggregate(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Tính trung bình các chỉ số sau khi benchmark."""
        if not results:
            return {}
        return {
            "faithfulness_mean": round(statistics.mean(r["faithfulness"] for r in results), 3),
            "relevance_mean": round(statistics.mean(r["relevance"] for r in results), 3),
            "context_precision_mean": round(statistics.mean(r["context_precision"] for r in results), 3),
        }