"""A deterministic, self-contained HTML report — the Pixel Failure Console.

Renders a :class:`~entropy_loop_core.triage.RegressionTriage` as a single HTML
file a human can read at a glance: summary cards, the policy result, and sections
for new / persistent / resolved / skipped cases. It is intentionally
self-contained — inline CSS only, no external stylesheets, scripts, fonts, images,
or network requests — and deterministic: no timestamps, no hostnames, standard
library only.

The visual language is a tasteful, terminal-style, pixel-art inspired dark theme
built purely from CSS. It reads fine without JavaScript and prints reasonably.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

from .contract import JUNIT_SEMANTICS
from .triage import CaseTransition, RegressionTriage

_TITLE = "Entropy Loop Failure Console"
_SUBTITLE = "AI agent regressions as CI evidence"

_EVIDENCE_FILES = ("manifest.json", "summary.txt", "triage.json", "triage.md")

_SUGGESTED_COMMAND = (
    "entropy-loop write-ci-evidence baseline.json current.json \\\n"
    "  --fail-on new-failures \\\n"
    "  --evidence-dir reports/entropy-loop-evidence \\\n"
    "  --junit-report reports/entropy-loop-junit.xml \\\n"
    "  --html-report reports/entropy-loop.html"
)

# Inline, self-contained, pixel-art inspired dark terminal theme. No URLs.
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
}
.wrap { max-width: 900px; margin: 0 auto; }
.pixelbar {
  height: 10px; margin-bottom: 16px;
  background: repeating-linear-gradient(90deg,
    var(--new) 0 10px, var(--persist) 10px 20px, var(--resolved) 20px 30px,
    var(--skip) 30px 40px, var(--accent) 40px 50px);
  image-rendering: pixelated;
}
h1 { font-size: 22px; margin: 0; letter-spacing: 1px; }
.subtitle { color: var(--muted); margin: 4px 0 2px; }
.meta { color: var(--muted); font-size: 13px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px; margin: 20px 0; }
.card { background: var(--panel); border: 2px solid var(--line);
  box-shadow: 4px 4px 0 #05070b; padding: 12px 14px; }
.card .n { font-size: 30px; font-weight: 700; }
.card .l { color: var(--muted); font-size: 12px; text-transform: uppercase;
  letter-spacing: 1px; }
.card.new .n { color: var(--new); }
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
""".strip()


def _card(label: str, value: int, cls: str = "") -> str:
    css = f"card {cls}".strip()
    return (
        f'<div class="{css}"><div class="n">{value}</div>'
        f'<div class="l">{escape(label)}</div></div>'
    )


def _group(triage: RegressionTriage, transition: str) -> list[CaseTransition]:
    return [t for t in triage.transitions if t.transition == transition]


def _section(title: str, transitions: list[CaseTransition]) -> str:
    parts = [f"<h2>{escape(title)}</h2>"]
    if not transitions:
        parts.append('<p class="empty">None.</p>')
        return "\n".join(parts)
    items = ["<ul>"]
    for t in transitions:
        message = t.current_message or t.baseline_message
        suffix = f' <span class="msg">— {escape(message)}</span>' if message else ""
        items.append(f'<li><span class="id">{escape(t.case_id)}</span>{suffix}</li>')
    items.append("</ul>")
    parts.append("\n".join(items))
    return "\n".join(parts)


def export_regression_triage_html(triage: RegressionTriage) -> str:
    """Render a triage as a deterministic, self-contained HTML report."""
    from . import __version__

    result_cls = "pass" if triage.success else "fail"
    result_word = "PASS" if triage.success else "FAIL"
    policy = escape(triage.policy or "new-failures")

    cards = "".join(
        [
            _card("Total cases", triage.case_count),
            _card("New failures", triage.new_failure_count, "new"),
            _card("Persistent failures", triage.persistent_failure_count, "persist"),
            _card("Resolved", triage.fixed_count, "resolved"),
            _card(
                "Skipped / missing", triage.skipped_count + triage.missing_count, "skip"
            ),
        ]
    )

    evidence = "\n".join(
        f'<li><span class="id">{escape(f)}</span></li>' for f in _EVIDENCE_FILES
    )

    body = f"""<div class="wrap">
<div class="pixelbar"></div>
<h1>{escape(_TITLE)}</h1>
<p class="subtitle">{escape(_SUBTITLE)}</p>
<p class="meta">entropy-loop-core v{escape(__version__)} · policy: {policy}</p>

<div class="cards">{cards}</div>

<div class="result {result_cls}">
  <span class="badge">{result_word}</span>
  &nbsp;{escape(triage.summary)}
</div>

<p class="note">{escape(JUNIT_SEMANTICS)}</p>

{_section("New Failures", _group(triage, "new_failure"))}
{_section("Persistent Failures", _group(triage, "persistent_failure"))}
{_section("Resolved Cases", _group(triage, "fixed"))}
{
        _section(
            "Skipped / Missing Cases",
            _group(triage, "new_skip")
            + _group(triage, "still_skipped")
            + _group(triage, "missing_in_current"),
        )
    }

<h2>Evidence Files</h2>
<ul>
{evidence}
</ul>

<h2>Suggested CI Command</h2>
<pre>{escape(_SUGGESTED_COMMAND)}</pre>

<footer>
Deterministic local report · no network calls · no telemetry ·
no GitHub API calls · not root-cause analysis · no guaranteed-correctness claims.
</footer>
</div>"""

    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(_TITLE)}</title>\n"
        f"<style>\n{_STYLE}\n</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


def write_regression_triage_html(triage: RegressionTriage, path: str | Path) -> None:
    """Write a triage HTML report to ``path`` (creating parent directories)."""
    target = Path(path)
    if target.parent != Path(""):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(export_regression_triage_html(triage), encoding="utf-8")
