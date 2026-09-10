# Module note: Dark Theme Stylesheet Module.
# Purpose: Defines the dark color theme stylesheet string (Catppuccin Mocha-inspired palette) used across all window components.
# Plain-language overexplanation for beginners:
# This file contains all the CSS styling rules that give the desktop app its dark theme appearance.
# It sets background colors, font sizes, button rounded corners, hover highlight effects, and checkbox styling.

# Dark Theme Stylesheet Module.
# Purpose: Defines the dark color theme stylesheet string (Catppuccin Mocha-inspired palette) used across all window components.
# Layout Context: Sets global color values and typography across all visual widgets in MainWindow (1200x780 pixels).
# Signal & Hover Feedback: Dynamic visual changes on user focus, mouse hover, item selection, and button clicks.
# Testing value suggestions: Can test modifying hex colors or applying stylesheet string to individual PyQt6 widgets.
# Color palette options & choices:
#   - Base background (`QMainWindow`, `QWidget`): `#1e1e2e` (Dark Slate Blue)
#   - Container & input background (`QLineEdit`, `QComboBox`, `QTextEdit`, `QTableWidget`): `#181825` (Crust Dark)
#   - Accent primary color (`#exportButton`, active borders): `#89b4fa` (Lavender Blue Accent)
#   - Hover highlight background (`QPushButton:hover`): `#45475a` / `#b4befe`
#   - Text colors (`color`): `#cdd6f4` (Primary white-blue text), `#a6adc8` (Secondary header text)
# Typography choices: Standard font 'Inter' / 'Cantarell' 13px; fixed-width 'Monospace' 10pt for code preview.
# What happens when CSS rules are invalid: PyQt6 parser skips invalid property rules and defaults to native desktop theme.

