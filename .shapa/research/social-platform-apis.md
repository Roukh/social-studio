---
id: social-platform-apis
type: reference
created: "2026-10-01T00:00:00Z"
consequence: 7
locus: output
summary: Per-platform auth/token, upload limits, scheduling, metadata, ToS-automation and review/cost facts behind social-studio's posting adapters.
scope: repo
status: active
---

# social-platform-apis — posting constraints per platform

The direct posting route this research informed (social-studio's own platform adapters) was removed on 2026-10-06; social-studio now posts only through Buffer ([[buffer-api-coverage]]). Kept as reference.

Reference for social-studio's own posting pipeline (it posts approved videos itself, no third-party scheduler). Gathered 2026-10-01 against each platform's live docs.

## Question

For each platform social-studio can post to: what are the auth flow and token lifetime, upload mechanics and limits, scheduling support, metadata limits, ToS automation restrictions, and review/audit cost — and is there an idempotency key to prevent double-posting?

## Method

Live official docs fetched and quoted 2026-10-01, tagged `[v]` where directly confirmed. Tagged `[3p]` (third-party/inferred) where unreachable: X's media-upload/automation-rules pages (404), Pinterest's docs (JS SPA), `docs.bsky.app` (TLS failure; worked around via the AT Protocol spec site and raw lexicon JSON on GitHub).

## Findings

### Summary matrix

| Platform | Auth / PKCE / redirect | Token lifetime | Upload mechanism & limits | Scheduling | Review / cost |
|---|---|---|---|---|---|
| Instagram (Instagram Login) | OAuth2 Business Login; redirect not confirmed | 1h short / 60d long-lived, re-exchanged (no refresh grant) | `video_url` only, must be publicly hosted, no local upload [v] | None | Advanced Access needs Meta App Review; pre-review limited to app-role accounts. Free |
| Instagram (Facebook Login) | OAuth2 FB Login for Business | Same 60d pattern | Resumable `rupload.facebook.com`, local binary via `offset`/`file_size` or `file_url`, covers VIDEO/REELS/STORIES [v] | None | Same App Review gate. Free. **Built** (Meta resumable upload) |
| Facebook Pages | OAuth2 FB Login for Business; Page token from 60d user token | 60d (Page token) | Resumable `rupload.facebook.com` or chunked `upload_phase` start/transfer/finish, or `file_url`. Reels: 1080x1920 (540x960 min), 3-90s, 24-60fps, H.264/H.265/VP9/AV1, AAC 128kbps+ 48kHz [v] | Yes: `scheduled_publish_time`. Feed 10min-75d; Reels guide says 10min-29d — treat 29d as binding for Reels [v] | Dev mode = Admins/Devs/Testers, else App Review. Free. **Built** |
| Threads | OAuth2, own endpoint | 1h/60d; `th_refresh_token` needs token ≥24h old; unused 60d = permanent expiry [v] | Public URL only (cURL fetch), MOV/MP4, HEVC/H.264, AAC ≤48kHz, 23-60fps, ≤300s, ≤1GB, aspect 0.01:1-10:1, ≤100Mbps VBR [v] | None | Dev mode = invited Testers only until App Review. Free. Not built |
| LinkedIn (Member) | OAuth2 code flow, **no PKCE**, no loopback (exact HTTPS redirect, no query/fragment); auth code expires 30min | Access 60d flat; refresh token only for approved Marketing Developer Platform partners, 365d sliding [v] | Videos API: `initializeUpload`→4MB chunks `PUT`→`ETag`→`finalizeUpload`; URLs expire 30d; practical spec ~500MB/30min MP4 (page also claims 5GB cap — conflicting, verify live) [v] | None (states: DRAFT/PUBLISHED/PUBLISH_REQUESTED/PUBLISH_FAILED) | Rate limits unpublished, per-app in Developer Portal only — do not hardcode. Free. **Automation banned by ToS** → draft-folder only |
| LinkedIn (Organization) | Same mechanism; scope `w_organization_social`, role-gated | Same | Same Videos API | None | Needs Community Management API grant + Administrator/DSC-Poster/Content-Admin role. Same automation ban → draft-folder only |
| YouTube | OAuth2 installed-app (loopback `127.0.0.1`/`[::1]` recommended) or device flow (headless); PKCE recommended not mandatory | Access ~1h; refresh has no fixed expiry but dies after 6mo idle, 100-token/account cap, or forced 7d churn in "Testing" | `videos.insert` resumable chunked, 256KB multiples (chunking discouraged), `video/*`/octet-stream, max 256GB [v] | Native: `status.privacyStatus=private` + `status.publishAt` ISO8601; past timestamp publishes immediately [v] | `videos.insert` = 1 unit, default 100/day (was ~1600u/10k pool pre-2025-12-04). New API projects stay **private until a compliance audit clears**. Free. **Built**; audit is open work |
| TikTok | OAuth2, PKCE required (desktop/mobile); verified HTTPS redirect domain per app, no localhost exception found | Access 24h; refresh 365d [v] | Direct Post (public, audit-gated) vs inbox/drafts (user publishes manually in-app, no audit needed); `FILE_UPLOAD` chunked `PUT` w/ `Content-Range`, URL valid 1h, init limited 6 req/min/token; alt `PULL_FROM_URL` [v] | None | Unaudited clients hard-locked to `SELF_ONLY`. Guidelines name "a utility tool to help upload content to the account(s) you or your team manages" as an **unacceptable** audit target [v]. Free → draft-folder only |
| X (Twitter) | OAuth2 code + PKCE (effectively mandatory); loopback unconfirmed | Access 2h default; refresh only with `offline.access` scope (lifetime unstated) | Historic `media/upload.json` INIT/APPEND/FINALIZE chunked; endpoint page 404'd this session, historically needed OAuth1.0a even under v2 — verify live [3p] | None found | No free posting tier: $0.015/post, $0.20/post with a link, $0.015 DM, $0.010 delete; reads capped 3M/month before Enterprise [v]. **Built** (v2 chunked); paid-tier live test is open work |
| Bluesky | AT Protocol OAuth2.1 (PKCE+DPoP mandatory) with explicit `http://localhost` client_id exception, or legacy app password via `createSession` (simplest) | Access ≤30min (≤15min/5min rec if no revocation); refresh ≤2wk total session (public clients) or ≤180d/token (confidential) [v] | `com.atproto.repo.uploadBlob`, `video/mp4` ≤300MB (was 100MB), ≤20 `.vtt` tracks (≤20KB each), alt text; no duration cap in schema, public ~60s limit is server-side [3p] | None; `createRecord` posts immediately [v] | No app review; free. **Built** (blob upload); live test with a real session is open work |
| Pinterest | OAuth2 flavor/PKCE/redirect/lifetimes unconfirmed (SPA docs); scopes `boards:read/write`, `pins:read/write` via auth-code or client_credentials [v] | Unconfirmed | No `video_url` option: must register via Media API for a `media_id`, then `source_type:"video_id"` (register-then-reference, like TikTok/LinkedIn). Historic help-center figures ~2GB/~15min MP4/MOV/M4V [3p] | None found in schema | Industry-reported trial-vs-standard tiers, unconfirmed [3p]. Free. Not built |

### Metadata limits worth hardcoding
IG/FB: `alt_text` image-only, JPEG-only, carousels ≤10 items, 100 posts/24h (IG), 30 Reels/24h (FB Page). Threads: 250 posts/24h/profile. YouTube: title ≤100 chars, description ≤5000 bytes, tags ≤500 chars combined, thumbnail ≤50MB (was 2MB until 2026-09-14), `status.containsSyntheticMedia` bool (AI disclosure), `status.selfDeclaredMadeForKids` schema-optional but policy-required. TikTok: `is_aigc` bool, `video_cover_timestamp_ms`, `privacy_level` gated by audit. X: 280 chars (more for Premium), alt text via separate call. Bluesky: text ≤3000 UTF-8 bytes/300 graphemes, links/mentions/hashtags as byte-range `facets`, ≤8 `tags` (≤64 graphemes), self-applied `labels`. Pinterest: `alt_text` ≤500 chars, `link` ≤2048 chars, `ai_disclosures` enum (`AI_MODIFIED`, `SYNTHETIC_PERFORMER`) — most precise AI-disclosure schema found. LinkedIn: `commentary` supports mention/hashtag annotations; `content.article` does not auto-scrape the URL, fields must be set manually.

### ToS automation risk (why LinkedIn/TikTok are draft-only)
LinkedIn API Terms §3.1, verbatim: "Use the Content or the APIs to automate posting on the LinkedIn Services" is prohibited [v]. TikTok's Content Sharing Guidelines name "a utility tool to help upload contents to the account(s) you or your team manages" as an unacceptable audit target [v] — a near-verbatim match for this tool. No equivalent ban was found for Meta, YouTube, X, Bluesky, or Pinterest; those frame consented self-posting as compliant use.

### Idempotency / duplicate-post gap (open work)
No publish/upload-init endpoint reviewed (Meta containers, YouTube `videos.insert`, X chunked upload, Bluesky `uploadBlob`/`createRecord`) carries a documented idempotency key or client-token. A crash/retry between a successful upload and the local DB write can double-post. Fix needs either a per-platform idempotency key (none found to reuse) or a remote existence lookup before retrying (e.g. list recent videos/posts by caption+timestamp) — per-adapter, no shared mechanism.

### Live-test gap (open work)
Built adapters still need a live test against a real developer app: Meta App Review (Instagram/Facebook Advanced Access), YouTube's compliance audit (or uploads stay private), X's paid tier, a real Bluesky session.

### BYOA, hosting, token storage
- **BYOA**: Postiz (AGPL-3.0) and Mixpost Lite (MIT) both require each self-hoster's own per-platform app; a shared app would concentrate the exact risk TikTok's/LinkedIn's ToS already flag. Right call for a single-user local tool.
- **Public-URL hosting** (IG-Login, Threads, TikTok `PULL_FROM_URL`, Pinterest): presigned R2/S3 URLs, not tunnels. R2: ≤7-day expiry, zero egress fees [v]. Cloudflare Quick Tunnels are dev-only, no uptime guarantee, 200 in-flight cap [v] — unfit here.
- **Token storage**: OS keyring needs a desktop session on Linux and falls back to plaintext via `keyrings.alt` [v]. Use `.env` (`chmod 600`, gitignored) as the baseline, keyring opt-in. Refresh tokens rotate on use (LinkedIn confirmed [v]) — always persist the new one.

## Sources

- https://developers.facebook.com/docs/instagram-platform/ (get-started, content-publishing, instagram-api-with-facebook-login, video-api/guides/reels-publishing)
- https://developers.facebook.com/docs/graph-api/reference/page/ (feed, videos)
- https://developers.facebook.com/docs/threads/ (get-started, get-started/long-lived-tokens, posts)
- https://learn.microsoft.com/en-us/linkedin/ (shared/authentication/authorization-code-flow, shared/authentication/programmatic-refresh-tokens, marketing/community-management/shares/posts-api, marketing/community-management/shares/videos-api, shared/api-guide/concepts/rate-limits)
- https://www.linkedin.com/legal/l/api-terms-of-use
- https://developers.google.com/youtube/v3/ (docs/videos/insert, docs/videos, guides/auth/installed-apps, guides/using_resumable_upload_protocol, determine_quota_cost, revision_history), https://developers.google.com/identity/protocols/oauth2 (+limited-input-device, production-readiness/restricted-scope-verification), https://developers.google.com/youtube/terms/
- https://developers.tiktok.com/doc/ (oauth-user-access-token-management, content-posting-api-get-started, content-posting-api-reference-direct-post, content-sharing-guidelines)
- https://docs.x.com/ (resources/fundamentals/authentication/oauth-2-0/authorization-code, x-api/getting-started/pricing)
- https://atproto.com/specs/oauth, raw lexicon JSON: lexicons/app/bsky/embed/video.json, lexicons/app/bsky/feed/post.json (bluesky-social/atproto on GitHub)
- https://developers.pinterest.com/docs/api/v5/pins-create/
- https://github.com/gitroomhq/postiz-app, https://github.com/inovector/mixpost (+ LICENSE files)
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPresignedURL.html, https://developers.cloudflare.com/r2/ (api/s3/presigned-urls, pricing), https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/
- https://pypi.org/project/keyring/

## Date

Gathered 2026-10-01; condensed 2026-10-06 for the format 4 wiki.
