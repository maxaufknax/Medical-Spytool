#!/usr/bin/env python3
"""
Web Interface Test für die Einfache Suche
"""

import requests
import time
import json
from datetime import datetime

def test_web_search():
    """Test der Web-Suchfunktionalität."""
    base_url = "http://127.0.0.1:5000"
    
    print(f"{'='*80}")
    print(f"WEB INTERFACE TEST - EINFACHE SUCHE")
    print(f"Testing URL: {base_url}")
    print(f"Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    # Test 1: Hauptseite laden
    try:
        print("\n1. Teste Hauptseite...")
        response = requests.get(base_url)
        if response.status_code == 200:
            print("✅ Hauptseite erfolgreich geladen")
            if "Einfache Suche" in response.text:
                print("✅ 'Einfache Suche' gefunden auf der Hauptseite")
            else:
                print("❌ 'Einfache Suche' nicht auf der Hauptseite gefunden")
        else:
            print(f"❌ Hauptseite Fehler: {response.status_code}")
    except Exception as e:
        print(f"❌ Fehler beim Laden der Hauptseite: {e}")
    
    # Test 2: Such-Seite laden
    try:
        print("\n2. Teste Such-Seite...")
        response = requests.get(f"{base_url}/search")
        if response.status_code == 200:
            print("✅ Such-Seite erfolgreich geladen")
            if "Einfache Suche" in response.text:
                print("✅ 'Einfache Suche' Tab gefunden")
            else:
                print("❌ 'Einfache Suche' Tab nicht gefunden")
        else:
            print(f"❌ Such-Seite Fehler: {response.status_code}")
    except Exception as e:
        print(f"❌ Fehler beim Laden der Such-Seite: {e}")
    
    # Test 3: Einfache Suche durchführen
    try:
        print("\n3. Teste Einfache Suche mit 'anette melk'...")
        search_data = {
            'database': 'Combined',
            'search_term': 'anette melk',
            'max_results': '20'
        }
        
        response = requests.post(f"{base_url}/search", data=search_data)
        
        if response.status_code == 200:
            print("✅ Suche erfolgreich ausgeführt")
            
            # Check für Ergebnisse
            if "Ergebnisse gefunden" in response.text:
                print("✅ Suchergebnisse gefunden")
                
                # Versuche Anzahl der Ergebnisse zu extrahieren
                if "Transplantation" in response.text or "Pediatric" in response.text:
                    print("✅ Relevante Ergebnisse zu 'anette melk' gefunden")
                else:
                    print("⚠️ Ergebnisse gefunden, aber Relevanz unklar")
                    
            elif "Keine Ergebnisse gefunden" in response.text:
                print("❌ Keine Ergebnisse gefunden - das sollte nicht passieren")
            else:
                print("⚠️ Unklarer Ergebnisstatus")
                
        else:
            print(f"❌ Suche Fehler: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Fehler bei der Suche: {e}")
    
    # Test 4: Schnellsuche von der Hauptseite
    try:
        print("\n4. Teste Schnellsuche von der Hauptseite...")
        search_data = {
            'database': 'Combined',
            'search_term': 'diabetes mellitus'
        }
        
        response = requests.post(f"{base_url}/search", data=search_data)
        
        if response.status_code == 200:
            print("✅ Schnellsuche erfolgreich ausgeführt")
            
            if "Ergebnisse gefunden" in response.text or "diabetes" in response.text.lower():
                print("✅ Ergebnisse für 'diabetes mellitus' gefunden")
            else:
                print("⚠️ Möglicherweise keine Ergebnisse für 'diabetes mellitus'")
        else:
            print(f"❌ Schnellsuche Fehler: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Fehler bei der Schnellsuche: {e}")
    
    # Test 5: Teste leere Suche (sollte Fehler geben)
    try:
        print("\n5. Teste Validierung mit leerem Suchbegriff...")
        search_data = {
            'database': 'Combined',
            'search_term': '',
            'max_results': '100'
        }
        
        response = requests.post(f"{base_url}/search", data=search_data)
        
        # Sollte zur Suchseite zurückkehren oder Fehler anzeigen
        if response.status_code == 200:
            print("✅ Leere Suche korrekt behandelt (keine 500 Fehler)")
        else:
            print(f"⚠️ Unerwarteter Status bei leerer Suche: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Fehler bei der Validierungstest: {e}")
    
    print(f"\n{'='*80}")
    print(f"WEB INTERFACE TEST ABGESCHLOSSEN")
    print(f"Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")

if __name__ == "__main__":
    # Kurz warten, damit der Server gestartet ist
    print("Warte 3 Sekunden auf Server-Start...")
    time.sleep(3)
    
    test_web_search()
