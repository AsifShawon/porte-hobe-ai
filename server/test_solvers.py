"""
Comprehensive testing framework for multi-agent solvers
Tests against benchmark problems and validates with Groq API (large models)

Test Flow:
1. Run our multi-agent pipeline
2. Get answer from Groq large model
3. Compare and score
"""

import asyncio
import json
from typing import List, Dict
from specialized_solvers import math_solver, code_solver, solve_problem
from datetime import datetime
import os

# Benchmark Problems
MATH_BENCHMARKS = [
    {
        "id": "math_001",
        "difficulty": "easy",
        "problem": "Solve for x: 2x + 5 = 13",
        "expected_answer": "x = 4",
        "concepts": ["algebra", "linear_equations"]
    },
    {
        "id": "math_002",
        "difficulty": "easy",
        "problem": "What is 15% of 80?",
        "expected_answer": "12",
        "concepts": ["percentages", "arithmetic"]
    },
    {
        "id": "math_003",
        "difficulty": "medium",
        "problem": "Find the derivative of f(x) = 3x² + 2x - 5",
        "expected_answer": "f'(x) = 6x + 2",
        "concepts": ["calculus", "derivatives"]
    },
    {
        "id": "math_004",
        "difficulty": "medium",
        "problem": "A triangle has sides of length 3, 4, and 5. Is it a right triangle? Prove your answer using the Pythagorean theorem.",
        "expected_answer": "Yes, because 3² + 4² = 9 + 16 = 25 = 5²",
        "concepts": ["geometry", "pythagorean_theorem"]
    },
    {
        "id": "math_005",
        "difficulty": "hard",
        "problem": "Solve the system of equations: 2x + 3y = 12 and 4x - y = 5",
        "expected_answer": "x = 3, y = 2",
        "concepts": ["algebra", "systems_of_equations"]
    },
    {
        "id": "math_006",
        "difficulty": "hard",
        "problem": "Find the integral of ∫(2x)/(x² + 1) dx",
        "expected_answer": "ln|x² + 1| + C",
        "concepts": ["calculus", "integration", "substitution"]
    },
    {
        "id": "math_007",
        "difficulty": "expert",
        "problem": "Find the limit: lim(x→0) (sin(x)/x)",
        "expected_answer": "1",
        "concepts": ["calculus", "limits", "trigonometry"]
    },
    {
        "id": "math_008",
        "difficulty": "expert",
        "problem": "Prove that the sum of the first n positive integers is n(n+1)/2 using mathematical induction.",
        "expected_answer": "Proof using mathematical induction with base case and inductive step",
        "concepts": ["mathematical_induction", "proofs", "series"]
    }
]

CODE_BENCHMARKS = [
    {
        "id": "code_001",
        "difficulty": "easy",
        "problem": "Write a Python function to check if a string is a palindrome (reads the same forwards and backwards). Ignore spaces and case.",
        "expected_output": "Function that returns True/False",
        "concepts": ["strings", "algorithms"]
    },
    {
        "id": "code_002",
        "difficulty": "easy",
        "problem": "Write a function that finds the maximum number in a list without using the built-in max() function.",
        "expected_output": "Function using iteration",
        "concepts": ["lists", "iteration"]
    },
    {
        "id": "code_003",
        "difficulty": "medium",
        "problem": "Implement a function to reverse a singly linked list in-place. Return the new head of the list.",
        "expected_output": "Function that reverses linked list with O(n) time, O(1) space",
        "concepts": ["linked_lists", "pointers", "data_structures"]
    },
    {
        "id": "code_004",
        "difficulty": "medium",
        "problem": "Given an array of integers and a target sum, find all unique pairs of numbers that add up to the target. Return the pairs as a list of tuples.",
        "expected_output": "Function using hash map for O(n) solution",
        "concepts": ["arrays", "hash_maps", "two_sum"]
    },
    {
        "id": "code_005",
        "difficulty": "hard",
        "problem": "Write a function to find the longest palindromic substring in a given string. If there are multiple palindromes of the same length, return the first one found.",
        "expected_output": "Dynamic programming or expand-around-center solution",
        "concepts": ["dynamic_programming", "strings", "palindromes"]
    },
    {
        "id": "code_006",
        "difficulty": "hard",
        "problem": "Implement a LRU (Least Recently Used) cache with O(1) get and put operations. The cache should have a maximum capacity and evict the least recently used item when full.",
        "expected_output": "Class using OrderedDict or hash map + doubly linked list",
        "concepts": ["data_structures", "hash_maps", "caching"]
    },
    {
        "id": "code_007",
        "difficulty": "expert",
        "problem": "Implement a function to serialize and deserialize a binary tree. The serialization should be compact and the deserialization should rebuild the exact tree structure.",
        "expected_output": "Two functions using BFS or DFS traversal",
        "concepts": ["trees", "serialization", "BFS", "DFS"]
    },
    {
        "id": "code_008",
        "difficulty": "expert",
        "problem": "Implement Dijkstra's shortest path algorithm for a weighted graph. The function should return the shortest distances from a source node to all other nodes.",
        "expected_output": "Implementation with priority queue/heap",
        "concepts": ["graphs", "algorithms", "shortest_path", "priority_queue"]
    }
]


