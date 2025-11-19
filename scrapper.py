import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
# L'URL fournie pour le classement du Cygne
URL = "https://competitions.ffbb.com/ligues/guy/comites/0973/clubs/guy0973007/equipes/200000005178873/classement"
OUTPUT_FILE = "data.json"

def fetch_data():
    """
    Récupère le HTML de la page FFBB.
    Utilise un User-Agent pour ne pas être bloqué (simule un navigateur).
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"🔌 Connexion à {URL}...")
        response = requests.get(URL, headers=headers)
        response.raise_for_status() # Lève une erreur si le code n'est pas 200
        response.encoding = 'utf-8' # Force l'encodage pour les accents
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la connexion : {e}")
        return None

def parse_standings(html):
    """
    Analyse le HTML pour extraire le tableau du classement.
    """
    soup = BeautifulSoup(html, 'html.parser')
    standings = []

    # Recherche de tous les tableaux
    tables = soup.find_all('table')
    
    target_table = None
    
    # On cherche le tableau qui contient "Pts" (Points) dans son en-tête
    for table in tables:
        if table.find('th') and "Pts" in table.text:
            target_table = table
            break
            
    if not target_table:
        print("⚠️ Aucun tableau de classement trouvé sur la page.")
        return []

    # On parcourt les lignes du corps du tableau (tbody)
    rows = target_table.find_all('tr')
    
    for row in rows:
        cols = row.find_all('td')
        # Une ligne valide de classement a généralement beaucoup de colonnes
        # Structure typique FFBB: Rang, Equipe, Pts, Joués, Gagnés, Perdus...
        if len(cols) > 2:
            try:
                team_name = cols[1].text.strip()
                
                # Nettoyage simple du nom (parfois il y a des espaces en trop)
                team_name = " ".join(team_name.split())

                team_data = {
                    "rank": cols[0].text.strip(),
                    "name": team_name,
                    "points": cols[2].text.strip(),
                    "played": cols[3].text.strip(),
                    "won": cols[4].text.strip(),
                    "lost": cols[5].text.strip(),
                    # On peut ajouter le goal average si dispo dans les colonnes suivantes
                }
                standings.append(team_data)
            except IndexError:
                continue

    return standings

def save_to_json(data):
    """
    Sauvegarde les données extraites dans un fichier JSON.
    """
    final_structure = {
        "updated_at": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "source": URL,
        "standings": data
    }
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_structure, f, ensure_ascii=False, indent=2)
        print(f"✅ Données sauvegardées dans '{OUTPUT_FILE}'")
    except IOError as e:
        print(f"❌ Erreur lors de l'écriture du fichier : {e}")

def main():
    print("🏀 Démarrage du Scraper Basket Guyane...")
    html = fetch_data()
    
    if html:
        standings_data = parse_standings(html)
        if standings_data:
            print(f"📊 {len(standings_data)} équipes trouvées.")
            save_to_json(standings_data)
        else:
            print("⚠️ Aucune donnée de classement extraite.")
    else:
        print("❌ Abandon.")

if __name__ == "__main__":
    main()