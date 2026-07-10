# docs/assets/demo-v1.tape — README demo GIF for the v1.0.0 launch.
#
# Records the REAL CLI, no fake output, no network:
#   version 1.0.0 -> doctor -> replay-demo -> CI reports (JSON/Markdown/JUnit/HTML)
#   -> Korean HTML console -> stability contract (boundaries + package_version).
#
# VHS: https://github.com/charmbracelet/vhs
#   vhs docs/assets/demo-v1.tape   ->   docs/assets/demo.gif

Output docs/assets/demo.gif

Set Shell "bash"
Set FontSize 20
Set Width 1220
Set Height 760
Set Padding 30
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set Framerate 24
Set TypingSpeed 32ms

# Hidden setup: activate the CLI, use a clean prompt (no username/paths), pick a
# short output dir. Only real commands appear on screen.
Hide
Type "source .venv/bin/activate 2>/dev/null || true"
Enter
Type "export PS1='$ '"
Enter
Type "export PS2='  '"
Enter
Type "D=/tmp/entropy-loop-demo"
Enter
Type "clear"
Enter
Show

# 1 — Identity: version 1.0.0 and a healthy install.
Sleep 400ms
Type `python -c "import entropy_loop_core as e; print(e.__version__)"`
Enter
Sleep 900ms
Type "entropy-loop doctor"
Enter
Sleep 1300ms

Hide
Type "clear"
Enter
Show

# 2 — The loop: capture a failure, replay it as a regression case.
Type "entropy-loop replay-demo"
Enter
Sleep 2200ms

Hide
Type "clear"
Enter
Show

# 3 — CI-readable evidence: JSON / Markdown / JUnit XML / HTML console.
Type "rm -rf $D && mkdir -p $D"
Enter
Sleep 300ms
Type "entropy-loop compare-reports examples/baseline_regression_report.json examples/current_regression_report.json --fail-on never --json-report $D/triage.json --markdown-report $D/triage.md --junit-report $D/triage.xml --html-report $D/triage.html --html-locale en"
Enter
Sleep 1300ms
Type "ls -1 $D"
Enter
Sleep 1300ms

# 4 — Bilingual: a Korean HTML failure console.
Type "entropy-loop compare-reports examples/baseline_regression_report.json examples/current_regression_report.json --fail-on never --html-report $D/triage-ko.html --html-locale ko"
Enter
Sleep 1300ms

Hide
Type "clear"
Enter
Show

# 5 — The stable contract: deterministic boundaries and package_version 1.0.0.
Type "entropy-loop contract | python -m json.tool | head -20"
Enter
Sleep 2000ms
Type `entropy-loop contract | python -m json.tool | grep -E '"(project|contract_version|package_version)"'`
Enter
Sleep 2000ms
