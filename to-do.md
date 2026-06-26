# World Cup Date — To-Do / Wishlist

Future ideas for **https://worldcup-date.onrender.com** (repo: `nealtheseal108/worldcup-date`).
Everything lives in the single `index.html`.

## 🎵 Record a custom song for the site
- Record an original / personal track (a little song or voice note for Sidhya) to use as the
  background music instead of — or as the first track before — the current playlist.
- The player is currently a YouTube IFrame playlist (the `MUSIC` array in `index.html`).
  A recorded file would swap in an `<audio>` element (host the MP3 in the repo or on Render),
  played first, then hand off to the playlist.
- Keep the Spotify-style bottom bar working with it (title/artist, play/pause, prev/next).

## ⏱️ Live day-of tracker (for July 6, 2026)
- A live view that, on the actual date, highlights where we are in the itinerary in real time.
- **Now / Next:** auto-highlight the current timeline beat from the clock; show a countdown to
  kickoff (5:00 PM) and to each upcoming step.
- Nice-to-haves: live match clock/score, 2 Line transit status, weather.
- **Live score tracker:** during the match, show the live World Cup score + clock for our game (the matchup is already wired as the `MATCHUP` var; pull from a football score API/feed).
- **Post-match analysis + planning:** after full time, swap in a quick post-match recap/analysis and a "what's next" planner (head to dinner now vs wait out the crowd, adjust timings based on how it went / if it went to extra time).
- v1 needs no backend — a client-side clock that highlights the active itinerary row and shows
  "starts in X min" is enough; layer live data in later.

## 📌 Before the date — to confirm
- [ ] **Sidhya's dad confirms the flight booking** — the whole date hinges on this, so lock it in first.

## ✅ Already shipped
- Looping music playlist (Shotput slowed+reverb → Link Up → Heat Waves → Babydoll → Flight's Booked)
  with a Spotify-style bottom player bar (prev / play-pause / next).
- Editorial type system: Inter (body/headings) + Courier Prime (typewriter labels) + Instrument Serif accent.
- Shareable Kalshi-style ticket card — PNG and animated GIF export.
- Budget-aware vegetarian meal picks ($/$$, no splurges) with Eastside options on the 2 Line home.
- Itinerary beats incl. the post-dinner Salt & Straw + Bellevue Downtown Park moment.
