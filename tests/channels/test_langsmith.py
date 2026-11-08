"""Synthetic conversation traces never contain the actor or operational context."""

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

from langsmith import tracing_context

from cyberpunks.channels.conversation import ConversationService
from cyberpunks.channels.models import ChatRequest, Intention, IntentionData


class Operations:
    def context(self, actor, scenario):
        return {"plan": {}, "private_field": "synthetic-private-context"}


class Provider:
    async def turn(self, prompt):
        return Intention(
            kind="clarify", language="ro", reply="Bună", action=None,
            data=dict.fromkeys(IntentionData.model_fields), evidence=[], task_goal=None,
        ), {"provider": "synthetic"}


def test_trace_contains_only_message_role_channel_and_reply(monkeypatch):
    monkeypatch.setenv("LANGSMITH_API_KEY", "synthetic-key")
    records = []
    actor = SimpleNamespace(role="customer", user_id="synthetic-private-user")
    request = ChatRequest(message="Întrebare sintetică")
    with (
        patch("langsmith.run_trees.RunTree.post", lambda run, *a, **kw: records.append(run.inputs)),
        patch("langsmith.run_trees.RunTree.patch", lambda run, *a, **kw: records.append(run.outputs)),
        tracing_context(enabled=True),
    ):
        result = asyncio.run(ConversationService(Operations(), Provider()).chat(actor, request, event_key="wa-call:123"))
    assert result["reply"] == "Bună"
    assert records == [
        {"message": "Întrebare sintetică", "role": "customer", "channel": "whatsapp_call"},
        {"reply": "Bună", "provider": "synthetic"},
    ]


def test_tracing_disabled_does_not_post():
    actor = SimpleNamespace(role="customer")
    with patch("langsmith.run_trees.RunTree.post") as post, tracing_context(enabled=False):
        asyncio.run(ConversationService(Operations(), Provider()).chat(actor, ChatRequest(message="Test sintetic")))
    post.assert_not_called()
