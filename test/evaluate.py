#!/usr/bin/env python3
"""
MathOdyssey Multi-Stage Reasoning Pipeline Evaluation

Architecture:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────┐
│ Stage 1         │───▶│ Stage 2          │───▶│ Stage 3         │───▶│ Stage 4      │
│ Planning        │    │ Specialized      │    │ Finalization    │    │ External     │
│ qwen2.5-3b      │    │ mathstral/qwen   │    │ gemma3-4b       │    │ Gemini API   │
│                 │    │ -coder           │    │                 │    │              │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────┘
      ▼                       ▼                       ▼                     ▼
   Problem              Step-by-step            Verified &            Equivalence
   Analysis &           Solution                Corrected             Check vs
   Solving Plan                                 Final Answer          Gold Label
"""

import os
import json
import time
import re
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Literal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import traceback

# Third-party imports
try:
    import requests
    from datasets import load_dataset
    import google.generativeai as genai
    from tqdm import tqdm
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install requests datasets google-generativeai tqdm --break-system-packages")
    exit(1)

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class Config:
    """Configuration for the evaluation pipeline."""
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    
    # Model names (adjust to your local model names)
    planner_model: str = "qwen2.5:3b-instruct-q5_K_M"
    math_expert_model: str = "mathstral:latest"
    code_expert_model: str = "qwen2.5-coder:7b"
    auditor_model: str = "gemma3:4b"
    
    # Gemini settings
    gemini_model: str = "gemini-1.5-flash"
    gemini_api_key: Optional[str] = None  # Set via GEMINI_API_KEY env var
    
    # Evaluation settings
    max_samples: Optional[int] = None  # None = all samples
    timeout_seconds: int = 120
    max_retries: int = 2
    
    # Output settings
    output_dir: str = "./results"
    save_intermediate: bool = True
    
    # Temperature settings
    planner_temp: float = 0.3
    expert_temp: float = 0.2
    auditor_temp: float = 0.1
    judge_temp: float = 0.0


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PlanningOutput:
    """Output from Stage 1: Planning."""
    problem_type: str  # "math", "programming", "mixed"
    key_concepts: List[str]
    solving_steps: List[str]
    expected_difficulty: str  # "easy", "medium", "hard"
    raw_response: str


@dataclass
class ExpertOutput:
    """Output from Stage 2: Specialized Solving."""
    solution_steps: List[str]
    intermediate_results: List[str]
    final_answer: str
    model_used: str
    raw_response: str


@dataclass  
class AuditorOutput:
    """Output from Stage 3: Finalization & Self-Correction."""
    verified_answer: str
    corrections_made: List[str]
    confidence_score: float  # 0.0 - 1.0
    reasoning_summary: str
    raw_response: str


@dataclass
class JudgeOutput:
    """Output from Stage 4: External Judging."""
    is_correct: bool
    equivalence_type: str  # "exact", "equivalent", "partial", "incorrect"
    explanation: str
    raw_response: str


@dataclass
class EvaluationResult:
    """Complete evaluation result for a single problem."""
    problem_id: int
    problem_label: str
    problem_statement: str
    gold_answer: str
    
    # Stage outputs
    planning: Optional[PlanningOutput] = None
    expert: Optional[ExpertOutput] = None
    auditor: Optional[AuditorOutput] = None
    judge: Optional[JudgeOutput] = None
    
    # Metadata
    total_time_seconds: float = 0.0
    stage_times: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    success: bool = False


# ============================================================================
# Ollama Client
# ============================================================================

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        timeout: int = 120
    ) -> str:
        """Generate a response from Ollama using chat API."""
        # Use /api/chat endpoint (works with all Ollama versions)
        url = f"{self.base_url}/api/chat"
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 4096,
            }
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            # Extract content from chat response
            return result.get("message", {}).get("content", "")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request to {model} timed out after {timeout}s")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    
    def check_model_available(self, model: str) -> bool:
        """Check if a model is available in Ollama."""
        try:
            url = f"{self.base_url}/api/tags"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            # Check both exact match and prefix match
            return any(model in name or name.startswith(model.split(":")[0]) for name in model_names)
        except:
            return False