# Complete rule-by-rule breakdown (13 rules total). For each rule: selector, properties, and visual effect.
#
# RULE 1  `QMainWindow, QWidget`
#   - background-color: #1e1e2e  -> paints the whole window canvas dark slate blue (the overall dark theme).
#   - color: #cdd6f4             -> default text color of every widget is a light blue-white.
#   - font-family / font-size: 13 -> every widget text renders in Cantarell/Inter fallback list at 13px.
#   - Tester values: change background-color to #11111b (near-black) or #000000 to test contrast; raise font-size to 14/16.
#
# RULE 2  `QGroupBox` (section containers like "Conversations & Sessions")
#   - border: 1px solid #45475a  -> thin slate border outlines each group box.
#   - border-radius: 8px         -> softly rounded 8px corners. Try 0 (square) or 16 (very round).
#   - margin-top: 10px           -> 10px gap above the border so the title text can float over it.
#   - padding-top: 12px          -> 12px space between the title and the group's inner content.
#   - font-weight: bold; color: #89b4fa -> group titles are bold lavender-blue.
#   - Tester values: margin-top 0..20, padding-top 4..20; verify the title stays legible at extremes.
#
# RULE 3  `QGroupBox::title`
#   - subcontrol-origin: margin; subcontrol-position: top left -> title sits at the top-left OVER the border line.
#   - padding: 0 5px             -> 5px horizontal breathing room around the title text.
#   - Tester values: top center / top right positions for a different title style.
#
# RULE 4  `QLineEdit, QComboBox, QTextEdit, QListWidget, QTableWidget` (all input/data widgets)
#   - background-color: #181825  -> dark crust fill for every editable/list area.
#   - color: #cdd6f4             -> light text inside inputs.
#   - border: 1px solid #313244  -> subtle dark border; the default (unfocused) input state.
#   - border-radius: 6px         -> softly rounded corners; try 0 (square) or 12 (pill-ish).
#   - padding: 6px               -> 6px inner padding so text does not touch the border.
#   - selection-background-color: #313244; selection-color: #89b4fa -> highlighted text: dark fill + lavender glyphs.
#   - Tester values: padding 0..12; selection colors can be swapped to #585b70 / #cdd6f4.
#
# RULE 5  `QLineEdit:focus, QComboBox:focus, QTextEdit:focus`
#   - border: 1px solid #89b4fa  -> focused input border turns lavender-blue to show keyboard focus.
#   - Tester note: focus is the only state here; :hover is not styled, so hovering changes nothing for inputs.
#
# RULE 6  `QHeaderView::section` (the header row of the session table)
#   - background-color: #181825  -> header cells share the dark crust fill.
#   - color: #a6adc8             -> muted blue-grey header labels.
# (UX Note: The header text color #a6adc8 on background #181825 has a contrast ratio of approximately 3.5:1,
#   which fails WCAG AA requirements (minimum 4.5:1 for normal text). Consider lightening the header text
#   color to #b4befe or darker to meet accessibility standards.)
#   - padding: 6px               -> 6px padding inside each header cell.
#   - border: 1px solid #313244  -> grid lines between header cells.
#   - font-weight: bold          -> "Status/Date/Agent/Scripts/Title" labels are bold.
#   - Tester values: color #89b4fa for an accent header look, or background-color #313244 for contrast.
#
# RULE 7  `QTableWidget::item:selected, QListWidget::item:selected`
#   - background-color: #313244  -> selected row/cell fill turns dark surface grey.
#   - color: #89b4fa             -> selected text turns lavender-blue.
#   - Tester values: try #45475a fill for a softer highlight.
#
# RULE 8  `QPushButton` (general buttons)
#   - background-color: #313244  -> default button fill dark grey.
#   - color: #cdd6f4             -> light button label text.
#   - border: 1px solid #45475a  -> slate border.
#   - border-radius: 6px         -> 6px rounded corners; try 0..20.
#   - padding: 8px 16px          -> 8px vertical, 16px horizontal padding (tall-ish buttons).
#   - font-weight: bold          -> button labels are bold.
#   - Tester values: padding 4px 8px for compact buttons; 12px 24px for large touch targets.
#
# RULE 9  `QPushButton:hover`
#   - background-color: #45475a  -> hover fill lightens one step toward slate.
#   - color: #89b4fa; border: 1px solid #89b4fa -> hover label and border both turn lavender.
#   - Tester values: #585b70 fill would be the pressed color leaked into hover (not recommended).
#
# RULE 10 `QPushButton:pressed`
#   - background-color: #585b70  -> the instant you press, fill darkens one more step.
#   - Tester note: color/border are unchanged while pressed; add rules here to tint them too.
#
# RULE 11 `QPushButton#exportButton` (the accent 💾 Export button)
#   - background-color: #89b4fa  -> solid lavender fill, the loudest color in the app.
#   - color: #11111b             -> near-black label text for high contrast on lavender.
#   - border: none               -> no border at all (flat design).
#   - font-size: 14px            -> one pixel larger than the 13px default (slightly more emphasis).
#   - Tester values: swap to #b4befe for a lighter button, or #181825 + #89b4fa text for an inverted look.
#
# RULE 12 `QPushButton#exportButton:hover`
#   - background-color: #b4befe  -> hover lightens the accent button to pale lavender.
#   - Tester note: label stays #11111b; border stays none.
#
# RULE 13 `QCheckBox`
#   - spacing: 8px               -> 8px horizontal gap between the box and its label text.
#   - Tester note: other checkbox styling is handled by QCheckBox::indicator rules below.
#
# RULE 14 `QCheckBox::indicator` (the little square box)
#   - width/height: 18px         -> 18x18 pixel square indicator (unchecked size).
#   - border-radius: 4px         -> slightly rounded square corners.
#   - border: 1px solid #45475a  -> slate outline.
#   - background-color: #181825  -> dark fill when unchecked.
#   - Tester values: 14px for compact boxes, 24px for touch-friendly boxes; radius 0 for sharp squares.
#
# RULE 15 `QCheckBox::indicator:checked`
#   - background-color: #89b4fa  -> checked state fills the box lavender.
#   - image: none                -> deliberately no native checkmark glyph is drawn.
#   - Tester note: because there is no image, the checked signal is a plain filled square.
#     To draw a real checkmark, swap `image: none` for `image: url(/path/check.svg)`.
#
# RULE 16 `QProgressBar` (footer progress bar container)
#   - border: 1px solid #313244; border-radius: 6px -> rounded dark outline.
#   - text-align: center         -> the percentage text centers inside the bar.
#   - background-color: #181825  -> the unfilled track is dark crust.
#   - color: #cdd6f4             -> percentage text is light.
#   - Tester values: border-radius 0..12; add font-weight: bold for heavier percentage text.
#
# RULE 17 `QProgressBar::chunk` (the colored fill segment)
#   - background-color: #89b4fa  -> the moving fill is lavender.
#   - border-radius: 5px         -> slightly rounded fill segment (matches the 6px bar, 1px border).
#   - Tester values: swap color to #a6e3a1 (green) or #f9e2af (yellow) for different progress feedback.

