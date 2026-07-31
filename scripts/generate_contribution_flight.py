from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path


API_URL = "https://api.github.com/graphql"
USERNAME = os.getenv("GITHUB_USERNAME", "nurbukeaydin")
TOKEN = os.environ["GITHUB_TOKEN"]
OUTPUT = Path("assets/contribution-flight.svg")


QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            contributionLevel
            date
            weekday
          }
        }
      }
    }
  }
}
"""


def get_calendar() -> dict:
    body = json.dumps(
        {
            "query": QUERY,
            "variables": {
                "login": USERNAME
            }
        }
    ).encode()

    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "nurbukeaydin-profile",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)

    if result.get("errors"):
        raise RuntimeError(result["errors"])

    return (
        result["data"]["user"]
        ["contributionsCollection"]
        ["contributionCalendar"]
    )


def create_svg(calendar: dict) -> str:
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]

    cell = 11
    gap = 4
    step = cell + gap

    left = 28
    top = 4
    duration = 14

    grid_width = len(weeks) * step - gap
    width = grid_width + left * 2

    colors = {
        "NONE": "#2c2438",
        "FIRST_QUARTILE": "#4c2b66",
        "SECOND_QUARTILE": "#7540a8",
        "THIRD_QUARTILE": "#a855f7",
        "FOURTH_QUARTILE": "#e879f9",
    }

    cells = []
    active = []

    for week_index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            x = left + week_index * step
            y = top + int(day["weekday"]) * step

            level = day["contributionLevel"]
            count = int(day["contributionCount"])

            opacity = "0.42" if level == "NONE" else "1"

            cells.append(
                f'<rect x="{x}" y="{y}" '
                f'width="{cell}" height="{cell}" '
                f'rx="3" fill="{colors[level]}" '
                f'opacity="{opacity}"/>'
            )

            if count > 0:
                active.append(
                    (
                        x + cell / 2,
                        y + cell / 2
                    )
                )

    if not active:
        middle = top + 3 * step

        active = [
            (left, middle),
            (left + grid_width, middle),
        ]

    flight_path = " ".join(
        f'{"M" if index == 0 else "L"} {x:.1f} {y:.1f}'
        for index, (x, y) in enumerate(active)
    )

    sparkles = []

    for index, (x, y) in enumerate(active):
        moment = (
            index / max(1, len(active))
        ) * 0.88

        before = max(0, moment - 0.012)
        after = min(0.98, moment + 0.045)

        sparkles.append(
            f'<g transform="translate({x:.1f} {y:.1f})" '
            f'opacity="0">'

            '<path '
            'd="M0-7 2-2 7 0 2 2 0 7-2 2-7 0-2-2Z" '
            'fill="#f5d0fe"/>'

            f'<animate '
            f'attributeName="opacity" '
            f'values="0;0;1;0;0" '
            f'keyTimes="0;{before:.3f};'
            f'{moment:.3f};{after:.3f};1" '
            f'dur="{duration}s" '
            f'repeatCount="indefinite"/>'

            '</g>'
        )

    return f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    width="{width}"
    height="120"
    viewBox="0 0 {width} 120"
>

<defs>

  <linearGradient id="bar" x1="0" x2="1">
    <stop offset="0%" stop-color="#7c3aed"/>
    <stop offset="55%" stop-color="#a855f7"/>
    <stop offset="100%" stop-color="#f0abfc"/>
  </linearGradient>

  <filter
      id="glow"
      x="-100%"
      y="-100%"
      width="300%"
      height="300%"
  >
    <feGaussianBlur
        stdDeviation="2.2"
        result="blur"
    />

    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>

  <path
      id="flight"
      d="{flight_path}"
      fill="none"
  />

</defs>

<style>


</style>

{"".join(cells)}

<path
    d="{flight_path}"
    fill="none"
    stroke="#c084fc"
    stroke-width="1.4"
    stroke-linecap="round"
    stroke-linejoin="round"
    opacity="0.16"
/>

{"".join(sparkles)}

<g filter="url(#glow)">

  <polygon
      points="
        -11,1
        -3,-7
        0,-2
        12,-6
        5,1
        11,7
        0,4
        -7,9
        -5,2
      "
      fill="#c084fc"
  >

    <animateMotion
        dur="{duration}s"
        repeatCount="indefinite"
        rotate="auto"
    >
      <mpath xlink:href="#flight"/>
    </animateMotion>

  </polygon>

</g>

<rect
    x="{left}"
    y="110"
    width="{grid_width}"
    height="6"
    rx="3"
    fill="#2c2438"
    opacity="0.55"
/>

<rect
    x="{left}"
    y="110"
    width="0"
    height="6"
    rx="3"
    fill="url(#bar)"
>

  <animate
      attributeName="width"
      values="
        0;
        {grid_width};
        {grid_width};
        0
      "
      keyTimes="
        0;
        0.88;
        0.94;
        1
      "
      dur="{duration}s"
      repeatCount="indefinite"
  />

</rect>


</svg>
"""


calendar = get_calendar()

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT.write_text(
    create_svg(calendar),
    encoding="utf-8"
)

print(f"Generated {OUTPUT}")
