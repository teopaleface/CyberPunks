"""Codex local prin abonamentul ChatGPT, fără unelte, MCP sau configurări personale."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
import tempfile
from pathlib import Path

from pydantic import ValidationError

from cyberpunks.channels.models import ChannelError, Intention

PROVIDER = "codex-cli-chatgpt"
# Explicit switches, in addition to a clean CODEX_HOME and empty workspace.
DISABLED_FEATURES = (
    "shell_tool",
    "unified_exec",
    "apply_patch_freeform",
    "js_repl",
    "code_mode",
    "apps",
    "plugins",
    "hooks",
    "multi_agent",
    "browser_use",
    "computer_use",
    "image_generation",
    "view_image",
    "memories",
    "skill_search",
    "search_tool",
    "tool_suggest",
)
MAX_PROCESS_BYTES = 512_000


def command(binary: str, cwd: Path, schema: Path, model: str) -> list[str]:
    args = [
        binary,
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--ephemeral",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--json",
        "--color",
        "never",
        "--cd",
        str(cwd),
        "--output-schema",
        str(schema),
        "--model",
        model,
    ]
    config = {
        "approval_policy": '"never"',
        "forced_login_method": '"chatgpt"',
        "model_provider": '"openai"',
        "model_reasoning_effort": '"low"',
        "model_verbosity": '"low"',
        "service_tier": '"priority"',
        "web_search": '"disabled"',
        "mcp_servers": "{}",
        "project_doc_max_bytes": "0",
        "skills.bundled.enabled": "false",
        "skills.include_instructions": "false",
        "tools.update_plan.enabled": "false",
        "tools.experimental_request_user_input.enabled": "false",
        "history.persistence": '"none"',
        "shell_environment_policy.inherit": '"none"',
        "allow_login_shell": "false",
        "include_apps_instructions": "false",
        "include_collaboration_mode_instructions": "false",
    }
    for key, value in config.items():
        args += ["-c", f"{key}={value}"]
    for feature in DISABLED_FEATURES:
        args += ["--disable", feature]
    return args + ["-"]


def parse_events(raw: bytes) -> tuple[Intention, dict]:
    final = None
    usage = None
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except (ValueError, UnicodeError):
            raise ChannelError("provider_protocol", "The conversation provider returned an invalid response.") from None
        if event.get("type") in ("turn.failed", "error"):
            raise ChannelError(
                "provider_failed", "The conversation provider could not complete this turn. No action was executed."
            )
        item = event.get("item", {})
        if item and item.get("type") not in {"agent_message", "reasoning"}:
            # Fail closed if CLI versions unexpectedly enable any tool.
            raise ChannelError("provider_tool_violation", "The conversation provider attempted an unavailable tool.")
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            final = item.get("text")
        if event.get("type") == "turn.completed":
            usage = event.get("usage", {})
    if not final or usage is None:
        raise ChannelError("provider_incomplete", "The conversation provider did not finish. No action was executed.")
    try:
        intention = Intention.model_validate_json(final)
    except (ValidationError, ValueError):
        raise ChannelError("provider_schema", "The conversation provider returned an unsupported intention.") from None
    return intention, {k: v for k, v in usage.items() if k in {"input_tokens", "output_tokens", "cached_input_tokens"}}


async def _bounded_read(stream: asyncio.StreamReader) -> bytes:
    chunks, size = [], 0
    while data := await stream.read(8192):
        size += len(data)
        if size > MAX_PROCESS_BYTES:
            raise ChannelError("provider_output_limit", "The conversation provider exceeded its response limit.")
        chunks.append(data)
    return b"".join(chunks)


class CodexProvider:
    def __init__(self, *, timeout: float = 55, model: str | None = None):
        self.timeout = timeout
        self.model = model or os.getenv("DAYBREAK_CODEX_MODEL", "gpt-6.1-sol")

    async def turn(self, prompt: str) -> tuple[Intention, dict]:
        binary = shutil.which("codex")
        auth_home = Path(os.getenv("CODEX_HOME", str(Path.home() / ".codex")))
        auth_file = auth_home / "auth.json"
        if not binary or not auth_file.is_file():
            raise ChannelError("provider_auth_missing", "Codex ChatGPT sign-in is required on this local machine.")
        # Never pass application env, internal token, ElevenLabs key or user config to Codex.
        with tempfile.TemporaryDirectory(prefix="daybreak-conversation-") as tmp:
            root = Path(tmp)
            cwd = root / "empty-workspace"
            private = root / "private-auth"
            cwd.mkdir(mode=0o700)
            private.mkdir(mode=0o700)
            shutil.copyfile(auth_file, private / "auth.json")
            (private / "auth.json").chmod(0o600)
            schema = root / "intention-schema.json"
            schema.write_text(json.dumps(Intention.model_json_schema()))
            env = {
                "PATH": os.environ.get("PATH", "/opt/homebrew/bin:/usr/bin:/bin"),
                "HOME": str(root),
                "CODEX_HOME": str(private),
                "TMPDIR": str(root),
                "LANG": "en_US.UTF-8",
                "TERM": "dumb",
            }
            args = command(binary, cwd, schema, self.model)
            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=cwd,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
            try:
                async with asyncio.timeout(self.timeout):
                    proc.stdin.write(prompt.encode())
                    await proc.stdin.drain()
                    proc.stdin.close()
                    out, _err = await asyncio.gather(_bounded_read(proc.stdout), _bounded_read(proc.stderr))
                    await proc.wait()
                if proc.returncode:
                    # Raw stderr can contain credentials or provider diagnostics. Do not relay it.
                    raise ChannelError(
                        "provider_unavailable",
                        "Codex could not answer using the existing ChatGPT sign-in. No action was executed.",
                    )
                intention, usage = parse_events(out)
                return intention, {
                    "provider": PROVIDER,
                    "model": self.model,
                    "usage": usage,
                    "tools_enabled": False,
                    "authentication": "chatgpt",
                    "ephemeral": True,
                }
            except TimeoutError:
                raise ChannelError(
                    "provider_timeout", "The conversation timed out. No action was executed. Try again.", 504
                ) from None
            finally:
                if proc.returncode is None:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    await proc.wait()
