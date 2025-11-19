# Dynamic Prompts - Before & After Examples

This document shows the dramatic improvement in responses when using dynamic, intent-aware prompts versus static prompts.

## Example 1: "How to get better in calculus?"

### ❌ **BEFORE (Static Prompts)** - What You're Seeing Now

```
🧠 Show thinking process ▼

AI Reasoning Process:
The user is asking for advice on how to improve their understanding of Calculus.
To provide effective guidance, we need to consider the fundamental concepts in
Calculus such as limits, derivatives, and integrals. We should also discuss
effective studying strategies and resources...

NEED_SEARCH: yes SEARCH_QUERY: best calculus study methods, tips for improving
calculus skills, resources for learning calculus effectively

<SEARCH_RESULTS> Query: best calculus study methods...
[Long search results]

1. Problem Restatement / Understanding
You are looking for advice on how to improve your understanding of Calculus...

2. Key Concepts / Theory
- Limits: The foundation of calculus...
- Derivatives: Measure the rate at which a function changes...
- Integrals: Measure the area under or between curves...

3. Step-by-Step Solution / Reasoning

Algebra and Trigonometry Review
Ensure you have a strong grasp...

Differentiation Techniques
- Power Rule: d/dx(x^n) = nx^(n-1)
- Product Rule: (uv)' = u'v + uv'
- Quotient Rule: (u/v)' = ...

4. Example / Demonstration
[Shows Python code for differentiation]
```

**Problems:**
- Treats it like a problem to solve
- Shows formulas and code immediately
- No personalized learning path
- Too technical, not conversational
- Doesn't ask about current level
- Missing clear next steps

---

### ✅ **AFTER (Dynamic Prompts)** - What You'll Get

```
📚 Welcome to Your Calculus Journey!

Great question! Getting better at calculus is all about building a solid
foundation and practicing consistently. Let me create a personalized roadmap
for you.

**Prerequisites**
Before diving deeper, make sure you're comfortable with:
✓ Algebra (solving equations, working with functions)
✓ Trigonometry basics (sin, cos, tan)
✓ Graphing functions

If any of these feel shaky, that's okay - we can review them as we go!

**Your Learning Path**

**Phase 1: Master Limits (2-3 weeks)**
   - What you'll learn: Understanding how functions behave as they approach values
   - Time: 2-3 weeks with daily practice
   - Why it matters: Limits are the foundation of everything in calculus

**Phase 2: Differentiation (3-4 weeks)**
   - What you'll learn: Finding rates of change and slopes
   - Practical applications: Velocity, optimization, curve sketching
   - Time: 3-4 weeks

**Phase 3: Integration (3-4 weeks)**
   - What you'll learn: Finding areas and accumulated change
   - Real-world uses: Physics, economics, probability
   - Time: 3-4 weeks

**Phase 4: Applications (2 weeks)**
   - Bringing it all together with real problems
   - Related rates, optimization, volumes

**Let's Start! 🎯**
I recommend starting with limits using this approach:
1. Begin with numerical limits (evaluating as x approaches a value)
2. Then move to graphical understanding
3. Finally, learn the algebraic techniques

**How do you learn best?**
- Do you prefer working through examples first, or understanding theory?
- Should we start with a quick limit problem to gauge where you're at?
- How much time can you dedicate daily? (15 min, 30 min, 1 hour?)

Let me know and I'll tailor the lessons to your style! 😊
```

**Improvements:**
- ✅ Warm, conversational tone
- ✅ Clear 4-phase roadmap with timelines
- ✅ Explains WHY each phase matters
- ✅ Concrete first step
- ✅ Asks about learning preferences
- ✅ No overwhelming formulas upfront
- ✅ Personalized and encouraging

---

## Example 2: "I want to learn Python"

### ❌ **BEFORE**

```
1. Problem Restatement
You want to learn Python programming.

2. Key Concepts
- Variables: Containers for storing data
- Data Types: int, str, list, dict...
- Control Flow: if, for, while...
[Long list of concepts]

3. Solution
Here's a basic Python program:
print("Hello World")
[Shows code examples]
```

---

### ✅ **AFTER**

