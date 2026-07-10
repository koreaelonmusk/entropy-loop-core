"""A deterministic, self-contained HTML report — the Pixel Failure Console.

Renders a :class:`~entropy_loop_core.triage.RegressionTriage` as a single HTML
file a human can read at a glance: summary cards, the policy result, and sections
for new / persistent / resolved / skipped cases. It supports English (``en``) and
Korean (``ko``) locales.

It is intentionally self-contained — inline CSS only, no external stylesheets,
scripts, fonts, images, or network requests — and deterministic: no timestamps,
no hostnames, standard library only. The pixel-art inspired dark theme uses subtle
CSS-only motion that is fully disabled under ``prefers-reduced-motion: reduce``,
and every section is readable without animation or JavaScript.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

from .contract import JUNIT_SEMANTICS
from .triage import CaseTransition, RegressionTriage

# Supported HTML report locales.
HTML_LOCALES = ("en", "ko")

_EVIDENCE_FILES = ("manifest.json", "summary.txt", "triage.json", "triage.md")

_SUGGESTED_COMMAND = (
    "entropy-loop write-ci-evidence baseline.json current.json \\\n"
    "  --fail-on new-failures \\\n"
    "  --evidence-dir reports/entropy-loop-evidence \\\n"
    "  --junit-report reports/entropy-loop-junit.xml \\\n"
    "  --html-report reports/entropy-loop.html"
)

_KO_SEMANTICS = (
    "JUnit 실패는 리포트에 표시되는 회귀/테스트 상태를 의미하며, "
    "실제 프로세스 종료 코드는 선택한 fail-on 정책이 결정합니다."
)

_STRINGS = {
    "en": {
        "title": "Entropy Loop Failure Console",
        "subtitle": "AI agent regressions as CI evidence",
        "pass": "PASS",
        "fail": "FAIL",
        "policy": "policy",
        "c_total": "Total cases",
        "c_new": "New failures",
        "c_persist": "Persistent failures",
        "c_resolved": "Resolved",
        "c_skip": "Skipped / missing",
        "s_new": "New Failures",
        "s_persist": "Persistent Failures",
        "s_resolved": "Resolved Cases",
        "s_skip": "Skipped / Missing Cases",
        "s_evidence": "Evidence Files",
        "s_command": "Suggested CI Command",
        "empty": "None.",
        "semantics": JUNIT_SEMANTICS,
        "footer": (
            "Deterministic local report · no network calls · no telemetry · "
            "no GitHub API calls · not root-cause analysis · "
            "no guaranteed-correctness claims."
        ),
    },
    "ko": {
        "title": "엔트로피 루프 실패 콘솔",
        "subtitle": "AI 에이전트 회귀를 CI 증거로 변환",
        "pass": "통과",
        "fail": "실패",
        "policy": "정책",
        "c_total": "전체 케이스",
        "c_new": "신규 실패",
        "c_persist": "지속 실패",
        "c_resolved": "해결됨",
        "c_skip": "건너뜀 / 누락",
        "s_new": "신규 실패",
        "s_persist": "지속 실패",
        "s_resolved": "해결된 케이스",
        "s_skip": "건너뜀 / 누락 케이스",
        "s_evidence": "증거 파일",
        "s_command": "추천 CI 명령어",
        "empty": "없음.",
        "semantics": _KO_SEMANTICS,
        "footer": (
            "결정적 로컬 리포트 · 네트워크 호출 없음 · 텔레메트리 없음 · "
            "GitHub API 호출 없음 · 근본 원인 분석 아님 · 정확성 보장 없음."
        ),
    },
}

# Inline, self-contained, pixel-art inspired dark terminal theme with subtle
# CSS-only motion. No URLs, no external assets. Motion is disabled under
# prefers-reduced-motion.
_STYLE = """
:root {
  --bg: #0d0f14; --panel: #141821; --ink: #e6edf3; --muted: #8b98a5;
  --line: #2a313c; --new: #ff5c57; --persist: #ffb454; --resolved: #5cff8f;
  --skip: #6ab0ff; --accent: #b18cff;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font-family: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace;
  line-height: 1.5; padding: 24px;
  background-image: linear-gradient(var(--line) 1px, transparent 1px),
    linear-gradient(90deg, var(--line) 1px, transparent 1px);
  background-size: 22px 22px; background-blend-mode: soft-light;
}
.wrap { max-width: 900px; margin: 0 auto; animation: boot 600ms ease-out both; }
.pixelbar {
  height: 10px; margin-bottom: 16px;
  background: repeating-linear-gradient(90deg,
    var(--new) 0 10px, var(--persist) 10px 20px, var(--resolved) 20px 30px,
    var(--skip) 30px 40px, var(--accent) 40px 50px);
  background-size: 250px 10px; image-rendering: pixelated;
  animation: shimmer 6s linear infinite;
}
h1 { font-size: 22px; margin: 0; letter-spacing: 1px; }
.subtitle { color: var(--muted); margin: 4px 0 2px; }
.meta { color: var(--muted); font-size: 13px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px; margin: 20px 0; }
.card { background: var(--panel); border: 2px solid var(--line);
  box-shadow: 4px 4px 0 #05070b; padding: 12px 14px;
  transition: transform 120ms ease, box-shadow 120ms ease; }
