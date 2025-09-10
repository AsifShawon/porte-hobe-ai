"""
Example usage of the TutorAgent with different prompt configurations
"""

import asyncio
from agent import TutorAgent
from langchain_core.messages import HumanMessage, AIMessage

async def demo_prompt_configurations():
    """Demonstrate different prompt configurations"""
    
    print("🎓 TutorAgent Prompt Configuration Demo")
    print("=" * 50)
    
    # Initialize agent
    agent = TutorAgent()
    
    # Test different configurations
    configurations = [
        {"subject": None, "level": "standard", "description": "Default Configuration"},
        {"subject": "math", "level": "standard", "description": "Math-focused"},
        {"subject": "coding", "level": "standard", "description": "Coding-focused"},
        {"subject": "math", "level": "simple", "description": "Simple Math"},
        {"subject": "coding", "level": "simple", "description": "Simple Coding"},
    ]
    
    sample_questions = [
        "What is calculus?",
        "How do I implement a binary search algorithm?",
        "Explain the concept of derivatives",
        "What is object-oriented programming?"
    ]
    
    for config in configurations:
        print(f"\n📋 Testing: {config['description']}")
        print("-" * 30)
        
        # Configure the agent
        if config["subject"]:
            agent.set_subject_focus(config["subject"])
        agent.set_complexity_level(config["level"])
        
        # Show the current prompts being used
        print(f"Think Prompt Length: {len(agent.think_prompt)} characters")
        print(f"Answer Prompt Length: {len(agent.answer_prompt)} characters")
        print(f"Subject Focus: {agent.subject_focus}")
        print(f"Complexity Level: {agent.complexity_level}")
        
        # Reset for next iteration
        agent.reset_prompts()
    
    print("\n✅ Demo completed!")

def show_prompt_examples():
    """Show examples of different prompts"""
    from prompts import (
        THINK_PROMPT, ANSWER_PROMPT, SIMPLE_THINK_PROMPT, 
        MATH_FOCUSED_PROMPT, CODING_FOCUSED_PROMPT
    )
    
    print("🔍 Prompt Examples")
    print("=" * 50)
    
    prompts = {
        "Standard Think Prompt": THINK_PROMPT,
        "Standard Answer Prompt": ANSWER_PROMPT,
        "Simple Think Prompt": SIMPLE_THINK_PROMPT,
        "Math-focused Prompt": MATH_FOCUSED_PROMPT,
        "Coding-focused Prompt": CODING_FOCUSED_PROMPT,
    }
    
    for name, prompt in prompts.items():
        print(f"\n📝 {name}:")
        print("-" * 30)
        # Show first 200 characters to give an idea of the prompt
        preview = prompt.replace('\n', ' ').strip()[:200] + "..."
        print(f"Preview: {preview}")
        print(f"Length: {len(prompt)} characters")
        print(f"Placeholders: {prompt.count('{')} found")

async def test_agent_with_math_focus():
    """Test the agent with math-focused prompts"""
    print("\n🧮 Testing Math-Focused Agent")
    print("=" * 40)
    
    agent = TutorAgent()
    agent.set_subject_focus("math")
    
    # Test with a math question
    question = "What is the derivative of x^2 + 3x + 2?"
    print(f"Question: {question}")
    
    # Note: This would actually run the agent if you have Ollama running
    # final_state = await agent.run(question, [])
    # print(f"Answer: {final_state.get('final_answer', 'No answer')}")
    
    print("✅ Math-focused test setup complete")

async def test_agent_with_coding_focus():
    """Test the agent with coding-focused prompts"""
    print("\n💻 Testing Coding-Focused Agent")
    print("=" * 40)
    
    agent = TutorAgent()
    agent.set_subject_focus("coding")
    
    # Test with a coding question
    question = "How do I implement a stack data structure in Python?"
    print(f"Question: {question}")
    
    # Note: This would actually run the agent if you have Ollama running
    # final_state = await agent.run(question, [])
    # print(f"Answer: {final_state.get('final_answer', 'No answer')}")
    
    print("✅ Coding-focused test setup complete")

if __name__ == "__main__":
    print("🚀 Starting Prompt System Demo")
    
    # Show prompt examples
    show_prompt_examples()
    
    # Run async demos
    asyncio.run(demo_prompt_configurations())
    asyncio.run(test_agent_with_math_focus())
    asyncio.run(test_agent_with_coding_focus())
    
    print("\n🎉 All demos completed!")
