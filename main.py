import io, json, pathlib, re, tarfile
from datetime import datetime as dt
from xml.etree import ElementTree as ET
from email_sending import send_email

import httpx
from bs4 import BeautifulSoup
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
    link = [a["href"] for a in soup.find_all("a", href=lambda h: h and h.endswith(".tar.gz"))]
    temp = []
    for x in link:
        #split on - , (if not - then we just skip)
        if x.startswith("JORF_") and x.endswith(".tar.gz"):
            parts = x.split("-")
            temp.append(parts)

    keep = {}
    for date_part, time_part in temp:
        # on retire le ".tar.gz" puis on convertit en entier
        num = int(time_part.split(".")[0])
        if date_part not in keep or num < keep[date_part][0]:
            keep[date_part] = (num, time_part)

    # on reconstruit la liste d’origine (tri facultatif par date décroissante)
    result = [[date, time] for date, (num, time) in keep.items()]
    result.sort(key=lambda lst: lst[0], reverse=False)   # plus récent d’abord
    # concatenate the elements of each tuple
    result_concatenated = ["-".join(x) for x in result]
    return link

    link = result_concatenated[-arg]

    titre_jofr = link.split("/")[-1].split(".")[0]  
    url  = INDEX_URL + link
    print("⬇️  Téléchargement :", url)
    return httpx.get(url, timeout=120).content,titre_jofr

def iter_article_xml(bin_archive: bytes):
    with tarfile.open(fileobj=io.BytesIO(bin_archive), mode="r:gz") as tar:
        for m in tar:
            if "/article/JORF/ARTI/" in m.name and m.name.endswith(".xml"):
                yield tar.extractfile(m).read()


def main(archive,titre):
    ok, titre_jofr = archive,titre
    xml_iter = iter_article_xml(ok)
    arts = [parse_article(x) for x in xml_iter]
    body_email_pertinents = ""
    body_email_proteges = ""

    body_email_pertinents = f"<h2 style='color:#000091;'>Articles pertinents ({titre_jofr})</h2><ul>"
    body_email_proteges = f"<h2 style='color:orange;'>Articles protégés</h2><ul>"
    folder = pathlib.Path("data")
    folder.mkdir(exist_ok=True)
    folder_jofr = folder / titre_jofr
    folder_jofr.mkdir(exist_ok=True)

    print(f"✅ {len(arts)} articles extraits de l'archive.")
    if len(arts)>1000:
        return
    dict = {}
    for (cid, titre, texte) in arts:
       old = dict.get(cid, None)
       if old is None:
           dict[cid] = (titre, texte)
       else:
           texte_old = old[1]
           text_new = texte_old + "\n\n" + texte
           dict[cid] = (old[0], text_new)
    arts = [(cid, titre, texte) for cid, (titre, texte) in dict.items()]
    print(f"✅ {len(arts)} articles extraits de l'archive.")

    
    link_proteges = pathlib.Path.joinpath(folder_jofr, "articles_proteges.txt")
    link_pertinents = pathlib.Path.joinpath(folder_jofr, "articles_pertinents.txt")
    liste_articles_ininteressants = ["avis de vacance","délégation de signature"]
    # remove old files if they exist
    if link_proteges.exists():
        link_proteges.unlink()
    if link_pertinents.exists():
        link_pertinents.unlink()
    titres_pertinents: set[str] = set()     # ← NEW
    out = []

    for i, (cid, titre, texte) in enumerate(arts):
        titre_norm = " ".join(titre.lower().split())
        if any(x in titre_norm for x in liste_articles_ininteressants):
            print(f"[{i:>3}/{len(arts)}] —  {titre_norm} — pas pertinent")
            continue
        if "accès protégé" in titre_norm:
            titres_pertinents.add(titre_norm)
            print(f"[{i:>3}/{len(arts)}] ⏭️  accès protégé, pas de classification")
            with open(link_proteges, "a", encoding="utf-8") as f:
                f.write(f"Accès protégé | {titre} | {BASE_LGF + cid}\n")
            body_email_proteges += f"<li style='margin-bottom:10px;'><strong>{titre}</strong> — <a href='{BASE_LGF+cid}'>Voir l'article</a></li>"
            continue
        # ──────────────────────────────────────────────────────────────

        notes,score,indice,résumé,montant = classify_notes(titre, texte)

        if notes:
            out.append((notes,score,titre,indice,résumé,montant, BASE_LGF + cid))
            with open(link_pertinents, "a", encoding="utf-8") as f:
                f.write(f"{score:>3}% | {titre} | {indice} | {résumé} | {notes} | {montant} | {BASE_LGF+cid}\n")
            print(f"[{i:>3}/{len(arts)}] ✅ {score:>3}% {titre[:60]}…")
        else:
            print(f"[{i:>3}/{len(arts)}] —  {titre_norm} — pas pertinent")
    print(f"\n✅ {len(out)} articles pertinents trouvés.")
    out.sort(reverse=True, key=lambda x: x[1])  # trie par score décroissant
    #split on - in titre_jofr
    titre_jofr = titre_jofr.split("-")[0]
    body_email_pertinents = f"<h2 style='color:#000091;'>Articles pertinents ({titre_jofr})</h2><ul>"
    for notes,score,titre,indice,résumé,montant,lien in out:
        body_email_pertinents += (
            f"<li style='margin-bottom:10px;'><strong>{titre} ({score:>3}%)</strong><br>"
            f"<em>Résumé:</em> {résumé}<br><br>"
            f"<em>Indice:</em> {indice}<br>"
            f"<em>Notes:</em> {notes}<br>"
            f"<em>Montant:</em> {montant}<br>"
            f"<a href='{lien}'>Voir l'article </a></li>"
        )
    body_email_pertinents += "</ul>"
    with open(pathlib.Path.joinpath(folder_jofr, "summary.html"), "w", encoding="utf-8") as f:
        f.write(body_email_pertinents + body_email_proteges)
    send_email("Compte rendu " + titre_jofr,
               body_email_pertinents)


