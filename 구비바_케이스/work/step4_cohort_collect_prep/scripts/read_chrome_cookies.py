"""
Chrome cookie DB에서 특정 도메인의 쿠키를 읽고 복호화.
operator 지시에 의한 단일 도메인 한정 읽기.
쿠키 값은 메모리에만 유지, 파일/로그 저장 안 함.
"""

import os
import sys
import json
import base64
import shutil
import sqlite3
import tempfile

def get_encryption_key():
    local_state_path = os.path.join(
        os.environ["LOCALAPPDATA"],
        "Google", "Chrome", "User Data", "Local State"
    )
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)

    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    # Remove DPAPI prefix "DPAPI"
    encrypted_key = encrypted_key[5:]

    import win32crypt
    decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return decrypted_key


def decrypt_cookie_value(encrypted_value, key):
    if not encrypted_value:
        return ""

    # v10/v20 prefix = AES-256-GCM
    if encrypted_value[:3] in (b'v10', b'v20'):
        nonce = encrypted_value[3:15]
        ciphertext = encrypted_value[15:]
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aes = AESGCM(key)
        try:
            return aes.decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception:
            return "(decrypt failed)"

    # Older DPAPI-only encryption
    try:
        import win32crypt
        return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode("utf-8")
    except Exception:
        return "(decrypt failed)"


def read_cookies(profile_name, domain_filter):
    cookie_db = os.path.join(
        os.environ["LOCALAPPDATA"],
        "Google", "Chrome", "User Data", profile_name, "Network", "Cookies"
    )

    if not os.path.exists(cookie_db):
        print(f"[error] Cookie DB not found: {cookie_db}")
        return []

    # Copy DB to avoid Chrome lock
    tmp = tempfile.mktemp(suffix=".db")
    shutil.copy2(cookie_db, tmp)

    key = get_encryption_key()

    conn = sqlite3.connect(tmp)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, encrypted_value, host_key, path, is_httponly, is_secure, expires_utc "
        "FROM cookies WHERE host_key LIKE ?",
        (f"%{domain_filter}%",)
    )

    cookies = []
    for name, encrypted_value, host_key, path, is_httponly, is_secure, expires_utc in cursor.fetchall():
        enc_bytes = bytes(encrypted_value) if encrypted_value else b''
        prefix = enc_bytes[:3] if len(enc_bytes) >= 3 else enc_bytes
        value = decrypt_cookie_value(encrypted_value, key)
        cookies.append({
            "name": name,
            "value": value,
            "domain": host_key,
            "path": path,
            "httpOnly": bool(is_httponly),
            "secure": bool(is_secure),
            "_enc_len": len(enc_bytes),
            "_prefix": prefix,
        })

    conn.close()
    os.unlink(tmp)
    return cookies


def main():
    domain = "softc.one"
    profile = "Profile 1"

    print(f"[read] Profile: {profile}")
    print(f"[read] Domain filter: {domain}")
    print()

    cookies = read_cookies(profile, domain)

    if not cookies:
        print("[result] No cookies found")
        return

    print(f"[result] {len(cookies)} cookies found:")
    for c in cookies:
        http_flag = " [httpOnly]" if c["httpOnly"] else ""
        print(f"  {c['name']} (val={len(c['value'])}ch, enc={c['_enc_len']}B, prefix={c['_prefix']}){http_flag} domain={c['domain']}")

    # cookie string 조합 (메모리만, 출력 안 함)
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

    print()
    print(f"[bridge] Total cookie string: {len(cookie_str)} chars")
    print("[bridge] Testing with curl_cffi...")
    print()

    # 바로 테스트
    from curl_cffi import requests as cffi_requests

    url = "https://viewership.softc.one/channel/naverchzzk/269edc95873a1ec9fc534851c0783d1f"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Cookie": cookie_str,
    }

    resp = cffi_requests.get(url, headers=headers, impersonate="chrome")
    print(f"[result] Status: {resp.status_code}")
    print(f"[result] Content-Length: {len(resp.text)}")

    text = resp.text

    if "Vercel Security Checkpoint" in text or "_vercel_challenge" in text:
        print("[FAIL] Vercel challenge returned even with full cookies")
        # 어떤 Vercel 관련 헤더가 왔는지
        for k, v in resp.headers.items():
            if 'vercel' in k.lower():
                print(f"  {k}: {v[:100]}")
        return

    import re
    has_follower = "followerCount" in text
    has_category = "category" in text and "viewership" in text

    print(f"[result] followerCount present: {has_follower}")
    print(f"[result] category+viewership present: {has_category}")

    if has_follower and has_category:
        print()
        print("[PASS] Cookie bridge works!")
        fol = re.findall(r'"followerCount":(\d+)', text)
        if fol:
            print(f"[sample] followerCount: {fol[-1]}")
        cats = re.findall(r'"category":"([^"]+)","sumLiveViews":\d+,"viewership":(\d+)', text)
        for c, v in cats[:3]:
            print(f"[sample] category: {c} (viewership: {v})")
    else:
        print()
        print("[FAIL] Page received but no RSC data")
        print(f"[debug] first 300 chars: {text[:300]}")


if __name__ == "__main__":
    main()
