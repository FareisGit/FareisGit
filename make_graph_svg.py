#!/usr/bin/env python3
"""
Render the live GitHub contribution calendar as a dark-themed SVG.

ghchart.rshah.org works but paints a light background, which looks wrong
against a dark profile README. This pulls the same data from GitHub's GraphQL
API (via `gh`) and draws it in GitHub's own dark palette instead.
"""

import json
import subprocess
import sys

USER = sys.argv[1] if len(sys.argv) > 1 else "FareisGit"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/contributions.svg"

QUERY = """
{
  user(login: "%s") {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { firstDay contributionDays { date weekday contributionCount } }
      }
    }
  }
}
""" % USER

raw = subprocess.run(
    ["gh", "api", "graphql", "-f", "query=" + QUERY],
    capture_output=True, text=True, check=True,
).stdout
cal = json.loads(raw)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = cal["weeks"]

# GitHub's dark-theme palette
EMPTY = "#161b22"
LEVELS = ["#0e4429", "#006d32", "#26a641", "#39d353"]
TEXT = "#7d8590"

CELL, GAP = 11, 3
STRIDE = CELL + GAP
PAD_L, PAD_T = 30, 20

counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
peak = max(counts) if counts else 0


def shade(n):
    if n <= 0:
        return EMPTY
    if peak <= 0:
        return LEVELS[0]
    q = n / peak
    if q <= 0.25:
        return LEVELS[0]
    if q <= 0.50:
        return LEVELS[1]
    if q <= 0.75:
        return LEVELS[2]
    return LEVELS[3]


width = PAD_L + len(weeks) * STRIDE + 6
height = PAD_T + 7 * STRIDE + 4

parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
    'viewBox="0 0 %d %d" role="img" aria-label="Contribution graph">'
    % (width, height, width, height),
    '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",'
    'Helvetica,Arial,sans-serif;font-size:9px;fill:%s}</style>' % TEXT,
    '<rect width="100%%" height="100%%" fill="none"/>',
]

# month labels
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
last_month = None
for x, w in enumerate(weeks):
    month = int(w["firstDay"][5:7])
    if month != last_month:
        parts.append('<text x="%d" y="%d">%s</text>'
                     % (PAD_L + x * STRIDE, PAD_T - 7, MONTHS[month - 1]))
        last_month = month

# weekday labels
for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
    parts.append('<text x="0" y="%d">%s</text>'
                 % (PAD_T + row * STRIDE + CELL - 1, label))

# cells
for x, w in enumerate(weeks):
    for d in w["contributionDays"]:
        parts.append(
            '<rect x="%d" y="%d" width="%d" height="%d" rx="2" ry="2" fill="%s"/>'
            % (PAD_L + x * STRIDE, PAD_T + d["weekday"] * STRIDE,
               CELL, CELL, shade(d["contributionCount"]))
        )

parts.append("</svg>")

import os
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
open(OUT, "w").write("\n".join(parts))
sys.stderr.write("wrote %s (%d weeks, %d contributions, peak %d)\n"
                 % (OUT, len(weeks), cal["totalContributions"], peak))
