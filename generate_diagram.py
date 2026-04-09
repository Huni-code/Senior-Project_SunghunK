"""Generate pipeline architecture diagram as PNG."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(13, 7.5))
ax.set_xlim(0, 13)
ax.set_ylim(0, 7.5)
ax.axis("off")
fig.patch.set_facecolor("white")

def box(ax, x, y, w, h, text, color="#dce8f7", fontsize=9.5):
    rect = mpatches.FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.12", linewidth=1.3,
        edgecolor="#4a6fa5", facecolor=color, zorder=2)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color="#1a1a2e",
            multialignment="center", zorder=3)

def arrow_straight(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color="#4a6fa5", lw=1.5),
        zorder=1)

def arrow_corner(ax, x1, y1, xmid, ymid, x2, y2):
    """L-shaped arrow via midpoint."""
    ax.annotate("", xy=(xmid, ymid), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-", color="#4a6fa5", lw=1.5), zorder=1)
    ax.annotate("", xy=(x2, y2), xytext=(xmid, ymid),
        arrowprops=dict(arrowstyle="-|>", color="#4a6fa5", lw=1.5), zorder=1)

# ── Column centers ──────────────────────────────────────────────
BW, BH = 2.4, 1.0   # box width, height
X = [0.3, 3.2, 6.1, 9.0]   # left edges of 4 columns
CX = [x + BW/2 for x in X]  # centers: 1.5, 4.4, 7.3, 10.2

# ── Row 1: Data Sources (y = 5.9–6.9) ─────────────────────────
Y1 = 5.9
box(ax, X[0], Y1, BW, BH, "builtin.com\n(Web Scraper)",        color="#d4edda")
box(ax, X[1], Y1, BW, BH, "SEC EDGAR\n(Financial API)",         color="#d4edda")
box(ax, X[2], Y1, BW, BH, "Stack Overflow\nSurvey (CSV)",       color="#d4edda")
box(ax, X[3], Y1, BW, BH, "BLS\n(Employment API)",              color="#d4edda")
ax.text(6.0, 7.15, "Data Sources", ha="center", fontsize=10.5,
        color="#2c6e49", fontstyle="italic", fontweight="bold")

# ── Row 2: Pipeline (y = 4.1–5.1) ─────────────────────────────
Y2 = 4.1
box(ax, X[0], Y2, BW, BH, "Playwright\nScraper\n(7,601 raw)",   color="#fff3cd")
box(ax, X[1], Y2, BW, BH, "CIK Matcher\n+ EDGAR API\n(15,952 rows)", color="#fff3cd")
box(ax, X[2], Y2, BW, BH, "SO Survey\nAnalyzer\n(2017–2025)",   color="#fff3cd")
box(ax, X[3], Y2, BW, BH, "BLS\nProcessor\n(11 sectors)",       color="#fff3cd")
ax.text(6.0, 5.38, "Processing Pipeline (Python)", ha="center", fontsize=10.5,
        color="#7b4f00", fontstyle="italic", fontweight="bold")

# ── Row 3: LLM (left) + SQLite DB (center-wide) ───────────────
Y3 = 2.2
box(ax, X[0], Y3, BW, BH, "LLM Classification\n(Claude Haiku)\n16 sectors · 5 rev models",
    color="#ffd6e7", fontsize=9)

# DB box spans columns 1–3
DB_X, DB_W = X[1], X[3] + BW - X[1]   # from col1 left to col3 right = 3.2 to 11.4
box(ax, DB_X, Y3, DB_W, BH,
    "SQLite Database  (data/companies.db)       10 tables · 4,001 companies",
    color="#dce8f7", fontsize=10)

# ── Row 4: Dashboard ───────────────────────────────────────────
Y4 = 0.4
DASH_X = 3.5
DASH_W = 5.5
box(ax, DASH_X, Y4, DASH_W, BH,
    "Streamlit Dashboard  (dashboard.py · Streamlit Cloud)       6 Sections · Opportunity Score",
    color="#d4edda", fontsize=10)

# ── Arrows: Row1 → Row2 (straight down) ───────────────────────
for cx in CX:
    arrow_straight(ax, cx, Y1, cx, Y2 + BH)

# ── Arrows: Row2 → Row3 ───────────────────────────────────────
# Playwright → LLM (straight down)
arrow_straight(ax, CX[0], Y2, CX[0], Y3 + BH)

# LLM → DB (straight right)
arrow_straight(ax, X[0] + BW, Y3 + BH/2, DB_X, Y3 + BH/2)

# CIK Matcher → DB top (straight down)
arrow_straight(ax, CX[1], Y2, CX[1], Y3 + BH)

# SO Analyzer → DB top (straight down)
arrow_straight(ax, CX[2], Y2, CX[2], Y3 + BH)

# BLS Processor → DB right edge (L-shaped: down then left)
BLS_CX = CX[3]
DB_RIGHT = DB_X + DB_W
arrow_corner(ax, BLS_CX, Y2,
             BLS_CX, Y3 + BH/2,
             DB_RIGHT, Y3 + BH/2)

# ── Arrow: DB → Dashboard ─────────────────────────────────────
DB_CENTER_X = DB_X + DB_W / 2
arrow_straight(ax, DB_CENTER_X, Y3, DB_CENTER_X, Y4 + BH)

plt.tight_layout(pad=0.5)
plt.savefig("architecture_diagram.png", dpi=150, bbox_inches="tight",
            facecolor="white")
print("Saved: architecture_diagram.png")
