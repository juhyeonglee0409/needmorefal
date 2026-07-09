# -*- coding: utf-8 -*-
"""strong 17 카드 HTML -> 인라인용 PNG (메일 본문 삽입용)."""
import json
import os
import re
import subprocess
from pathlib import Path

CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
BASE = Path(__file__).parent
CARDS = BASE / "cards_20260704"

q = [json.loads(l) for l in (BASE / "send_queue_20260704.ndjson").open(encoding="utf-8")]
ok = 0
for x in [x for x in q if x["tier"] == "strong"]:
    sn = re.sub(r"[^\w가-힣]+", "_", x["channel_name"]).strip("_")
    png = CARDS / f"{sn}.png"
    html = (CARDS / f"{sn}.html").as_posix()
    subprocess.run([
        CHROME, "--headless", "--disable-gpu",
        f"--screenshot={png.as_posix()}",
        "--window-size=700,1120", "--hide-scrollbars",
        f"file:///{html}",
    ], capture_output=True)
    if png.exists():
        ok += 1
    else:
        print("FAIL:", sn)
print(f"PNG {ok}/17")
