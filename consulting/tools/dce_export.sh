#!/usr/bin/env bash
# Discord DM 로그 내보내기 래퍼 (DiscordChatExporter.Cli v2.47.3)
# 토큰은 레포 밖 ~/.dce_token 파일에서만 읽는다. 채팅/커밋에 토큰 노출 금지.
#
# 사용법:
#   ./dce_export.sh list                              # DM 채널 목록 (채널 ID 확인용)
#   ./dce_export.sh <channel_id> <output.json>        # 전체 내보내기
#   ./dce_export.sh <channel_id> <output.json> 2026-08-04  # 해당 날짜 이후만
set -euo pipefail

DCE="C:/Users/faust/tools/dce/DiscordChatExporter.Cli.exe"
TOKEN_FILE="$HOME/.dce_token"

if [ ! -f "$TOKEN_FILE" ]; then
  echo "토큰 파일이 없습니다: $TOKEN_FILE"
  echo "디스코드 토큰을 한 줄로 저장해 주세요. 이 파일은 레포 밖이라 커밋되지 않습니다."
  exit 1
fi
TOKEN="$(tr -d '[:space:]' < "$TOKEN_FILE")"

if [ "${1:-}" = "list" ]; then
  "$DCE" dm -t "$TOKEN"
  exit 0
fi

CHANNEL="${1:?채널 ID 필요}"
OUT="${2:?출력 경로 필요}"
AFTER="${3:-}"

ARGS=(export -c "$CHANNEL" -t "$TOKEN" -f Json -o "$OUT")
if [ -n "$AFTER" ]; then ARGS+=(--after "$AFTER"); fi
"$DCE" "${ARGS[@]}"
echo "저장: $OUT"
