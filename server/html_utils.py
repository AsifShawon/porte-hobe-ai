"""
HTML Utilities for safe HTML generation and sanitization
Ensures AI-generated HTML is safe to render in the frontend
"""

import bleach
from typing import Dict, Any, List
import re

# Allowed HTML tags for educational content
ALLOWED_TAGS = [
    # Text formatting
    'p', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'strong', 'em', 'u', 'code', 'pre', 'blockquote',
    # Lists
    'ul', 'ol', 'li',
    # Tables
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    # Containers
    'div', 'span', 'section', 'article',
    # Media (restricted)
    'img', 'svg', 'canvas',
    # Interactive (safe)
    'details', 'summary',
    # Links
    'a',
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'style'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'width', 'height'],
    'svg': ['viewBox', 'width', 'height', 'xmlns'],
    'td': ['colspan', 'rowspan'],
    'th': ['colspan', 'rowspan'],
    'code': ['class'],  # For syntax highlighting classes
}

ALLOWED_STYLES = [
    'color', 'background-color', 'font-size', 'font-weight',
    'text-align', 'margin', 'padding', 'border', 'width', 'height',
    'display', 'flex-direction', 'justify-content', 'align-items'
]


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks
    
    Args:
        html_content: Raw HTML string
    
    Returns:
        Sanitized HTML string safe to render
    """
    if not html_content:
        return ""
    
    # Clean with bleach
    clean_html = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        styles=ALLOWED_STYLES,
        strip=True
    )
    
    return clean_html


def generate_teaching_html(content_type: str, data: Dict[str, Any]) -> str:
    """
    Generate structured HTML for different types of teaching content
    
    Args:
        content_type: Type of content ('explanation', 'example', 'exercise', 'visual')
        data: Content data
    
    Returns:
        HTML string
    """
    if content_type == 'explanation':
        return _generate_explanation_html(data)
    elif content_type == 'example':
        return _generate_example_html(data)
    elif content_type == 'exercise':
        return _generate_exercise_html(data)
    elif content_type == 'visual':
        return _generate_visual_html(data)
    elif content_type == 'table':
        return _generate_table_html(data)
    else:
        return f"<p>{sanitize_html(str(data))}</p>"


def _generate_explanation_html(data: Dict[str, Any]) -> str:
    """Generate HTML for explanatory content"""
    title = data.get('title', '')
    content = data.get('content', '')
    examples = data.get('examples', [])
    
    html = f"""
    <div class="teaching-card explanation">
        <h3 class="teaching-title">{sanitize_html(title)}</h3>
        <div class="teaching-content">
            <p>{sanitize_html(content)}</p>
        </div>
    """
    
    if examples:
        html += '<div class="examples-section">'
        for idx, example in enumerate(examples, 1):
            html += f'<div class="example"><strong>Example {idx}:</strong> {sanitize_html(example)}</div>'
        html += '</div>'
    
    html += '</div>'
    
    return html


def _generate_example_html(data: Dict[str, Any]) -> str:
    """Generate HTML for code examples"""
    title = data.get('title', 'Example')
    code = data.get('code', '')
    language = data.get('language', 'python')
    explanation = data.get('explanation', '')
    
    html = f"""
    <div class="teaching-card example">
        <h4 class="example-title">{sanitize_html(title)}</h4>
        <pre><code class="language-{sanitize_html(language)}">{sanitize_html(code)}</code></pre>
    """
    
    if explanation:
        html += f'<p class="explanation">{sanitize_html(explanation)}</p>'
    
    html += '</div>'
    
    return html


def _generate_exercise_html(data: Dict[str, Any]) -> str:
    """Generate HTML for practice exercises"""
    question = data.get('question', '')
    hint = data.get('hint', '')
    difficulty = data.get('difficulty', 'medium')
    
    html = f"""
    <div class="teaching-card exercise" data-difficulty="{sanitize_html(difficulty)}">
        <div class="exercise-header">
            <span class="difficulty-badge">{sanitize_html(difficulty).title()}</span>
        </div>
        <div class="exercise-question">
            <p>{sanitize_html(question)}</p>
        </div>
    """
    
    if hint:
        html += f"""
        <details class="exercise-hint">
            <summary>💡 Hint</summary>
            <p>{sanitize_html(hint)}</p>
        </details>
        """
    
    html += '</div>'
    
    return html


def _generate_visual_html(data: Dict[str, Any]) -> str:
    """Generate HTML for visual diagrams using text/table"""
    diagram_type = data.get('type', 'flowchart')
    steps = data.get('steps', [])
    
    if diagram_type == 'flowchart':
        html = '<div class="visual-diagram flowchart">'
        for idx, step in enumerate(steps):
            html += f'<div class="flow-step">Step {idx + 1}: {sanitize_html(step)}</div>'
            if idx < len(steps) - 1:
                html += '<div class="flow-arrow">↓</div>'
        html += '</div>'
    
    elif diagram_type == 'comparison':
        html = '<div class="visual-diagram comparison">'
        html += '<table class="comparison-table">'
        html += '<tr><th>Option A</th><th>Option B</th></tr>'
        for item in steps:
            html += f'<tr><td>{sanitize_html(item.get("a", ""))}</td><td>{sanitize_html(item.get("b", ""))}</td></tr>'
        html += '</table></div>'
    
    else:
        html = f'<div class="visual-diagram">{sanitize_html(str(data))}</div>'
    
    return html


def _generate_table_html(data: Dict[str, Any]) -> str:
    """Generate HTML table"""
    headers = data.get('headers', [])
    rows = data.get('rows', [])
    caption = data.get('caption', '')
    
    html = '<div class="teaching-card table-container">'
    
    if caption:
        html += f'<div class="table-caption">{sanitize_html(caption)}</div>'
    
    html += '<table class="teaching-table">'
    
    if headers:
        html += '<thead><tr>'
        for header in headers:
            html += f'<th>{sanitize_html(header)}</th>'
        html += '</tr></thead>'
    
    html += '<tbody>'
    for row in rows:
        html += '<tr>'
        for cell in row:
            html += f'<td>{sanitize_html(str(cell))}</td>'
        html += '</tr>'
    html += '</tbody>'
    
    html += '</table></div>'
    
    return html


def wrap_response_html(html_content: str, metadata: Dict[str, Any] = None) -> str:
    """
    Wrap the response HTML in a container with metadata
    
    Args:
        html_content: The main HTML content
        metadata: Optional metadata to include
    
    Returns:
        Wrapped HTML string
    """
    meta_attrs = []
    if metadata:
        for key, value in metadata.items():
            meta_attrs.append(f'data-{key}="{sanitize_html(str(value))}"')
    
    meta_str = ' '.join(meta_attrs)
    
    return f"""
    <div class="ai-response-container" {meta_str}>
        {sanitize_html(html_content)}
    </div>
    """


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from markdown-style text
    
    Returns:
        List of dicts with 'language' and 'code'
    """
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    code_blocks = []
    for language, code in matches:
        code_blocks.append({
            'language': language or 'text',
            'code': code.strip()
        })
    
    return code_blocks


def format_math_expression(expression: str) -> str:
    """
    Format mathematical expression for display
    Wraps in appropriate delimiters for KaTeX rendering
    """
    # Check if already wrapped
    if expression.startswith('$') or expression.startswith('\\['):
        return expression
    
    # Inline math
    if len(expression) < 50:
        return f'${expression}$'
    
    # Display math
    return f'$$\n{expression}\n$$'


__all__ = [
    'sanitize_html',
    'generate_teaching_html',
    'wrap_response_html',
    'extract_code_blocks',
    'format_math_expression'
]
