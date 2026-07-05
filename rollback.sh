#!/usr/bin/env bash
#
# Emergency rollback — restore the last-known-good invite to the LIVE site in one command.
#
# Use this if a change you pushed (e.g. a new photo-section animation) misbehaves on a
# real phone and you need the live URL back to a working state immediately.
#
#   ./rollback.sh            # restore the version tagged 'stable' and push it live
#   ./rollback.sh <ref>      # restore any git commit/tag instead (e.g. ./rollback.sh 5cbcbc6)
#
# It does NOT rewrite history — it makes a NEW commit that restores the old file contents,
# then pushes, which triggers Vercel to redeploy. Safe to run anytime.
#
set -euo pipefail
cd "$(dirname "$0")"

TARGET="${1:-stable}"
LIVE_URL="https://arjita-archit.vercel.app/"

echo "→ Rolling RokaInvite.dc.html back to '$TARGET'…"

# make sure the ref exists locally (tags may only be on the remote after a fresh clone)
git fetch --tags --quiet 2>/dev/null || true
if ! git rev-parse --verify --quiet "$TARGET^{commit}" >/dev/null; then
  echo "✗ '$TARGET' is not a known commit or tag. Available restore tags:"
  git tag --list
  exit 1
fi

git checkout "$TARGET" -- RokaInvite.dc.html

if git diff --cached --quiet -- RokaInvite.dc.html; then
  echo "✓ RokaInvite.dc.html already matches '$TARGET' — nothing to roll back."
  exit 0
fi

git commit -m "rollback: restore '$TARGET' invite (reverting a change that broke on mobile)" RokaInvite.dc.html
git push

echo "✓ Pushed. Vercel redeploys the restored version in ~30s → $LIVE_URL"
