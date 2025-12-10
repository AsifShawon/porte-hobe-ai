"""Minimal MCP-compatible server exposing web_search, time, and weather tools.

This is a lightweight JSON-RPC 2.0 over stdio implementation to prototype
Model Context Protocol style tooling without an external dependency.

Methods implemented:
  tools/list -> returns available tools metadata
  tools/call -> executes a named tool with arguments

Run:
  python mcp_server.py

Then connect with an MCP client (or manually echo JSON lines):
  echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python mcp_server.py
"""
from __future__ import annotations

import sys
import json
import time
import traceback
from datetime import datetime
from typing import Any, Dict
import urllib.request
import urllib.parse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools import create_search_tool
from embedding_engine import search_user_memory, search_universal_memory
from specialist_models import solve_math, solve_code, verify_answer, route_query

# Initialize shared search tool once
try:
    _SEARCH_TOOL = create_search_tool()
except Exception as e:  # pragma: no cover
    _SEARCH_TOOL = None
    SEARCH_INIT_ERROR = str(e)
else:
    SEARCH_INIT_ERROR = None


def web_search(query: str, max_results: int | None = None) -> Dict[str, Any]:
    if not query:
        raise ValueError("query required")
    if _SEARCH_TOOL is None:
        raise RuntimeError(f"Search tool unavailable: {SEARCH_INIT_ERROR}")
    payload = {"query": query}
    if max_results:
        payload["max_results"] = max_results
    res = _SEARCH_TOOL.invoke(payload)
    print(f"web_search results: {res}")
    # TavilySearch may return list/dict; normalize
    if isinstance(res, (list, tuple)):
        return {"results": res}
    if isinstance(res, dict):
        return res
    return {"results": str(res)}


def current_time(timezone: str | None = None) -> Dict[str, Any]:
    tz = timezone or "UTC"
    try:
        dt = datetime.now(ZoneInfo(tz))
    except ZoneInfoNotFoundError:
        dt = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
        tz = "UTC"
    return {
        "timezone": tz,
        "iso": dt.isoformat(),
        "unix": int(dt.timestamp()),
        "readable": dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }


def weather(location: str) -> Dict[str, Any]:
    if not location:
        raise ValueError("location required")

    # Geocoding
    geo_url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode({
        "name": location,
        "count": 1,
        "language": "en",
        "format": "json",
    })
    with urllib.request.urlopen(geo_url, timeout=10) as r:
        geo_data = json.loads(r.read().decode("utf-8"))
    results = geo_data.get("results") or []
    if not results:
        raise ValueError(f"Location not found: {location}")
    first = results[0]
    lat = first["latitude"]
    lon = first["longitude"]
    resolved_name = first.get("name")
    country = first.get("country")

    # Current weather
    forecast_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
    })
    with urllib.request.urlopen(forecast_url, timeout=10) as r:
        forecast = json.loads(r.read().decode("utf-8"))
    current = forecast.get("current", {})

    return {
        "location_query": location,
        "resolved_location": f"{resolved_name}, {country}",
        "latitude": lat,
        "longitude": lon,
        "current": {
            "temperature_c": current.get("temperature_2m"),
            "apparent_temperature_c": current.get("apparent_temperature"),
            "relative_humidity_percent": current.get("relative_humidity_2m"),
            "wind_speed_mps": current.get("wind_speed_10m"),
            "weather_code": current.get("weather_code"),
            "time": current.get("time"),
        },
        "source": "open-meteo.com",
    }


def memory_search(query: str, user_id: str | None = None, k: int = 5, scope: str = "both") -> Dict[str, Any]:
    """Search vector memory in Supabase.

    scope: 'user' (private), 'universal' (global), or 'both'.
    """
    if not query:
        raise ValueError("query required")
    out: Dict[str, Any] = {}
    if scope in ("user", "both") and user_id:
        try:
            out["user_memory"] = search_user_memory(user_id=user_id, text=query, k=k)
        except Exception as e:
            out["user_memory_error"] = str(e)
    if scope in ("universal", "both"):
        try:
            out["universal_memory"] = search_universal_memory(text=query, k=k)
        except Exception as e:
            out["universal_memory_error"] = str(e)
    return out