.card:hover { transform: translateY(-2px); box-shadow: 6px 6px 0 #05070b; }
.card .n { font-size: 30px; font-weight: 700; }
.card .l { color: var(--muted); font-size: 12px; text-transform: uppercase;
  letter-spacing: 1px; }
.card.new .n { color: var(--new); animation: pulse 2.4s ease-in-out infinite; }
.card.persist .n { color: var(--persist); }
.card.resolved .n { color: var(--resolved); }
.card.skip .n { color: var(--skip); }
.result { border: 2px solid var(--line); background: var(--panel);
  padding: 12px 14px; margin: 8px 0 20px; }
.result.pass { border-color: var(--resolved); }
.result.fail { border-color: var(--new); }
.badge { display: inline-block; padding: 2px 8px; border: 2px solid currentColor;
  font-weight: 700; }
.pass .badge { color: var(--resolved); }
.fail .badge { color: var(--new); }
.note { color: var(--muted); font-size: 13px; border-left: 3px solid var(--accent);
  padding-left: 10px; margin: 16px 0; }
h2 { font-size: 15px; text-transform: uppercase; letter-spacing: 1px;
  border-bottom: 2px solid var(--line); padding-bottom: 6px; margin: 24px 0 10px; }
ul { list-style: none; padding: 0; margin: 0; }
li { padding: 6px 0; border-bottom: 1px dashed var(--line); }
li .id { color: var(--ink); font-weight: 700; }
li .msg { color: var(--muted); }
.empty { color: var(--muted); }
pre { background: #05070b; border: 2px solid var(--line); padding: 12px;
  overflow-x: auto; color: var(--resolved); }
footer { color: var(--muted); font-size: 12px; margin-top: 28px;
  border-top: 2px solid var(--line); padding-top: 12px; }
@keyframes boot { from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: none; } }
@keyframes shimmer { from { background-position: 0 0; }
  to { background-position: 250px 0; } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.72; } }
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
  .wrap { opacity: 1; transform: none; }
}
""".strip()


def _card(label: str, value: int, cls: str = "") -> str:
    css = f"card {cls}".strip()
    return (
        f'<div class="{css}"><div class="n">{value}</div>'
        f'<div class="l">{escape(label)}</div></div>'
    )


def _group(triage: RegressionTriage, transition: str) -> list[CaseTransition]:
    return [t for t in triage.transitions if t.transition == transition]


def _section(title: str, transitions: list[CaseTransition], empty: str) -> str:
    parts = [f"<h2>{escape(title)}</h2>"]
    if not transitions:
        parts.append(f'<p class="empty">{escape(empty)}</p>')
        return "\n".join(parts)
    items = ["<ul>"]
    for t in transitions:
        message = t.current_message or t.baseline_message
        suffix = f' <span class="msg">— {escape(message)}</span>' if message else ""
        items.append(f'<li><span class="id">{escape(t.case_id)}</span>{suffix}</li>')
    items.append("</ul>")
    parts.append("\n".join(items))
    return "\n".join(parts)


def export_regression_triage_html(triage: RegressionTriage, locale: str = "en") -> str:
    """Render a triage as a deterministic, self-contained HTML report.

    Args:
        triage: The triage to render.
        locale: ``"en"`` (default) or ``"ko"``.

    Raises:
        ValueError: If ``locale`` is not a supported locale.
    """
    if locale not in HTML_LOCALES:
        allowed = ", ".join(HTML_LOCALES)
        raise ValueError(f"unsupported locale {locale!r} (expected one of: {allowed})")
    from . import __version__

    s = _STRINGS[locale]
    result_cls = "pass" if triage.success else "fail"
    result_word = s["pass"] if triage.success else s["fail"]
    policy = escape(triage.policy or "new-failures")

    cards = "".join(
        [
            _card(s["c_total"], triage.case_count),
            _card(s["c_new"], triage.new_failure_count, "new"),
            _card(s["c_persist"], triage.persistent_failure_count, "persist"),
            _card(s["c_resolved"], triage.fixed_count, "resolved"),
            _card(s["c_skip"], triage.skipped_count + triage.missing_count, "skip"),
        ]
    )

    evidence = "\n".join(
        f'<li><span class="id">{escape(f)}</span></li>' for f in _EVIDENCE_FILES
    )

    skip_group = (
        _group(triage, "new_skip")
        + _group(triage, "still_skipped")
        + _group(triage, "missing_in_current")
    )
    meta = f"entropy-loop-core v{escape(__version__)} · {escape(s['policy'])}: {policy}"

    body = f"""<div class="wrap">
<div class="pixelbar"></div>
<h1>{escape(s["title"])}</h1>
<p class="subtitle">{escape(s["subtitle"])}</p>
<p class="meta">{meta}</p>

<div class="cards">{cards}</div>

<div class="result {result_cls}">
  <span class="badge">{escape(result_word)}</span>
  &nbsp;{escape(triage.summary)}
</div>

<p class="note">{escape(s["semantics"])}</p>

{_section(s["s_new"], _group(triage, "new_failure"), s["empty"])}
{_section(s["s_persist"], _group(triage, "persistent_failure"), s["empty"])}
{_section(s["s_resolved"], _group(triage, "fixed"), s["empty"])}
{_section(s["s_skip"], skip_group, s["empty"])}

<h2>{escape(s["s_evidence"])}</h2>
<ul>
{evidence}
</ul>

<h2>{escape(s["s_command"])}</h2>
<pre>{escape(_SUGGESTED_COMMAND)}</pre>

<footer>{escape(s["footer"])}</footer>
</div>"""

    return (
        "<!doctype html>\n"
        f'<html lang="{escape(locale)}">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(s['title'])}</title>\n"
        f"<style>\n{_STYLE}\n</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


def write_regression_triage_html(
    triage: RegressionTriage, path: str | Path, locale: str = "en"
) -> None:
    """Write a triage HTML report to ``path`` (creating parent directories)."""
    target = Path(path)
    if target.parent != Path(""):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        export_regression_triage_html(triage, locale=locale), encoding="utf-8"
    )
