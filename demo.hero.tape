# demo.hero.tape — cinematic README hero GIF for v0.3.0 replay.
#
# Scene 1: a clean narrative frame. Scene 2: the REAL `entropy-loop replay-demo`.
# The narrative printer is defined in a hidden setup block, so only clean
# commands appear on screen.
# VHS: https://github.com/charmbracelet/vhs
#   vhs demo.hero.tape   ->   docs/assets/demo.gif
#
# `demo.tape` remains the plain, lower-level recording asset.

Output docs/assets/demo.gif

Set Shell "bash"
Set FontSize 22
Set Width 1200
Set Height 720
Set Padding 40
Set Theme "Dracula"
Set WindowBar Colorful
Set TypingSpeed 55ms

# Hidden setup: activate the CLI, use a clean prompt, and define the narrative.
Hide
Type "source .venv/bin/activate 2>/dev/null || true"
Enter
Type "export PS1='$ '"
Enter
Type "story() { printf '\n  Entropy Loop Core v0.3.0\n  A Failure Compiler for AI agents\n\n  AI agents often fail the same way twice.\n  Turn failed outputs into regression cases.\n  Replay them before the same bug ships again.\n\n  FailureTrace -> Lesson -> RegressionCase -> Replay -> Report\n\n'; }"
Enter
Type "clear"
Enter
Show

# Scene 1 — the problem and the loop.
Sleep 700ms
Type "story"
Enter
Sleep 4s

# Scene cut to a clean screen.
Hide
Type "clear"
Enter
Show

# Scene 2 — the real command and its result.
Type "entropy-loop replay-demo"
Sleep 400ms
Enter
Sleep 4s
