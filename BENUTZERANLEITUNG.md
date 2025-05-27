# MedicalSpyTool - Benutzeranleitung

## 🚀 Schnellstart-Anleitung

### 1. Anwendung starten
```bash
# Option 1: Automatisches Startskript (empfohlen)
start_application.bat

# Option 2: Manuell
python main.py
```

Die Anwendung startet auf: **http://127.0.0.1:5000**

### 2. Erste Schritte

#### Schnellsuche
1. Öffnen Sie die Startseite
2. Geben Sie einen Suchbegriff ein (z.B. "Diabetes")
3. Klicken Sie auf "Suchen"
4. Die Anwendung durchsucht automatisch alle verfügbaren Datenbanken

#### Erweiterte Suche
1. Gehen Sie zu "Suche" in der Navigation
2. Wählen Sie eine spezifische Datenbank (PubMed, DNB, etc.)
3. Konfigurieren Sie Filter und Parameter
4. Starten Sie die Suche

### 3. Personenverwaltung

#### Personen hinzufügen
1. Navigieren Sie zu "Personen"
2. Klicken Sie "Person hinzufügen"
3. Füllen Sie die Felder aus:
   - Name
   - Suchbegriffe
   - Zusätzliche Begriffe (optional)

#### Beispiel-Person erstellen
```json
{
  "name": "Dr. Max Mustermann",
  "search_terms": ["Max Mustermann", "M Mustermann"],
  "additional_terms": ["Diabetes", "Insulin", "Metabolismus"],
  "affiliation": "Universitätsklinikum"
}
```

### 4. Suchfunktionen

#### Verfügbare Datenbanken
- **PubMed**: Medizinische Publikationen
- **DNB**: Deutsche Nationalbibliothek  
- **Scopus**: Wissenschaftliche Abstracts
- **Web of Science**: Zitationsdatenbank
- **GEPRIS**: Deutsche Forschungsprojekte

#### Suchparameter
- **Suchbegriff**: Hauptkeyword
- **Datumsbereich**: Von/Bis Filter
- **Publikationstyp**: Artikel, Review, etc.
- **Sprache**: Deutsch, Englisch, etc.
- **Max. Ergebnisse**: 1-10.000

### 5. Ergebnisse verwalten

#### Ergebnisse anzeigen
1. Nach einer Suche erscheinen die Ergebnisse automatisch
2. Nutzen Sie Filter und Sortierung
3. Exportieren Sie die Daten

#### Export-Optionen
- **Excel**: Detaillierte Tabellen mit allen Metadaten
- **CSV**: Einfache Datenexport für weitere Verarbeitung
- **Eindeutige Dateinamen**: Verhindert Überschreibung

### 6. Analyse-Features

#### Statistiken
- Anzahl Publikationen pro Jahr
- Verteilung nach Datenbanken
- Häufigste Autoren
- Zitationsanalyse

#### Visualisierungen
- Zeitverlauf der Publikationen
- Datenbankverteilung
- Author-Netzwerke

### 7. Konfiguration

#### API-Keys konfigurieren (optional)
1. Gehen Sie zu "Einstellungen"
2. Tragen Sie API-Keys ein:
   - PubMed API Key (für höhere Rate Limits)
   - Scopus API Key
   - Web of Science API Key

#### Ausgabepfade anpassen
- Output-Verzeichnis: Wo Exports gespeichert werden
- Personen-Listen: Wo Personendaten gespeichert werden
- Logs: Wo Anwendungslogs geschrieben werden

### 8. Tipps für effektive Nutzung

#### Suchstrategien
- **Verwenden Sie synonyme Begriffe**: "Diabetes" + "Diabetes mellitus"
- **Nutzen Sie Wildcards**: "Diabet*" findet auch "Diabetic", "Diabetology"
- **Kombinieren Sie Autoren**: "Max Mustermann" AND "Diabetes"

#### Performance-Optimierung
- Beginnen Sie mit kleineren Ergebnismengen (100-500)
- Nutzen Sie spezifische Datumsbereiche
- Verwenden Sie gezielte Suchbegriffe

#### Datenqualität
- Überprüfen Sie Duplikate
- Validieren Sie wichtige Ergebnisse manuell
- Nutzen Sie mehrere Datenbanken für vollständige Abdeckung

### 9. Fehlerbehebung

#### Häufige Probleme
- **Port bereits belegt**: Ändern Sie den Port in main.py
- **API-Limits erreicht**: Warten Sie oder verwenden Sie API-Keys
- **Langsame Suchen**: Reduzieren Sie Max. Ergebnisse

#### Log-Dateien
Überprüfen Sie `logs/medicalspytool.log` für detaillierte Fehlerinformationen.

### 10. Erweiterte Features

#### Suchprofile
1. Erstellen Sie wiederverwendbare Suchkonfigurationen
2. Speichern Sie komplexe Suchparameter
3. Teilen Sie Profile mit Kollegen

#### Batch-Verarbeitung
1. Laden Sie Personenlisten aus CSV/Excel
2. Führen Sie automatisierte Suchen durch
3. Verarbeiten Sie große Datenmengen effizient

---

## 🔧 Technische Details

### Systemanforderungen
- Python 3.8+
- 4GB RAM empfohlen
- Internetverbindung
- 1GB freier Speicherplatz

### Supported Dateiformate
- **Import**: CSV, Excel, JSON
- **Export**: Excel, CSV, JSON

### Sicherheit
- Lokale Ausführung (keine Daten in der Cloud)
- API-Keys werden lokal gespeichert
- Alle Daten bleiben auf Ihrem System

---

Viel Erfolg mit der MedicalSpyTool Anwendung! 🎯
