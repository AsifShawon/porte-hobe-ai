import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { message, history } = await request.json()
    
    console.log('API Route: Calling FastAPI with message:', message)

    // Call your FastAPI backend streaming endpoint
    const response = await fetch(`${process.env.FASTAPI_URL || 'http://localhost:8000'}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        history: history || [],
      }),
    })

    if (!response.ok) {
      console.error('FastAPI response not ok:', response.status, response.statusText)
      throw new Error(`Failed to get response from AI service: ${response.status}`)
    }

    console.log('API Route: Got response from FastAPI, streaming back...')
    console.log('FastAPI response headers:', Object.fromEntries(response.headers.entries()))

    // Return the streaming response directly
    return new NextResponse(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
      },
    })

  } catch (error) {
    console.error('Chat API Error:', error)
    
    // Return a streaming fallback response
    const fallbackResponse = generateFallbackResponse()
    const thinkingContent = generateThinkingContent()
    
    const stream = new ReadableStream({
      start(controller) {
        // Send thinking content first
        const thinkingData = {
          response: "",
          thinking_content: thinkingContent,
          type: "thinking",
          request_id: Date.now().toString(),
          timestamp: new Date().toISOString()
        }
        controller.enqueue(`data: ${JSON.stringify(thinkingData)}\n\n`)
        
        // Wait a bit, then send final response
        setTimeout(() => {
          const finalData = {
            response: fallbackResponse,
            thinking_content: "",
            type: "response",
            request_id: Date.now().toString(),
            timestamp: new Date().toISOString()
          }
          controller.enqueue(`data: ${JSON.stringify(finalData)}\n\n`)
          controller.close()
        }, 1000)
      }
    })

    return new NextResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
      },
    })
  }
}

function generateFallbackResponse(): string {
  const responses = [
    `I'm your AI tutor ready to help with programming and mathematics! Here's what I can assist you with:

**Programming Topics:**
- Variables, functions, and data structures
- Object-oriented programming concepts
- Algorithms and problem-solving strategies
- Code debugging and optimization

**Mathematics Topics:**
- Algebra and calculus concepts
- Linear algebra and statistics
- Mathematical proofs and reasoning
- Applied mathematics in programming

**Example Code:**
\`\`\`python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
\`\`\`

**Mathematical Formula:**
The derivative of x² is: **2x**

Feel free to ask specific questions about any of these topics!`,

    `Great question! I'm designed to provide comprehensive explanations. Let me show you my capabilities:

**For Programming:**
- **Syntax help**: Understanding language-specific syntax
- **Best practices**: Writing clean, efficient code
- **Debugging**: Finding and fixing common errors
- **Concepts**: Data structures, algorithms, design patterns

**For Mathematics:**
- **Step-by-step solutions**: Breaking down complex problems
- **Visual explanations**: Helping you understand concepts
- **Applications**: How math applies to programming
- **Practice problems**: Reinforcing your learning

**Sample Math Problem:**
If f(x) = x² + 3x + 2, find f'(x):
*Solution: f'(x) = 2x + 3*

Ask me anything specific and I'll provide detailed explanations!`,

    `Hello! I'm your autonomous teaching assistant. Currently in demo mode, but here's how I help students learn:

**Interactive Learning:**
- Ask questions and get detailed explanations
- See my reasoning process step-by-step
- Get examples and practice problems
- Receive feedback on your understanding

**Programming Example:**
\`\`\`javascript
// Binary search implementation
function binarySearch(arr, target) {
    let left = 0, right = arr.length - 1;
    
    while (left <= right) {
        let mid = Math.floor((left + right) / 2);
        if (arr[mid] === target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
\`\`\`

**Mathematical Concept:**
Limits in calculus: lim(x→0) sin(x)/x = 1

What would you like to explore today?`
  ]
  
  return responses[Math.floor(Math.random() * responses.length)]
}

function generateThinkingContent(): string {
  const thinkingProcesses = [
    `**Analyzing the user's question:**

1. **Intent Recognition**: Determining what specific help the user needs
2. **Topic Classification**: Is this programming, mathematics, or conceptual?
3. **Difficulty Assessment**: What level of explanation is appropriate?
4. **Context Gathering**: What background knowledge should I assume?

**Planning my response:**
- Structure: Introduction → Core concept → Examples → Practice
- Tone: Educational but approachable
- Depth: Comprehensive but not overwhelming

**Selecting relevant examples:**
- Code samples that illustrate the concept clearly
- Mathematical notation that supports understanding
- Real-world applications to show relevance

*Preparing comprehensive educational response...*`,
    
    `**Breaking down the learning objective:**

**Step 1: Understanding the Query**
- What is the user trying to learn or solve?
- Are there any implicit assumptions I should address?
- What misconceptions might exist around this topic?

**Step 2: Pedagogical Approach**
- Start with fundamentals before advanced concepts
- Use analogies and metaphors for complex ideas
- Provide multiple perspectives on the same concept

**Step 3: Content Organization**
- Theory explanation with clear definitions
- Practical examples with step-by-step walkthrough
- Common pitfalls and how to avoid them
- Next steps for deeper learning

*Crafting educational content with examples...*`,
    
    `**Educational strategy formulation:**

**Content Analysis:**
- Core concepts that need explanation
- Prerequisites the user should understand
- Connections to other topics

**Teaching Method Selection:**
- Visual aids through code examples
- Mathematical notation for precision
- Analogies for intuitive understanding
- Progressive complexity building

**Response Structure Planning:**
1. **Hook**: Engaging opening to capture interest
2. **Explain**: Core concept with clear definitions
3. **Example**: Concrete illustration of the concept
4. **Practice**: Suggested exercises or next steps
5. **Connect**: How this relates to broader learning

*Generating comprehensive tutorial content...*`
  ]
  
  return thinkingProcesses[Math.floor(Math.random() * thinkingProcesses.length)]
}
