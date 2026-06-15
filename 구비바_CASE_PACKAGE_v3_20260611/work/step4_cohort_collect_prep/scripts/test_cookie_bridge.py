"""
구비바 §4 — Vercel cookie bridge 테스트

SOFTC.ONE detail 페이지 1건을 curl_cffi로 요청해서
Vercel JS challenge를 쿠키만으로 통과하는지 확인.

사용법:
  python test_cookie_bridge.py --cookie "key1=val1; key2=val2"
  python test_cookie_bridge.py --cookie-file cookies.txt

쿠키 얻는 법 (브라우저 콘솔):
  document.cookie
  → 복사해서 --cookie 인자로 전달

테스트 대상: 구비바 채널 detail 페이지 (공개 데이터)
"""

import argparse
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def test_with_curl_cffi(cookie_str, url):
    from curl_cffi import requests as cffi_requests

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Cookie": cookie_str,
    }

    print(f"[test] URL: {url}")
    print(f"[test] Transport: curl_cffi (chrome TLS fingerprint)")
    print(f"[test] Cookie length: {len(cookie_str)} chars")
    print()

    resp = cffi_requests.get(url, headers=headers, impersonate="chrome")

    print(f"[result] Status: {resp.status_code}")
    print(f"[result] Content-Length: {len(resp.text)}")

    # 응답 헤더에서 Set-Cookie 확인
    for k, v in resp.headers.items():
        if k.lower() == 'set-cookie':
            # 쿠키 값은 출력하지 않고 이름만
            name = v.split('=')[0]
            flags = [p.strip() for p in v.split(';')[1:] if p.strip()]
            print(f"[header] Set-Cookie: {name}=... flags=[{', '.join(flags)}]")

    # 판정
    if resp.status_code == 429:
        print("[result] RATE LIMITED (429)")
        # 429여도 내용 확인 - Vercel이 실제 페이지를 429로 줄 수 있음
        text = resp.text
        has_data = "followerCount" in text or "channelId" in text
        has_challenge = "Vercel Security Checkpoint" in text or "_vercel_challenge" in text
        print(f"[result] 429 body contains RSC data: {has_data}")
        print(f"[result] 429 body contains Vercel challenge: {has_challenge}")
        if has_data:
            print("[info] 429 but data present - rate limit hit, but cookie bridge likely works")
        if not has_data and not has_challenge:
            print(f"[debug] first 500 chars: {text[:500]}")
        if has_challenge:
            import re
            # Vercel challenge 메커니즘 파악
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', text[:5000], re.DOTALL)
            for i, s in enumerate(scripts[:3]):
                if len(s) > 10:
                    print(f"[debug] script[{i}] (first 200): {s[:200]}")
            # cookie 이름 패턴 찾기
            cookie_refs = re.findall(r'["\']([a-zA-Z_][a-zA-Z0-9_]*)["\'].*?cookie', text[:10000], re.IGNORECASE)
            if cookie_refs:
                print(f"[debug] cookie refs in body: {cookie_refs[:10]}")
            # 전체 헤더 출력 (값은 요약)
            print(f"[debug] response headers:")
            for k, v in resp.headers.items():
                val = v[:80] + '...' if len(v) > 80 else v
                print(f"  {k}: {val}")
        return False

    if resp.status_code != 200:
        print(f"[result] HTTP {resp.status_code}")
        return False

    text = resp.text

    # Vercel challenge 페이지 감지
    if "Vercel Security Checkpoint" in text or "_vercel_challenge" in text:
        print("[result] BLOCKED — Vercel JS challenge 페이지 반환")
        print("[result] 쿠키만으로는 불충분. httpOnly 쿠키가 필요하거나, 다른 검증 존재.")
        return False

    # RSC payload 존재 확인
    has_follower = "followerCount" in text
    has_category = "category" in text and "viewership" in text
    has_channel = "channelId" in text or "chzzkId" in text

    print(f"[result] followerCount 포함: {has_follower}")
    print(f"[result] category+viewership 포함: {has_category}")
    print(f"[result] channelId 포함: {has_channel}")

    if has_follower and has_category:
        print()
        print("[PASS] Cookie bridge 작동 확인!")
        print("[PASS] CLI에서 enrichment 가능.")
        # 샘플 추출
        import re
        fol = re.findall(r'"followerCount":(\d+)', text)
        if fol:
            print(f"[sample] followerCount: {fol[-1]}")
        cats = re.findall(r'"category":"([^"]+)","sumLiveViews":\d+,"viewership":(\d+)', text)
        if cats:
            for c, v in cats[:3]:
                print(f"[sample] category: {c} (viewership: {v})")
        return True
    else:
        print()
        print("[FAIL] 페이지는 받았으나 RSC 데이터 없음.")
        print(f"[debug] 첫 500자: {text[:500]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Vercel cookie bridge test")
    parser.add_argument("--cookie", type=str, help="Cookie string (key1=val1; key2=val2)")
    parser.add_argument("--cookie-file", type=str, help="File containing cookie string")
    parser.add_argument("--url", type=str,
        default="https://viewership.softc.one/channel/naverchzzk/269edc95873a1ec9fc534851c0783d1f",
        help="Test URL (default: 구비바 detail page)")
    args = parser.parse_args()

    if args.cookie_file:
        with open(args.cookie_file, "r") as f:
            cookie_str = f.read().strip()
    elif args.cookie:
        cookie_str = args.cookie
    else:
        print("쿠키를 입력하세요.")
        print("  --cookie \"key1=val1; key2=val2\"")
        print("  --cookie-file cookies.txt")
        print()
        print("브라우저 콘솔에서: document.cookie")
        sys.exit(1)

    success = test_with_curl_cffi(cookie_str, args.url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
