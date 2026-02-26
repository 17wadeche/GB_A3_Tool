from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class LeanToolGuidance:
    tool_name: str
    when_to_use: str
    output_expected: str
    starter_prompt: str


def _call_ai_json(system_prompt: str, user_payload: Dict[str, Any], api_key: str | None = None) -> Dict[str, Any]:
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. AI coaching requires a configured API key.")

    body = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        "temperature": 0.2,
    }

    req = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=45) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"AI API call failed: {exc}") from exc

    content = raw["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("AI returned non-JSON content. Please retry.") from exc


def api_key_available(session_api_key: str | None = None) -> bool:
    return bool((session_api_key or "").strip() or os.getenv("OPENAI_API_KEY"))


def coach_define_phase(
    problem_statement: str,
    define_fields: Dict[str, Any],
    question: str = "",
    api_key: str | None = None,
) -> Dict[str, Any]:
    system_prompt = (
        "You are a Lean Six Sigma Black Belt coach. Return STRICT JSON only with keys: "
        "problem_feedback, define_feedback, rewrites, proposed_fields, tool_guidance, answer. "
        "Rules: (1) Rewrite all filled Define fields for clarity/rigor. "
        "(2) proposed_fields should only include suggestions for blank fields; do not overwrite filled fields. "
        "(3) Provide Black Belt-level guidance across DMAIC/LSS tools (VOC, CTQ, SIPOC, process mapping, VSM, MSA, capability, control plan). "
        "problem_feedback format: {score:int,strengths:list,missing_components:list,suggested_rewrite:str,detected_context:str}. "
        "define_feedback format: {score:int,strengths:list,improvements:list}. "
        "rewrites format: object mapping field names to rewritten text for any fields provided by user. "
        "tool_guidance format: list of objects with tool_name, when_to_use, output_expected, starter_prompt. "
        "answer should respond to the optional user question using current Define context."
    )

    payload = {
        "problem_statement": problem_statement,
        "define_fields": define_fields,
        "question": question,
    }
    result = _call_ai_json(system_prompt, payload, api_key=api_key)

    result.setdefault("problem_feedback", {"score": 0, "strengths": [], "missing_components": [], "suggested_rewrite": "", "detected_context": "general"})
    result.setdefault("define_feedback", {"score": 0, "strengths": [], "improvements": []})
    result.setdefault("rewrites", {})
    result.setdefault("proposed_fields", {})
    result.setdefault("tool_guidance", [])
    result.setdefault("answer", "")
    return result


def tool_guidance_from_result(result: Dict[str, Any]) -> List[LeanToolGuidance]:
    items = result.get("tool_guidance", []) or []
    out: List[LeanToolGuidance] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        out.append(
            LeanToolGuidance(
                tool_name=str(item.get("tool_name", "")),
                when_to_use=str(item.get("when_to_use", "")),
                output_expected=str(item.get("output_expected", "")),
                starter_prompt=str(item.get("starter_prompt", "")),
            )
        )
    return out
