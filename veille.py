#!/usr/bin/env python3
"""Veille ParkStay : alerte si une place se libère à Cape Le Grand (Lucky Bay, Le Grand Beach).

Tourne sur GitHub Actions toutes les heures. Si une place est libre, ouvre une
« issue » sur le dépôt : GitHub envoie alors un e-mail et une notification.
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

CAMPINGS = {43: "Lucky Bay", 46: "Le Grand Beach"}
ARRIVEE = dt.date(2026, 12, 30)
DEPART = dt.date(2027, 1, 2)
HEURES_PARIS = range(7, 23)  # de 7 h à 22 h, heure française
ENTETES = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
                   "(KHTML, like Gecko) Version/18.0 Safari/605.1.15"),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-AU,en;q=0.9,fr;q=0.8",
    "Referer": "https://parkstay.dbca.wa.gov.au/",
}


def disponibilites(cg):
    url = (f"https://parkstay.dbca.wa.gov.au/api/availability/{cg}.json"
           f"?arrival={ARRIVEE:%Y/%m/%d}&departure={DEPART:%Y/%m/%d}"
           f"&num_adult=1&num_child=0&num_concession=0&num_infant=0")
    req = urllib.request.Request(url, headers=ENTETES)
    try:
        data = json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        print(f"ParkStay a répondu {e.code} : {e.read()[:500]!r}")
        raise
    nuits = [ARRIVEE + dt.timedelta(days=i) for i in range((DEPART - ARRIVEE).days)]
    libres = set()
    for site in data["sites"]:
        if not site.get("gearType", {}).get("campervan", True):
            continue
        for nuit, dispo in zip(nuits, site["availability"]):
            if dispo[0]:  # True = réservable
                libres.add(nuit)
    return sorted(libres)


def main():
    heure = dt.datetime.now(ZoneInfo("Europe/Paris")).hour
    if os.environ.get("GITHUB_EVENT_NAME") == "schedule" and heure not in HEURES_PARIS:
        print(f"{heure} h à Paris : hors plage, rien à faire.")
        return
    trouve = []
    for cg, nom in CAMPINGS.items():
        libres = disponibilites(cg)
        print(f"{nom} : {', '.join(f'{n:%d/%m}' for n in libres) or 'rien de libre'}")
        if libres:
            trouve.append(f"- **{nom}** : nuit(s) du {', '.join(f'{n:%d/%m}' for n in libres)}")
    if trouve:
        with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as f:
            f.write("alerte<<FIN\n" + "\n".join(trouve) + "\nFIN\n")


if __name__ == "__main__":
    sys.exit(main())
