#!/usr/bin/env bash
set -euo pipefail

CREDS_FILE="credentials.yaml"

echo "================================================"
echo "  Canvas Module Downloader — Setup"
echo "================================================"
echo

# ── API_URL ──────────────────────────────────────────────────────────
echo "Step 1: Canvas URL"
echo "  This is your institution's Canvas domain."
echo "  Example: https://myschool.instructure.com"
echo
read -rp "Canvas URL: " API_URL

# Strip trailing slash
API_URL="${API_URL%/}"

if [[ -z "$API_URL" ]]; then
    echo "Error: Canvas URL cannot be empty." >&2
    exit 1
fi

# ── API_KEY ──────────────────────────────────────────────────────────
echo
echo "Step 2: Canvas API Token"
echo "  To generate a token:"
echo "    1. Log into Canvas"
echo "    2. Go to Account → Settings"
echo "    3. Scroll to 'Approved Integrations'"
echo "    4. Click '+ New Access Token'"
echo "    5. Copy the token shown (you won't be able to see it again)"
echo
read -rsp "API Token (input hidden): " API_KEY
echo  # newline after hidden input

if [[ -z "$API_KEY" ]]; then
    echo "Error: API token cannot be empty." >&2
    exit 1
fi

# ── Write file ───────────────────────────────────────────────────────
cat > "$CREDS_FILE" <<EOF
API_URL: ${API_URL}
API_KEY: ${API_KEY}
EOF

chmod 600 "$CREDS_FILE"

echo
echo "Saved to $CREDS_FILE (permissions set to 600)."
echo
echo "You're all set! Run the downloader with:"
echo "  python canvas_module_downloader.py"