class SolverTester:
    """Comprehensive test framework for solver agents"""

    def __init__(self, validate_with_groq: bool = False, groq_model: str = "mixtral"):
        self.results = []
        self.validate_with_groq = validate_with_groq
        self.groq_model = groq_model

        if validate_with_groq and not os.getenv("GROQ_API_KEY"):
            print("\n⚠️  Warning: GROQ_API_KEY not set. Validation will be skipped.")
            print("Set it with: export GROQ_API_KEY='your_key_here'\n")
            self.validate_with_groq = False

    async def test_math_solver(self, benchmark: Dict) -> Dict:
        """Test math solver on a benchmark problem"""
        print(f"\n{'='*70}")
        print(f"📐 Testing Math Problem: {benchmark['id']} ({benchmark['difficulty'].upper()})")
        print(f"{'='*70}")
        print(f"Problem: {benchmark['problem']}")
        print(f"Expected: {benchmark['expected_answer']}")
        print(f"{'='*70}\n")

        start_time = datetime.now()

        try:
            result = await math_solver.solve(
                problem=benchmark['problem'],
                context="",
                validate_with_groq=self.validate_with_groq,
                groq_model=self.groq_model
            )

            end_time = datetime.now()
            time_taken = (end_time - start_time).total_seconds()

            # Print results
            print(f"\n📋 STAGE 1 - PLANNING:")
            print(f"  Problem Type: {result['stage_1_plan'].get('problem_type', 'N/A')}")
            print(f"  Key Concepts: {', '.join(result['stage_1_plan'].get('key_concepts', []))}")
            print(f"  Difficulty: {result['stage_1_plan'].get('difficulty', 'N/A')}")

            print(f"\n🔬 STAGE 2 - SOLVING (mathstral):")
            solution_preview = result['stage_2_solution']['solution_text'][:300]
            print(f"  {solution_preview}...")

            print(f"\n✨ STAGE 3 - FINAL ANSWER (gemma2):")
            print(f"  Answer: {result['stage_3_final_answer']['answer'][:200]}...")
            print(f"  Confidence: {result['stage_3_final_answer']['confidence']:.2%}")
            print(f"  Self-Check: {result['stage_3_final_answer'].get('self_check', 'N/A')}")

            # Groq validation results
            if result['stage_4_validation']:
                val = result['stage_4_validation']
                if val.get('validated'):
                    print(f"\n🚀 STAGE 4 - GROQ VALIDATION ({self.groq_model.upper()}):")
                    comp = val['comparison']
                    print(f"  Our Solution Correct: {comp['our_solution_correct']}")
                    print(f"  Large Model Correct: {comp['large_model_correct']}")
                    print(f"  Similarity Score: {comp['similarity_score']:.2%}")
                    print(f"  Better Solution: {comp['better_solution']}")
                    print(f"  Our Quality: {comp['our_solution_quality']}")
                    print(f"  Tokens Used: {val['tokens_used']}")
                else:
                    print(f"\n⚠️  STAGE 4 - Validation Error: {val.get('error', 'Unknown')}")

            print(f"\n⏱️  Total Time: {time_taken:.2f}s")
            print(f"{'='*70}\n")

            return {
                "benchmark_id": benchmark['id'],
                "difficulty": benchmark['difficulty'],
                "expected_answer": benchmark['expected_answer'],
                "our_answer": result['final_answer'],
                "confidence": result['confidence'],
                "time_taken": time_taken,
                "groq_validation": result['stage_4_validation'],
                "full_result": result
            }

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}\n")
            import traceback
            traceback.print_exc()
            return {
                "benchmark_id": benchmark['id'],
                "difficulty": benchmark['difficulty'],
                "success": False,
                "error": str(e)
            }

    async def test_code_solver(self, benchmark: Dict) -> Dict:
        """Test code solver on a benchmark problem"""
        print(f"\n{'='*70}")
        print(f"💻 Testing Code Problem: {benchmark['id']} ({benchmark['difficulty'].upper()})")
        print(f"{'='*70}")
        print(f"Problem: {benchmark['problem']}")
        print(f"Expected: {benchmark['expected_output']}")
        print(f"{'='*70}\n")

        start_time = datetime.now()

        try:
            result = await code_solver.solve(
                problem=benchmark['problem'],
                context="",
                validate_with_groq=self.validate_with_groq,
                groq_model=self.groq_model
            )

            end_time = datetime.now()
            time_taken = (end_time - start_time).total_seconds()

            # Print results
            print(f"\n📋 STAGE 1 - PLANNING:")
            print(f"  Problem Type: {result['stage_1_plan'].get('problem_type', 'N/A')}")
            print(f"  Language: {result['stage_1_plan'].get('language', 'N/A')}")
            print(f"  Approach: {result['stage_1_plan'].get('approach', 'N/A')}")
            print(f"  Complexity: Time {result['stage_1_plan'].get('time_complexity', 'N/A')}, Space {result['stage_1_plan'].get('space_complexity', 'N/A')}")

            print(f"\n💡 STAGE 2 - CODING (qwen2.5-coder):")
            solution_preview = result['stage_2_solution']['solution_text'][:300]
            print(f"  {solution_preview}...")

            print(f"\n✨ STAGE 3 - FINAL ANSWER (gemma2):")
            print(f"  Answer Preview: {result['stage_3_final_answer']['answer'][:200]}...")
            print(f"  Confidence: {result['stage_3_final_answer']['confidence']:.2%}")

            # Groq validation results
            if result['stage_4_validation']:
                val = result['stage_4_validation']
                if val.get('validated'):
                    print(f"\n🚀 STAGE 4 - GROQ VALIDATION ({self.groq_model.upper()}):")
                    comp = val['comparison']
                    print(f"  Our Solution Correct: {comp['our_solution_correct']}")
                    print(f"  Large Model Correct: {comp['large_model_correct']}")
                    print(f"  Similarity Score: {comp['similarity_score']:.2%}")
                    print(f"  Better Solution: {comp['better_solution']}")
                    print(f"  Our Quality: {comp['our_solution_quality']}")
                    print(f"  Tokens Used: {val['tokens_used']}")
                else:
                    print(f"\n⚠️  STAGE 4 - Validation Error: {val.get('error', 'Unknown')}")

            print(f"\n⏱️  Total Time: {time_taken:.2f}s")
            print(f"{'='*70}\n")

            return {
                "benchmark_id": benchmark['id'],
                "difficulty": benchmark['difficulty'],
                "expected_output": benchmark['expected_output'],
                "our_answer": result['final_answer'],
                "confidence": result['confidence'],
                "time_taken": time_taken,
                "groq_validation": result['stage_4_validation'],
                "full_result": result
            }

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}\n")
            import traceback
            traceback.print_exc()
            return {
                "benchmark_id": benchmark['id'],
                "difficulty": benchmark['difficulty'],
                "success": False,
                "error": str(e)
            }

    async def run_all_tests(self, test_type: str = "both"):
        """
        Run all benchmark tests

        Args:
            test_type: 'math', 'code', or 'both'
        """
        print("\n" + "="*70)
        print("🚀 STARTING COMPREHENSIVE MULTI-AGENT SOLVER TESTING")
        print("="*70)
        print(f"Validation with Groq: {'✅ ENABLED' if self.validate_with_groq else '❌ DISABLED'}")
        if self.validate_with_groq:
            print(f"Groq Model: {self.groq_model}")
        print("="*70)

        math_results = []
        code_results = []

        # Test math problems
        if test_type in ["math", "both"]:
            print(f"\n\n{'='*70}")
            print("📐 MATH SOLVER TESTS")
            print("="*70)
            for benchmark in MATH_BENCHMARKS:
                result = await self.test_math_solver(benchmark)
                math_results.append(result)
                await asyncio.sleep(2)  # Rate limiting

        # Test code problems
        if test_type in ["code", "both"]:
            print(f"\n\n{'='*70}")
            print("💻 CODE SOLVER TESTS")
            print("="*70)
            for benchmark in CODE_BENCHMARKS:
                result = await self.test_code_solver(benchmark)
                code_results.append(result)
                await asyncio.sleep(2)  # Rate limiting

        # Summary
        self._print_summary(math_results, code_results)

        return {
            "math_results": math_results,
            "code_results": code_results,
            "test_type": test_type,
            "validated_with_groq": self.validate_with_groq
        }

    def _print_summary(self, math_results: List[Dict], code_results: List[Dict]):
        """Print comprehensive test summary"""
        print("\n\n" + "="*70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("="*70)

        # Math summary
        if math_results:
            math_total = len(math_results)
            math_completed = sum(1 for r in math_results if 'error' not in r)
            math_avg_time = sum(r.get('time_taken', 0) for r in math_results if 'error' not in r) / max(math_completed, 1)
            math_avg_conf = sum(r.get('confidence', 0) for r in math_results if 'error' not in r) / max(math_completed, 1)

            print(f"\n📐 MATH SOLVER PERFORMANCE:")
            print(f"  Completed: {math_completed}/{math_total}")
            print(f"  Avg Time: {math_avg_time:.2f}s")
            print(f"  Avg Confidence: {math_avg_conf:.2%}")

            if self.validate_with_groq:
                validated = [r for r in math_results if r.get('groq_validation', {}).get('validated')]
                if validated:
                    our_correct = sum(1 for r in validated if r['groq_validation']['comparison']['our_solution_correct'])
                    similarity_avg = sum(r['groq_validation']['comparison']['similarity_score'] for r in validated) / len(validated)
                    better_count = sum(1 for r in validated if r['groq_validation']['comparison']['better_solution'] in ['A', 'equal'])

                    print(f"\n  🚀 GROQ VALIDATION RESULTS:")
                    print(f"    Our Solutions Correct: {our_correct}/{len(validated)} ({our_correct/len(validated)*100:.1f}%)")
                    print(f"    Avg Similarity: {similarity_avg:.2%}")
                    print(f"    Our Solution Better/Equal: {better_count}/{len(validated)} ({better_count/len(validated)*100:.1f}%)")

        # Code summary
        if code_results:
            code_total = len(code_results)
            code_completed = sum(1 for r in code_results if 'error' not in r)
            code_avg_time = sum(r.get('time_taken', 0) for r in code_results if 'error' not in r) / max(code_completed, 1)
            code_avg_conf = sum(r.get('confidence', 0) for r in code_results if 'error' not in r) / max(code_completed, 1)

            print(f"\n💻 CODE SOLVER PERFORMANCE:")
            print(f"  Completed: {code_completed}/{code_total}")
            print(f"  Avg Time: {code_avg_time:.2f}s")
            print(f"  Avg Confidence: {code_avg_conf:.2%}")

            if self.validate_with_groq:
                validated = [r for r in code_results if r.get('groq_validation', {}).get('validated')]
                if validated:
                    our_correct = sum(1 for r in validated if r['groq_validation']['comparison']['our_solution_correct'])
                    similarity_avg = sum(r['groq_validation']['comparison']['similarity_score'] for r in validated) / len(validated)
                    better_count = sum(1 for r in validated if r['groq_validation']['comparison']['better_solution'] in ['A', 'equal'])

                    print(f"\n  🚀 GROQ VALIDATION RESULTS:")
                    print(f"    Our Solutions Correct: {our_correct}/{len(validated)} ({our_correct/len(validated)*100:.1f}%)")
                    print(f"    Avg Similarity: {similarity_avg:.2%}")
                    print(f"    Our Solution Better/Equal: {better_count}/{len(validated)} ({better_count/len(validated)*100:.1f}%)")

        # Overall
        total_completed = (len(math_results) if math_results else 0) + (len(code_results) if code_results else 0)
        total_problems = len(MATH_BENCHMARKS if math_results else []) + len(CODE_BENCHMARKS if code_results else [])

        print(f"\n🎯 OVERALL PERFORMANCE:")
        print(f"  Total Problems Tested: {total_problems}")
        print(f"  Total Completed: {total_completed}")

        print("\n" + "="*70)


async def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description='Test multi-agent solvers')
    parser.add_argument('--type', choices=['math', 'code', 'both'], default='both',
                        help='Type of tests to run')
    parser.add_argument('--groq', action='store_true',
                        help='Validate with Groq API (requires GROQ_API_KEY)')
    parser.add_argument('--model', choices=['llama-70b', 'mixtral', 'llama-8b'], default='mixtral',
                        help='Groq model to use for validation')

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print("🧪 MULTI-AGENT SOLVER TESTING FRAMEWORK")
    print(f"{'='*70}")
    print(f"Test Type: {args.type}")
    print(f"Groq Validation: {'✅' if args.groq else '❌'}")
    if args.groq:
        print(f"Groq Model: {args.model}")
    print(f"{'='*70}\n")

    tester = SolverTester(validate_with_groq=args.groq, groq_model=args.model)
    results = await tester.run_all_tests(test_type=args.type)

    # Save results
    output_file = f'solver_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n✅ Full results saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