if __name__ == "__main__":
    with open("./logs/dl_errors.txt", "a") as f:
        f.write(f"\n\n--- Nouvelle exécution : {dt.now().isoformat()} ---\n")
    with open("./logs/analyze_errors.txt", "a") as f:
        f.write(f"\n\n--- Nouvelle exécution : {dt.now().isoformat()} ---\n")
    with open("last_done.txt", "r") as f:
        last_done = f.readline().strip()
        titre = last_done.split("-")[0]
        links = latest_archive_bytes(1)
        real_links= []
        for i,link in enumerate(links):
            a,b = link.split("-")
            if b[0] != "2":
                if "JORF" in a:
                    real_links.append(link)
        for i,link in enumerate(real_links):
            a,b = link.split("-")
            if a == titre:
                real_links = real_links[i+1:]
                break
    for i,link in enumerate(real_links):
        url  = INDEX_URL + link
        print("⬇️  Téléchargement :", url)
        titre_jofr = link.split(".")[0]
        archive = None
        for _ in range(3):
            try:
                archive_temp = httpx.get(url, timeout=120)
                archive = archive_temp
                break
            except Exception as e:
                print(f"Erreur lors du téléchargement de l'archive {url} : {e}")
        if archive is None :
            print(f"Échec du téléchargement de l'archive {url} après 3 tentatives.")
            with open("./logs/dl_errors.txt", "a") as f:
                f.write(f"Échec du téléchargement de l'archive {url} après 3 tentatives.\n")
            continue
        try:
            main(archive.content,titre_jofr)
            with open("last_done.txt", "w") as f:
                f.write(link + "\n")
            
        except Exception as e:
            print(f"Erreur lors du traitement de l'archive {url} : {e}")
            with open("./logs/analyze_errors.txt", "a") as f:
                f.write(f"Erreur lors du traitement de l'archive {url} : {e}\n")
