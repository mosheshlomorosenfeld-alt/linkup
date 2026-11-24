# Linkup — collabs & jobs

Moshe Rosenfeld's tool for finding music collaborators and music-industry jobs.

- **Collaborator finder** — pick a role (vocalist, producer, DJ, topliner, mix engineer…) and a sound (EDM, pop, rave, Jewish/Yeshiva, R&B…) and get pre-filled searches on 17 platforms: Instagram, TikTok, YouTube, SoundCloud, Spotify, BandLab, SoundBetter, Fiverr, AirGigs, Backstage, LinkedIn, Reddit, X, Discord, Kompoz and Google. Includes an outreach-DM generator.
- **Job finder** — one search opens on 22 job boards (LinkedIn, Indeed, Google Jobs, Glassdoor, ZipRecruiter, Monster, Handshake, EntertainmentCareers, Music Business Worldwide, Greenhouse/Lever/Workday ATS…) plus 12 label and industry career pages.
- **Live feed** — a GitHub Action pulls fresh music jobs every morning into `data/jobs.json`.
- **Tracker** — save people and jobs, score collaborators on fit (genre, quality, reach, vibe), move them through a pipeline. Saved in your browser.

## Turn it on (one time)

1. **Pages:** Settings → Pages → Source: *Deploy from a branch* → `main` / root → Save. The site goes live at `https://mosheshlomorosenfeld-alt.github.io/linkup/`.
2. **First feed run:** Actions tab → *Fetch jobs* → *Run workflow*. After that it runs daily on its own.

## Pull from even more sites (optional)

Free sources (Remotive, The Muse, Arbeitnow, Jobicy, Himalayas) need nothing. Add any of these under Settings → Secrets and variables → Actions to switch on more:

| Secret | What it adds |
|---|---|
| `SERPAPI_KEY` | Google Jobs — listings from LinkedIn, Indeed, Glassdoor, ZipRecruiter and more (free tier at serpapi.com) |
| `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` | Adzuna US (free at developer.adzuna.com) |
| `USAJOBS_KEY` + `USAJOBS_EMAIL` | USAJobs (free at developer.usajobs.gov) |

Change the keywords and locations in `config.json`.