# ============================================================================
# Stage Implementations
# ============================================================================

class Stage1Planner:
    """Stage 1: Planning - Understand problem and create solving plan."""
    
    SYSTEM_PROMPT = """You are an expert problem analyzer. Your job is to:
1. Understand the mathematical/programming problem
2. Identify the problem type and key concepts
3. Create a structured solving plan

Respond in the following JSON format ONLY (no other text):
{
    "problem_type": "math" | "programming" | "mixed",
    "key_concepts": ["concept1", "concept2", ...],
    "solving_steps": ["step1", "step2", ...],
    "expected_difficulty": "easy" | "medium" | "hard"
}"""

    def __init__(self, client: OllamaClient, model: str, temperature: float = 0.3):
        self.client = client
        self.model = model
        self.temperature = temperature
    
    def analyze(self, problem: str) -> PlanningOutput:
        """Analyze the problem and create a solving plan."""
        prompt = f"""Analyze this problem and create a solving plan:

Problem:
{problem}

Respond with JSON only."""

        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            system=self.SYSTEM_PROMPT,
            temperature=self.temperature
        )
        
        # Parse JSON response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
            
            return PlanningOutput(
                problem_type=data.get("problem_type", "math"),
                key_concepts=data.get("key_concepts", []),
                solving_steps=data.get("solving_steps", []),
                expected_difficulty=data.get("expected_difficulty", "medium"),
                raw_response=response
            )
        except (json.JSONDecodeError, ValueError):
            # Fallback if JSON parsing fails
            return PlanningOutput(
                problem_type="math",
                key_concepts=[],
                solving_steps=["Solve the problem step by step"],
                expected_difficulty="medium",
                raw_response=response
            )


class Stage2Expert:
    """Stage 2: Specialized Solving - Domain expert generates solution."""
    
    MATH_SYSTEM = """You are a mathematics expert. Solve the problem step-by-step.
Show all your work clearly. At the end, provide your FINAL ANSWER in the format:
**FINAL ANSWER: [your answer]**"""

    CODE_SYSTEM = """You are a programming expert. Solve the problem step-by-step.
If code is needed, write clean, working code. At the end, provide your FINAL ANSWER in the format:
**FINAL ANSWER: [your answer]**"""

    def __init__(
        self,
        client: OllamaClient,
        math_model: str,
        code_model: str,
        temperature: float = 0.2
    ):
        self.client = client
        self.math_model = math_model
        self.code_model = code_model
        self.temperature = temperature
    
    def solve(self, problem: str, plan: PlanningOutput) -> ExpertOutput:
        """Generate a solution using the appropriate expert model."""
        # Select model based on problem type
        if plan.problem_type == "programming":
            model = self.code_model
            system = self.CODE_SYSTEM
        else:
            model = self.math_model
            system = self.MATH_SYSTEM
        
        # Build prompt with plan context
        steps_text = "\n".join(f"- {s}" for s in plan.solving_steps)
        concepts_text = ", ".join(plan.key_concepts) if plan.key_concepts else "general mathematics"
        
        prompt = f"""Problem:
{problem}

Solving Plan:
Key concepts: {concepts_text}
Steps to follow:
{steps_text}

Now solve this problem completely. Show all work and provide a clear FINAL ANSWER."""

        response = self.client.generate(
            model=model,
            prompt=prompt,
            system=system,
            temperature=self.temperature
        )
        
        # Extract final answer
        final_answer = self._extract_final_answer(response)
        
        return ExpertOutput(
            solution_steps=self._extract_steps(response),
            intermediate_results=[],
            final_answer=final_answer,
            model_used=model,
            raw_response=response
        )
    
    def _extract_final_answer(self, response: str) -> str:
        """Extract the final answer from the response."""
        patterns = [
            r'\*\*FINAL ANSWER:\s*(.+?)\*\*',
            r'FINAL ANSWER:\s*(.+?)(?:\n|$)',
            r'[Tt]he answer is[:\s]+(.+?)(?:\.|$)',
            r'[Aa]nswer[:\s]+(.+?)(?:\n|$)',
            r'=\s*(\d+(?:\.\d+)?)\s*$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        # Return last line as fallback
        lines = [l.strip() for l in response.strip().split('\n') if l.strip()]
        return lines[-1] if lines else ""
    
    def _extract_steps(self, response: str) -> List[str]:
        """Extract solution steps from the response."""
        steps = []
        for line in response.split('\n'):
            line = line.strip()
            if re.match(r'^(\d+[\.\):]|\-|\*|Step)', line):
                steps.append(line)
        return steps if steps else [response[:500]]


class Stage3Auditor:
    """Stage 3: Finalization & Self-Correction - Verify and correct the solution."""
    
    SYSTEM_PROMPT = """You are a meticulous mathematical auditor. Your job is to:
1. Review the proposed solution carefully
2. Identify and correct any errors
3. Verify the final answer is correct
4. Provide a confidence score (0.0 to 1.0)

Respond in the following JSON format ONLY:
{
    "verified_answer": "the correct final answer",
    "corrections_made": ["correction1", "correction2", ...],
    "confidence_score": 0.95,
    "reasoning_summary": "brief explanation of verification"
}"""

    def __init__(self, client: OllamaClient, model: str, temperature: float = 0.1):
        self.client = client
        self.model = model
        self.temperature = temperature
    
    def verify(self, problem: str, expert_output: ExpertOutput) -> AuditorOutput:
        """Verify the expert's solution and correct if needed."""
        prompt = f"""Problem:
{problem}

Expert's Solution:
{expert_output.raw_response}

Expert's Final Answer: {expert_output.final_answer}

Please verify this solution. Check for:
1. Computational errors
2. Logical mistakes
3. Missing steps
4. Incorrect final answer

Respond with JSON only."""

        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            system=self.SYSTEM_PROMPT,
            temperature=self.temperature
        )
        
        # Parse JSON response
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found")
            
            return AuditorOutput(
                verified_answer=str(data.get("verified_answer", expert_output.final_answer)),
                corrections_made=data.get("corrections_made", []),
                confidence_score=float(data.get("confidence_score", 0.5)),
                reasoning_summary=data.get("reasoning_summary", ""),
                raw_response=response
            )
        except (json.JSONDecodeError, ValueError):
            # Fallback: use expert's answer
            return AuditorOutput(
                verified_answer=expert_output.final_answer,
                corrections_made=[],
                confidence_score=0.5,
                reasoning_summary="Failed to parse auditor response",
                raw_response=response
            )


