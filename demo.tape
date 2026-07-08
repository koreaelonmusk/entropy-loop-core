# demo.tape — record `entropy-loop demo` to demo.gif with VHS.
#
# VHS: https://github.com/charmbracelet/vhs
#   brew install vhs      # or: go install github.com/charmbracelet/vhs@latest
#   vhs demo.tape         # produces demo.gif
#
# No GIF is committed to this repo; run the command above to generate one.

Output demo.gif

Set Shell "bash"
Set FontSize 18
Set Width 1100
Set Height 720
Set Padding 24
Set Theme "Dracula"
Set TypingSpeed 60ms

Type "entropy-loop demo"
Sleep 500ms
Enter
Sleep 3s

Type "entropy-loop doctor"
Sleep 300ms
Enter
Sleep 2s
