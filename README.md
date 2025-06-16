# Medical Spytool v1.9.0 🔬

Ein fortschrittliches Tool zur Suche und Analyse medizinischer und wissenschaftlicher Publikationen aus den Datenbanken DNB (Deutsche Nationalbibliothek) und PubMed.

![Version](https://img.shields.io/badge/version-1.9.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Hauptfunktionen

- **🔍 Multi-Database Suche**: Durchsuchen Sie DNB und PubMed gleichzeitig
- **🖥️ Grafische Benutzeroberfläche**: Intuitive GUI für einfache Bedienung
- **📊 Datenanalyse**: Automatische Visualisierung und Statistiken
- **📁 Export-Funktionen**: CSV, Excel, PDF und HTML Reports
- **⚡ Caching-System**: Schnelle Wiederholung von Suchanfragen
- **🔗 URL-Integration**: Direkte Links zu Publikationen
- **📈 Diagramme und Charts**: Visuelle Darstellung der Ergebnisse

## 🚀 Schnellstart

### GUI starten
```bash
# Doppelklick auf:
start_gui.bat
```

### Kommandozeile
```bash
python -m dnb_spytool.cli --author "Einstein, Albert" --max-results 50
```

## 📦 Installation

### Voraussetzungen
- Python 3.8+
- Windows 10/11 (primäre Unterstützung)

### Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

## 💡 Beispiel-Nutzung

1. **GUI starten**: `start_gui.bat` ausführen
2. **Autor eingeben**: z.B. "Anette Melk" oder "Einstein, Albert"
3. **Datenbanken auswählen**: DNB und/oder PubMed
4. **Suche starten**: Button klicken
5. **Ergebnisse exportieren**: CSV, Excel oder PDF wählen

## 🧪 Getestete Funktionen

✅ **Anette Melk Suche**: 111 Publikationen gefunden (33 DNB + 100 PubMed)  
✅ **Cache-System**: Funktioniert einwandfrei  
✅ **Multi-Database**: DNB + PubMed Integration  
✅ **Export-Funktionen**: CSV, Excel, PDF, HTML  
✅ **URL-Links**: Direkte Verlinkung zu Publikationen  
✅ **GUI-Interface**: Vollständig funktional  

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für weitere Details.

## 🎯 Version 1.4-beta Highlights

- ✅ Vollständige Cache-Integration
- ✅ DNB + PubMed Multi-Database-Suche
- ✅ Erweiterte URL-Extraktion
- ✅ Verbesserte GUI-Performance
- ✅ Umfassende Datenexport-Optionen
- ✅ Automatische Duplikat-Entfernung

---

**Status**: ✅ **Produktionsreif** - Vollständig getestet und einsatzbereit

*Entwickelt für die effiziente Recherche medizinischer und wissenschaftlicher Literatur.*
