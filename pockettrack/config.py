"""
Configuration settings, constants, theme colours, and formatting standards
for the PocketTrack application.
"""
import os

# ==========================================
# FILE PATHS
# ==========================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "expenses.txt")
STYLE_FILE = os.path.join(BASE_DIR, "assets", "style.css")


# ==========================================
# FORMATTING STANDARDS
# ==========================================

CURRENCY_SYMBOL = "₹"
DATE_STORAGE_FORMAT = "%d-%m-%Y"
DATE_DISPLAY_FORMAT = "%d %b %Y"
MONTH_DISPLAY_FORMAT = "%b %Y"
MONTH_FULL_FORMAT = "%B %Y"


# ==========================================
# THEME COLOURS (pastel green palette)
# ==========================================

BG = "#F3FAF1"          # very light mint cream
SIDEBAR = "#DFF3E3"     # soft green
CARD = "#FFFFFF"        # white cards
BORDER = "#BFE5CB"      # green border
GREEN = "#7BCB98"       # main pastel green
DEEP_GREEN = "#3E9A6A"  # darker green for headings
SOFT_GREEN = "#DFF5E6"  # very soft green fill
SKY = "#BBD9F0"
BUTTER = "#FFF1A8"
PEACH = "#FFD3B6"
MINT = "#A8E6CF"
LAVENDER = "#D9CCFF"
TEXT = "#3F5247"        # deep green-grey text
MUTED = "#7B8F83"       # soft grey-green
GRID_GREEN = "#E3F3E8"
BUTTON_HOVER_GREEN = "#93D8AB"
BG_RADIAL_DOT = "#DCEFE0"


# ==========================================
# CATEGORIES & SPEND BUCKETS
# ==========================================

CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Education",
    "Bills",
    "Entertainment",
    "Health",
    "Other"
]

# Spending ranges for the daily ring.
# Each item is (label, upper limit, colour).
# The last range has no upper limit (None).
SPEND_BUCKETS = [
    ("0", 0, "#EEF3EE"),
    ("1-20", 20, "#DDF3E4"),
    ("21-40", 40, "#BDE8CB"),
    ("41-60", 60, "#9DDDB3"),
    ("61-80", 80, "#7BCB98"),
    ("81-100", 100, "#5DB880"),
    ("101-150", 150, "#3F9F68"),
    ("151+", None, "#2D7F52")
]

