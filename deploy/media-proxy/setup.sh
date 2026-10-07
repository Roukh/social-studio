#!/usr/bin/env bash
# One-time Railway media hosting for social-studio. The operator runs it in a terminal:
#
#   deploy/media-proxy/setup.sh <social-studio project folder>
#
# 1. creates a private bucket next to the media proxy service in the Railway project this folder is
#    linked to (`railway link`), unless it exists;
# 2. points the proxy at the bucket through Railway variable references (Railway resolves them; the
#    keys never land here) and waits until the redeployed proxy reports ok;
# 3. runs `social-studio channel connect media`, handing it the bucket keys through environment
#    variables only (never printed, never on a command line); connect then writes a probe object and
#    reads it back through the public URL.
set -euo pipefail

PROJECT=$(cd "${1:?usage: setup.sh <social-studio project folder>}" && pwd)
BUCKET_NAME=${BUCKET_NAME:-social-studio-videos}
SERVICE=${SERVICE:-social-studio-media}
REGION=${REGION:-iad}
HERE=$(cd "$(dirname "$0")" && pwd)
STUDIO=${STUDIO:-$HERE/../../.venv/bin/social-studio}
cd "$HERE"

railway status >/dev/null 2>&1 || { echo "link this folder first: cd $HERE && railway link" >&2; exit 1; }

if railway bucket list --json | jq -e --arg n "$BUCKET_NAME" 'any(.[]; .name == $n)' >/dev/null; then
  echo "bucket $BUCKET_NAME exists"
else
  railway bucket create "$BUCKET_NAME" --region "$REGION"
fi

ref() { printf '%s=${{%s.%s}}' "$1" "$BUCKET_NAME" "$1"; }
# A new bucket deploys in the background; its credentials exist only once it is deployed.
printf 'waiting for bucket %s to deploy' "$BUCKET_NAME"
CREDS=
for _ in $(seq 36); do
  CREDS=$(railway bucket credentials --bucket "$BUCKET_NAME" --json 2>/dev/null) &&
    jq -e '.accessKeyId and .secretAccessKey and .bucketName' >/dev/null <<<"$CREDS" && break
  CREDS=; printf '.'; sleep 5
done
echo
[ -n "$CREDS" ] || { echo "bucket $BUCKET_NAME is still not deployed after 3 minutes: open the Railway canvas" \
  "(railway open), deploy any staged changes, then run this again" >&2; exit 1; }
case $(jq -r '.urlStyle // "virtual"' <<<"$CREDS") in path*) STYLE=path ;; *) STYLE=virtual ;; esac
railway variable set --service "$SERVICE" "$(ref ENDPOINT)" "$(ref BUCKET)" "$(ref ACCESS_KEY_ID)" \
  "$(ref SECRET_ACCESS_KEY)" "$(ref REGION)" "ADDRESSING=$STYLE" >/dev/null
echo "proxy $SERVICE now reads bucket $BUCKET_NAME ($STYLE-hosted URLs)"

PUBLIC=$(railway domain list --service "$SERVICE" --json | jq -r '[.. | strings | select(test("up\\.railway\\.app"))][0] // empty')
[ -n "$PUBLIC" ] || { echo "no Railway domain on $SERVICE: run railway domain --service $SERVICE" >&2; exit 1; }
case $PUBLIC in https://*) ;; *) PUBLIC="https://${PUBLIC#http://}" ;; esac

printf 'waiting for %s to redeploy' "$PUBLIC"
for _ in $(seq 72); do
  [ "$(curl -fsS --max-time 10 "$PUBLIC/healthz" 2>/dev/null)" = ok ] && break
  printf '.'; sleep 5
done
echo
[ "$(curl -fsS --max-time 10 "$PUBLIC/healthz" 2>/dev/null)" = ok ] || { echo "proxy not ready; check: railway logs --service $SERVICE" >&2; exit 1; }

MEDIA_ENDPOINT=$(jq -r .endpoint <<<"$CREDS")
MEDIA_BUCKET=$(jq -r .bucketName <<<"$CREDS")
MEDIA_REGION=$(jq -r '.region // "auto"' <<<"$CREDS")
MEDIA_ACCESS_KEY_ID=$(jq -r .accessKeyId <<<"$CREDS")
MEDIA_SECRET_ACCESS_KEY=$(jq -r .secretAccessKey <<<"$CREDS")
unset CREDS
export MEDIA_ENDPOINT MEDIA_BUCKET MEDIA_REGION MEDIA_ACCESS_KEY_ID MEDIA_SECRET_ACCESS_KEY
export MEDIA_ADDRESSING=$STYLE MEDIA_PUBLIC_URL=$PUBLIC
"$STUDIO" --project "$PROJECT" channel connect media
unset MEDIA_ACCESS_KEY_ID MEDIA_SECRET_ACCESS_KEY

echo "media hosting ready. Next: $STUDIO --project $PROJECT channel connect buffer"
