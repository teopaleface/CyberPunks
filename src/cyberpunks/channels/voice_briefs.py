"""Fast grounded speech, ONLY after the private verified three-role demo wrapper.

This module never establishes identity, changes roles or confirms an operation.
The caller supplies its server-verified Actor and connection selection.
Safety wording verified by the coordinator against DSU's guide, page 2:
https://app.dsu.mai.gov.ro/uploads/GHID_SIGURANTA_final_logo_nou_3e032274bd.pdf
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from copy import deepcopy

from cyberpunks.agentic.pdf_report import reason_for_visit
from cyberpunks.operations.models import Actor
from cyberpunks.operations.service import OperationsService

SCENARIO = "demo-vara"
SAFETY = "Nu te apropia; dacă există pericol imediat, sună la 112."
EQUIPMENT_UNKNOWN = "Echipamentul nu este precizat în ordin; verifică la dispecer."


def _plain(message):
    return "".join(c for c in unicodedata.normalize("NFD", message.casefold()) if not unicodedata.combining(c))


def _reported_incident(text):
    # Conservative on purpose: quotations, hypotheses and negations belong to the LLM.
    if re.search(
        r"""["„”«»`]|'[^']+'|\b(daca|ipotetic|presupun|presupunem|citat|exemplu|poate|nu|ar|as|nici)\b"""
        r"|\bn[ -](a|am|au)\b|\b(sa zicem|imagineaza|a spus|a zis|spune ca|zice ca)\b",
        text,
    ):
        return None
    if (
        re.search(r"\bstalp(?:ul|u)?\b", text)
        and re.search(r"\b(picat|cazut|prabusit|doborat)\b", text)
        and re.search(r"\b(mi[ -]a|raportez|semnalez)\b|^(a cazut|s[ -]a prabusit)\b", text)
    ):
        return "fallen_pole"
    if re.search(r"\b(stalp(?:ul|u)?|fir|fire|cablu|cabluri)\b", text):
        return None
    if re.search(r"\b(mi[ -]a picat curentul|a cazut curentul|s[ -]a intrerupt curentul|am ramas fara curent)\b", text):
        return "outage"
    if re.search(r"\b(raportez|semnalez)\b", text) and re.search(r"\b(incident(?:ul)?|curent(?:ul)?)\b", text):
        return "ambiguous"
    return None


def trusted_next_stop(context, actor):
    """Return only remaining stops in this crew's currently approved routes.

    Revalidate the context's canonical next_stop against approval and findings;
    next_stop_status alone is not proof of approval for any particular crew.
    """
    plan = context["plan"]
    approved = {a.get("crew_id") for a in plan.get("approvals", []) if a.get("stale") is False}
    by_id = {w["work_item_id"]: w for w in context.get("work_items", [])}
    routes = [
        r
        for r in plan.get("routes", [])
        if actor.crew_id
        and r.get("crew_id") == actor.crew_id
        and (plan.get("approved") is True or actor.crew_id in approved)
    ]
    remaining = []
    seen = set()
    for route in routes:
        for stop in route.get("stops", []):
            wid = stop.get("work_item_id")
            if wid in by_id and not by_id[wid].get("findings") and wid not in seen:
                remaining.append(stop)
                seen.add(wid)
    canonical = context.get("next_stop") or {}
    next_stop = next((s for s in remaining if s["work_item_id"] == canonical.get("work_item_id")), None)
    return routes, remaining, next_stop or (remaining[0] if remaining else None), by_id


def _equipment(items):
    requirements = []
    for item in items:
        explicit = []
        for container in (item.get("effort") or {}, item.get("extra") or {}):
            for key in ("equipment", "required_equipment", "equipment_requirements"):
                value = container.get(key)
                if isinstance(value, str) and value.strip():
                    explicit.append(value.strip())
                elif isinstance(value, list) and value and all(isinstance(v, str) and v.strip() for v in value):
                    explicit.extend(v.strip() for v in value)
        if not explicit:
            return EQUIPMENT_UNKNOWN, False
        requirements.extend(explicit)
    phrase = ", ".join(dict.fromkeys(requirements))
    if not phrase or len(phrase.split()) > 8:
        return EQUIPMENT_UNKNOWN, False
    return f"Echipament precizat: {phrase}.", True


def spoken_location(label):
    """Keep the verified place in speech; the work order retains technical IDs."""
    match = re.fullmatch(r"Contor MTR-[^,]+,\s*PT-[^,]+,\s*(.+)", str(label))
    if match:
        place = re.sub(r"\s*\(sintetic\)\s*$", "", match[1]).strip()
        if place:
            return "verificarea contorului din " + place
    return str(label)


