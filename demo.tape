# demo.tape — record `entropy-loop demo` to demo.gif with VHS.
#
# VHS: https://github.com/charmbracelet/vhs
#   brew install vhs      # or: go install github.com/charmbracelet/vhs@latest
#   vhs demo.tape         # produces demo.gif
#
# No GIF is committed to source; run the command above to (re)generate one.

Output demo.gif

Set Shell "bash"
Set FontSize 18
Set Width 1100
Set Height 720
Set Padding 24
Set Theme "Dracula"
Set TypingSpeed 55ms

# Put the CLI on PATH without showing the setup in the recording. Works from the
# repo root after `pip install -e ".[dev]"`; falls back to whatever is on PATH.
Hide
Type "source .venv/bin/activate 2>/dev/null || true"
Enter
Type "clear"
Enter
Show

Type "entropy-loop demo"
Sleep 500ms
Enter
Sleep 3s

Type "entropy-loop doctor"
Sleep 300ms
Enter
Sleep 2s
