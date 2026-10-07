---
id: buffer-api-coverage
type: reference
created: "2026-10-06T21:30:00Z"
consequence: 7
locus: output
summary: What Buffer's 2026 API covers for social-studio (Instagram, X, Facebook, scheduling, metrics, comments) and what it leaves out, with limits and sources.
scope: repo
status: active
---

# Buffer API coverage for social-studio

The operator, 2026-10-06, asked to connect Buffer instead of building the publishing, calendar and platform layer from scratch, and asked whether Buffer covers Instagram, X, Facebook, scheduling, the API, feedback, comments and engagement analysis. This note answers that question. It sits next to [[social-platform-apis]], which covers posting directly to each platform.

## Question

Can social-studio drive Buffer from code to post to Instagram, X and Facebook, schedule posts, read engagement, and read or reply to comments?

## Findings

| Need | Through the API | Notes |
|---|---|---|
| Instagram | yes | post, story and reel; user tags; first comment |
| Facebook | yes | |
| X | yes | Buffer notes X is subject to X's own API plan restrictions |
| Scheduling | yes | `createPost` with queue or a custom ISO time; edit and delete |
| API access | yes | GraphQL at api.buffer.com, official MCP server at mcp.buffer.com/mcp, CLI; personal key or OAuth 2.0; every plan, Free included |
| Post metrics | partly | reactions, comments count, reposts, shares, impressions, reach, views; saves and follows on Instagram; pulled daily, up to ~24 h lag; "a missing metric does not mean zero"; personal API key only, OAuth app clients cannot read metrics |
| Read comments | no | the reference lists no comment query |
| Reply to comments | no | no comment mutation; only the "first comment" on Instagram at post time |
| Feedback and comment analysis | no | Buffer Community (10 networks, Instagram, Facebook and X included; free up to 3 channels) is in the Buffer app only |
| Webhooks | no | polling only |
| Media upload | no | media must be at a public URL Buffer can fetch |

Limits: 100 requests per 15 min. Per 24 h: 250 on Free and Essentials, 500 on Team. Per 30 days: 3,000, 7,500 and 15,000. One channel per `createPost`. The legacy v1 REST API retires 2027-02-01, with brownouts on 2026-11-11 and 2026-12-09; build on GraphQL only.

Pricing, from third-party sources: Free; Essentials about $5-6 per channel per month; Team about $10-12 per channel per month; tier discounts above 10 channels.

## What this means for the build

- Covered by Buffer: publishing, calendar and scheduling on all three platforms, plus daily per-post numbers.
- Not covered: reading comments, replying to them and analysing them from code. Those need a second source: each platform's own API (Instagram Graph and Facebook Graph comment endpoints, X API v2 replies on a paid tier), or a separate inbox product with an API.
- Media hosting: approved videos need a public, stable URL before `createPost`. Buffer's hosting guide (developers.buffer.com/guides/hosting-media) rules out signed or expiring links, because Buffer fetches the file when the post goes out; it names Cloudinary and Cloudflare R2.

## Decision and build (2026-10-06)

The operator chose Buffer for posting and scheduling only, over GraphQL, with the operator picking each post at a terminal (rule R14). Comments and engagement are out for now. As built (feature F6): `platforms/buffer.py`, `platforms/media.py` (S3-compatible, SigV4) and `posting.py`; see [[schedule-publish]].

## Sources

- https://buffer.com/resources/buffer-api-is-here/
- https://developers.buffer.com/reference.html (no comment query or mutation, no upload mutation)
- https://developers.buffer.com/guides/post-metrics.html (metric list, insightsRead scope, personal key only, daily cadence)
- https://developers.buffer.com/guides/api-limits.html
- https://buffer.com/resources/introducing-community/ (Community networks and plans)
- https://www.postzen.dev/blog/buffer-api ("no reading or replying to comments through the API")
- https://zernio.com/blog/buffer-pricing, https://napoleoncat.com/blog/buffer-pricing/ (pricing)
- https://glama.ai/mcp/servers/nqj5i7jy3d (MCP server listing)

## Date

Gathered 2026-10-06.
