"""
Specialist Model Tools for MCP Server
Uses local Ollama models for domain-specific tasks
"""
from __future__ import annotations

import json
import logging
from typing import Dict, Any, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

# ============================================================================
# MODEL CONFIGURATIONS
# ============================================================================

MODELS = {
    "main": "qwen2.5:3b-instruct-q5_K_M",
    "math": "gemma3-math:latest",
    "code": "qwen2.5-coder:7b",
    "verify": "gemma3:4b",
    "embedding": "embeddinggemma:latest"
}

# ============================================================================
# MATH SOLVER
# ============================================================================

def solve_math(problem: str, show_steps: bool = True, verify: bool = True) -> Dict[str, Any]:
    """
    Solve mathematical problems using gemma3-math fine-tuned model.

    Args:
        problem: Math problem to solve
        show_steps: Whether to show step-by-step solution
        verify: Whether to verify the answer with gemma3:4b

    Returns:
        Solution with steps and optional verification
    """
    logger.info(f"🔢 Solving math problem with gemma3-math: {problem[:100]}")

    try:
        # Initialize gemma3-math model
        math_llm = ChatOllama(
            model=MODELS["math"],
            temperature=0.1,
            num_predict=1000
        )

        # Create prompt
        if show_steps:
            system_prompt = """You are Gemma3-Math, a fine-tuned mathematical reasoning specialist. Solve the problem with rigorous step-by-step reasoning.

Format your response as:
SOLUTION: [final answer with units if applicable]
STEPS:
1. [Understand the problem - identify given information and what's being asked]
2. [Choose appropriate method/formula and explain why]
3. [Show detailed calculations with intermediate steps]
4. [Verify the answer makes sense in context]
...

Guidelines:
- Show ALL transformations explicitly
- Justify each major step with reasoning
- Check your work and verify units/constraints
- For complex problems, break into sub-problems
- State any assumptions clearly"""
        else:
            system_prompt = """You are Gemma3-Math, a fine-tuned mathematical specialist. Provide the final answer with brief justification."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Problem: {problem}")
        ]

        # Get solution
        response = math_llm.invoke(messages)
        solution_text = response.content

        # Parse solution and steps
        solution = None
        steps = []

        if "SOLUTION:" in solution_text:
            parts = solution_text.split("SOLUTION:", 1)
            if len(parts) > 1:
                solution_part = parts[1].split("STEPS:", 1)[0].strip()
                solution = solution_part

                if "STEPS:" in solution_text:
                    steps_part = solution_text.split("STEPS:", 1)[1].strip()
                    steps = [s.strip() for s in steps_part.split("\n") if s.strip()]

        if not solution:
            solution = solution_text.strip()

        result = {
            "solution": solution,
            "steps": steps if show_steps else [],
            "full_response": solution_text
        }

        # Verify if requested
        if verify:
            verification = verify_answer(
                question=problem,
                answer=solution,
                explanation="\n".join(steps) if steps else solution_text
            )
            result["verification"] = verification

        logger.info(f"✅ Math solution generated: {solution[:100]}")
        return result

    except Exception as e:
        logger.error(f"❌ Math solver failed: {e}")
        return {
            "error": str(e),
            "solution": None,
            "steps": []
        }


# ============================================================================
# CODE SOLVER
# ============================================================================

def solve_code(
    task: str,
    language: str = "python",
    test_cases: Optional[List[Dict]] = None,
    verify: bool = True
) -> Dict[str, Any]:
    """
    Generate code solutions using qwen2.5-coder:7b model.

    Args:
        task: Coding task description
        language: Programming language (python, javascript, etc.)
        test_cases: Optional test cases to validate
        verify: Whether to verify code quality with gemma3:4b

    Returns:
        Code solution with explanation and optional verification
    """
    logger.info(f"💻 Solving code task with qwen2.5-coder:7b: {task[:100]}")

    try:
        # Initialize code model
        code_llm = ChatOllama(
            model=MODELS["code"],
            temperature=0.2,
            num_predict=2000
        )

        # Create prompt
        system_prompt = f"""You are an expert {language} programmer. Write clean, efficient code.

Format your response as:
CODE:
```{language}
[your code here]
```

EXPLANATION:
[brief explanation of the approach]

