import json
import re
import time
import httpx


GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash-lite:generateContent"
)
API_KEY = "AIzaSyAHLPg-Mo1Cwxo782LKVLrgIJYyyM-Yk10"     # DOIT contenir ta clé

def gemini_call(prompt: str, max_tries: int = 8) -> str:
    """
    Appelle Gemini Flash Lite et renvoie le texte brut de la réponse.
    • Gère les erreurs 429 (quota) en attendant le temps demandé.
    """
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 256}
    }
    url = f"{GEMINI_ENDPOINT}?key={API_KEY}"

    for attempt in range(1, max_tries + 1):
        try:
            r = httpx.post(url, headers=headers, json=body, timeout=60)
            if r.status_code == 429:
                # -------- quota exceeded → on attend puis on ré-essaye -------
                retry_after = int(r.headers.get("Retry-After", "30"))/2
                backoff     = 2 ** (attempt - 1)          # 1→1 s, 2→2 s, 3→4 s…
                wait_sec    = retry_after + backoff
                print(f"⚠️  429 – attente {wait_sec}s…")
                time.sleep(wait_sec)
                continue

            r.raise_for_status()             # autres erreurs HTTP éventuelles
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]

        except httpx.HTTPStatusError as e:
            backoff = 2 ** (attempt - 1)
            print(f"⚠️ HTTP {e.response.status_code} – retry dans {backoff}s")
            time.sleep(backoff)
        except Exception as e:
            backoff = 2 ** (attempt - 1)
            print(f"⚠️ Exception {e.__class__.__name__} – retry dans {backoff}s")
            time.sleep(backoff)

    raise RuntimeError("Gemini API – trop d’échecs consécutifs")


SYSTEM_PROMPT = """
SYSTEM:
Tu es un expert de la comptabilité de l’État.

Analyse le texte utilisateur et réponds UNIQUEMENT par un objet JSON :

{
  "notes":  [<nombres>],          # entiers dans {8,11,14,15,16,20}
  "score":  <0-100>               # % d’importance (0 = sans intérêt, 100 = crucial)
}

• La liste DOIT être vide si aucune note n’est concernée par l'article.  
• “score” est ta mesure globale de pertinence et de degré d'importance pour les notes retenues ; il doit être élevé si l'article a un impact en comptabilité générale de l'État.

──────────────────────────  Rappels détaillés  ──────────────────────────
Note 8 – Immobilisations financières  
  • Participations, créances rattachées à des participations, prêts et avances, fonds sans personnalité juridique, contrats de désendettement et de développement  
    immobilisations financières, participations publiques, actifs financiers de l’État,  
    créances rattachées,  
    dotations en capital, France 2030, investissements d’avenir, participations de l’État,  
    État actionnaire, comptes consolidés,  
    valeur d’équivalence,  
    participation financière publique, établissement public.

Note 11 – Dettes financières  
  • dettes de l’État, emprunts publics, titres négociables, obligations  
    assimilables du Trésor, OAT vertes, bons du Trésor à taux fixe,  
    obligations souveraines, primes et décotes, contrats de partenariat public-privé, contrats de location-financement, emprunts repris de tiers pris en charge par l’État  
    dette publique, Agence France Trésor, instruments de dette.

Note 14 – Autres passifs  
  • passifs divers, bons du Trésor émis au profit du Fonds monétaire international, quote-part de la France au FMI, monnaie métallique, France 2030, programmes d’investissements d’avenir, dotations consommables France 2030 et investissements d’avenir, dotations budgétaires, subventions France 2030, dotations BPI, dotations Caisse des dépôts, dotations ADEME, dotations ANR.

Note 15 – Trésorerie  
  • trésorerie de l’État, fonds en caisse, compte du Trésor à la Banque de France, valeurs mobilières de placement, placements à court terme, placements sur le marché interbancaire, correspondants du Trésor.

Note 16 – Comptes de régularisation  
  • écart au bilan d’ouverture, charges à répartir, dotations non consommables, comptes de dépôts de fonds au Trésor, IDEX PIA,  
    régularisations investissements d’avenir, écart de conversion FMI.

Note 20 – Charges et produits financiers  
  • charges financières, intérêts de la dette, produits financiers,  
    gains et pertes de change, amortissements financiers,  
    reprises sur provisions financières, rémunération des participations.
"""


def classify_notes(titre:str, texte:str):
    prompt = (
        SYSTEM_PROMPT
        + "\n───────────────────────────────────────────────\nUSER :\n"
        + titre + "\n\n" + texte
    )
    rep_raw = gemini_call(prompt)
    # print(rep_raw)  # pour debug
    try:
        data = json.loads(rep_raw.strip())
    except json.JSONDecodeError:
        try:
            match = re.search(r"```json\s*(\{.*?\})\s*```", rep_raw, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
            else:
                raise ValueError("Aucun bloc JSON trouvé.")
        except Exception as e:
            print("⚠️ Impossible d’extraire le JSON :", str(e))
            return [], 0

    return data.get("notes", []), data.get("score", 0)