class Stage4Judge:
    """Stage 4: External Judging - Compare with gold label using Gemini."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    def judge(self, problem: str, predicted: str, gold: str) -> JudgeOutput:
        """Judge if the predicted answer matches the gold answer."""
        prompt = f"""You are a mathematical equivalence judge. Determine if the predicted answer is mathematically equivalent to the gold (correct) answer.

Problem:
{problem}

Predicted Answer: {predicted}
Gold Answer: {gold}

Consider:
1. Different notations (e.g., 1/2 = 0.5 = 50%)
2. Equivalent expressions (e.g., 2√2 = √8)
3. Rounding differences for numerical answers
4. Order of elements in sets/tuples

Respond in JSON format ONLY:
{{
    "is_correct": true/false,
    "equivalence_type": "exact" | "equivalent" | "partial" | "incorrect",
    "explanation": "brief explanation of your judgment"
}}"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=500,
                )
            )
            
            response_text = response.text
            
            # Parse JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found")
            
            return JudgeOutput(
                is_correct=data.get("is_correct", False),
                equivalence_type=data.get("equivalence_type", "incorrect"),
                explanation=data.get("explanation", ""),
                raw_response=response_text
            )
        except Exception as e:
            # Fallback: simple string comparison
            is_correct = self._simple_compare(predicted, gold)
            return JudgeOutput(
                is_correct=is_correct,
                equivalence_type="exact" if is_correct else "incorrect",
                explanation=f"Gemini API error: {str(e)}. Fell back to string comparison.",
                raw_response=str(e)
            )
    
    def _simple_compare(self, pred: str, gold: str) -> bool:
        """Simple string comparison as fallback."""
        # Normalize both strings
        pred_norm = re.sub(r'\s+', '', str(pred).lower())
        gold_norm = re.sub(r'\s+', '', str(gold).lower())
        return pred_norm == gold_norm