# Palette color coverage checklist:
#   Used by this stylesheet: #1e1e2e, #181825, #313244, #45475a, #585b70, #89b4fa, #b4befe, #11111b, #cdd6f4, #a6adc8.
#   Used elsewhere, not in this file: #a6e3a1 (green "✓ EXPORTED" text in gui/handlers/filter_sessions.py line 82).
#   Not used anywhere in the project: #f38ba8 (red) and #f9e2af (yellow); adding them is safe, nothing overrides them.
#
# (UX Note: Global font size is fixed at 13px with no support for system font scaling. Users who have set
#   their OS to use larger fonts will find the application text artificially constrained. Consider detecting
#   the system font size and adjusting accordingly, or providing a settings dialog to change font size.)
#
# (Accessibility Note: Focus indicators rely solely on border color changes (#89b4fa). Users with color
#   blindness may struggle to distinguish focused vs unfocused states. Consider adding a secondary focus
#   indicator such as a glow effect, inner shadow, or width change to make focus more discernible.)
#
# (Touch Note: Button padding is 8px vertical x 16px horizontal, creating touch targets approximately
#   32px tall. This falls short of the recommended 44x44dp minimum for touch interfaces (iOS HIG,
#   Material Design). Consider increasing padding to 12px 24px for better touch accessibility.)
#
# (Touch Note: Checkbox indicators are 18x18px, well below the 24x24px minimum recommended for touch
#   targets. This makes checkboxes difficult to click on touchscreens. Consider increasing to at least
#   24x24px via the QCheckBox::indicator width/height properties.)

# Line note: DARK_STYLESHEET holds the complete multi-line CSS rules applied to the application window via `self.setStyleSheet()`.
# Tester note: this is a plain str; print it to inspect, or concatenate extra rules onto it to layer styling.
DARK_STYLESHEET = """
/* Base window background (#1e1e2e) and global font family/size (13px) settings */
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Cantarell', 'Inter', 'DejaVu Sans', 'Noto Color Emoji', 'Segoe UI Emoji', 'Symbola', sans-serif;
    font-size: 13px;
}

/* Section container box styling with 1px border (#45475a), 8px rounded corners, 10px top margin, 12px top padding, and blue title text (#89b4fa) */
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 12px;
    font-weight: bold;
    color: #89b4fa;
}

/* Group box header title positioning aligned to top left with 5px horizontal padding */
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
}

/* Input fields, dropdown menus, text areas, lists, and tables background (#181825), border (#313244), 6px radius, and 6px padding */
QLineEdit, QComboBox, QTextEdit, QListWidget, QTableWidget {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #313244;
    selection-color: #89b4fa;
}

/* Input field focus indicator signal state: turns 1px border to primary accent blue (#89b4fa) */
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #89b4fa;
}

/* Table header column labels styling with crust background (#181825), muted header text (#a6adc8), 6px padding, and bold weight */
QHeaderView::section {
    background-color: #181825;
    color: #a6adc8;
    padding: 6px;
    border: 1px solid #313244;
    font-weight: bold;
}

/* Table and list item selection highlight colors (#313244 background with #89b4fa text) */
QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #313244;
    color: #89b4fa;
}

/* General button design for standard action buttons with 6px rounded corners and 8px 16px padding */
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}

/* Button mouse hover signal state: changes background to #45475a and border/text to blue (#89b4fa) */
QPushButton:hover {
    background-color: #45475a;
    color: #89b4fa;
    border: 1px solid #89b4fa;
}

/* Button pressed signal state: darkens background to #585b70 */
QPushButton:pressed {
    background-color: #585b70;
}

/* Accent highlight styling specifically for the main Export button (#exportButton) with prominent blue (#89b4fa) and 14px text */
QPushButton#exportButton {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
    font-size: 14px;
}

/* Export button hover signal state: lightens background to #b4befe */
QPushButton#exportButton:hover {
    background-color: #b4befe;
}

/* Checkbox toggle controls spacing (8px gap between box and text label) */
QCheckBox {
    spacing: 8px;
}

/* Checkbox visual box indicator: 18x18 pixels square with 4px rounded corners and #181825 dark fill */
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #45475a;
    background-color: #181825;
}

/* Checkbox checked signal state: fills box indicator with blue (#89b4fa) */
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    image: none;
}

/* Progress indicator bar container styling with 6px rounded corners and #181825 background */
QProgressBar {
    border: 1px solid #313244;
    border-radius: 6px;
    text-align: center;
    background-color: #181825;
    color: #cdd6f4;
}

/* Progress bar fill chunk animation: blue (#89b4fa) with 5px rounded corners */
QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 5px;
}
"""
