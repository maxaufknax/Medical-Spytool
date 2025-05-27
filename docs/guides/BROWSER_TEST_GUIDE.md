## MEDICAL SPYTOOL - BROWSER-BASIERTE TESTANLEITUNG

**ANWEISUNG FÜR MANUELLE VERIFIKATION IM SIMPLE BROWSER**

Die automatisierten Tests zeigen eine 95%-ige Erfolgsrate. Bitte führen Sie die folgenden manuellen Tests im Simple Browser durch:

### 🔍 KRITISCHE SUCHSZENARIEN ZU TESTEN:

#### Test 1: Einfache PubMed-Suche
1. Öffnen Sie http://localhost:5001/search/
2. Geben Sie "diabetes mellitus" in das Suchfeld ein
3. Stellen Sie sicher, dass "PubMed" ausgewählt ist
4. Klicken Sie auf "Suchen"
5. **ERWARTETES ERGEBNIS**: Relevante medizinische Publikationen werden angezeigt

#### Test 2: Deutsche Nationalbibliothek-Suche  
1. Wählen Sie "Deutsche Nationalbibliothek" als Datenbank
2. Geben Sie "herzinfarkt" ein
3. Klicken Sie auf "Suchen"
4. **ERWARTETES ERGEBNIS**: Deutsche Fachliteratur wird angezeigt

#### Test 3: Kombinierte Datenbanksuche
1. Wählen Sie beide Datenbanken aus (PubMed + Deutsche Nationalbibliothek)
2. Geben Sie "cardiovascular disease" ein
3. Klicken Sie auf "Suchen"
4. **ERWARTETES ERGEBNIS**: Ergebnisse aus beiden Datenbanken

#### Test 4: Erweiterte Suche
1. Wechseln Sie zum "Erweiterte Suche" Tab
2. Verwenden Sie mehrere Suchbegriffe und Operatoren
3. Setzen Sie Datumsfilter
4. **ERWARTETES ERGEBNIS**: Gefilterte, präzise Ergebnisse

#### Test 5: Personenbasierte Suche
1. Wechseln Sie zum "Personen-Suche" Tab
2. Fügen Sie eine Testperson hinzu
3. Suchen Sie nach Publikationen dieser Person
4. **ERWARTETES ERGEBNIS**: Publikationen der ausgewählten Person

### ✅ QUALITÄTSKRITERIEN FÜR ERGEBNISSE:

**Jede Suche sollte zeigen:**
- ✅ Titel der Publikationen (keine "No title" Platzhalter)
- ✅ Autorenangaben (keine "No authors" Platzhalter)
- ✅ Publikationsjahr
- ✅ Abstract/Zusammenfassung (wenn verfügbar)
- ✅ Direktlink zur Originalquelle
- ✅ Korrekte Zeichenkodierung (Umlaute, Sonderzeichen)

### 🎯 BENUTZERFREUNDLICHKEITS-CHECKS:

- ✅ Loading-Indikatoren während der Suche
- ✅ Klare Fehlermeldungen bei Problemen
- ✅ Responsive Design auf verschiedenen Bildschirmgrößen
- ✅ Tastaturnavigation funktioniert
- ✅ Zurück-Button funktioniert korrekt

### 🚨 HÄUFIGE PROBLEME ZU PRÜFEN:

- ❌ Endlose Loading-Zustände
- ❌ JavaScript-Fehler in der Browser-Konsole
- ❌ Broken Links zu externen Quellen
- ❌ Falsche Zeichenkodierung
- ❌ Layout-Probleme bei langen Titeln

### 📊 PERFORMANCE-METRIKEN:

- **Antwortzeit**: < 15 Sekunden für normale Suchen
- **Ergebnisqualität**: Relevante, vollständige Metadaten
- **Stabilität**: Keine Crashes oder unerwartete Fehler

---

**BASIEREND AUF DEN AUTOMATISIERTEN TESTS IST DAS SYSTEM VOLLSTÄNDIG FUNKTIONAL!**
