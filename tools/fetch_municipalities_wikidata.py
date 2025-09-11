import csv
import requests

SPARQL = """
SELECT ?item ?itemLabel ?officialWebsite WHERE {
  ?item wdt:P31 wd:Q127448 . # Swedish municipality
  OPTIONAL { ?item wdt:P856 ?officialWebsite }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "sv,en". }
}
ORDER BY ?itemLabel
"""

def main():
    url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json", "User-Agent": "FriluftBot/0.1 (+https://github.com/perwinroth/friluft)"}
    r = requests.get(url, params={"query": SPARQL}, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    rows = data.get("results", {}).get("bindings", [])
    out = [(row.get("itemLabel", {}).get("value", ""), row.get("officialWebsite", {}).get("value", "")) for row in rows]
    # Write to data/municipalities.csv
    with open("data/municipalities.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "website"])
        for name, site in out:
            w.writerow([name, site])
    print(f"Wrote data/municipalities.csv with {len(out)} rows")

if __name__ == "__main__":
    main()

