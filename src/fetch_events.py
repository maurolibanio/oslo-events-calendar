import json
import requests
from datetime import date, timedelta

today = date.today()
future = today + timedelta(days=365)

BASE_URL = "https://www.visitoslo.com/api/eventlist/events"

CATEGORY_IDS = (
    "505552,506042,507212,507232,"
    "505772,506922,506802,519862,"
    "506032,513572,506232,505792,"
    "500602,508172,508182,502032,"
    "507222,509172"
)

all_events = []
offset = 0
total_results = None

while True:

    url = (
        f"{BASE_URL}"
        f"?pageId=837"
        f"&language=en"
        f"&offset={offset}"
        f"&CategoryIds={CATEGORY_IDS}"
        f"&FromDate={today.isoformat()}"
        f"&ToDate={future.isoformat()}"
    )

    print(f"Fetching offset={offset}")

    response = requests.get(
        url,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    if total_results is None:
        total_results = data.get(
            "totalResults",
            0
        )

        print(
            f"Total results reported by API: "
            f"{total_results}"
        )

    events = data.get("events", [])

    if not events:
        break

    all_events.extend(events)

    print(
        f"Collected {len(all_events)} "
        f"of {total_results}"
    )

    offset += len(events)

    if len(all_events) >= total_results:
        break

output = {
    "generatedAt": today.isoformat(),
    "totalResults": len(all_events),
    "events": all_events
}

with open(
    "events.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=2
    )

print(
    f"Finished. Saved "
    f"{len(all_events)} events."
)
