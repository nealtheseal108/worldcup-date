# worldcup-date — handoff (2026-07-07)

Gift site for Sidhya, built around July 6, 2026 (World Cup Round of 16 watch-party date, Seattle). The date already happened. The site is now half memento/diary, half still-active tool (photo/video album, movie compilation, Utah trip planning).

## 🔴 CRITICAL — do this first

**The backend has not been redeployed since July 5.** Every backend fix from the last two days (score/minute/play badge columns, 40MB→80MB upload cap) is sitting in git but NOT live. This is why photo/video uploads have been failing/slow.

**Fix:** [Render dashboard → worldcup-diary → Manual Deploy → Deploy latest commit](https://dashboard.render.com/web/srv-d90c0bb7uimc7398j010)

There is no API/MCP tool that can trigger this — confirmed repeatedly this session. It requires a human click.

**Open question, awaiting your yes/no:** turn on auto-deploy for this service (currently off) so this never happens again. Tradeoff: every future commit (even frontend-only ones) would also restart the backend — brief, harmless at this scale, but worth knowing before I flip it. I attempted this once already and it was correctly blocked by the safety layer since you hadn't explicitly said yes to *that specific* change.

## Architecture

| Service | Type | ID | Notes |
|---|---|---|---|
| `worldcup-date` | Static site | `srv-d8upfr6q1p3s73f1m5ug` | index.html, auto-deploys on push to `main` |
| `worldcup-diary` | Flask + Postgres backend | `srv-d90c0bb7uimc7398j010` | Clip/state sync API, **auto-deploy OFF** (manual only) |
| `worldcup-diary-keepalive` | Cron job | `crn-d95dhjlckfvc73b8c6sg` | Pings `/api/health` every 10 min so the free-tier backend doesn't cold-sleep |

Render workspace: "Neal's Workspace" (`tea-d76nd97afjfc73a831ug`).

Backend: `CLOUD.url = https://worldcup-diary.onrender.com`, key `wcd_d1ary_Kq7Fz9mR2pX8sV4nL6tB3` (in index.html as `CLOUD`). Postgres backing it **expires 2026-07-27** — anything meant to last needs to be exported before then (there's a "time capsule" backup-everything feature in the site itself for this).

Two Postgres tables: `clips` (photos/videos, `sec` column tags which bucket/leg — `'photo'`/`'video'`/`'bv-photo'`/`'bv-video'` are free-standing album buckets, `'s0'`–`'s5'` are the 6 real itinerary legs) and `state` (generic key-value sync for picks, bingo—now removed, Utah passport, flight log, etc. — see `SYNCED_KEYS` in index.html).

## What changed this session (chronological, all pushed to `main`)

- Identity system (nealp108/sidhya6/guest), cloud state sync for every interactive piece (not just photos)
- Mass photo + video upload (existing files, not just live capture) — both the general album and a per-itinerary-leg version, plus the July-4 Bellevue Park mini-date album
- Live-match score/minute/significant-play badge on captured media (**not live yet — needs the backend redeploy above**)
- Fixed: arrival-pass tap-to-edit was completely dead (no handler ever wired up)
- Fixed: `exportMovie()` could hang forever if the tab lost focus mid-render (rAF → setInterval)
- Fixed: cloud-state boot no longer discards a slow/cold backend's answer — self-heals instead of requiring a manual reload
- Pike Place Market neon sign (die-cut badge replica, flickering) on the Pier 62 venue card and as a static page-bottom flourish
- 92 independently fact-checked World Cup 2026 trivia questions (new standalone quiz, step15) — kept separate from the personal "how well do you know us" quiz on purpose
- Removed Babu Bingo and Photo Missions entirely — confirmed via real cloud data neither was touched during the actual date; gamified activities don't fit being present on a real date (saved as a standing lesson in memory)
- **Replaced the planned itinerary with what actually happened**: Redmond Tech → Pier 62 (the match) → Pier 59 → Falafel King (dinner) → Bellevue Downtown → home. Dropped the now-dead "add to calendar" button and its helpers, and the "stolen hour" R-mode joke (that leg no longer exists).
- Fixed: bracket view broke visually past the quarterfinals on wide/desktop screens (scale-cap math, not the underlying connector logic, which was always correct)
- Fixed: Utah-plan nav button overflowed off-screen on mobile (4-button row needed `flex-wrap`)
- Fixed: Bellevue Park pass overlay couldn't scroll to its own bottom content (`overflow:hidden` → `overflow-y:auto`)

## Known-good / verified this session

Verified live in preview (not just code-read) for: mass photo/video upload → cloud sync → gallery render → lightbox playback, per-leg record-or-add-video → movie gatherer inclusion, cloud self-heal race fix, bracket zoom scale fix, Bellevue scroll fix, nav-button wrap fix, FIFA quiz scoring/reveal, new itinerary structure end-to-end (share card, timeline, tk-steps).

**Not yet verified against the *live* production backend** (blocked on the redeploy above): live-match badges actually persisting to the cloud DB, 80MB upload cap actually taking effect.

## Outstanding / needs your input

1. **Backend redeploy** (see top — do this first, then ping me to verify).
2. **Auto-deploy toggle** — yes/no (see above).
3. **Stale test data in the shared cloud `state` store** — flagged a while back, never resolved: `wc_pick`/`wc_arrival_from`/`wc_return_no`/`wc_return_date`/`wc_bingo_seed` may still hold values I pushed while testing, not real data from you or Sidhya. Low priority now that bingo is removed entirely (that key is inert) and the pick/arrival/return keys get overwritten by real use anyway — but flagging again since it was never explicitly resolved.
4. **Task #40** (pre-existing, still pending): generate decoy options for 20 real diabolical quiz quotes via Fable — never picked back up.
5. Once you've actually uploaded your real July 6 photos/videos, worth a final check that they render correctly across the album, the per-leg diary rows, and the movie compilation.

## Test bypasses built into the site (don't leave these in a URL you actually use)

- `?rec=1` — removes the recording time/length cap
- `?end=1` — force-unlocks the diary/movie/return-flight reveal early
- `?egg` — the barcode easter egg
