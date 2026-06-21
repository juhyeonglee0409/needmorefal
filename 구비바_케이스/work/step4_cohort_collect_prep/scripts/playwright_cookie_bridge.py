"""
Playwright cookie bridge test.
Playwright로 실제 브라우저를 열어 Vercel challenge 해결 후,
context.cookies()로 쿠키를 읽고 curl_cffi로 전달 테스트.
"""

import io
import re
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET_URL = "https://viewership.softc.one/channel/naverchzzk/269edc95873a1ec9fc534851c0783d1f"
ORIGIN = "https://viewership.softc.one"


def main():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        print("[pw] Launching Chromium (headed, stealth)...")
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            delete navigator.__proto__.webdriver;
        """)

        print(f"[pw] Navigating to {TARGET_URL}...")
        page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)

        title = page.title()
        print(f"[pw] Page title: {title}")

        if "Vercel" in title or "checkpoint" in title.lower():
            print("[pw] Vercel challenge detected, waiting 10s for auto-solve...")
            time.sleep(10)
            page.reload(wait_until="networkidle", timeout=30000)
            title = page.title()
            print(f"[pw] After reload: {title}")

        # Read all cookies for the origin
        cookies = context.cookies(ORIGIN)
        print(f"\n[pw] {len(cookies)} cookies for {ORIGIN}:")
        for c in cookies:
            http_flag = " [httpOnly]" if c.get("httpOnly") else ""
            print(f"  {c['name']} ({len(c.get('value',''))}ch){http_flag} domain={c.get('domain','')}")

        # Build cookie string
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        print(f"\n[bridge] Cookie string: {len(cookie_str)} chars")

        # Verify page has real data (not challenge)
        content = page.content()
        pw_has_data = "followerCount" in content
        print(f"[pw] Page has followerCount: {pw_has_data}")

        browser.close()

    # Now test with curl_cffi
    if not cookie_str:
        print("[bridge] No cookies to test")
        return

    print("\n[bridge] Testing with curl_cffi...")
    from curl_cffi import requests as cffi_requests

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
        print("[FAIL] curl_cffi blocked by Vercel even with Playwright cookies")
        for k, v in resp.headers.items():
            if 'vercel' in k.lower():
                print(f"  {k}: {v[:100]}")
        print("\n[conclusion] Cookie bridge FAILS at curl_cffi transport layer.")
        print("[conclusion] Vercel fingerprints the HTTP client beyond cookies.")
        print("[alternative] Playwright itself can be the transport (bypasses Vercel).")
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
    else:
        print(f"\n[FAIL] No RSC data in response")
        print(f"[debug] first 300: {text[:300]}")


if __name__ == "__main__":
    main()
