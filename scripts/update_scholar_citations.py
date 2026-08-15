#!/usr/bin/env python3
"""Update the cached Google Scholar citation count used by the Jekyll site."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


PROFILE_URL = "https://scholar.google.com/citations?user=PIFjuPoAAAAJ&hl=en"
DATA_FILE = Path(__file__).resolve().parents[1] / "_data" / "scholar.yml"


def fetch_profile() -> str:
    request = Request(
        PROFILE_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as error:  # Network and rate-limit errors share retry logic.
            last_error = error
            if attempt < 2:
                time.sleep(10 * (attempt + 1))

    raise RuntimeError("Unable to fetch the Google Scholar profile") from last_error


def extract_citations(profile_html: str) -> int:
    patterns = (
        r">Citations</a>\s*</td>\s*<td[^>]*class=\"gsc_rsb_std\"[^>]*>\s*([\d,]+)",
        r"Citations.*?class=\"gsc_rsb_std\"[^>]*>\s*([\d,]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, profile_html, flags=re.DOTALL)
        if match:
            return int(match.group(1).replace(",", ""))

    raise RuntimeError("Google Scholar citation count was not found")


def main() -> None:
    citations = extract_citations(fetch_profile())
    updated = datetime.now(timezone.utc).date().isoformat()
    DATA_FILE.write_text(
        f'citations: {citations}\nupdated: "{updated}"\nprofile_url: "{PROFILE_URL}"\n',
        encoding="utf-8",
    )
    print(f"Google Scholar citations: {citations} (updated {updated})")


if __name__ == "__main__":
    main()
