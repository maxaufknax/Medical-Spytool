# Medical Spytool Export System

## Übersicht
Das Export-System der Medical Spytool Anwendung ermöglicht es Benutzern, Suchergebnisse und Analysen in verschiedenen Formaten zu exportieren. Diese Dokumentation beschreibt die Architektur, Konfiguration und Verwendung des Export-Systems.

## Unterstützte Export-Formate

Die Anwendung unterstützt die folgenden Export-Formate:

1. **CSV** (Comma-Separated Values)
   - Standard-Tabellenformat
   - Einfache Integration mit Excel, LibreOffice, etc.
   - UTF-8-Kodierung mit BOM für beste Kompatibilität

2. **Excel** (XLSX)
   - Natives Microsoft Excel-Format
   - Unterstützt Formatierung, mehrere Tabellenblätter und Formeln
   - Verwendet openpyxl-Bibliothek für die Generierung

3. **JSON** (JavaScript Object Notation)
   - Hierarchisches Datenformat
   - Ideal für Programmierschnittstellen und Datenanalysen
   - Vollständige Struktur der Daten bleibt erhalten

4. **PDF** (Portable Document Format)
   - Archivierungsfreundliches Format
   - Reproduzierbare Darstellung auf allen Geräten
   - Unterstützt Tabellen, Diagramme und Textformatierung

## Architektur

Das Export-System basiert auf einer modularen Architektur:

1. **Export-Controller** (`backend/blueprints/export.py`)
   - Verarbeitet Export-Anfragen
   - Validiert Benutzerberechtigungen
   - Ruft den entsprechenden Export-Service auf

2. **Export-Services** (`backend/utils/export_helpers.py`)
   - Format-spezifische Implementierungen
   - Datenkonvertierung und -verarbeitung
   - Dateinamengenerierung und Metadaten

3. **Datenquellen-Adapter**
   - Verbindung zu verschiedenen Datenquellen
   - Einheitliche Schnittstelle für Export-Services
   - Unterstützt Datenbanken, Dateien und API-Ergebnisse

## Konfiguration

Die Export-Konfiguration kann über verschiedene Parameter angepasst werden:

### Allgemeine Einstellungen

- **default_export_format**: Standardformat für Exporte (Standard: "csv")
- **export_directory**: Verzeichnis für temporäre Exportdateien
- **include_metadata**: Ob Metadaten in Exporten enthalten sein sollen (Standard: true)
- **max_export_size**: Maximale Anzahl von Datensätzen pro Export (0 = unbegrenzt)

### Format-spezifische Einstellungen

#### CSV-Einstellungen
```json
{
  "csv": {
    "delimiter": ",",
    "quotechar": "\"",
    "encoding": "utf-8-sig",
    "date_format": "%Y-%m-%d"
  }
}
```

#### Excel-Einstellungen
```json
{
  "excel": {
    "sheet_name": "Suchergebnisse",
    "include_charts": true,
    "header_style": {
      "bold": true,
      "bg_color": "#4F81BD",
      "font_color": "#FFFFFF"
    }
  }
}
```

#### PDF-Einstellungen
```json
{
  "pdf": {
    "page_size": "A4",
    "orientation": "landscape",
    "include_header": true,
    "include_footer": true
  }
}
```

## Datenfelder-Konfiguration

Benutzer können auswählen, welche Felder in den Export einbezogen werden sollen:

### Standard-Exportfelder
```json
{
  "default_export_fields": [
    "title",
    "authors",
    "journal",
    "year",
    "abstract",
    "doi",
    "pubmed_id"
  ]
}
```

### Erweiterte Felder
```json
{
  "extended_export_fields": [
    "keywords",
    "mesh_terms",
    "publication_type",
    "cited_by_count",
    "impact_factor",
    "full_citation"
  ]
}
```

## Verwendung des Export-Systems

### Über die Benutzeroberfläche

1. Führen Sie eine Suche durch
2. Wählen Sie die gewünschten Ergebnisse aus
3. Klicken Sie auf "Exportieren"
4. Wählen Sie das gewünschte Format und die Felder aus
5. Klicken Sie auf "Download starten"

### Über die API

```python
import requests

# Authentifizieren
response = requests.post('http://localhost:5000/api/login', json={
    'username': 'user',
    'password': 'password'
})
token = response.json()['token']

# Suchanfrage senden
search_response = requests.post('http://localhost:5000/api/search', 
    json={'query': 'cancer treatment', 'source': 'pubmed'},
    headers={'Authorization': f'Bearer {token}'}
)
search_id = search_response.json()['search_id']

# Ergebnisse exportieren
export_response = requests.post('http://localhost:5000/api/export',
    json={
        'search_id': search_id,
        'format': 'excel',
        'fields': ['title', 'authors', 'abstract', 'journal']
    },
    headers={'Authorization': f'Bearer {token}'},
    stream=True
)

# Datei speichern
with open('results.xlsx', 'wb') as f:
    for chunk in export_response.iter_content(chunk_size=8192):
        f.write(chunk)
```

## Sicherheitsaspekte

Das Export-System implementiert mehrere Sicherheitsmaßnahmen:

1. **Zugriffskontrollen**
   - Nur authentifizierte Benutzer können Exporte erstellen
   - Rollenbasierte Berechtigungen für bestimmte Export-Formate
   - Export-Limits basierend auf Benutzerrolle

2. **Datenschutz**
   - Sensible Felder können ausgeschlossen werden
   - Verschlüsselung von Export-Dateien möglich
   - Automatisches Löschen temporärer Dateien

3. **Ressourcenschutz**
   - Rate-Limiting für Export-Anfragen
   - Begrenzung der Dateigröße und Datensatzanzahl
   - Asynchrone Verarbeitung für große Exporte

## Anpassung und Erweiterung

Das Export-System kann auf verschiedene Weise angepasst und erweitert werden:

### Hinzufügen eines neuen Export-Formats

1. Erstellen Sie eine neue Export-Handler-Klasse in `export_handlers.py`
2. Registrieren Sie das neue Format in der Export-Konfiguration
3. Fügen Sie UI-Elemente für das neue Format hinzu

### Anpassen der Datenverarbeitung

Die Datenverarbeitung kann durch Anpassen der Export-Services modifiziert werden:

```python
def custom_data_processor(data, options):
    """Benutzerdefinierte Datenverarbeitung vor dem Export"""
    # Daten transformieren
    processed_data = transform_data(data)
    
    # Zusätzliche Felder hinzufügen
    for item in processed_data:
        item['custom_field'] = calculate_custom_value(item)
        
    return processed_data
```

## Fehlerbehandlung und Logging

Das Export-System protokolliert detaillierte Informationen über Export-Aktivitäten:

- Erfolgreiche Exporte werden mit Benutzer, Format und Zeitstempel protokolliert
- Fehler werden mit Diagnoseinformationen protokolliert
- Performance-Metriken werden für Optimierungszwecke erfasst

## Best Practices

1. Große Datenmengen sollten als Hintergrundaufgabe exportiert werden
2. Benutzer sollten über verfügbare Export-Optionen informiert werden
3. Exportierte Daten sollten Metadaten zur Quelle und zum Zeitpunkt enthalten
4. Regelmäßige Überprüfung der Export-Performance bei steigenden Datenmengen

---

Zuletzt aktualisiert: Mai 2025
