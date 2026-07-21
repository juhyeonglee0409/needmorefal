#!/bin/zsh

set -u

PROJECT_DIR="/Users/isaaclee/Desktop/gunsmith-workshop/Contextwins Project/tools/corpus"
PORT="8000"
URL="http://127.0.0.1:${PORT}/corpus_explorer.html"

echo "Corpus Explorer"
echo "================"

cd "$PROJECT_DIR" || {
  echo "Project folder not found:"
  echo "$PROJECT_DIR"
  echo
  read "?Press Enter to close..."
  exit 1
}

if [[ ! -f "data/corpus_tagged.ndjson" ]]; then
  echo "Missing source data: data/corpus_tagged.ndjson"
  echo
  read "?Press Enter to close..."
  exit 1
fi

if [[ ! -f "data/explorer_data.json" || "data/corpus_tagged.ndjson" -nt "data/explorer_data.json" || "build_explorer_data.py" -nt "data/explorer_data.json" ]]; then
  echo "Building explorer_data.json..."
  python3 build_explorer_data.py || {
    echo
    echo "Build failed."
    read "?Press Enter to close..."
    exit 1
  }
fi

if lsof -nP -iTCP:${PORT} -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port ${PORT} is already in use. Opening existing local server:"
  echo "$URL"
  open "$URL"
  echo
  echo "If the page still shows a data-load error, stop the existing server and run this shortcut again."
  echo "You can close this window."
  read "?Press Enter to close..."
  exit 0
fi

echo "Starting local server on port ${PORT}..."
python3 -m http.server "$PORT" &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1
  fi
}
trap cleanup INT TERM EXIT

sleep 1
if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
  echo "Server failed to start."
  echo
  read "?Press Enter to close..."
  exit 1
fi

echo "Opening:"
echo "$URL"
open "$URL"
echo
echo "Keep this Terminal window open while using Corpus Explorer."
echo "Press Ctrl-C to stop the server."

wait "$SERVER_PID"
