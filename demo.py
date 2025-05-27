#!/usr/bin/env python3
"""
Demo-Script für MedicalSpyTool
Führt eine Beispielsuche durch und zeigt die wichtigsten Features
"""

import time
import sys
import os

def demo_intro():
    """Zeige Intro"""
    print("🎯 MedicalSpyTool - Live-Demo")
    print("=" * 50)
    print()
    print("Diese Demo führt Sie durch die wichtigsten Features der Anwendung.")
    print()
    input("Drücken Sie Enter um zu starten...")
    print()

def demo_config():
    """Demo der Konfiguration"""
    print("📋 1. Konfiguration laden")
    print("-" * 30)
    
    try:
        from utils.config_manager import load_settings
        config = load_settings()
        
        print(f"✅ Standard-Datenbank: {config.get('default_database')}")
        print(f"✅ Output-Pfad: {config.get('output_path')}")
        print(f"✅ Eindeutige Dateinamen: {config.get('unique_filenames')}")
        print()
        
        time.sleep(2)
        return True
    except Exception as e:
        print(f"❌ Fehler beim Laden der Konfiguration: {e}")
        return False

def demo_database_connectors():
    """Demo der Datenbankverbindungen"""
    print("🔌 2. Datenbankverbindungen")
    print("-" * 30)
    
    try:
        from database_connectors import PubMedConnector, DNBConnector
        
        # PubMed
        pubmed = PubMedConnector()
        print(f"✅ PubMed Connector initialisiert")
        print(f"   - Basis-URL: {pubmed.base_url}")
        
        # DNB  
        dnb = DNBConnector()
        print(f"✅ DNB Connector initialisiert") 
        print(f"   - Basis-URL: {dnb.base_url}")
        
        print()
        time.sleep(2)
        return True
    except Exception as e:
        print(f"❌ Fehler bei Datenbankverbindungen: {e}")
        return False

def demo_search_simulation():
    """Simuliere eine Suche"""
    print("🔍 3. Suchsimulation")
    print("-" * 30)
    
    search_term = "Diabetes"
    print(f"Simuliere Suche für: '{search_term}'")
    print()
    
    # Simuliere Suchschritte
    steps = [
        ("Initialisiere PubMed-Suche", 1),
        ("Sende Anfrage an PubMed API", 2),
        ("Verarbeite PubMed-Ergebnisse", 1),
        ("Initialisiere DNB-Suche", 1),
        ("Sende Anfrage an DNB API", 2),
        ("Verarbeite DNB-Ergebnisse", 1),
        ("Zusammenführung der Ergebnisse", 1),
        ("Deduplizierung", 1),
        ("Suche abgeschlossen", 0)
    ]
    
    for step, delay in steps:
        print(f"  🔄 {step}...")
        time.sleep(delay)
        print(f"  ✅ {step}")
    
    print()
    print("📊 Simulierte Ergebnisse:")
    print("   - PubMed: 1,234 Publikationen gefunden")
    print("   - DNB: 567 Publikationen gefunden") 
    print("   - Nach Deduplizierung: 1,678 einzigartige Publikationen")
    print()
    
    time.sleep(3)
    return True

def demo_export_simulation():
    """Simuliere einen Export"""
    print("📄 4. Export-Simulation")
    print("-" * 30)
    
    print("Simuliere Excel-Export...")
    
    # Simuliere Export-Schritte
    export_steps = [
        ("Erstelle Excel-Arbeitsmappe", 1),
        ("Füge Publikationsdaten hinzu", 2),
        ("Formatiere Spalten", 1),
        ("Füge Statistiken hinzu", 1),
        ("Speichere Datei", 1)
    ]
    
    for step, delay in export_steps:
        print(f"  🔄 {step}...")
        time.sleep(delay)
        print(f"  ✅ {step}")
    
    print()
    print("📁 Exportdatei würde gespeichert als:")
    print("   ./output/diabetes_search_2025-05-27_125959.xlsx")
    print()
    
    time.sleep(2)
    return True

def demo_flask_routes():
    """Demo der Flask-Routes"""
    print("🌐 5. Webanwendung")
    print("-" * 30)
    
    try:
        from main import app
        
        print("Flask-Anwendung erfolgreich geladen!")
        print()
        print("Verfügbare Routes:")
        
        # Zeige wichtige Routes
        routes = [
            ("GET /", "Startseite mit Schnellsuche"),
            ("GET /search", "Erweiterte Suchoptionen"),
            ("POST /search", "Suchausführung"),
            ("GET /persons", "Personenverwaltung"),
            ("GET /results", "Suchergebnisse anzeigen"),
            ("GET /analysis", "Statistische Auswertungen"),
            ("GET /export", "Export-Optionen"),
            ("GET /settings", "Anwendungseinstellungen")
        ]
        
        for route, description in routes:
            print(f"  🔗 {route:<15} - {description}")
        
        print()
        print("🌟 Die Anwendung läuft auf: http://127.0.0.1:5000")
        print()
        
        time.sleep(3)
        return True
    except Exception as e:
        print(f"❌ Fehler beim Laden der Flask-App: {e}")
        return False

def demo_summary():
    """Zeige Zusammenfassung"""
    print("🎉 Demo abgeschlossen!")
    print("=" * 50)
    print()
    print("Die MedicalSpyTool Anwendung ist vollständig funktionsfähig und bietet:")
    print()
    print("✅ Multi-Datenbank Suche (PubMed, DNB, Scopus, WoS, GEPRIS)")
    print("✅ Benutzerfreundliche Weboberfläche")
    print("✅ Personenverwaltung für gezielte Suchen")
    print("✅ Flexible Export-Optionen (Excel, CSV)")
    print("✅ Statistische Auswertungen und Visualisierungen")
    print("✅ Konfigurierbare Einstellungen")
    print("✅ Vollständiges Logging und Fehlerbehandlung")
    print()
    print("🚀 Starten Sie die Anwendung mit: python main.py")
    print("🌐 Öffnen Sie dann: http://127.0.0.1:5000")
    print()
    print("📖 Weitere Informationen finden Sie in:")
    print("   - README.md (Technische Übersicht)")
    print("   - BENUTZERANLEITUNG.md (Detaillierte Anleitung)")
    print()

def main():
    """Führe die komplette Demo durch"""
    demo_intro()
    
    demos = [
        demo_config,
        demo_database_connectors,
        demo_search_simulation,
        demo_export_simulation,
        demo_flask_routes
    ]
    
    for demo in demos:
        if not demo():
            print("Demo wurde aufgrund eines Fehlers abgebrochen.")
            return 1
    
    demo_summary()
    return 0

if __name__ == "__main__":
    sys.exit(main())
