import asyncio
import json
from pathlib import Path

import pytest

from cyberpunks.channels.codex import CodexProvider, command, parse_events
from cyberpunks.channels.limits import Limits
from cyberpunks.channels.models import ChannelError

from .conftest import intention


def test_cli_command_disables_tools_and_never_uses_full_access(tmp_path):
    args = command("codex", tmp_path / "empty", tmp_path / "schema.json", "gpt-6.1-sol")
    assert all(flag in args for flag in ["--ignore-user-config", "--ignore-rules", "--ephemeral", "--output-schema"])
    assert "read-only" in args and "danger-full-access" not in args
    for disabled in ["shell_tool", "unified_exec", "apps", "plugins", "multi_agent", "view_image"]:
        assert args[args.index(disabled) - 1] == "--disable"
    assert 'web_search="disabled"' in args and "mcp_servers={}" in args
    assert 'forced_login_method="chatgpt"' in args
    assert 'service_tier="priority"' in args
    assert 'model_verbosity="low"' in args


@pytest.mark.parametrize("kind", ["command_execution", "file_change", "mcp_tool_call", "web_search"])
def test_any_unexpected_tool_event_fails_closed(kind):
    raw = json.dumps({"type": "item.completed", "item": {"type": kind}}).encode()
    with pytest.raises(ChannelError, match="unavailable tool"):
        parse_events(raw)


def test_incomplete_or_malformed_output_is_not_success():
    for raw in [b"not json", b'{"type":"turn.completed"}', b'{"type":"turn.failed"}']:
        with pytest.raises(ChannelError):
            parse_events(raw)


def test_typed_output_rejects_identity_and_generic_actions():
    bad = intention().model_dump()
    bad["data"]["actor"] = {"role": "dispatcher"}
    raw = b"\n".join(
        json.dumps(e).encode()
        for e in [
            {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(bad)}},
            {"type": "turn.completed", "usage": {}},
        ]
    )
    with pytest.raises(ChannelError, match="unsupported intention"):
        parse_events(raw)


def test_limits_block_concurrent_actor_and_limit_voice_sessions():
    async def run():
        limiter = Limits(per_minute=2)
        async with limiter.acquire(("org", "user")):
            with pytest.raises(ChannelError):
                async with limiter.acquire(("org", "user")):
                    pass
        async with limiter.acquire(("org", "user")):
            pass
        with pytest.raises(ChannelError):
            async with limiter.acquire(("org", "user")):
                pass
        for _ in range(3):
            async with limiter.acquire(("org", "voice-user"), voice=True):
                pass
        with pytest.raises(ChannelError):
            async with limiter.acquire(("org", "voice-user"), voice=True):
                pass

    asyncio.run(run())


def test_timeout_kills_isolated_process_and_never_inherits_secrets(tmp_path, monkeypatch):
    import sys

    import cyberpunks.channels.codex as module

    auth = tmp_path / "source-auth"
    auth.mkdir()
    (auth / "auth.json").write_text('{"synthetic":"not-a-real-credential"}')
    monkeypatch.setenv("CODEX_HOME", str(auth))
    monkeypatch.setenv("DAYBREAK_INTERNAL_TOKEN", "synthetic-secret-never-in-child")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "synthetic-key-never-in-child")
    monkeypatch.setattr(module.shutil, "which", lambda _: sys.executable)
    captured = {}
    original = module.asyncio.create_subprocess_exec

    async def spawn(*args, **kwargs):
        captured.update(kwargs)
        assert "DAYBREAK_INTERNAL_TOKEN" not in kwargs["env"]
        assert "ELEVENLABS_API_KEY" not in kwargs["env"]
        assert str(kwargs["cwd"]) != str(tmp_path)
        assert not list(kwargs["cwd"].iterdir())
        return await original(sys.executable, "-c", "import time; time.sleep(60)", **kwargs)

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", spawn)
    with pytest.raises(ChannelError) as result:
        asyncio.run(CodexProvider(timeout=0.1).turn("synthetic test"))
    assert result.value.code == "provider_timeout"
    assert not captured["cwd"].exists()
    assert not Path(captured["env"]["CODEX_HOME"]).exists()
