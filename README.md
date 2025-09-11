# Friluft

A simple project that scrapes Swedish outdoor POIs (friluftsliv: hiking, paddling, camping, viewpoints, shelters, etc.) from OpenStreetMap via Overpass, and renders them on a Leaflet web map.

## Structure

- `scraper/overpass_scraper.py`: Fetches data from Overpass and writes GeoJSON.
- `data/`: Output folder for `friluft.geojson`.
- `web/`: Static Leaflet map to visualize the data.

## Install

Prerequisites: Python 3.9+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Scrape data

This queries Overpass for Swedish POIs related to hiking, paddling, and outdoor recreation, and writes `data/friluft.geojson`.

Filtering:
- Only keeps places that have a valid website/contact URL in OSM tags (e.g. `website`, `contact:website`, `url`).

```bash
python scraper/overpass_scraper.py --out data/friluft.geojson
```

Options:

- `--categories`: Comma-separated subset of categories to fetch. Defaults to all.
  - Available: `national_park,nature_reserve,camp_site,shelter,viewpoint,picnic_site,slipway,canoe_kayak,boat_rental,trailhead,bbq,drinking_water,toilets,swimming_area`
- `--endpoint`: Overpass endpoints (comma-separated to rotate; default includes kumi + overpass-api.de)
- `--include-social`: Allow social profile URLs if `website` is missing (e.g. Facebook/Instagram/Twitter)
- `--retries`: Retries per Overpass query across endpoints (default 3)

## Run the map

Serve the `web/` folder with any static server and open in a browser. For example:

```bash
python -m http.server --directory web 8000
# Then open http://localhost:8000
```

The map reads `../data/friluft.geojson` by default. If serving from another root, adjust the fetch path in `web/app.js`.

## GitHub Pages (auto-deploy)

This repo includes a GitHub Actions workflow to scrape fresh data and publish the static site to GitHub Pages on every push to `main`.

1. Create the public repo `perwinroth/friluft` and push this project (see below).
2. GitHub → Settings → Pages: set Source to "GitHub Actions" (the workflow handles deploys).
3. After the workflow finishes, open: `https://perwinroth.github.io/friluft/web/`.

Workflow details:
- Installs Python + deps, runs ETL (OSM + optional extra sources), enriches from OpenGraph.
- Validates non-empty output, generates `web/list.html`, publishes `web/` and `data/` via Pages.
- Weekly refresh via cron; configure extra source URLs via environment in the workflow.

## Next.js app (bookable product MVP)

- Location: `site/` (Next.js 14, App Router). Pages:
  - `/` (home), `/search` (map + filters), `/l/[slug]` (listing), `/aktivitet/[slug]`, `/region/[slug]`.
  - API stubs: `/api/listings` (GET), `/api/leads` (POST).
- Dev
  ```bash
  cd site
  npm install
  npm run dev
  # open http://localhost:3000
  ```
- Data access: server reads `../data/places.json` (fallback to `../data/friluft.geojson`). Run ETL before `npm run build` for fresh content.
- SEO: JSON‑LD for WebSite/Product/Offer, Next sitemap, canonical metadata; static place pages also generated in `web/places/`.
- Deploy (Vercel recommended): import `site/` as a project, set root to `friluft/site`, build command `npm run build`, output `.next`.

## ETL (extended data pipeline)

- Entry point: `etl/run_etl.py` combines sources, dedupes, enriches, and writes outputs:
  - OSM via Overpass (website-only filter)
  - Optional: HAV badplatser (env: `HAV_BADPLATSER_URL`)
  - Optional: Municipal open dataset CSV/JSON (env: `MUNICIPAL_DATASET_URL`, `MUNICIPAL_DATASET_TYPE`, `MUNICIPAL_ACTIVITY`)
  - Enrichment: fetch OpenGraph/schema.org from websites (limit via `ENRICH_MAX`)
- Outputs:
  - `data/places.json`: combined, enriched places (includes opening_hours, open_now when determined, link_ok, link_status, website_final)
  - `data/friluft.geojson`: geojson for the map (includes open_now, link_ok to show status badges)

Run locally:
```bash
OVERPASS_ENDPOINT=https://overpass.kumi.systems/api/interpreter \
ENRICH_MAX=100 \
LINKCHECK_MAX=100 \
python etl/run_etl.py
```

## Push to GitHub

```bash
cd friluft
git init -b main
git add .
git commit -m "Initial: website-only scraper, map with clustering, Node server + Pages workflow"
git remote add origin https://github.com/perwinroth/friluft.git
git push -u origin main
```

## Data and licensing

- Data source: OpenStreetMap, via Overpass API. Data is © OpenStreetMap contributors (ODbL).
- This repository is MIT licensed (code). See `LICENSE`.

## Notes

- The scraper stores a category list per feature, includes best-effort `name` (prefers Swedish), and links to `website`. Features without a website/contact URL are discarded.
- Ways and relations use Overpass `out center` to provide a point geometry.
- You can extend categories and tag filters in `CATEGORY_DEFS` inside the scraper.