TIME_COMPLEXITY: [e.g., O(n)]
SPACE_COMPLEXITY: [e.g., O(1)]
"""

        test_info = ""
        if test_cases:
            test_info = f"\n\nTest cases:\n{json.dumps(test_cases, indent=2)}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Task: {task}{test_info}")
        ]

        # Get code solution
        response = code_llm.invoke(messages)
        response_text = response.content

        # Parse code and explanation
        code = None
        explanation = None
        time_complexity = None
        space_complexity = None

        # Extract code block
        if f"```{language}" in response_text:
            parts = response_text.split(f"```{language}", 1)
            if len(parts) > 1:
                code_part = parts[1].split("```", 1)[0].strip()
                code = code_part
        elif "```" in response_text:
            parts = response_text.split("```", 1)
            if len(parts) > 1:
                code_part = parts[1].split("```", 1)[0].strip()
                code = code_part

        # Extract explanation
        if "EXPLANATION:" in response_text:
            expl_part = response_text.split("EXPLANATION:", 1)[1]
            explanation = expl_part.split("TIME_COMPLEXITY:", 1)[0].strip()

        # Extract complexities
        if "TIME_COMPLEXITY:" in response_text:
            time_part = response_text.split("TIME_COMPLEXITY:", 1)[1]
            time_complexity = time_part.split("\n", 1)[0].strip()

        if "SPACE_COMPLEXITY:" in response_text:
            space_part = response_text.split("SPACE_COMPLEXITY:", 1)[1]
            space_complexity = space_part.split("\n", 1)[0].strip()

        result = {
            "code": code or response_text,
            "explanation": explanation,
            "time_complexity": time_complexity,
            "space_complexity": space_complexity,
            "language": language,
            "full_response": response_text
        }

        # Run test cases if provided
        if test_cases and code:
            test_results = []
            # Note: Actual execution would require safe sandboxing
            # For now, just return structure
            for tc in test_cases:
                test_results.append({
                    "input": tc.get("input"),
                    "expected": tc.get("expected"),
                    "status": "pending"  # Would be "passed"/"failed" after execution
                })
            result["test_results"] = test_results

        # Verify if requested
        if verify and code:
            verification = verify_code_quality(
                code=code,
                task=task,
                language=language
            )
            result["verification"] = verification

        logger.info(f"✅ Code solution generated")
        return result

    except Exception as e:
        logger.error(f"❌ Code solver failed: {e}")
        return {
            "error": str(e),
            "code": None,
            "explanation": None
        }


# ============================================================================
# ANSWER VERIFIER
# ============================================================================

def verify_answer(
    question: str,
    answer: str,
    explanation: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify answer correctness using gemma3:4b model.

    Args:
        question: Original question
        answer: Proposed answer
        explanation: Optional explanation of the answer

    Returns:
        Verification result with confidence and suggestions
    """
    logger.info(f"✓ Verifying answer with gemma3:4b")

    try:
        # Initialize verifier model
        verify_llm = ChatOllama(
            model=MODELS["verify"],
            temperature=0.0,
            num_predict=500
        )

        # Create verification prompt
        system_prompt = """You are an expert answer verifier. Evaluate if the answer is correct.

Respond in this format:
IS_CORRECT: [yes/no/partial]
CONFIDENCE: [0.0-1.0]
ISSUES: [list any problems, or 'none']
SUGGESTIONS: [improvements, or 'none']
"""

        context = f"Question: {question}\nAnswer: {answer}"
        if explanation:
            context += f"\nExplanation: {explanation}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]

        # Get verification
        response = verify_llm.invoke(messages)
        verification_text = response.content

        # Parse verification
        is_correct = "yes"
        confidence = 0.7
        issues = []
        suggestions = []

        if "IS_CORRECT:" in verification_text:
            correct_part = verification_text.split("IS_CORRECT:", 1)[1].split("\n", 1)[0].strip().lower()
            is_correct = correct_part

        if "CONFIDENCE:" in verification_text:
            conf_part = verification_text.split("CONFIDENCE:", 1)[1].split("\n", 1)[0].strip()
            try:
                confidence = float(conf_part)
            except:
                pass

        if "ISSUES:" in verification_text:
            issues_part = verification_text.split("ISSUES:", 1)[1].split("SUGGESTIONS:", 1)[0].strip()
            if issues_part.lower() != "none":
                issues = [i.strip() for i in issues_part.split("\n") if i.strip()]

        if "SUGGESTIONS:" in verification_text:
            sugg_part = verification_text.split("SUGGESTIONS:", 1)[1].strip()
            if sugg_part.lower() != "none":
                suggestions = [s.strip() for s in sugg_part.split("\n") if s.strip()]

        result = {
            "is_correct": is_correct in ["yes", "true"],
            "correctness_level": is_correct,  # yes/no/partial
            "confidence": confidence,
            "issues": issues,
            "suggestions": suggestions,
            "verified_by": MODELS["verify"],
            "full_response": verification_text
        }

        logger.info(f"✅ Verification complete: {is_correct} (confidence: {confidence})")
        return result

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return {
            "is_correct": None,
            "confidence": 0.0,
            "error": str(e)
        }