def answer_demo(
    operations: OperationsService, actor: Actor, message: str, *, event_key: str, connection_id: str | None = None
) -> dict | None:
    """Read full authorized context, answer bounded intents or defer to the actual LLM.

    Caller MUST have verified the private demo allowlist before invoking this.
    prepare() persists only a real proposal; no confirm/send/dispatch is called.
    """
    context = operations.context(actor, SCENARIO)
    plan = context["plan"]
    version = plan.get("version")
    if not version:
        return None
    text = _plain(message)
    provenance = {
        "write_executed": False,
        "scenario": SCENARIO,
        "plan_version": version,
        "historical_date": plan.get("plan_date"),
        "synthetic": context.get("synthetic", True),
        "source": "OperationsService.context",
        "event_key": event_key,
        "role": actor.role,
    }

    def answer(reply, proposal=None, **evidence):
        return {"reply": reply, "proposal": proposal, "provenance": {**provenance, **evidence}}

    if actor.role == "customer":
        incident = _reported_incident(text)
        if incident is None:
            return None
        if incident == "ambiguous":
            return answer("Te referi la un stâlp căzut sau la o întrerupere de curent?", clarification_required=True)
        connections = [c for c in context.get("connections", []) if c.get("connection_id") == connection_id]
        if not connection_id or len(connections) != 1 or connection_id not in actor.connection_ids:
            question = "Pentru ce loc de consum asociat contului raportezi incidentul?"
            return answer(f"{SAFETY} {question}" if incident == "fallen_pole" else question)
        if not isinstance(event_key, str) or not event_key.strip():
            raise ValueError("A server event key is required to prepare a demo proposal")
        # Preserve the original speech, including Romanian accents, in the real proposal.
        if len(message) > 1800:
            return None
        key = "voice-demo:" + hashlib.sha256(event_key.encode()).hexdigest()
        data = {"connection_id": connection_id, "plan_version": version, "idempotency_key": key}
        if incident == "fallen_pole":
            action = "request_human"
            data.update(
                priority="urgent", reason=f"Demo sintetic: clientul raportează un stâlp căzut. Relatare: {message}"
            )
            reply = f"{SAFETY} Cererea urgentă către operator e pregătită pentru Confirm în aplicație; nu este salvată sau trimisă."
        else:
            action = "create_case"
            data.update(symptom=message, symptom_type="outage")
            reply = "În scenariul demo, sesizarea de întrerupere este pregătită pentru Confirm în aplicație; încă nu este salvată."
        proposal = operations.prepare(actor, action, data, SCENARIO)
        return answer(
            reply,
            proposal,
            incident=incident,
            proposal_prepared=True,
            snapshot={"plan_version": version, "connection": deepcopy(connections[0]), "message": message},
        )

    if actor.role == "dispatcher":
        if not re.search(r"\b(cate|numar|numarul)\b", text):
            return None
        queue = bool(re.search(r"\b(tichete|tichet|coada|revizuire)\b", text))
        all_work = bool(re.search(r"\b(lucrari|sarcini|interventii)\b", text))
        if not queue and not all_work:
            return None
        items = context.get("work_items", [])
        if queue:
            items = [w for w in items if (w.get("decision") or {}).get("decision") == "human_review"]
        safety = sum((w.get("impact") or {}).get("safety_flag") is True for w in items)
        subject = "coada de revizuire" if queue else "întregul plan de lucrări"
        return answer(
            f"În {subject}, în scenariul demo, sunt {len(items)} {'tichete' if queue else 'lucrări'}, dintre care {safety} cu semnal de siguranță.",
            queue_scope="human_review" if queue else "all_work_items",
            total=len(items),
            safety_count=safety,
            priority_criterion="impact.safety_flag == true; safety signal, not a high-priority classification",
            work_item_ids=[w["work_item_id"] for w in items],
        )

    if actor.role == "technician":
        if not re.search(r"\b(ce am de facut|urmatoarea oprire|urmatoarea interventie|traseu|echipament)\b", text):
            return None
        routes, remaining, stop, by_id = trusted_next_stop(context, actor)
        if not routes:
            return answer("Traseul echipei tale nu este încă aprobat, în scenariul demo.", route_approved=False)
        if not stop:
            return answer("În scenariul demo, nu mai ai opriri fără constatări în traseul aprobat.", remaining=0)
        item = by_id[stop["work_item_id"]]
        location = item.get("location") or {}
        label = location.get("address") or location.get("label") or stop.get("title")
        if not label or len(str(label).split()) > 10:
            return None
        equipment, equipment_known = _equipment([by_id[s["work_item_id"]] for s in remaining])
        reply = f"În demo ai {len(remaining)} opriri rămase; urmează {spoken_location(label)}, pe traseul aprobat."
        reason = reason_for_visit((item.get("decision") or {}).get("reason_ro") or "")
        # Only the canonical human formatter supplies reasons. Unbounded formulas
        # or long source text go to the LLM rather than being truncated into a claim.
        if "de ce" in text:
            if not reason or re.search(r"[=<>]|\b(?:Scor|score)\b", reason) or len((reply + " " + reason).split()) > 45:
                return None
            reply += " " + reason
        else:
            reply += " " + equipment
        if len(reply.split()) > 45:
            return None
        return answer(
            reply,
            route_approved=True,
            crew_id=actor.crew_id,
            remaining=len(remaining),
            next_stop=deepcopy(stop),
            equipment_known=equipment_known,
            reason_source="decision.reason_ro via reason_for_visit" if "de ce" in text else None,
        )
    return None
