"""Documentation contract tests for the v1 launch surface."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
HTML_DOC = ROOT / "docs" / "html-report.md"
CONTRACT_DOC = ROOT / "docs" / "stability-contract.md"


def test_key_docs_exist() -> None:
    assert HTML_DOC.is_file()
    assert CONTRACT_DOC.is_file()


def test_readme_has_english_positioning() -> None:
    text = README.read_text(encoding="utf-8")
    assert "AI agents fail in loops." in text
    assert "human-readable failure console" in text


def test_readme_has_korean_positioning() -> None:
    text = README.read_text(encoding="utf-8")
    assert "한국어" in text
    assert "AI 에이전트 실패를 테스트" in text


def test_docs_mention_korean_locale() -> None:
    text = HTML_DOC.read_text(encoding="utf-8")
    assert "--html-locale ko" in text
    assert "엔트로피 루프 실패 콘솔" in text


def test_docs_mention_reduced_motion() -> None:
    assert "prefers-reduced-motion" in HTML_DOC.read_text(encoding="utf-8")


def test_docs_mention_no_external_assets() -> None:
    text = HTML_DOC.read_text(encoding="utf-8").lower()
    assert "self-contained" in text
    assert "no external" in text


def test_docs_mention_no_default_artifact_upload() -> None:
    text = (
        HTML_DOC.read_text(encoding="utf-8")
        + CONTRACT_DOC.read_text(encoding="utf-8")
        + (ROOT / "docs" / "ci-evidence.md").read_text(encoding="utf-8")
    ).lower()
    assert "artifact" in text


def test_docs_do_not_overclaim() -> None:
    for doc in (HTML_DOC, CONTRACT_DOC):
        text = doc.read_text(encoding="utf-8").lower()
        # Only disclaimers ("not root-cause", "no guaranteed") are allowed.
        assert "self-healing" not in text
        assert "prevents all regressions" not in text
        # root-cause / guarantee must appear only as negations
        for token in ("root-cause", "guarantee"):
            for idx in _find_all(text, token):
                window = text[max(0, idx - 24) : idx]
                assert "no " in window or "not " in window, (doc.name, token)


def _find_all(text: str, token: str) -> list[int]:
    out, start = [], 0
    while True:
        i = text.find(token, start)
        if i == -1:
            return out
        out.append(i)
        start = i + 1
