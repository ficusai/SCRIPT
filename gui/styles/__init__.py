# Styles package initialization file.
# Purpose: Exports DARK_STYLESHEET string containing Catppuccin-inspired dark theme styling rules for Qt widgets.
# Layout Context: Controls colors for all window components (#1e1e2e base background, #181825 input dark fill, #89b4fa primary accents).
# Signal & Event Theme Effects: Button hover states change background to #45475a and text/border to #89b4fa; press state changes background to #585b70.
# Testing value suggestions: Import stylesheet string in Python REPL (`from gui.styles import DARK_STYLESHEET`).
# Parameter choices: DARK_STYLESHEET provides dark theme CSS rules (#1e1e2e base background, #89b4fa accent highlight).
# What happens if empty/invalid: If stylesheet string is empty or invalid, PyQt6 widgets fall back to standard OS native styling.

# How to experiment with the theme (tester options):
#   - Apply to one widget only: `win.session_table.setStyleSheet("QTableWidget { background-color: #181825; }")`
#     overrides the global stylesheet for that widget.
#   - Reset everything: `win.setStyleSheet("")` returns every widget to the native OS look.
#   - Layer extra rules: `win.setStyleSheet(DARK_STYLESHEET + "\nQPushButton { padding: 12px; }")`.
#   - Inspect the raw string: `print(DARK_STYLESHEET)` shows every rule documented in dark_stylesheet.py.

# Palette summary produced by this stylesheet:
#   - #1e1e2e base window background; #181825 input/table/header fills.
#   - #313244 widget surfaces, borders for inputs, and selection highlight.
#   - #45475a group-box/button borders and button hover fill.
#   - #585b70 pressed-button fill.
#   - #89b4fa primary accent (focus borders, selected text, button fills, progress chunk).
#   - #b4befe lighter accent used for the Export button hover fill.
#   - #cdd6f4 primary text; #a6adc8 muted header text; #11111b near-black text on the accent Export button.

# Line note: Import and expose the DARK_STYLESHEET string variable containing Qt CSS rules.
from .dark_stylesheet import DARK_STYLESHEET
