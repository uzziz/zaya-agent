#!/usr/bin/env python3
"""
Zaya Agent Live Demo Server
Streams AI responses with visible thought process + tool calls to the landing page.
Run: python demo_server.py
Serves: http://localhost:3847
"""

import json
import os
import sys
import uuid
import asyncio
from pathlib import Path
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

# ── Config ────────────────────────────────────────────────────────────────────
PORT = 3847
DEMO_DIR = Path(__file__).parent

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-sonnet-4-5"
FALLBACK_MODEL = "minimax/minimax-m2.7"

app = Flask(__name__)
CORS(app)

# ── Demo scenarios ─────────────────────────────────────────────────────────────
SCENARIOS = {
    "code-review": {
        "emoji": "🔍",
        "title": "Code Review",
        "prompt": "Review this function for bugs and suggest improvements:\n\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)",
        "tools": ["web_search", "terminal"],
        "description": "Find bugs, explain the problem, suggest a fix",
    },
    "research": {
        "emoji": "📡",
        "title": "Research Task",
        "prompt": "What are the top 3 LLM reasoning frameworks as of early 2026? Give a one-line summary of each.",
        "tools": ["web_search"],
        "description": "Search the web, summarize findings, cite sources",
    },
    "terminal-task": {
        "emoji": "🖥️",
        "title": "Terminal Task",
        "prompt": "Show me what's running on this machine — list processes using the most CPU and memory.",
        "tools": ["terminal", "file_search"],
        "description": "Execute commands, analyze output, report findings",
    },
    "creative": {
        "emoji": "🎨",
        "title": "Creative Writing",
        "prompt": "Write a 3-paragraph product announcement for a new AI agent called Zaya by Xia Labs. Make it compelling, technical, and a bit mysterious.",
        "tools": [],
        "description": "Draft, refine, and polish a final version",
    },
    "debug": {
        "emoji": "🐛",
        "title": "Bug Hunt",
        "prompt": "Explain why this code is slow and rewrite it to be fast:\n\nimport time\ndata = list(range(10_000_000))\nresult = []\nfor x in data:\n    if x % 2 == 0:\n        result.append(x * x)\nprint(sum(result))",
        "tools": ["terminal"],
        "description": "Diagnose the bottleneck, explain Big O, provide optimized code",
    },
}

# ── Streaming helpers ──────────────────────────────────────────────────────────
def thinking_block(text: str) -> str:
    return json.dumps({"type": "thinking", "content": text}) + "\n"


def tool_start_block(tool_name: str, tool_input: str) -> str:
    return json.dumps({"type": "tool_start", "tool": tool_name, "input": tool_input}) + "\n"


def tool_end_block(tool_name: str, tool_output: str) -> str:
    return json.dumps({"type": "tool_end", "tool": tool_name, "output": tool_output}) + "\n"


def text_block(text: str) -> str:
    return json.dumps({"type": "text", "content": text}) + "\n"


def done_block() -> str:
    return json.dumps({"type": "done"}) + "\n"


async def stream_response(prompt: str, model: str) -> str:
    """Stream a response from OpenRouter-compatible API."""
    import urllib.request

    if not OPENROUTER_API_KEY:
        # Fallback demo — simulate realistic streaming
        steps = [
            ("thinking", "Let me analyze this problem carefully. I need to understand what's being asked before I execute any tools..."),
            ("thinking", "The user wants me to review the code. Let me first understand the algorithm and identify potential issues..."),
            ("tool_start", "terminal", "python3 -c \"\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\nprint(fib(10))\n\""),
            ("tool_end", "terminal", "55"),
            ("thinking", "Good, the function works for small inputs. Now let me test with a larger value to identify the performance issue..."),
            ("tool_start", "terminal", "python3 -c \"import time; start=time.time(); fib(30); print(f'Time: {time.time()-start:.4f}s')\""),
            ("tool_end", "terminal", "Time: 0.3120s"),
            ("thinking", "I see the problem. The time complexity is O(2^n) — exponential! Each call spawns two more. Let me also check memory usage and then rewrite with memoization."),
            ("text", "\n🔴 **Bug found: Exponential time complexity (O(2^n))**\n\nThe naive recursive approach recomputes the same Fibonacci values exponentially many times. For n=30, that's over a million function calls.\n\n✅ **Fix: Use memoization**\n\n```python\nfrom functools import lru_cache\n\n@lru_cache(maxsize=None)\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\n```\n\nWith memoization: **O(n) time, O(n) space**. fib(30) goes from ~300ms to ~0.0001ms — a **3,000x speedup**."),
        ]
        
        for step in steps:
            if step[0] == "thinking":
                yield thinking_block(step[1])
                await asyncio.sleep(0.4)
            elif step[0] == "tool_start":
                yield tool_start_block(step[1], step[2])
                await asyncio.sleep(0.2)
            elif step[0] == "tool_end":
                yield tool_end_block(step[1], step[2])
                await asyncio.sleep(0.3)
            elif step[0] == "text":
                yield text_block(step[1])
                await asyncio.sleep(0.3)
        yield done_block()
        return

    # Real API call
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://xialabs.ai",
        "X-Title": "Zaya Agent Live Demo",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": """You are Zaya, an AI agent by Xia Labs. You are helpful, precise, and technical.
When you reason, show your thinking clearly (prefix with "Thinking:").
When you use a tool, describe what you're about to do before calling it.
Keep responses concise but complete. Use code blocks for code.""",
            },
            {"role": "user", "content": prompt},
        ],
        "stream": True,
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OPENROUTER_BASE}/chat/completions",
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            for line in resp:
                line = line.decode().strip()
                if not line or line == "data: [DONE]":
                    continue
                if line.startswith("data: "):
                    chunk = json.loads(line[6:])
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    if delta.get("content"):
                        content = delta["content"]
                        # Detect thinking
                        if content.startswith("Thinking:") or content.startswith("```think"):
                            yield thinking_block(content)
                        else:
                            yield text_block(content)
    except Exception as e:
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    yield done_block()


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return app.send_static_file("demo.html")


@app.route("/scenarios")
def scenarios():
    return jsonify(SCENARIOS)


@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json() or {}
    prompt = body.get("prompt", "")
    model = body.get("model", DEFAULT_MODEL)

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    session_id = str(uuid.uuid4())

    def generate():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            gen = stream_response(prompt, model)
            # Handle sync iteration of async generator
            while True:
                try:
                    chunk = loop.run_until_complete(gen.__anext__())
                    yield chunk
                except StopAsyncIteration:
                    break
        finally:
            loop.close()

    return Response(generate(), mimetype="application/x-ndjson")


# ── Entry ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"  Zaya Agent Demo Server")
    print(f"  Local:   http://localhost:{PORT}")
    print(f"  Network: http://0.0.0.0:{PORT}")
    print(f"  API key: {'✓ set' if OPENROUTER_API_KEY else '✗ using demo mode'}")
    print()
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
