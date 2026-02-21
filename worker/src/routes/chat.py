"""
POST /api/v1/chat — provider-agnostic AI chat.

Uses the connection from Authorization: Bearer <connectionId> to know which
provider to use. Fetches fresh overview data, builds a condensed context,
and calls Workers AI. The user can ask anything about their cloud waste and costs.
"""
import json
import js
from pyodide.ffi import to_js
from workers import Response
from services import CredentialService
from providers import get_provider
from utils import error, ok


def _condense_overview(overview: dict) -> str:
    """Build a short text summary of the overview for the model context."""
    lines = []
    summary = overview.get("summary") or {}
    lines.append(
        f"Summary: {summary.get('total_resources', 0)} resources, "
        f"{summary.get('waste_count', 0)} with waste, "
        f"{summary.get('over_provisioned', 0)} over-provisioned, "
        f"{summary.get('under_provisioned', 0)} under-provisioned."
    )
    cards = overview.get("summary_cards") or []
    for c in cards:
        val = c.get("value")
        if val is not None and c.get("id") != "billing":
            lines.append(f"- {c.get('label', '')}: {val}")
    billing = overview.get("billing") or {}
    if billing.get("currency_code"):
        lines.append(f"Currency: {billing['currency_code']}.")
    ps = billing.get("potential_savings")
    if ps and ps.get("value"):
        lines.append(f"Potential savings: {ps['value']} {ps.get('currency', '')}.")
    top = billing.get("top_services") or []
    if top:
        lines.append("Top services by cost: " + ", ".join(f"{s.get('service', '')} ({s.get('cost', 0)})" for s in top[:5]))
    highlights = overview.get("highlights") or []
    if highlights:
        lines.append("Highlights (issues to focus on):")
        for h in highlights:
            name = h.get("name") or h.get("id") or "?"
            reason = h.get("reason", "")
            action = h.get("recommended_action", "")
            est = h.get("estimated_savings", {}) or {}
            sav = f" (~{est.get('value')} {est.get('currency', '')}/mo)" if est.get("value") else ""
            lines.append(f"  - {name} ({reason}){sav}. {action}")
    compute = overview.get("compute") or []
    wasteful = [r for r in compute if r.get("waste_reason") and r.get("waste_reason") != "none"]
    if wasteful and len(wasteful) <= 20:
        lines.append("Wasteful resources:")
        for r in wasteful:
            lines.append(f"  - {r.get('name', r.get('id', '?'))} ({r.get('resource_type', '')}): {r.get('waste_reason', '')}. {r.get('recommended_action', '')}")
    return "\n".join(lines)


def _build_messages(context: str, user_message: str) -> list[dict]:
    system_content = (
        "You are Trim, a cloud waste and cost assistant. "
        "Use only the data below. Give clear, explanatory answers: say why something matters and what the impact is. "
        "When you recommend an action, always include a step-by-step list (e.g. 'Step 1: ... Step 2: ...') so the user can follow it exactly. "
        "Use 2–4 short paragraphs when useful, then end with clear steps. "
        "When prioritizing (e.g. what to fix first), explain why you ordered items that way (savings, risk, or effort)."
    )
    return [
        {"role": "system", "content": f"{system_content}\n\nCurrent cloud state:\n{context}"},
        {"role": "user", "content": user_message},
    ]


async def chat(env, request) -> Response:
    try:
        body = json.loads(await request.text())
    except Exception:
        return error("Invalid JSON body", 400)

    message = (body.get("message") or "").strip()
    if not message:
        return error("Missing or empty 'message'", 400)

    creds = await CredentialService(env).resolve(request)
    if creds is None:
        return error("Missing or invalid Authorization header", 401)

    provider_name = creds.get("provider")
    provider = get_provider(provider_name, creds.get("credentials") or {})
    if provider is None:
        return error(f"Unknown provider: {provider_name}", 400)

    try:
        overview = await provider.get_overview(request)
    except Exception as e:
        return error(f"Failed to fetch overview: {e}", 500)

    context = _condense_overview(overview)
    messages = _build_messages(context, message)

    ai = getattr(env, "AI", None)
    if ai is None:
        return error("AI not configured", 503)

    try:
        options = to_js({"messages": messages}, dict_converter=js.Object.fromEntries)
        result = await ai.run("@cf/meta/llama-3.1-8b-instruct-fp8", options)
    except Exception as e:
        return error(f"AI error: {e}", 502)

    # Workers AI returns an object with .response (text); may be JsProxy or dict
    reply = None
    if hasattr(result, "response"):
        reply = getattr(result, "response", None)
    if reply is None and isinstance(result, dict):
        reply = result.get("response")
    if reply is None:
        reply = str(result).strip() if result else "I couldn't generate a reply."
    reply = (reply or "").strip()

    return ok({"reply": reply})
