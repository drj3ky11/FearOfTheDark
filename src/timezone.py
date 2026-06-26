"""
Timezone Inference from Post Timestamps
========================================
The core idea: people are creatures of habit. They sleep, work, and browse forums
on a predictable daily schedule. If we aggregate thousands of post timestamps per
user and plot their activity by hour (UTC), we'll see a clear trough during sleeping
hours and a peak during waking hours.

By finding the UTC offset that best aligns their activity to a "normal" waking window
(08:00–23:00 local time), we can infer their likely timezone — and from there,
narrow down their region or country.

Caveats:
- Users with <5 posts don't have enough data for a reliable estimate.
- Professional carders may operate odd hours deliberately.
- The self-reported 'timezoneoffset' in the user table is worth comparing against
  our inferred value — a mismatch can indicate VPN use or deliberate obfuscation.
"""

import numpy as np
import pandas as pd
from collections import Counter


# Rough UTC offset → region mapping.
# Intentionally coarse — we're narrowing down a country, not a city.
OFFSET_TO_REGION = {
    -12: "Pacific (US)",
    -11: "Pacific (US)",
    -10: "Hawaii",
    -9:  "Alaska",
    -8:  "US West Coast",
    -7:  "US Mountain",
    -6:  "US Central / Mexico",
    -5:  "US East Coast / Colombia",
    -4:  "US East Coast (DST) / Venezuela",
    -3:  "Brazil / Argentina",
    -2:  "Mid-Atlantic",
    -1:  "Azores",
     0:  "UK / West Africa",
     1:  "Central Europe / West Africa",
     2:  "Eastern Europe / Middle East",
     3:  "Russia (Moscow) / East Africa",
     4:  "Russia / UAE",
     5:  "Pakistan / Uzbekistan",
     6:  "Bangladesh / Kazakhstan",
     7:  "Southeast Asia / Russia",
     8:  "China / Singapore / Russia",
     9:  "Japan / Korea",
    10:  "Australia East",
    11:  "Solomon Islands",
    12:  "New Zealand",
}

# The window we expect most human activity to fall within (local time).
# 08:00–23:00 covers work hours, evenings, and late nights — a conservative but
# broad window that avoids penalizing night owls too harshly.
_ACTIVE_START = 8
_ACTIVE_END = 23


def infer_utc_offset(post_hours_utc: list[int]) -> int | None:
    """
    Given UTC hours of a user's posts, find the UTC offset that best explains
    their activity pattern.

    Method: for each candidate offset (-12 to +12), shift the activity histogram
    and score how many posts fall within the 08:00–23:00 window. The offset with
    the highest score is our best guess.

    Returns None if there are fewer than 5 posts (insufficient signal).
    """
    if len(post_hours_utc) < 5:
        return None

    # Build a 24-bin histogram of post counts by UTC hour
    counts = np.zeros(24, dtype=int)
    for h in post_hours_utc:
        counts[h % 24] += 1

    best_offset = None
    best_score = -1

    for offset in range(-12, 13):
        # np.roll shifts the histogram as if we're adjusting to local time
        shifted = np.roll(counts, offset)
        score = int(shifted[_ACTIVE_START:_ACTIVE_END + 1].sum())
        if score > best_score:
            best_score = score
            best_offset = offset

    return best_offset


def build_user_timezone_profile(posts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a per-user timezone profile from a posts DataFrame.

    Input DataFrame must have:
        - userid: int
        - dateline: timezone-aware datetime (UTC)

    Output columns:
        - userid
        - post_count: total posts analyzed
        - inferred_utc_offset: best-guess UTC offset
        - region: human-readable region from OFFSET_TO_REGION
        - activity_hours: 24-value CSV string (hourly post counts, for plotting)
    """
    posts = posts_df.dropna(subset=["userid", "dateline"]).copy()
    posts["hour_utc"] = posts["dateline"].dt.hour

    records = []
    for uid, group in posts.groupby("userid"):
        hours = group["hour_utc"].tolist()
        offset = infer_utc_offset(hours)
        region = OFFSET_TO_REGION.get(offset) if offset is not None else None

        # Store the raw histogram as a compact string — easy to parse for plotting
        hist = Counter(hours)
        activity = ",".join(str(hist.get(h, 0)) for h in range(24))

        records.append({
            "userid": uid,
            "post_count": len(hours),
            "inferred_utc_offset": offset,
            "region": region,
            "activity_hours": activity,
        })

    return pd.DataFrame(records)


def peak_hours(activity_hours_str: str) -> list[int]:
    """Return the top-3 most active UTC hours for a user, given their activity string."""
    counts = list(map(int, activity_hours_str.split(",")))
    return sorted(range(24), key=lambda h: -counts[h])[:3]
