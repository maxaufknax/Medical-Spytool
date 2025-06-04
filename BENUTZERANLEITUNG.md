# Medical Spytool - Benutzeranleitung

Herzlich willkommen zur Benutzeranleitung für das Medical Spytool! Dieses Dokument hilft Ihnen dabei, alle Funktionen des Medical Spytools effektiv zu nutzen.

## Inhaltsverzeichnis

1.  [Einleitung](#1-einleitung)
    *   [Was ist das Medical Spytool?](#was-ist-das-medical-spytool)
    *   [Für wen ist dieses Tool gedacht?](#für-wen-ist-dieses-tool-gedacht)
2.  [Erste Schritte](#2-erste-schritte)
    *   [Oberflächenüberblick](#oberflächenüberblick)
    *   [Wichtige Konfiguration: API-Schlüssel](#wichtige-konfiguration-api-schlüssel)
3.  [Die Suchfunktionen im Detail](#3-die-suchfunktionen-im-detail)
    *   [Einfache Suche (Alle Datenbanken)](#einfache-suche-alle-datenbanken)
    *   [Spezifische Datenbanksuche](#spezifische-datenbanksuche)
    *   [Personenbezogene Suche](#personenbezogene-suche)
4.  [Personen verwalten](#4-personen-verwalten)
    *   [Wozu Personenprofile?](#wozu-personenprofile)
    *   [Eine neue Person anlegen](#eine-neue-person-anlegen)
    *   [Gespeicherte Personen nutzen](#gespeicherte-personen-nutzen)
    *   [Personen löschen](#personen-löschen)
5.  [Suchprofile verwenden](#5-suchprofile-verwenden)
    *   [Was sind Suchprofile?](#was-sind-suchprofile)
    *   [Ein Suchprofil speichern](#ein-suchprofil-speichern)
    *   [Ein Suchprofil laden und nutzen](#ein-suchprofil-laden-und-nutzen)
    *   [Suchprofile verwalten](#suchprofile-verwalten)
6.  [Suchergebnisse verstehen und nutzen](#6-suchergebnisse-verstehen-und-nutzen)
    *   [Die Ergebnisseite](#die-ergebnisseite)
    *   [Ergebnisse filtern](#ergebnisse-filtern)
    *   [Spaltenansicht anpassen](#spaltenansicht-anpassen)
    *   [Detailansicht einer Publikation](#detailansicht-einer-publikation)
7.  [Datenanalyse](#7-datenanalyse)
    *   [Visualisierungen](#visualisierungen)
    *   [Statistiken](#statistiken)
    *   [Meistzitierte Publikationen](#meistzitierte-publikationen)
8.  [Datenexport](#8-datenexport)
    *   [Exportformate (Excel, CSV)](#exportformate-excel-csv)
    *   [Exporteinstellungen anpassen](#exporteinstellungen-anpassen)
9.  [Anwendungseinstellungen](#9-anwendungseinstellungen)
    *   [API-Schlüssel verwalten](#api-schlüssel-verwalten)
    *   [Speicherpfade und Exportoptionen](#speicherpfade-und-exportoptionen)
    *   [Allgemeine Sucheinstellungen](#allgemeine-sucheinstellungen)
10. [Logs und Diagnose (Für fortgeschrittene Nutzer)](#10-logs-und-diagnose-für-fortgeschrittene-nutzer)
    *   [Log-Ansichten verstehen](#log-ansichten-verstehen)
    *   [Diagnosewerkzeuge nutzen](#diagnosewerkzeuge-nutzen)
11. [Fehlerbehebung / FAQ](#11-fehlerbehebung--faq)

---

## 1. Einleitung

### Was ist das Medical Spytool?
Das Medical Spytool ist eine leistungsstarke Software, die entwickelt wurde, um Ihnen die Suche und Analyse von wissenschaftlichen Publikationen und Forschungsprojekten zu erleichtern. Stellen Sie es sich als Ihren persönlichen Assistenten vor, der gleichzeitig in mehreren wichtigen Datenbanken wie PubMed, Scopus, Web of Science und weiteren nach den Informationen sucht, die Sie benötigen. Zusätzlich hilft Ihnen das Tool, den Überblick über Ihre Recherchen zu behalten und die gefundenen Daten aufzubereiten.

### Für wen ist dieses Tool gedacht?
Dieses Tool wurde für eine breite Zielgruppe im wissenschaftlichen und medizinischen Bereich konzipiert:
*   **Forscher und Wissenschaftler**: Zur Literaturrecherche, Verfolgung von Publikationstrends und Analyse von Forschungsfeldern.
*   **Medizinisches Fachpersonal**: Um aktuelle Studien und Leitlinien schnell zu finden.
*   **Studenten**: Zur Unterstützung bei Seminar-, Bachelor-, Master- oder Doktorarbeiten.
*   **Bibliothekare und Informationsspezialisten**: Als Werkzeug zur Unterstützung ihrer Nutzer.

Kurz gesagt: Jeder, der regelmäßig wissenschaftliche Literatur recherchiert, kann vom Medical Spytool profitieren.

---

## 2. Erste Schritte

### Oberflächenüberblick
Nach dem Start der Anwendung sehen Sie die Hauptoberfläche. Die Navigation erfolgt hauptsächlich über die Menüleiste am oberen Rand:

*   **Start**: Die Startseite mit einer Schnellsuche und Links zu Hauptfunktionen.
*   **Suche**: Das Herzstück des Tools. Hier können Sie verschiedene Suchmodi auswählen und Ihre Recherchen durchführen.
*   **Personen**: Verwalten Sie hier Profile von Autoren oder Forschern für wiederkehrende Suchen.
*   **Ergebnisse**: Zeigt die Resultate Ihrer letzten Suche an.
*   **Analyse**: Bietet grafische Auswertungen und Statistiken zu Ihren Suchergebnissen.
*   **Export**: Ermöglicht das Herunterladen Ihrer Suchergebnisse in verschiedenen Formaten.
*   **Logs**: (Für fortgeschrittene Nutzer) Zeigt Protokolldateien der Anwendung an, hilfreich bei der Fehlersuche.
*   **Einstellungen**: Konfigurieren Sie hier API-Schlüssel und andere Programmeinstellungen.
*   **Info/Über**: Zeigt Informationen über die Anwendung und diese Benutzeranleitung.

### Wichtige Konfiguration: API-Schlüssel
Viele der angebundenen Datenbanken (wie Scopus, Web of Science) erfordern einen sogenannten **API-Schlüssel**, um auf ihre Daten zugreifen zu dürfen. Ohne diese Schlüssel können Sie möglicherweise nicht alle Datenbanken durchsuchen oder erhalten nur eingeschränkte Ergebnisse.

**So konfigurieren Sie Ihre API-Schlüssel:**
1.  Klicken Sie in der Menüleiste auf **Einstellungen**.
2.  Sie sehen nun Eingabefelder für die verschiedenen Datenbanken.
3.  Tragen Sie Ihre persönlichen API-Schlüssel in die entsprechenden Felder ein.
    *   **PubMed**: Ein Schlüssel ist optional, aber empfohlen für mehr Anfragen.
    *   **DNB**: Ein Token (API-Schlüssel) wird für die Nutzung der SRU-Schnittstelle benötigt.
    *   **Scopus & Web of Science**: Ein Schlüssel ist zwingend erforderlich.
    *   Links zur Beantragung der Schlüssel finden Sie direkt auf der Einstellungsseite.
4.  Nach der Eingabe eines Schlüssels validiert das System diesen kurz und zeigt den Status an (ein grünes Häkchen für gültig, ein rotes Kreuz für ungültig).
5.  Vergessen Sie nicht, am Ende auf **"Einstellungen speichern"** zu klicken.

**Hinweis**: Die Speicherpfade für Exporte und Personenlisten werden ebenfalls in den Einstellungen festgelegt. Standardmäßig werden Ordner wie `output` und `person_lists` im Arbeitsverzeichnis der Anwendung erwartet.

---

## 3. Die Suchfunktionen im Detail

Über den Menüpunkt **Suche** gelangen Sie zu den verschiedenen Suchmodi, die in Tabs organisiert sind:

### Einfache Suche (Alle Datenbanken)
*   **Zweck**: Ideal für eine schnelle, breite Suche über alle verfügbaren Datenbanken mit einem einzigen Suchbegriff.
*   **Anwendung**:
    1.  Geben Sie Ihren Suchbegriff in das Feld "Suchbegriff" ein (z.B. "Diabetes Mellitus", "Anette Melk").
    2.  Optional: Passen Sie die "Max. Ergebnisse" an (dies gilt pro Datenbank).
    3.  Klicken Sie auf "Suche starten".

### Spezifische Datenbanksuche
*   **Zweck**: Für eine gezielte Recherche in einer einzelnen Datenbank mit erweiterten Filtermöglichkeiten.
*   **Anwendung**:
    1.  **Datenbank auswählen**: Wählen Sie aus der Dropdown-Liste die gewünschte Datenbank (z.B. PubMed, Scopus).
    2.  **Suchfeld (dynamisch)**: Je nach gewählter Datenbank erscheinen hier spezifische Felder, in denen Sie suchen können (z.B. "Titel", "Autor", "MeSH Terms" bei PubMed). Wählen Sie "Alle Felder" für eine breite Suche innerhalb der Datenbank.
    3.  **Suchbegriff**: Geben Sie hier Ihren Hauptsuchbegriff ein.
    4.  **Personen (optional)**: Fügen Sie eine oder mehrere zuvor gespeicherte Personen hinzu, um die Suche auf Publikationen dieser Autoren zu fokussieren oder sie als Co-Autoren zu berücksichtigen.
    5.  **Publikationstyp (dynamisch)**: Filtern Sie nach bestimmten Arten von Veröffentlichungen (z.B. "Journal Article", "Review"). Die verfügbaren Typen passen sich der gewählten Datenbank an.
    6.  **Sprache (dynamisch)**: Beschränken Sie die Suche auf bestimmte Sprachen.
    7.  **Datumsbereich**: Aktivieren Sie das Kontrollkästchen und wählen Sie ein Start- und Enddatum, um den Publikationszeitraum einzugrenzen.
    8.  Klicken Sie auf "Suche starten".

### Personenbezogene Suche
*   **Zweck**: Schnelle Suche basierend auf einem zuvor unter "Personen" angelegten Profil.
*   **Anwendung**:
    1.  **Person auswählen**: Wählen Sie eine Person aus der Dropdown-Liste. Die für diese Person hinterlegten Suchbegriffe (Hauptsuchbegriff, zusätzliche Begriffe) werden automatisch für die Suche verwendet.
    2.  **Datenbank auswählen**: Entscheiden Sie, ob die Suche für die ausgewählte Person über "Alle Datenbanken" oder eine "Spezifische Datenbank" laufen soll.
    3.  Klicken Sie auf "Suche starten".

---

## 4. Personen verwalten

### Wozu Personenprofile?
Die Personenverwaltung ermöglicht es Ihnen, Profile für häufig gesuchte Autoren, Forscher oder andere relevante Personen anzulegen. Jedes Profil kann spezifische Suchbegriffe enthalten, die mit dieser Person assoziiert sind (z.B. verschiedene Schreibweisen des Namens, frühere Namen, typische Forschungsfelder oder Institutionen). Dies spart Zeit und erhöht die Präzision bei wiederkehrenden Suchen.

### Eine neue Person anlegen
1.  Navigieren Sie zum Menüpunkt **Personen**.
2.  Im linken Bereich finden Sie das Formular "Person hinzufügen":
    *   **Vorname & Nachname**: Pflichtfelder.
    *   **Suchbegriff (optional)**: Geben Sie hier den Hauptsuchbegriff ein, der für diese Person verwendet werden soll (z.B. "Melk A", "Melk, Anette"). Wenn leer gelassen, wird oft der Nachname verwendet.
    *   **Zusätzliche Suchbegriffe (optional)**: Fügen Sie hier weitere Begriffe hinzu, die die Suche in Kombination mit dem Hauptsuchbegriff verfeinern (z.B. "Nephrologie", "Charite Berlin").
3.  Klicken Sie auf "Hinzufügen". Die Person erscheint dann in der "Personenliste" auf der rechten Seite.

### Gespeicherte Personen nutzen
*   **In der "Personenbezogenen Suche"**: Wählen Sie die Person direkt aus der Dropdown-Liste aus.
*   **In der "Spezifischen Datenbanksuche"**: Tippen Sie im Feld "Personen" den Namen der Person. Es erscheint eine Autovervollständigungsliste, aus der Sie die gewünschte Person auswählen können.
*   **Direktsuche auf der Personenseite**: In der "Personenliste" oder im Kasten "Schnellsuche-Optionen" können Sie auf den Namen einer Person oder auf spezifische Datenbanksymbole klicken, um direkt eine Suche mit dieser Person zu starten.

### Personen löschen
1.  Gehen Sie zur Seite **Personen**.
2.  In der "Personenliste" finden Sie bei jeder Person in der Spalte "Aktionen" ein Zahnrad-Symbol für weitere Optionen.
3.  Klicken Sie auf das Zahnrad und wählen Sie "Person löschen".
4.  Bestätigen Sie die Sicherheitsabfrage.

---

## 5. Suchprofile verwenden

### Was sind Suchprofile?
Suchprofile sind gespeicherte Sucheinstellungen. Wenn Sie eine komplexe Suche mit vielen Filtern und Begriffen konfiguriert haben, können Sie diese als Profil speichern, um sie später schnell wieder aufrufen und ausführen zu können, ohne alle Parameter neu eingeben zu müssen.

### Ein Suchprofil speichern
1.  Konfigurieren Sie Ihre gewünschte Suche im Tab "Einfache Suche" oder "Spezifische Datenbanksuche".
2.  Klicken Sie unten auf den Button **"Als Profil speichern"**.
3.  Ein kleines Fenster (Modal) öffnet sich. Geben Sie einen aussagekräftigen **Profilnamen** ein.
4.  Klicken Sie auf "Speichern". Ihre aktuellen Sucheinstellungen (Suchbegriffe, gewählte Datenbank, Filter etc.) werden nun unter diesem Namen gesichert.

### Ein Suchprofil laden und nutzen
1.  Navigieren Sie zum Menüpunkt **Suchprofile**.
2.  Sie sehen eine Liste Ihrer gespeicherten Profile, dargestellt als Karten.
3.  Bei jedem Profil finden Sie den Button **"Profil laden & Suchen"**.
4.  Ein Klick darauf lädt die gespeicherten Einstellungen und führt Sie direkt zur Suchseite, wo die Parameter bereits ausgefüllt sind. Sie können die Suche dann direkt starten oder bei Bedarf noch anpassen.

### Suchprofile verwalten
Auf der Seite **Suchprofile** können Sie auch:
*   **Löschen**: Nicht mehr benötigte Profile über den "Löschen"-Button entfernen (mit Sicherheitsabfrage).

---

## 6. Suchergebnisse verstehen und nutzen

### Die Ergebnisseite
Nach einer erfolgreichen Suche werden die gefundenen Publikationen auf der Seite **Ergebnisse** angezeigt.
*   **Kopfzeile**: Zeigt die Anzahl der gefundenen Publikationen und den ursprünglichen Suchkontext. Buttons für den direkten Export und zur Analyse sind hier ebenfalls verfügbar.
*   **Ergebnistabelle**: Listet die Publikationen mit den wichtigsten Informationen auf (Datenbank, Titel, Autoren, Jahr, Zitationen, Typ).

### Ergebnisse filtern
Oberhalb der Ergebnistabelle befindet sich ein ausklappbares **Filter-Panel**:
*   **Textsuche**: Geben Sie einen Begriff ein, um die *aktuell angezeigten Ergebnisse* weiter nach diesem Text zu durchsuchen.
*   **Dynamische Filter**:
    *   **Datenbank**: Filtern Sie nach der Ursprungsdatenbank.
    *   **Publikationsjahr**: Stellen Sie einen Jahresbereich ein.
    *   **Publikationstyp**: Filtern Sie nach der Art der Publikation.
    *   **Autor**: Geben Sie einen Autorennamen ein, um die Ergebnisliste einzuschränken.
    Die Optionen für Datenbank-, Jahr- und Publikationstypfilter werden dynamisch basierend auf den aktuellen Suchergebnissen generiert.
*   **Filter zurücksetzen**: Setzt alle Filter im Panel zurück und zeigt wieder alle ursprünglichen Ergebnisse an.
*   **Filterstatistik**: Zeigt an, wie viele Ergebnisse den aktuellen Filtereinstellungen entsprechen.

### Spaltenansicht anpassen
Über den Button **"Spalten"** (oberhalb der Tabelle) können Sie ein Modal öffnen, um auszuwählen, welche Spalten in der Ergebnistabelle angezeigt oder ausgeblendet werden sollen (z.B. Institut, Sprache, Schlagwörter). Ihre Auswahl wird für die Dauer Ihrer Sitzung gespeichert.

### Detailansicht einer Publikation
In jeder Zeile der Ergebnistabelle finden Sie ein Info-Symbol (<i class="fas fa-info-circle"></i>). Ein Klick darauf öffnet ein Fenster (Modal) mit detaillierten Informationen zur jeweiligen Publikation, wie z.B.:
*   Vollständiger Titel, Autoren, Journal, Publikationsdetails
*   Abstract (Kurzzusammenfassung)
*   Schlagwörter (Keywords)
*   DOI, ISBN, PubMed ID (falls verfügbar)
*   Link zur Originalquelle (falls vorhanden)

---

## 7. Datenanalyse

Wenn Sie Suchergebnisse erhalten haben, können Sie über den Button **"Analysieren"** auf der Ergebnisseite (oder direkt über den Menüpunkt **Analyse**) zur Datenanalyse gelangen.
*   **Visualisierungen**:
    *   Die Seite zeigt Diagramme zur Verteilung der Publikationen.
    *   Sie können wählen, ob die Publikationen nach **Jahr**, **Datenbank** oder **Person (Suchkontext)** gruppiert und visualisiert werden sollen. Die Diagramme werden dynamisch geladen.
*   **Statistiken**: Eine Zusammenfassung zeigt die Gesamtanzahl der Publikationen, die Anzahl pro Datenbank und den abgedeckten Publikationszeitraum.
*   **Meistzitierte Publikationen**: Eine Tabelle listet die Top 10 Publikationen aus Ihren Ergebnissen auf, sortiert nach der Anzahl der Zitationen (sofern diese Information von den Datenbanken bereitgestellt wurde).

---

## 8. Datenexport

Sie können Ihre Suchergebnisse für die weitere Verwendung exportieren.
1.  Führen Sie zunächst eine Suche durch.
2.  Gehen Sie zur Seite **Export** (erreichbar von der Ergebnisseite oder über die Hauptnavigation).
3.  **Export-Optionen**:
    *   Wählen Sie, ob Sie die Daten als **Excel-Datei (.xlsx)** oder **CSV-Datei (.csv)** exportieren möchten. Klicken Sie auf den entsprechenden Button. Die Datei wird dann vom Server generiert und zum Download angeboten.
4.  **Exporteinstellungen anpassen**:
    *   **Spalten für den Export auswählen**: Legen Sie fest, welche Datenfelder (Spalten) in der Exportdatei enthalten sein sollen. Standardmäßig sind hier die in den "Einstellungen" festgelegten Spalten vorausgewählt.
    *   **Dateioptionen**:
        *   **Exportpfad**: (Wird serverseitig in den Einstellungen konfiguriert) Zeigt an, wo die Datei auf dem Server gespeichert wird, bevor sie heruntergeladen wird.
        *   **Eindeutige Dateinamen**: Wenn aktiviert, erhält jede Exportdatei einen Zeitstempel im Namen, um Überschreibungen zu vermeiden.
        *   **Dateiname-Präfix**: Ein von Ihnen festgelegter Namensanfang für jede Exportdatei.
    *   **Excel-Optionen**: Aktivieren/Deaktivieren Sie erweiterte Formatierungen, Autofilter und das Fixieren der Kopfzeile für Excel-Exporte.
    *   **CSV-Optionen**: Wählen Sie das Trennzeichen (z.B. Komma, Semikolon) und die Zeichenkodierung für CSV-Exporte.
    *   Klicken Sie auf **"Export-Einstellungen speichern"**, um Ihre Präferenzen für zukünftige Exporte zu sichern.

---

## 9. Anwendungseinstellungen

Unter **Einstellungen** können Sie das Medical Spytool an Ihre Bedürfnisse anpassen.
*   **API-Schlüssel verwalten**: Wie in [Abschnitt 2.2](#wichtige-konfiguration-api-schlüssel) beschrieben, geben Sie hier Ihre API-Schlüssel ein und validieren Sie diese.
*   **Speicherpfade und Exportoptionen**:
    *   **Ausgabeverzeichnis für Exporte**: Legt fest, in welchem Ordner auf dem Server die Exportdateien standardmäßig erstellt werden.
    *   **Verzeichnis für Personenlisten**: Legt fest, wo die Datei mit Ihren gespeicherten Personen (`persons.json`) liegt.
    *   **Eindeutige Dateinamen**: Standardeinstellung für die Option bei Exporten.
*   **Allgemeine Sucheinstellungen**:
    *   **Standard-Datenbank**: Wählen Sie die Datenbank, die im Tab "Spezifische Datenbanksuche" standardmäßig vorausgewählt sein soll.
*   **Spaltenauswahl für Export (Standard)**: Definieren Sie, welche Spalten standardmäßig beim Export von Daten berücksichtigt werden sollen.

Änderungen werden mit Klick auf **"Einstellungen speichern"** übernommen.

---

## 10. Logs und Diagnose (Für fortgeschrittene Nutzer)

Die Seite **Logs** bietet Einblicke in die internen Abläufe der Anwendung und ist besonders nützlich zur Fehlerdiagnose.
*   **Log-Ansichten**:
    *   **Standard-Log**: Zeigt wichtige Ereignisse, Warnungen und Fehler.
    *   **Erweiterter Log**: Enthält alle Log-Meldungen, einschließlich detaillierter Debug-Informationen.
*   **Filter- und Suchfunktionen**: Ermöglichen das schnelle Auffinden relevanter Logeinträge.
*   **Systeminformationen**: Eine Übersicht über die technische Umgebung der Anwendung (Betriebssystem, Python-Version, Konfigurationseinstellungen etc.). Enthält auch eine einfache Visualisierung der Speichernutzung.
*   **Diagnosewerkzeuge**:
    *   **Abhängigkeiten überprüfen**: Listet die installierten Programmbibliotheken und deren Versionen auf.
    *   **Datenbankverbindungen testen**: Prüft die Erreichbarkeit und den Status der angebundenen Datenbanken (basierend auf Konfiguration und ggf. API-Schlüsseln).
    *   **Speicherpfade überprüfen**: Kontrolliert, ob die konfigurierten Pfade existieren und beschreibbar sind.
    *   **Alle Logs zurücksetzen**: Löscht den Inhalt der Log-Datei (mit Bestätigung).
    Die Ergebnisse der Diagnose-Checks werden direkt auf der Seite angezeigt.

---

## 11. Fehlerbehebung / FAQ

*   **F: Eine Datenbanksuche liefert keine Ergebnisse, obwohl ich welche erwarte.**
    *   **A**: Überprüfen Sie unter "Einstellungen", ob der API-Schlüssel für die betreffende Datenbank korrekt eingetragen und gültig ist. Viele Datenbanken erfordern einen gültigen Schlüssel. Stellen Sie auch sicher, dass keine zu restriktiven Filter gesetzt sind.
*   **F: Die Anwendung zeigt eine Fehlermeldung an.**
    *   **A**: Notieren Sie sich die Fehlermeldung. Unter "Logs" finden Sie möglicherweise detailliertere Informationen. Die "Diagnosewerkzeuge" können ebenfalls Aufschluss geben. Kontaktieren Sie ggf. den Support und stellen Sie die Log-Informationen bereit.
*   **F: Exportierte Excel-Dateien sehen nicht richtig formatiert aus.**
    *   **A**: Stellen Sie sicher, dass unter "Export" -> "Exporteinstellungen" -> "Excel-Optionen" die Option "Formatierte Excel-Tabelle erstellen" aktiviert ist.
*   **F: Wie kann ich die Standardsprache für die Suche ändern?**
    *   **A**: Die Sprache der Suchergebnisse hängt von den Datenbanken und den indexierten Publikationen ab. Sie können jedoch in der "Spezifischen Datenbanksuche" einen Sprachfilter setzen, um die Ergebnisse auf eine bestimmte Sprache einzuschränken.
*   **F: Wo werden meine Personenlisten und Suchprofile gespeichert?**
    *   **A**: Diese werden als JSON-Dateien in den Verzeichnissen gespeichert, die Sie unter "Einstellungen" -> "Speicherpfade" festgelegt haben (standardmäßig `person_lists/` und `search_profiles/` im Anwendungsverzeichnis).

---

Wir hoffen, diese Anleitung hilft Ihnen bei der Nutzung des Medical Spytools! Bei weiteren Fragen oder Problemen zögern Sie nicht, den Support zu kontaktieren.
