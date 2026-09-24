import os
import re

import requests
from icalendar import Calendar
from icalendar.cal.calendar import Component

SOURCE_URL = "https://p.inh.tatar/music-room/v0/music-room.ics"
OUTPUT_DIR = "dist"
OUTPUT_FILE = "schedule.ics"

# Matching with event's description
ALIAS_RE = re.compile(r"Booked by https://t\.me/(\S+)")


def get_band_aliases() -> set[str]:
    """
    Extract band aliases from environment variable
    Example format: "alice123, @1tota33, @brurb_x1" (so @ is optional)
    """
    raw = os.environ.get("BAND_ALIASES", "")
    aliases = {a.strip().lstrip("@").lower() for a in raw.split(",") if a.strip()}
    if not aliases:
        raise SystemExit(
            "No aliases configured. Set a BAND_ALIASES repository variable "
            "(Settings -> Secrets and variables -> Actions -> Variables) to a "
            "comma-separated list, e.g. alice_tg,bob_tg,carol_tg"
        )
    return aliases


def matches_band(comp: Component, band_aliases: set[str]) -> bool:
    description = str(comp.get("description", ""))
    match = ALIAS_RE.search(description)
    if match:
        return match.group(1).lower() in band_aliases
    return False


def main() -> None:
    band_aliases = get_band_aliases()
    response = requests.get(SOURCE_URL, timeout=30)
    response.raise_for_status()
    source_cal = Calendar.from_ical(response.content)

    filtered_cal = Calendar()
    filtered_cal.add("prodid", "-//band-schedule-filter//")
    filtered_cal.add("version", "2.0")
    filtered_cal.add("method", "PUBLISH")
    filtered_cal["x-wr-calname"] = "Band Music Room Schedule"
    filtered_cal["x-wr-timezone"] = "Europe/Moscow"
    filtered_cal["x-wr-caldesc"] = "Filtered from innohassle.ru music-room schedule"

    all_events = source_cal.walk("VEVENT")
    kept = 0
    for component in all_events:
        if matches_band(component, band_aliases):
            filtered_cal.add_component(component)
            kept += 1

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    with open(out_path, "wb") as f:
        f.write(filtered_cal.to_ical())

    print(f"Kept {kept} of {len(all_events)} events for aliases: {sorted(band_aliases)}")
    print(f"Wrote to {out_path}")


if __name__ == "__main__":
    main()
