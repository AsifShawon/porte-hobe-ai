"""
Specialized solver agents for math and coding problems
Multi-agent pipeline: Planning -> Solving -> Synthesis -> Validation (Groq)

Architecture:
1. qwen2.5:3b - Fast planning and problem analysis
2. mathstral/qwen-coder - Specialized solving
3. gemma2:9b - Answer synthesis and formatting
4. Groq API (optional) - Validation against large models
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Dict, Optional
import json
import asyncio
from datetime import datetime
import os
from groq import AsyncGroq
import logging

logger = logging.getLogger(__name__)


class GroqValidator:
    """Validate answers using Groq API with large models"""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
            self.client = AsyncGroq(api_key=self.api_key)
        else:
            logger.warning("GROQ_API_KEY not found. Validation against large models will be skipped.")
            self.client = None

        # Available models
        self.models = {
            "llama-70b": "llama-3.1-70b-versatile",
            "mixtral": "mixtral-8x7b-32768",
            "llama-8b": "llama-3.1-8b-instant"  # Faster fallback
        }

    async def validate_answer(
        self,
        problem: str,
        our_answer: str,
        model: str = "mixtral"
    ) -> Dict:
        """Validate our answer against a large model"""

        if not self.client:
            return {
                "validated": False,
                "error": "Groq API key not configured",
                "large_model_answer": None
            }

        try:
            model_id = self.models.get(model, self.models["mixtral"])

            # Get large model's answer
            prompt = f"""Solve this problem and provide the final answer:

Problem: {problem}

Provide:
1. Your solution approach
2. Step-by-step work
3. Final answer clearly marked

Be thorough and accurate."""

            messages = [
                {"role": "system", "content": "You are an expert problem solver. Provide detailed, accurate solutions."},
                {"role": "user", "content": prompt}
            ]

            response = await self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=0.2,
                max_tokens=2000
            )

            large_model_answer = response.choices[0].message.content

            # Compare answers
            comparison_prompt = f"""Compare these two solutions to the same problem:

Problem: {problem}

Solution A (Our Pipeline):
{our_answer}

Solution B (Large Model - {model}):
{large_model_answer}

Analyze:
1. Are both solutions correct?
2. Which solution is better and why?
3. Are there any errors in either solution?
4. Similarity score (0.0-1.0)

Return JSON:
{{
    "both_correct": boolean,
    "our_solution_correct": boolean,
    "large_model_correct": boolean,
    "similarity_score": float,
    "better_solution": "A" or "B" or "equal",
    "our_solution_quality": "excellent/good/fair/poor",
    "comparison_notes": "detailed explanation"
}}"""

            comparison_messages = [
                {"role": "system", "content": "You are an expert solution evaluator. Compare solutions objectively. Return valid JSON only."},
                {"role": "user", "content": comparison_prompt}
            ]

            comparison_response = await self.client.chat.completions.create(
                model=model_id,
                messages=comparison_messages,
                temperature=0.1,
                max_tokens=1000
            )

            comparison = json.loads(comparison_response.choices[0].message.content)

            return {
                "validated": True,
                "large_model": model,
                "large_model_answer": large_model_answer,
                "comparison": comparison,
                "tokens_used": response.usage.total_tokens + comparison_response.usage.total_tokens
            }

        except Exception as e:
            logger.error(f"Groq validation error: {e}", exc_info=True)
            return {
                "validated": False,
                "error": str(e),
                "large_model_answer": None
            }


class MultiAgentSolver:
    """Base class for multi-agent problem solving"""

    def __init__(self):
        # Stage 1: Fast planner (3B model)
        self.planner = ChatOllama(
            model="qwen2.5:3b-instruct-q5_K_M",
            temperature=0.3,
            num_ctx=4096
        )

        # Stage 3: Answer synthesizer (9B model)
        self.synthesizer = ChatOllama(
            model="gemma2:9b",
            temperature=0.2,
            num_ctx=8192
        )

        # Stage 4: Groq validator (optional)
        self.validator = GroqValidator()

    async def solve(
        self,
        problem: str,
        context: str = "",
        validate_with_groq: bool = False,
        groq_model: str = "mixtral"
    ) -> Dict:
        """Main solving pipeline"""
        start_time = datetime.now()

        try:
            # Stage 1: Planning
            plan = await self._plan(problem, context)

            # Stage 2: Solving (implemented by subclasses)
            solution = await self._solve(problem, plan)

            # Stage 3: Synthesis (NEW!)
            final_answer = await self._synthesize(problem, plan, solution)

            # Stage 4: Validation (Optional)
            validation = None
            if validate_with_groq:
                validation = await self.validator.validate_answer(
                    problem=problem,
                    our_answer=final_answer["answer"],
                    model=groq_model
                )

            end_time = datetime.now()

            return {
                "problem": problem,
                "stage_1_plan": plan,
                "stage_2_solution": solution,
                "stage_3_final_answer": final_answer,
                "stage_4_validation": validation,
                "final_answer": final_answer["answer"],
                "confidence": final_answer["confidence"],
                "time_taken": (end_time - start_time).total_seconds(),
                "pipeline": self.__class__.__name__,
                "validated_with_groq": validate_with_groq
            }

        except Exception as e:
            logger.error(f"Solver error: {e}", exc_info=True)
            raise

    async def _plan(self, problem: str, context: str) -> Dict:
        """Stage 1: Create solving strategy"""
        raise NotImplementedError

    async def _solve(self, problem: str, plan: Dict) -> Dict:
        """Stage 2: Execute the plan (implemented by subclasses)"""
        raise NotImplementedError

    async def _synthesize(self, problem: str, plan: Dict, solution: Dict) -> Dict:
        """Stage 3: Synthesize final answer from plan + solution"""

        prompt = f"""You are a master educator synthesizing a final answer.

