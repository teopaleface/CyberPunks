"""Robustețea descărcării și a încărcării datelor A (fără rețea: serverul e simulat)."""

from __future__ import annotations

import httpx
import pytest

from cyberpunks.a_contoare import download, lcl


def _client(responses: list[int], body: bytes = b"abcdef") -> tuple[httpx.Client, list[int]]:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        code = responses[min(len(calls), len(responses) - 1)]
        calls.append(code)
        if code == 206:
            return httpx.Response(206, content=body[1:4])
        if code == 200:
            return httpx.Response(200, content=body * 1000)  # serverul a ignorat intervalul: ar trimite tot fișierul
        return httpx.Response(code)

    return httpx.Client(transport=httpx.MockTransport(handler)), calls


def test_range_request_retries_when_server_ignores_range() -> None:
    client, calls = _client([200, 429, 206])
    data = download._range_get(client, "https://example.org/f.zip", 1, 3, sleep=lambda s: None)
    assert data == b"bcd" and calls == [200, 429, 206]


def test_range_request_gives_up_with_clear_message() -> None:
    client, calls = _client([200])
    with pytest.raises(SystemExit, match="make a-data"):
        download._range_get(client, "https://example.org/f.zip", 1, 3, attempts=3, sleep=lambda s: None)
    assert len(calls) == 3


def test_partial_lcl_download_is_refused(monkeypatch, tmp_path) -> None:
    raw = tmp_path / "lcl"
    raw.mkdir()
    (raw / "LCL-June2015v2_0.csv").write_text("LCLid,stdorToU,DateTime,KWH/hh (per half hour) \n", encoding="utf-8")
    monkeypatch.setattr(lcl, "LCL_DIR", raw)
    monkeypatch.setattr(lcl, "HH_NPY", tmp_path / "nu-exista.npy")
    monkeypatch.setattr(lcl, "HH_META", tmp_path / "nu-exista.parquet")
    with pytest.raises(SystemExit, match="Lipsesc fișierele LCL"):
        lcl.load_lcl()
    assert len(lcl.expected_lcl_files()) == 45
