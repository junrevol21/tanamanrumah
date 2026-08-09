"""Buka URL di browser default (lebih andal daripada cmd start di mesin ini)."""
import sys
import webbrowser

if len(sys.argv) < 2:
    print("Pakai: python open_url.py <url>")
    sys.exit(1)
webbrowser.open(sys.argv[1])
print("Browser dibuka:", sys.argv[1][:80])
