#!/usr/bin/env python3
"""Fetch music-related jobs from public job APIs and write data/jobs.json.

Runs daily in GitHub Actions. Free sources need no keys. Optional sources turn on
automatically when their secrets are set in the repo (Settings → Secrets → Actions):
  SERPAPI_KEY              Google Jobs (pulls listings from LinkedIn, Indeed, Glassdoor, ZipRecruiter…)
  ADZUNA_APP_ID/ADZUNA_APP_KEY   Adzuna US
  USAJOBS_KEY + USAJOBS_EMAIL    USAJobs
Edit config.json to change keywords and locations.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json")))
KEYWORDS = [k.lower() for k in CFG["keywords"]]
UA = {"User-Agent": "linkup-job-fetcher/1.0 (+github actions)"}


def get(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(s or ""))).strip()


def relevant(*fields):
    text = " ".join(clean(f).lower() for f in fields)
    return any(re.search(r"\b" + re.escape(k) + r"\b", text) for k in KEYWORDS)


def job(title, company, location, url, source, posted=""):
    return {"title": clean(title)[:160], "company": clean(company)[:100] or "—",
            "location": clean(location)[:100], "url": url, "source": source, "posted": posted or ""}


def remotive():
    out = []
    for term in CFG["api_terms"]:
        d = get("https://remotive.com/api/remote-jobs?" + urllib.parse.urlencode({"search": term, "limit": 100}))
        for j in d.get("jobs", []):
            if relevant(j.get("title"), j.get("category"), j.get("tags")):
                out.append(job(j["title"], j.get("company_name"), j.get("candidate_required_location") or "Remote",
                               j["url"], "Remotive", j.get("publication_date", "")))
    return out


def themuse():
    out = []
    for loc in CFG["locations_muse"]:
        for page in range(3):
            d = get("https://www.themuse.com/api/public/jobs?" + urllib.parse.urlencode({"page": page, "location": loc}))
            for j in d.get("results", []):
                cats = " ".join(c.get("name", "") for c in j.get("categories", []))
                if relevant(j.get("name"), cats, (j.get("contents") or "")[:600]):
                    locs = ", ".join(l.get("name", "") for l in j.get("locations", []))
                    out.append(job(j["name"], (j.get("company") or {}).get("name"), locs,
                                   (j.get("refs") or {}).get("landing_page", ""), "The Muse", j.get("publication_date", "")))
            if page + 1 >= d.get("page_count", 0):
                break
    return out


def arbeitnow():
    out = []
    for page in range(1, 4):
        d = get(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
        for j in d.get("data", []):
            if relevant(j.get("title"), j.get("tags")):
                ts = j.get("created_at")
                posted = datetime.fromtimestamp(ts, timezone.utc).isoformat() if isinstance(ts, (int, float)) else ""
                out.append(job(j["title"], j.get("company_name"), j.get("location") or ("Remote" if j.get("remote") else ""),
                               j["url"], "Arbeitnow", posted))
    return out


def jobicy():
    out = []
    for tag in CFG["api_terms"]:
        d = get("https://jobicy.com/api/v2/remote-jobs?" + urllib.parse.urlencode({"count": 50, "tag": tag}))
        for j in d.get("jobs", []):
            if relevant(j.get("jobTitle"), j.get("jobIndustry"), j.get("jobExcerpt")):
                out.append(job(j["jobTitle"], j.get("companyName"), j.get("jobGeo") or "Remote", j["url"], "Jobicy", j.get("pubDate", "")))
    return out


def himalayas():
    out = []
    d = get("https://himalayas.app/jobs/api?limit=100")
    for j in d.get("jobs", []):
        if relevant(j.get("title"), j.get("categories"), (j.get("excerpt") or "")):
            ts = j.get("pubDate")
            posted = datetime.fromtimestamp(ts, timezone.utc).isoformat() if isinstance(ts, (int, float)) else ""
            out.append(job(j["title"], j.get("companyName"), ", ".join(j.get("locationRestrictions") or []) or "Remote",
                           j.get("applicationLink") or j.get("guid", ""), "Himalayas", posted))
    return out


def serpapi_google_jobs():
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        return []
    out = []
    for q in CFG["search_queries"]:
        for loc in CFG["locations"]:
            d = get("https://serpapi.com/search.json?" + urllib.parse.urlencode(
                {"engine": "google_jobs", "q": q, "location": loc, "hl": "en", "api_key": key}))
            for j in d.get("jobs_results", []):
                opts = j.get("apply_options") or []
                url = opts[0]["link"] if opts else j.get("share_link", "")
                via = (j.get("via") or "Google Jobs").replace("via ", "")
                out.append(job(j.get("title"), j.get("company_name"), j.get("location"), url, via,
                               (j.get("detected_extensions") or {}).get("posted_at", "")))
    return out


def adzuna():
    aid, akey = os.environ.get("ADZUNA_APP_ID"), os.environ.get("ADZUNA_APP_KEY")
    if not (aid and akey):
        return []
    out = []
    for q in CFG["search_queries"]:
        for loc in CFG["locations"]:
            d = get("https://api.adzuna.com/v1/api/jobs/us/search/1?" + urllib.parse.urlencode(
                {"app_id": aid, "app_key": akey, "what": q, "where": loc, "results_per_page": 50, "max_days_old": 30}))
            for j in d.get("results", []):
                out.append(job(j.get("title"), (j.get("company") or {}).get("display_name"),
                               (j.get("location") or {}).get("display_name"), j.get("redirect_url"), "Adzuna", j.get("created", "")))
    return out


def usajobs():
    key, email = os.environ.get("USAJOBS_KEY"), os.environ.get("USAJOBS_EMAIL")
    if not (key and email):
        return []
    out = []
    for q in CFG["search_queries"]:
        d = get("https://data.usajobs.gov/api/search?" + urllib.parse.urlencode({"Keyword": q, "ResultsPerPage": 50}),
                {"Authorization-Key": key, "User-Agent": email, "Host": "data.usajobs.gov"})
        for item in d.get("SearchResult", {}).get("SearchResultItems", []):
            m = item.get("MatchedObjectDescriptor", {})
            out.append(job(m.get("PositionTitle"), m.get("OrganizationName"), m.get("PositionLocationDisplay"),
                           m.get("PositionURI"), "USAJobs", m.get("PublicationStartDate", "")))
    return out


SOURCES = [remotive, themuse, arbeitnow, jobicy, himalayas, serpapi_google_jobs, adzuna, usajobs]


def main():
    jobs, report = [], {}
    for fn in SOURCES:
        try:
            got = fn()
            report[fn.__name__] = len(got)
            jobs += got
        except Exception as e:  # one broken source never kills the run
            report[fn.__name__] = f"error: {e}"
        time.sleep(1)
    seen, unique = set(), []
    for j in jobs:
        k = (j["title"].lower(), j["company"].lower())
        if j["url"] and k not in seen:
            seen.add(k)
            unique.append(j)
    unique.sort(key=lambda j: j["posted"] or "", reverse=True)
    out = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "sources": report, "jobs": unique[:600]}
    path = os.path.join(ROOT, "data", "jobs.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps(report, indent=1), f"\n{len(unique)} jobs written")


if __name__ == "__main__":
    sys.exit(main())
