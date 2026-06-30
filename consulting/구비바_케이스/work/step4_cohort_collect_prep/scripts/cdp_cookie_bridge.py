"""
CDP cookie bridge test.
Headless Chrome을 띄워서 softc.one 쿠키를 Chrome 자체가 복호화하도록 하고,
CDP로 평문 쿠키를 읽어서 curl_cffi로 테스트.
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import time

import requests as http_requests
import websocket

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PORT = 9223
TARGET_URL = "https://viewership.softc.one/channel/naverchzzk/269edc95873a1ec9fc534851c0783d1f"
COOKIE_DOMAIN = "softc.one"


def launch_headless_chrome(temp_dir):
    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={temp_dir}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--window-size=1280,720",
        "--remote-allow-origins=*",
    ]
    print(f"[cdp] Launching headless Chrome on port {DEBUG_PORT}...")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # wait for debug port
    for i in range(15):
        time.sleep(1)
        try:
            r = http_requests.get(f"http://127.0.0.1:{DEBUG_PORT}/json/version", timeout=2)
            if r.status_code == 200:
                print(f"[cdp] Chrome ready (pid={proc.pid})")
                return proc
        except Exception:
            pass
    print("[cdp] Chrome failed to start")
    proc.kill()
    return None


def cdp_send(ws, method, params=None):
    msg_id = int(time.time() * 1000) % 100000
    msg = {"id": msg_id, "method": method}
    if params:
        msg["params"] = params
    ws.send(json.dumps(msg))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id:
            return resp
        # skip events


def get_page_ws_url():
    # get first page target
    r = http_requests.get(f"http://127.0.0.1:{DEBUG_PORT}/json", timeout=5)
    targets = r.json()
    for t in targets:
        if t.get("type") == "page":
            return t["webSocketDebuggerUrl"]
    # create a new tab
    r = http_requests.get(f"http://127.0.0.1:{DEBUG_PORT}/json/new?{TARGET_URL}", timeout=5)
    return r.json()["webSocketDebuggerUrl"]


def main():
    temp_dir = tempfile.mkdtemp(prefix="chrome_cdp_")
    proc = None

    try:
        proc = launch_headless_chrome(temp_dir)
        if not proc:
            return

        ws_url = get_page_ws_url()
        print(f"[cdp] Connecting: {ws_url[:80]}...")
        ws = websocket.create_connection(ws_url, timeout=30)

        # Enable Network for cookies
        cdp_send(ws, "Network.enable")

        # Navigate to target
        print(f"[cdp] Navigating to {TARGET_URL}...")
        cdp_send(ws, "Page.navigate", {"url": TARGET_URL})

        # Wait for page load
        print("[cdp] Waiting for page load (15s for Vercel challenge)...")
        time.sleep(15)

        # Read cookies
        result = cdp_send(ws, "Network.getCookies", {"urls": [TARGET_URL, f"https://{COOKIE_DOMAIN}"]})
        cookies = result.get("result", {}).get("cookies", [])

        print(f"\n[cdp] {len(cookies)} cookies retrieved:")
        for c in cookies:
            http_flag = " [httpOnly]" if c.get("httpOnly") else ""
            val_len = len(c.get("value", ""))
            print(f"  {c['name']} ({val_len}ch){http_flag} domain={c.get('domain','')}")

        if not cookies:
            # Check what the page looks like
            result = cdp_send(ws, "Runtime.evaluate", {
                "expression": "document.title + ' | ' + document.body.innerText.substring(0, 300)"
            })
            page_info = result.get("result", {}).get("result", {}).get("value", "")
            print(f"[debug] Page: {page_info[:200]}")
            ws.close()
            return

        # Build cookie string
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        print(f"\n[bridge] Cookie string: {len(cookie_str)} chars")

        ws.close()

        # Test with curl_cffi
        print("[bridge] Testing with curl_cffi...\n")

        from curl_cffi import requests as cffi_requests
        import re

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Cookie": cookie_str,
        }

        resp = cffi_requests.get(TARGET_URL, headers=headers, impersonate="chrome")
        print(f"[result] Status: {resp.status_code}")
        print(f"[result] Content-Length: {len(resp.text)}")

        text = resp.text

        if "Vercel Security Checkpoint" in text:
            print("[FAIL] Vercel challenge still returned")
            for k, v in resp.headers.items():
                if 'vercel' in k.lower():
                    print(f"  {k}: {v[:100]}")
            return

        has_follower = "followerCount" in text
        has_category = "category" in text and "viewership" in text
        print(f"[result] followerCount: {has_follower}")
        print(f"[result] category+viewership: {has_category}")

        if has_follower and has_category:
            print("\n[PASS] Cookie bridge WORKS!")
            fol = re.findall(r'"followerCount":(\d+)', text)
            if fol:
                print(f"[sample] followerCount: {fol[-1]}")
            cats = re.findall(r'"category":"([^"]+)","sumLiveViews":\d+,"viewership":(\d+)', text)
            for c, v in cats[:3]:
                print(f"[sample] {c} (viewership: {v})")
        else:
            print(f"\n[FAIL] No RSC data")
            print(f"[debug] first 300: {text[:300]}")

    finally:
        if proc:
            proc.kill()
            proc.wait()
            print("\n[cdp] Chrome terminated")
        # cleanup temp dir
        import shutil
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
