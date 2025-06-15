"""
1. Télécharge la dernière archive JORF_YYYYMMDD.tar.gz
2. Extrait chaque article XML
3. Envoie (titre + extrait) au LLM (séquentiel)
4. Garde ceux qui mentionnent une des notes 8 / 11 / 14 / 15 / 16 / 20
5. Sauve un .txt trié par score : « XX % | Titre | URL »
"""
import io, json, pathlib, re, tarfile
from datetime import datetime as dt
from xml.etree import ElementTree as ET

import httpx
from bs4 import BeautifulSoup
import torch
import sys

from transformer import classify_notes

INDEX_URL = "https://echanges.dila.gouv.fr/OPENDATA/JORF/"
BASE_LGF  = "https://www.legifrance.gouv.fr/jorf/id/"


# -------- nettoyages --------------------------------------------------
_RE_SP = re.compile(r"[ \t\r]+")

def _clean(txt: str) -> str:
    txt = _RE_SP.sub(" ", txt)
    return re.sub(r"\s+\n", "\n", txt).strip()

def parse_article(xml_bytes: bytes):
    root  = ET.fromstring(xml_bytes)
    cid   = root.find(".//TEXTE").attrib.get("cid", "")
    titre = (root.findtext(".//TITRE_TA")
             or root.findtext(".//TITRE_TXT")
             or "(Titre manquant)")
    titre = _clean(titre)

    paras = []
    for cont in root.findall(".//CONTENU"):
        raw = "".join(cont.itertext())
        txt = _clean(raw)
        if txt:
            paras.append(txt)
    corps = "\n\n".join(paras)
    return cid, titre, corps

# -------- téléchargement archive --------------------------------------
def latest_archive_bytes(arg : int):
    soup = BeautifulSoup(httpx.get(INDEX_URL, timeout=30).text, "html.parser")
    link = [a["href"] for a in soup.find_all("a", href=lambda h: h and h.endswith(".tar.gz"))][-arg]
    url  = INDEX_URL + link
    print("⬇️  Téléchargement :", url)
    return httpx.get(url, timeout=120).content

def iter_article_xml(bin_archive: bytes):
    with tarfile.open(fileobj=io.BytesIO(bin_archive), mode="r:gz") as tar:
        for m in tar:
            if "/article/JORF/ARTI/" in m.name and m.name.endswith(".xml"):
                yield tar.extractfile(m).read()


def main(arg : int):
    xml_iter = iter_article_xml(latest_archive_bytes(arg))
    arts = [parse_article(x) for x in xml_iter]
    print("✅", len(arts), "articles XML extraits.")

    # clean old files
    pathlib.Path("articles_proteges.txt").unlink(missing_ok=True)
    pathlib.Path("articles_pertinents.txt").unlink(missing_ok=True)
    titres_pertinents: set[str] = set()     # ← NEW
    out = []

    for i, (cid, titre, texte) in enumerate(arts, 1):
        titre_norm = " ".join(titre.lower().split())
        if titre_norm in titres_pertinents:
            print(f"[{i:>3}/{len(arts)}] ⏭️  doublon déjà marqué pertinent")
            continue
        if "accès protégé" in titre_norm:
            titres_pertinents.add(titre_norm)
            print(f"[{i:>3}/{len(arts)}] ⏭️  accès protégé, pas de classification")
            with open("articles_proteges.txt", "a", encoding="utf-8") as f:
                f.write(f"Accès protégé | {titre} | {BASE_LGF + cid}\n")
            continue
        # ──────────────────────────────────────────────────────────────

        notes, score = classify_notes(titre, texte)

        if notes:
            titres_pertinents.add(titre_norm)                     
            out.append((score, titre, BASE_LGF + cid))

            with open("articles_pertinents.txt", "a", encoding="utf-8") as f:
                f.write(f"{score:>3}% | {titre} | {BASE_LGF+cid}\n")

            print(f"[{i:>3}/{len(arts)}] ✅ {score:>3}% {titre[:60]}…")
        else:
            print(f"[{i:>3}/{len(arts)}] —  {titre_norm} — pas pertinent")

    print(f"\n✅ {len(out)} articles pertinents trouvés.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg =int(sys.argv[1]) if len(sys.argv) > 1 else 1
	
        print(arg)
        main(arg)
    else:
        main()