Original Problem:
{problem}

Planning Phase (Analysis):
{json.dumps(plan, indent=2)}

Solution Phase (Work):
{solution['solution_text']}

Your Task:
Combine the planning analysis and the solution work to create a polished, clear final answer.

Provide:
1. A clear, well-formatted final answer
2. Key steps/reasoning (concise)
3. Any important notes or caveats
4. Self-assessment: Is this answer correct? (confidence 0.0-1.0)

Return JSON:
{{
    "answer": "polished final answer with formatting",
    "key_reasoning": ["step 1", "step 2", ...],
    "notes": "any important notes",
    "confidence": float,
    "self_check": "verification notes"
}}"""

        response = await self.synthesizer.ainvoke([
            SystemMessage(content="""You are gemma2, an expert at synthesizing clear, accurate answers.
Combine analysis and solution into a polished final answer.
Be thorough but concise. Return valid JSON only."""),
            HumanMessage(content=prompt)
        ])

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "answer": response.content,
                "key_reasoning": ["Synthesized answer"],
                "notes": "",
                "confidence": 0.7,
                "self_check": "JSON parsing failed, raw response used"
            }


class MathSolver(MultiAgentSolver):
    """Specialized solver for math problems"""

    def __init__(self):
        super().__init__()
        # Stage 2: Math specialist
        self.solver = ChatOllama(
            model="mathstral:latest",
            temperature=0.2,
            num_ctx=8192
        )

    async def _plan(self, problem: str, context: str) -> Dict:
        """Stage 1: Create math problem solving plan"""

        prompt = f"""Analyze this math problem and create a solving strategy.

Problem: {problem}
{f"Context: {context}" if context else ""}

Create a JSON plan with:
1. problem_type: (algebra, calculus, geometry, trigonometry, statistics, etc.)
2. key_concepts: [list of concepts needed]
3. solving_steps: [ordered list of steps to follow]
4. difficulty: (easy/medium/hard/expert)
5. estimated_time: (seconds)
6. special_notes: any important considerations

Return ONLY valid JSON, no other text."""

        response = await self.planner.ainvoke([
            SystemMessage(content="You are an expert math problem analyzer. Return valid JSON only."),
            HumanMessage(content=prompt)
        ])

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback
            return {
                "problem_type": "general",
                "key_concepts": ["mathematical reasoning"],
                "solving_steps": ["analyze", "solve", "verify"],
                "difficulty": "medium",
                "estimated_time": 60
            }

    async def _solve(self, problem: str, plan: Dict) -> Dict:
        """Stage 2: Solve math problem using mathstral"""

        prompt = f"""You are mathstral, an expert mathematician. Solve this problem following the plan.