TOOL_DEFS = {
    "web_search": {
        "name": "web_search",
        "description": "Search the web for up-to-date information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for"},
                "max_results": {"type": "integer", "description": "Max results to retrieve"}
            },
            "required": ["query"],
        },
    },
    # Alias for convenience
    "search": {
        "name": "search",
        "description": "Alias of web_search",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer"}
            },
            "required": ["query"],
        },
    },
    "time": {
        "name": "time",
        "description": "Get the current time (optionally for a specific timezone).",
        "input_schema": {
            "type": "object",
            "properties": {"timezone": {"type": "string", "description": "IANA timezone e.g. Europe/London"}},
        },
    },
    "weather": {
        "name": "weather",
        "description": "Get current weather for a location (city name).",
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string", "description": "City or place name"}},
            "required": ["location"],
        },
    },
    "memory_search": {
        "name": "memory_search",
        "description": "Search private (user) and/or universal memory via pgvector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "user_id": {"type": "string"},
                "k": {"type": "integer"},
                "scope": {"type": "string", "enum": ["user", "universal", "both"], "default": "both"}
            },
            "required": ["query"],
        },
    },
    "utility": {
        "name": "utility",
        "description": "Small helper utilities: ping/echo/now.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "enum": ["ping", "echo", "now"]},
                "args": {"type": "object"}
            },
            "required": ["name"],
        },
    },
    "solve_math": {
        "name": "solve_math",
        "description": "Solve mathematical problems step-by-step using gemma3-math fine-tuned model. Handles equations, calculus, algebra, geometry, trigonometry, etc. with enhanced reasoning.",
        "input_schema": {
            "type": "object",
            "properties": {
                "problem": {"type": "string", "description": "Math problem to solve"},
                "show_steps": {"type": "boolean", "description": "Show step-by-step solution", "default": True},
                "verify": {"type": "boolean", "description": "Verify answer with verification model", "default": True}
            },
            "required": ["problem"],
        },
    },
    "solve_code": {
        "name": "solve_code",
        "description": "Generate code solutions using qwen2.5-coder:7b. Supports multiple languages with quality verification.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Coding task description"},
                "language": {"type": "string", "description": "Programming language (python, javascript, java, etc.)", "default": "python"},
                "test_cases": {"type": "array", "description": "Test cases for validation"},
                "verify": {"type": "boolean", "description": "Verify code quality", "default": True}
            },
            "required": ["task"],
        },
    },
    "verify_answer": {
        "name": "verify_answer",
        "description": "Verify answer correctness using gemma3:4b model. Returns confidence score and suggestions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Original question"},
                "answer": {"type": "string", "description": "Proposed answer"},
                "explanation": {"type": "string", "description": "Optional explanation of the answer"}
            },
            "required": ["question", "answer"],
        },
    },
    "route_query": {
        "name": "route_query",
        "description": "Determine which specialist model to use for a query. Returns routing decision.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "User query"},
                "intent": {"type": "string", "description": "Intent type", "default": "general"},
                "domain": {"type": "string", "description": "Domain (programming/math/general)", "default": "general"}
            },
            "required": ["query"],
        },
    },
}


def _write(message: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def handle_request(req: Dict[str, Any]) -> None:
    jsonrpc = req.get("jsonrpc")
    if jsonrpc != "2.0":  # basic validation
        return
    _id = req.get("id")
    method = req.get("method")

    try:
        if method == "tools/list":
            result = {"tools": list(TOOL_DEFS.values())}
        elif method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if name == "web_search":
                result = web_search(arguments.get("query", ""), arguments.get("max_results"))
            elif name == "search":
                result = web_search(arguments.get("query", ""), arguments.get("max_results"))
            elif name == "time":
                result = current_time(arguments.get("timezone"))
            elif name == "weather":
                result = weather(arguments.get("location", ""))
            elif name == "memory_search":
                result = memory_search(
                    query=arguments.get("query", ""),
                    user_id=arguments.get("user_id"),
                    k=arguments.get("k", 5),
                    scope=arguments.get("scope", "both"),
                )
            elif name == "utility":
                util_name = arguments.get("name")
                args = arguments.get("args") or {}
                if util_name == "ping":
                    result = {"ok": True}
                elif util_name == "echo":
                    result = {"echo": args}
                elif util_name == "now":
                    result = current_time(args.get("timezone"))
                else:
                    raise ValueError(f"Unknown utility: {util_name}")
            elif name == "solve_math":
                result = solve_math(
                    problem=arguments.get("problem", ""),
                    show_steps=arguments.get("show_steps", True),
                    verify=arguments.get("verify", True)
                )
            elif name == "solve_code":
                result = solve_code(
                    task=arguments.get("task", ""),
                    language=arguments.get("language", "python"),
                    test_cases=arguments.get("test_cases"),
                    verify=arguments.get("verify", True)
                )
            elif name == "verify_answer":
                result = verify_answer(
                    question=arguments.get("question", ""),
                    answer=arguments.get("answer", ""),
                    explanation=arguments.get("explanation")
                )
            elif name == "route_query":
                result = route_query(
                    query=arguments.get("query", ""),
                    intent=arguments.get("intent", "general"),
                    domain=arguments.get("domain", "general")
                )
            else:
                raise ValueError(f"Unknown tool: {name}")
        else:
            raise ValueError(f"Unknown method: {method}")

        _write({"jsonrpc": "2.0", "id": _id, "result": result})
    except Exception as e:  # Return JSON-RPC error structure
        _write({
            "jsonrpc": "2.0",
            "id": _id,
            "error": {
                "code": -32000,
                "message": str(e),
                "data": {
                    "trace": traceback.format_exc(limit=3),
                },
            },
        })


def main() -> None:
    # Optionally send a ready notification (non-standard but useful for dev)
    _write({"jsonrpc": "2.0", "method": "status", "params": {"status": "ready"}})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            _write({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            })
            continue
        handle_request(req)


if __name__ == "__main__":  # pragma: no cover
    main()
