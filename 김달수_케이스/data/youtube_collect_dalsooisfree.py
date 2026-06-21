"""
YouTube Data API v3 — dalsooisfree 채널 영상 메타데이터 수집
실행: YOUTUBE_API_KEY 환경변수 설정 후 python youtube_collect_dalsooisfree.py
출력: youtube_dalsooisfree_videos.json, youtube_dalsooisfree_profile.json
의존성: pip install requests (표준 라이브러리 외 requests만 필요)
"""

import json
import os
import requests
import sys
import time
from pathlib import Path

HANDLE = "dalsooisfree"
BASE = "https://www.googleapis.com/youtube/v3"
OUT_DIR = Path(__file__).parent


def get_api_key():
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("[ERROR] YOUTUBE_API_KEY 환경변수가 설정되지 않았음")
        sys.exit(1)
    return api_key


def api_get(endpoint, params):
    params["key"] = get_api_key()
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=30)
    if r.status_code != 200:
        print(f"[ERROR] {endpoint} -> {r.status_code}: {r.text[:300]}")
        sys.exit(1)
    return r.json()


def get_channel():
    """채널 ID + 기본 프로필 조회"""
    data = api_get("channels", {
        "part": "snippet,statistics,contentDetails",
        "forHandle": HANDLE,
    })
    if not data.get("items"):
        # forHandle 실패 시 search 폴백
        print("[INFO] forHandle 실패, search 폴백 시도...")
        search = api_get("search", {
            "part": "snippet",
            "q": HANDLE,
            "type": "channel",
            "maxResults": 1,
        })
        if not search.get("items"):
            print("[ERROR] 채널을 찾을 수 없음")
            sys.exit(1)
        channel_id = search["items"][0]["snippet"]["channelId"]
        data = api_get("channels", {
            "part": "snippet,statistics,contentDetails",
            "id": channel_id,
        })
    return data["items"][0]


def get_all_videos(uploads_playlist_id):
    """업로드 재생목록에서 전체 영상 ID 목록 추출"""
    video_ids = []
    page_token = None
    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        data = api_get("playlistItems", params)
        for item in data.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])
        page_token = data.get("nextPageToken")
        if not page_token:
            break
        time.sleep(0.2)  # polite pacing
    return video_ids


def get_video_details(video_ids):
    """영상 ID 목록 -> 상세 메타데이터 (50개씩 배치)"""
    all_videos = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        data = api_get("videos", {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch),
        })
        for item in data.get("items", []):
            snippet = item["snippet"]
            stats = item.get("statistics", {})
            details = item.get("contentDetails", {})
            all_videos.append({
                "video_id": item["id"],
                "title": snippet.get("title"),
                "published_at": snippet.get("publishedAt"),
                "description": snippet.get("description", "")[:200],
                "duration": details.get("duration"),  # ISO 8601
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId"),
                "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url"),
            })
        time.sleep(0.2)
    return all_videos


def main():
    print(f"=== YouTube 데이터 수집: @{HANDLE} ===\n")

    # 1. 채널 프로필
    print("[1/3] 채널 프로필 조회...")
    channel = get_channel()
    profile = {
        "channel_id": channel["id"],
        "title": channel["snippet"]["title"],
        "description": channel["snippet"].get("description", ""),
        "custom_url": channel["snippet"].get("customUrl", ""),
        "published_at": channel["snippet"].get("publishedAt"),
        "subscriber_count": int(channel["statistics"].get("subscriberCount", 0)),
        "video_count": int(channel["statistics"].get("videoCount", 0)),
        "view_count": int(channel["statistics"].get("viewCount", 0)),
        "uploads_playlist": channel["contentDetails"]["relatedPlaylists"]["uploads"],
    }
    print(f"  채널: {profile['title']} | 구독 {profile['subscriber_count']} | 영상 {profile['video_count']}개")

    # 2. 전체 영상 ID
    print(f"\n[2/3] 영상 목록 수집 (업로드 재생목록: {profile['uploads_playlist']})...")
    video_ids = get_all_videos(profile["uploads_playlist"])
    print(f"  영상 ID {len(video_ids)}개 수집")

    # 3. 상세 메타데이터
    print(f"\n[3/3] 영상 상세 메타데이터 수집 ({len(video_ids)}개, 50개 배치)...")
    videos = get_video_details(video_ids)
    print(f"  상세 데이터 {len(videos)}개 수집 완료")

    # 저장
    profile_path = OUT_DIR / "youtube_dalsooisfree_profile.json"
    videos_path = OUT_DIR / "youtube_dalsooisfree_videos.json"

    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    with open(videos_path, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

    print(f"\n=== 완료 ===")
    print(f"  프로필: {profile_path}")
    print(f"  영상({len(videos)}개): {videos_path}")

    # 요약 통계
    if videos:
        total_views = sum(v["view_count"] for v in videos)
        shorts = [v for v in videos if _is_short(v["duration"])]
        print(f"\n  총 조회수: {total_views:,}")
        print(f"  Shorts(<=60s): {len(shorts)}개 / 일반: {len(videos)-len(shorts)}개")


def _is_short(iso_duration):
    """ISO 8601 duration -> 60초 이하 여부"""
    if not iso_duration:
        return False
    import re
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not m:
        return False
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return (h * 3600 + mi * 60 + s) <= 60


if __name__ == "__main__":
    main()