Problem: {problem}

Plan to Follow:
{json.dumps(plan, indent=2)}

Instructions:
1. Follow the solving steps in the plan
2. Show ALL your work step-by-step
3. Use proper mathematical notation (LaTeX where appropriate)
4. Explain your reasoning for each step
5. Double-check your calculations
6. Clearly mark your final answer

Provide a detailed, step-by-step solution."""

        response = await self.solver.ainvoke([
            SystemMessage(content="""You are mathstral, an expert mathematics solver specialized in rigorous problem-solving.
Provide detailed, step-by-step solutions with clear mathematical notation.
Show all work and explain your reasoning."""),
            HumanMessage(content=prompt)
        ])

        return {
            "solution_text": response.content,
            "model": "mathstral:latest",
            "approach": "step-by-step mathematical solution"
        }


class CodeSolver(MultiAgentSolver):
    """Specialized solver for coding problems"""

    def __init__(self):
        super().__init__()
        # Stage 2: Code specialist
        self.solver = ChatOllama(
            model="qwen2.5-coder:7b",
            temperature=0.3,
            num_ctx=8192
        )

    async def _plan(self, problem: str, context: str) -> Dict:
        """Stage 1: Create coding problem solving plan"""

        prompt = f"""Analyze this coding problem and create a solution strategy.

Problem: {problem}
{f"Context: {context}" if context else ""}

Create a JSON plan with:
1. problem_type: (algorithm, data_structure, implementation, debugging, optimization, etc.)
2. language: (python, javascript, java, etc.) - default to python
3. key_concepts: [list of concepts/algorithms needed]
4. approach: brief description of solving approach
5. edge_cases: [list of edge cases to consider]
6. time_complexity: expected time complexity
7. space_complexity: expected space complexity
8. difficulty: (easy/medium/hard/expert)

Return ONLY valid JSON, no other text."""

        response = await self.planner.ainvoke([
            SystemMessage(content="You are an expert coding problem analyzer. Return valid JSON only."),
            HumanMessage(content=prompt)
        ])

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "problem_type": "general",
                "language": "python",
                "key_concepts": ["programming"],
                "approach": "implement solution",
                "edge_cases": [],
                "time_complexity": "O(n)",
                "space_complexity": "O(1)",
                "difficulty": "medium"
            }

    async def _solve(self, problem: str, plan: Dict) -> Dict:
        """Stage 2: Solve coding problem using qwen2.5-coder"""

        prompt = f"""You are qwen2.5-coder, an expert programmer. Solve this problem following the plan.

Problem: {problem}

Plan to Follow:
{json.dumps(plan, indent=2)}

Instructions:
1. Write clean, well-commented code
2. Use {plan.get('language', 'python')}
3. Implement the approach described in the plan
4. Handle all edge cases mentioned
5. Add example usage
6. Explain your solution
7. Analyze time and space complexity

Provide production-quality code with clear explanations."""

        response = await self.solver.ainvoke([
            SystemMessage(content="""You are qwen2.5-coder, an expert programmer specialized in writing clean, efficient code.
Follow best practices, write clear comments, and handle edge cases.
Provide complete, working solutions."""),
            HumanMessage(content=prompt)
        ])

        return {
            "solution_text": response.content,
            "model": "qwen2.5-coder:7b",
            "language": plan.get('language', 'python')
        }


# Singleton instances
math_solver = MathSolver()
code_solver = CodeSolver()


async def solve_problem(
    problem: str,
    problem_type: str,
    context: str = "",
    validate_with_groq: bool = False,
    groq_model: str = "mixtral"
) -> Dict:
    """
    Main entry point for problem solving

    Args:
        problem: The problem to solve
        problem_type: 'math' or 'code'
        context: Additional context
        validate_with_groq: Whether to validate with Groq API
        groq_model: Which Groq model to use ('llama-70b', 'mixtral', 'llama-8b')

    Returns:
        Dict with solution and validation results
    """

    if problem_type == "math":
        return await math_solver.solve(problem, context, validate_with_groq, groq_model)
    elif problem_type == "code":
        return await code_solver.solve(problem, context, validate_with_groq, groq_model)
    else:
        raise ValueError(f"Unknown problem type: {problem_type}. Use 'math' or 'code'.")