```
🐍 Welcome to Python Programming!

Awesome choice! Python is perfect for beginners and incredibly powerful.
Let's map out your learning journey.

**Prerequisites**
None! Python is beginner-friendly. You just need:
✓ A computer
✓ Curiosity and patience
✓ 30 minutes a day

**Your Learning Path**

**Phase 1: Fundamentals (2 weeks)**
   - Variables, data types, basic operations
   - Print statements and input
   - First programs: calculator, Mad Libs game
   - Time: 2 weeks (30 min/day)

**Phase 2: Control Flow (2 weeks)**
   - If/else decisions
   - Loops (for and while)
   - Projects: number guessing game, to-do list
   - Time: 2 weeks

**Phase 3: Functions & Modules (2 weeks)**
   - Creating reusable code
   - Using Python's standard library
   - Project: password generator, file organizer
   - Time: 2 weeks

**Phase 4: Data Structures (2 weeks)**
   - Lists, dictionaries, sets
   - Working with collections
   - Project: contact manager, quiz game
   - Time: 2 weeks

**Let's Start Right Now! 🚀**
Open Python (or replit.com if you don't have it installed) and type:

```python
print("Hello, I'm learning Python!")
name = input("What's your name? ")
print(f"Nice to meet you, {name}!")
```

Run it and tell me what happens!

**Quick questions:**
- Have you programmed before in any language?
- Do you have Python installed, or should I help with that first?
- What made you want to learn Python?

I'm excited to be your guide! 🎉
```

---

## Example 3: "What is a derivative?" (Direct Question)

### ❌ **BEFORE**

```
<THINK>
The student is asking for the definition of a derivative. This is a
fundamental concept in calculus. I need to explain it clearly...
</THINK>

1. Problem Restatement
You are asking what a derivative is.

2. Key Concepts / Theory
A derivative is a measure of how a function changes...
[Long technical explanation with formulas]

3. Mathematical Definition
For a function f(x), the derivative f'(x) is defined as:
f'(x) = lim(h→0) [f(x+h) - f(x)] / h
[More formulas]
```

---

### ✅ **AFTER**

```
**Answer:**
A derivative measures how fast something is changing. Think of it as the
"speedometer" of math - it tells you the rate of change at any moment.

**Example:**
If f(x) = x², then f'(x) = 2x

At x = 3: the derivative is 2(3) = 6
This means at that point, for every tiny step you take in x, the function
goes up 6 times as fast.

**Related:**
- Limits (the foundation of derivatives)
- Integration (the reverse of differentiation)
- Applications (velocity, slopes, optimization)

Want me to show you how to find derivatives, or would you like more examples?
```

**Improvements:**
- ✅ NO thinking phase (direct answer)
- ✅ Simple, intuitive explanation
- ✅ One clear example
- ✅ Offers to go deeper if interested

---

## Example 4: "Solve 2x + 3 = 7"

### ❌ **BEFORE**

```
[Same generic problem-solving format]
```

---

### ✅ **AFTER**

```
**Problem:** Solve 2x + 3 = 7

**Solution:**

**Step 1: Isolate the variable term**
Start with: 2x + 3 = 7
Subtract 3 from both sides: 2x = 4

**Step 2: Solve for x**
Divide both sides by 2: x = 2

**Answer:** x = 2

**Verification:**
Let's check: 2(2) + 3 = 4 + 3 = 7 ✓

**Practice:**
Try these similar problems:
- 3x + 5 = 14
- 4x - 2 = 10
- 5x + 1 = 16
```

**Note:** This stays similar since it's actually a problem to solve, but now it
ONLY shows this format when appropriate!

---

## Key Differences Summary

| Aspect | Before (Static) | After (Dynamic) |
|--------|-----------------|-----------------|
| **Intent Detection** | None - treats all as problems | 11 intent types detected |
| **Response Type** | Always problem-solving format | Adapts to intent |
| **Thinking Display** | Always shown | Conditional (NONE/MINIMAL/MODERATE/FULL) |
| **Tone** | Academic, rigid | Conversational, encouraging |
| **Personalization** | None | Asks about level, preferences |
| **Structure** | Generic steps | Intent-specific (roadmap, solution, answer, etc.) |
| **Examples** | Code/formulas immediately | Intuition first, examples second |
| **Next Steps** | Missing | Clear guidance on what's next |
| **User Level** | Assumes advanced | Adapts to beginner/intermediate/advanced |

---

## How This Works

```
User Query: "How to get better in calculus?"
       ↓
Intent Classifier
       ↓
Intent: LEARNING_NEW_TOPIC
Topic: "calculus"
Thinking: MINIMAL
       ↓
Dynamic Prompt Manager
       ↓
Template: LearningRoadmapTemplate
       ↓
Generated Prompts:
  - Thinking: Brief roadmap planning
  - Answer: Structured learning path with phases
       ↓
TutorAgent
       ↓
Response: Personalized roadmap with clear next steps!
```

---

**The transformation is dramatic!** Instead of rigid, formula-heavy responses,
you get warm, personalized guidance that adapts to what the user actually needs.