def verify_code_quality(
    code: str,
    task: str,
    language: str
) -> Dict[str, Any]:
    """
    Verify code quality and correctness using gemma3:4b.

    Args:
        code: Code to verify
        task: Original task description
        language: Programming language

    Returns:
        Quality assessment with score and suggestions
    """
    logger.info(f"✓ Verifying code quality with gemma3:4b")

    try:
        verify_llm = ChatOllama(
            model=MODELS["verify"],
            temperature=0.0,
            num_predict=800
        )

        system_prompt = """You are a code review expert. Evaluate the code quality.

Check for:
- Correctness (solves the task)
- Edge cases handled
- Code clarity and readability
- Potential bugs

Respond in this format:
QUALITY_SCORE: [0.0-1.0]
CORRECTNESS: [yes/no/partial]
ISSUES: [list any bugs or problems, or 'none']
SUGGESTIONS: [improvements, or 'none']
"""

        context = f"Task: {task}\n\nCode ({language}):\n```{language}\n{code}\n```"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]

        response = verify_llm.invoke(messages)
        verification_text = response.content

        # Parse verification
        quality_score = 0.8
        correctness = "yes"
        issues = []
        suggestions = []

        if "QUALITY_SCORE:" in verification_text:
            score_part = verification_text.split("QUALITY_SCORE:", 1)[1].split("\n", 1)[0].strip()
            try:
                quality_score = float(score_part)
            except:
                pass

        if "CORRECTNESS:" in verification_text:
            correct_part = verification_text.split("CORRECTNESS:", 1)[1].split("\n", 1)[0].strip().lower()
            correctness = correct_part

        if "ISSUES:" in verification_text:
            issues_part = verification_text.split("ISSUES:", 1)[1].split("SUGGESTIONS:", 1)[0].strip()
            if issues_part.lower() != "none":
                issues = [i.strip() for i in issues_part.split("\n") if i.strip()]

        if "SUGGESTIONS:" in verification_text:
            sugg_part = verification_text.split("SUGGESTIONS:", 1)[1].strip()
            if sugg_part.lower() != "none":
                suggestions = [s.strip() for s in sugg_part.split("\n") if s.strip()]

        return {
            "quality_score": quality_score,
            "correctness": correctness,
            "issues": issues,
            "suggestions": suggestions,
            "verified_by": MODELS["verify"],
            "full_response": verification_text
        }

    except Exception as e:
        logger.error(f"❌ Code quality verification failed: {e}")
        return {
            "quality_score": 0.0,
            "error": str(e)
        }


# ============================================================================
# MODEL ROUTER
# ============================================================================

def route_query(query: str, intent: str = "general", domain: str = "general") -> Dict[str, Any]:
    """
    Determine which specialist model to use for a query.

    Args:
        query: User's query
        intent: Intent type (from intent classifier)
        domain: Domain (programming/math/general)

    Returns:
        Routing decision with model selection
    """
    # Math-related queries
    if domain == "mathematics" or intent == "solving_problem":
        # Check if it's a math problem
        math_keywords = ["solve", "calculate", "equation", "derivative", "integral", "∫", "∂", "x=", "y="]
        if any(kw in query.lower() for kw in math_keywords):
            return {
                "primary_model": MODELS["math"],
                "verification_model": MODELS["verify"],
                "strategy": "solve_then_verify",
                "tool": "solve_math"
            }

    # Code-related queries
    if domain == "programming" or intent in ["solving_problem", "debugging_code"]:
        code_keywords = ["write", "code", "function", "implement", "debug", "```", "class", "def ", "const "]
        if any(kw in query.lower() for kw in code_keywords):
            return {
                "primary_model": MODELS["code"],
                "verification_model": MODELS["verify"],
                "strategy": "solve_then_verify",
                "tool": "solve_code"
            }

    # Simple questions - no specialist needed
    return {
        "primary_model": MODELS["main"],
        "verification_model": None,
        "strategy": "direct_answer",
        "tool": None
    }