# ============================================================================
# Main Pipeline
# ============================================================================

class MathOdysseyPipeline:
    """Main evaluation pipeline orchestrating all stages."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize Ollama client
        self.ollama = OllamaClient(config.ollama_base_url)
        
        # Initialize stages
        self.planner = Stage1Planner(
            self.ollama, config.planner_model, config.planner_temp
        )
        self.expert = Stage2Expert(
            self.ollama, config.math_expert_model, config.code_expert_model, config.expert_temp
        )
        self.auditor = Stage3Auditor(
            self.ollama, config.auditor_model, config.auditor_temp
        )
        
        # Initialize Gemini judge
        api_key = config.gemini_api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self.logger.warning("No Gemini API key found. Stage 4 will use fallback comparison.")
            self.judge = None
        else:
            self.judge = Stage4Judge(api_key, config.gemini_model)
        
        # Create output directory
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging."""
        logger = logging.getLogger("MathOdyssey")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        
        return logger
    
    def check_models(self) -> Dict[str, bool]:
        """Check which models are available."""
        models = {
            "planner": self.config.planner_model,
            "math_expert": self.config.math_expert_model,
            "code_expert": self.config.code_expert_model,
            "auditor": self.config.auditor_model,
        }
        
        availability = {}
        for name, model in models.items():
            available = self.ollama.check_model_available(model)
            availability[name] = available
            status = "✓" if available else "✗"
            self.logger.info(f"  {status} {name}: {model}")
        
        return availability
    
    def evaluate_single(self, sample: Dict[str, Any]) -> EvaluationResult:
        """Evaluate a single problem through all stages."""
        start_time = time.time()
        
        result = EvaluationResult(
            problem_id=sample.get("problem_number", 0),
            problem_label=sample.get("label", ""),
            problem_statement=sample.get("problem_statement", ""),
            gold_answer=str(sample.get("answer", "")),
        )
        
        try:
            # Stage 1: Planning
            stage_start = time.time()
            result.planning = self.planner.analyze(result.problem_statement)
            result.stage_times["planning"] = time.time() - stage_start
            
            # Stage 2: Expert Solving
            stage_start = time.time()
            result.expert = self.expert.solve(result.problem_statement, result.planning)
            result.stage_times["expert"] = time.time() - stage_start
            
            # Stage 3: Auditing
            stage_start = time.time()
            result.auditor = self.auditor.verify(result.problem_statement, result.expert)
            result.stage_times["auditor"] = time.time() - stage_start
            
            # Stage 4: Judging
            if self.judge:
                stage_start = time.time()
                result.judge = self.judge.judge(
                    result.problem_statement,
                    result.auditor.verified_answer,
                    result.gold_answer
                )
                result.stage_times["judge"] = time.time() - stage_start
            else:
                # Fallback comparison
                pred_norm = re.sub(r'\s+', '', result.auditor.verified_answer.lower())
                gold_norm = re.sub(r'\s+', '', result.gold_answer.lower())
                is_correct = pred_norm == gold_norm
                result.judge = JudgeOutput(
                    is_correct=is_correct,
                    equivalence_type="exact" if is_correct else "incorrect",
                    explanation="Fallback string comparison (no Gemini API key)",
                    raw_response=""
                )
            
            result.success = True
            
        except Exception as e:
            result.errors.append(f"{type(e).__name__}: {str(e)}")
            self.logger.error(f"Error on problem {result.problem_id}: {e}")
            traceback.print_exc()
        
        result.total_time_seconds = time.time() - start_time
        return result
    
    def run(self) -> Dict[str, Any]:
        """Run the full evaluation pipeline."""
        self.logger.info("="*60)
        self.logger.info("MathOdyssey Multi-Stage Evaluation Pipeline")
        self.logger.info("="*60)
        
        # Check model availability
        self.logger.info("\nChecking model availability...")
        availability = self.check_models()
        
        if not all(availability.values()):
            missing = [k for k, v in availability.items() if not v]
            self.logger.warning(f"Missing models: {missing}")
            self.logger.warning("Some stages may fail. Pull models with: ollama pull <model>")
        
        # Load dataset
        self.logger.info("\nLoading MathOdyssey dataset...")
        dataset = load_dataset("MathOdyssey/MathOdyssey", split="test")
        
        samples = list(dataset)
        if self.config.max_samples:
            samples = samples[:self.config.max_samples]
        
        self.logger.info(f"Evaluating {len(samples)} problems...")
        
        # Run evaluation
        results: List[EvaluationResult] = []
        correct_count = 0
        
        for sample in tqdm(samples, desc="Evaluating"):
            result = self.evaluate_single(sample)
            results.append(result)
            
            if result.judge and result.judge.is_correct:
                correct_count += 1
            
            # Save intermediate results
            if self.config.save_intermediate:
                self._save_intermediate(result)
        
        # Calculate metrics
        total = len(results)
        successful = sum(1 for r in results if r.success)
        accuracy = correct_count / total if total > 0 else 0
        
        avg_time = sum(r.total_time_seconds for r in results) / total if total > 0 else 0
        
        # Compile summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "config": asdict(self.config),
            "metrics": {
                "total_problems": total,
                "successful_evaluations": successful,
                "correct_answers": correct_count,
                "accuracy": accuracy,
                "accuracy_percent": f"{accuracy*100:.2f}%",
                "average_time_per_problem": avg_time,
            },
            "stage_metrics": self._compute_stage_metrics(results),
            "error_summary": self._summarize_errors(results),
        }
        
        # Save final results
        self._save_results(results, summary)
        
        # Print summary
        self.logger.info("\n" + "="*60)
        self.logger.info("EVALUATION COMPLETE")
        self.logger.info("="*60)
        self.logger.info(f"Total Problems: {total}")
        self.logger.info(f"Successful Evaluations: {successful}")
        self.logger.info(f"Correct Answers: {correct_count}")
        self.logger.info(f"Accuracy: {accuracy*100:.2f}%")
        self.logger.info(f"Average Time: {avg_time:.2f}s per problem")
        self.logger.info(f"Results saved to: {self.config.output_dir}")
        
        return summary
    
    def _compute_stage_metrics(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Compute per-stage metrics."""
        metrics = {}
        
        for stage in ["planning", "expert", "auditor", "judge"]:
            times = [r.stage_times.get(stage, 0) for r in results if stage in r.stage_times]
            if times:
                metrics[stage] = {
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times),
                }
        
        # Confidence distribution
        confidences = [r.auditor.confidence_score for r in results if r.auditor]
        if confidences:
            metrics["auditor_confidence"] = {
                "mean": sum(confidences) / len(confidences),
                "high_confidence": sum(1 for c in confidences if c >= 0.8),
                "low_confidence": sum(1 for c in confidences if c < 0.5),
            }
        
        # Correction rate
        corrections = [len(r.auditor.corrections_made) for r in results if r.auditor]
        if corrections:
            metrics["corrections"] = {
                "total_corrections": sum(corrections),
                "problems_with_corrections": sum(1 for c in corrections if c > 0),
            }
        
        return metrics
    
    def _summarize_errors(self, results: List[EvaluationResult]) -> Dict[str, int]:
        """Summarize errors by type."""
        error_counts = {}
        for r in results:
            for error in r.errors:
                error_type = error.split(":")[0]
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        return error_counts
    
    def _save_intermediate(self, result: EvaluationResult):
        """Save intermediate result for a single problem."""
        path = Path(self.config.output_dir) / "intermediate"
        path.mkdir(exist_ok=True)
        
        filename = path / f"problem_{result.problem_id}.json"
        
        # Convert to serializable format
        data = {
            "problem_id": result.problem_id,
            "problem_label": result.problem_label,
            "problem_statement": result.problem_statement,
            "gold_answer": result.gold_answer,
            "predicted_answer": result.auditor.verified_answer if result.auditor else None,
            "is_correct": result.judge.is_correct if result.judge else None,
            "confidence": result.auditor.confidence_score if result.auditor else None,
            "total_time": result.total_time_seconds,
            "success": result.success,
            "errors": result.errors,
        }
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
    
    def _save_results(self, results: List[EvaluationResult], summary: Dict[str, Any]):
        """Save all results and summary."""
        output_dir = Path(self.config.output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary
        summary_path = output_dir / f"summary_{timestamp}.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        # Save detailed results
        detailed = []
        for r in results:
            item = {
                "problem_id": r.problem_id,
                "problem_label": r.problem_label,
                "gold_answer": r.gold_answer,
                "predicted_answer": r.auditor.verified_answer if r.auditor else None,
                "is_correct": r.judge.is_correct if r.judge else None,
                "equivalence_type": r.judge.equivalence_type if r.judge else None,
                "confidence": r.auditor.confidence_score if r.auditor else None,
                "problem_type": r.planning.problem_type if r.planning else None,
                "difficulty": r.planning.expected_difficulty if r.planning else None,
                "corrections_made": r.auditor.corrections_made if r.auditor else [],
                "expert_model": r.expert.model_used if r.expert else None,
                "total_time": r.total_time_seconds,
                "success": r.success,
                "errors": r.errors,
            }
            detailed.append(item)
        
        detailed_path = output_dir / f"detailed_results_{timestamp}.json"
        with open(detailed_path, "w") as f:
            json.dump(detailed, f, indent=2)
        
        # Save CSV for easy analysis
        csv_path = output_dir / f"results_{timestamp}.csv"
        with open(csv_path, "w") as f:
            headers = ["problem_id", "label", "gold", "predicted", "correct", "confidence", "time"]
            f.write(",".join(headers) + "\n")
            for r in results:
                row = [
                    str(r.problem_id),
                    r.problem_label,
                    f'"{r.gold_answer}"',
                    f'"{r.auditor.verified_answer if r.auditor else ""}"',
                    str(r.judge.is_correct if r.judge else ""),
                    f"{r.auditor.confidence_score:.2f}" if r.auditor else "",
                    f"{r.total_time_seconds:.2f}",
                ]
                f.write(",".join(row) + "\n")


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MathOdyssey Multi-Stage Evaluation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python mathodyssey_eval.py
  
  # Run on first 10 samples
  python mathodyssey_eval.py --max-samples 10
  
  # Use custom Ollama URL
  python mathodyssey_eval.py --ollama-url http://192.168.1.100:11434
  
  # Set Gemini API key
  export GEMINI_API_KEY=your-key-here
  python mathodyssey_eval.py

Required:
  - Ollama running locally with models pulled
  - GEMINI_API_KEY environment variable for Stage 4
        """
    )
    
    parser.add_argument(
        "--max-samples", type=int, default=None,
        help="Maximum number of samples to evaluate (default: all)"
    )
    parser.add_argument(
        "--ollama-url", type=str, default="http://localhost:11434",
        help="Ollama API base URL"
    )
    parser.add_argument(
        "--output-dir", type=str, default="./results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--planner-model", type=str, default="qwen2.5:3b-instruct-q5_K_M",
        help="Model for Stage 1 (planning)"
    )
    parser.add_argument(
        "--math-model", type=str, default="mathstral:latest",
        help="Model for Stage 2 (math expert)"
    )
    parser.add_argument(
        "--code-model", type=str, default="qwen2.5-coder:7b",
        help="Model for Stage 2 (code expert)"
    )
    parser.add_argument(
        "--auditor-model", type=str, default="gemma3:4b",
        help="Model for Stage 3 (auditor)"
    )
    parser.add_argument(
        "--timeout", type=int, default=120,
        help="Timeout in seconds per model call"
    )
    
    args = parser.parse_args()
    
    # Build config
    config = Config(
        ollama_base_url=args.ollama_url,
        planner_model=args.planner_model,
        math_expert_model=args.math_model,
        code_expert_model=args.code_model,
        auditor_model=args.auditor_model,
        max_samples=args.max_samples,
        output_dir=args.output_dir,
        timeout_seconds=args.timeout,
    )
    
    # Run pipeline
    pipeline = MathOdysseyPipeline(config)
    summary = pipeline.run()
    
    return 0 if summary["metrics"]["accuracy"] > 0 else 1


if __name__ == "__main__":
    exit(main())