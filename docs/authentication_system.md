# Medical Spytool Authentication System

## Übersicht
Die Medical Spytool Anwendung implementiert ein robustes, sicheres Authentifizierungssystem, das auf bewährten Sicherheitspraktiken basiert. Dieses Dokument beschreibt die wichtigsten Komponenten, Konfigurationen und Sicherheitsmerkmale des Authentifizierungssystems.

## Komponenten

### Flask-Login
- Kernkomponente für die Benutzersession-Verwaltung
- Verwaltet die Benutzerauthentifizierung und "Erinnern"-Funktionalität
- Implementiert sichere, serverseitige Session-Cookies

### Werkzeug Password Hashing
- Verwendet für sicheres Password-Hashing
- Implementiert Salting und sichere Hashing-Algorithmen
- Schützt vor Rainbow-Table- und Brute-Force-Angriffen

### CSRF-Schutz
- Flask-WTF CSRF-Schutz auf allen Formularen
- Verhindert Cross-Site Request Forgery-Angriffe
- Token-basierte Validierung für alle POST-Anfragen

## Benutzermodell

Das `User`-Modell implementiert die folgenden Attribute:
- `id`: Eindeutige Benutzer-ID
- `username`: Eindeutiger Benutzername
- `email`: Eindeutige E-Mail-Adresse
- `password_hash`: Gehashtes Passwort (nie im Klartext gespeichert)
- `role`: Benutzerrolle für rollenbasierte Zugriffskontrolle
- `is_active`: Flag für aktiven/inaktiven Account-Status
- `last_login`: Zeitstempel des letzten Logins
- `created_at`: Zeitstempel der Kontoerstellung

## Authentifizierungsablauf

1. **Login-Prozess**
   - Benutzer gibt Anmeldedaten ein
   - System validiert die Eingaben
   - Passwort wird gegen gespeichertes Hash verifiziert
   - Bei Erfolg: Benutzer wird angemeldet, Session erstellt
   - Bei Fehler: Fehlgeschlagene Anmeldung wird protokolliert, Fehlermeldung angezeigt

2. **Registrierungsprozess**
   - Benutzer gibt neue Kontoinformationen ein
   - System validiert Benutzernamen, E-Mail und Passwortrichtlinien
   - Passwort wird gehasht und in der Datenbank gespeichert
   - Optional: E-Mail-Bestätigung wird gesendet

3. **Passwort-Reset**
   - Benutzer fordert Passwort-Reset an
   - Zeitlich begrenzter Reset-Token wird erstellt und per E-Mail gesendet
   - Benutzer setzt neues Passwort mit gültigem Token
   - System validiert Token und aktualisiert Passwort-Hash

## Sicherheitsmaßnahmen

### Brute-Force-Schutz
- Fehlgeschlagene Anmeldeversuche werden protokolliert
- IP-basierte Ratenbegrenzung (Rate Limiting) bei vielen fehlgeschlagenen Anmeldungen
- Captcha nach mehreren fehlgeschlagenen Versuchen

### Passwortrichtlinien
- Mindestlänge: 8 Zeichen
- Erforderlich: Groß- und Kleinbuchstaben, Zahlen und Sonderzeichen
- Wörterbuchprüfung gegen bekannte schwache Passwörter

### Session-Sicherheit
- Sichere HttpOnly-Cookies
- Ablaufzeit der Session: 30 Minuten Inaktivität
- Session-Rotation nach erfolgreicher Anmeldung
- IP-basierte Session-Validierung

### Verschlüsselung
- TLS/SSL für alle Kommunikation
- Sichere HTTPS-Verbindungen erzwingen
- Sicherheits-Header: HSTS, X-Content-Type-Options

## Rollenbasierte Zugriffskontrolle

Das System implementiert die folgenden Rollen:
- **Admin**: Vollzugriff auf alle Systemfunktionen
- **Researcher**: Zugriff auf Suchfunktionen und Datenexport
- **Viewer**: Nur-Lese-Zugriff auf Suchergebnisse
- **Guest**: Begrenzte Sichtbarkeit von öffentlichen Daten

Rollen werden genutzt, um Benutzern nur die notwendigen Berechtigungen zu geben.

## Integration mit externen Systemen

Die Authentifizierung kann mit folgenden externen Systemen integriert werden:
- LDAP/Active Directory für Organisationsauthentifizierung
- OAuth2 für Single-Sign-On-Unterstützung
- SAML für Enterprise-Identitätsanbieter

## Fehlerbehandlung und Logging

- Alle Authentifizierungsereignisse werden detailliert protokolliert
- Erfolgreiche und fehlgeschlagene Anmeldeversuche werden aufgezeichnet
- Sicherheitsrelevante Ereignisse werden mit Zeitstempel, Benutzer und IP-Adresse gespeichert
- Logs werden sicher gespeichert und vor unbefugtem Zugriff geschützt

## Konfiguration und Anpassung

Die Authentifizierungseinstellungen können über folgende Konfigurationsoptionen angepasst werden:
- Passwortrichtlinien-Komplexität
- Session-Timeout-Dauer
- CSRF-Token-Gültigkeitsdauer
- Anmeldeversuchslimits

Diese Einstellungen befinden sich in der Konfigurationsdatei `config.py`.

## Best Practices

1. Regelmäßige Überprüfung der Sicherheitseinstellungen
2. Implementierung von Zwei-Faktor-Authentifizierung (2FA) für kritische Funktionen
3. Regelmäßige Sicherheitsaudits und Penetrationstests
4. Aktualisierung von Abhängigkeiten und Bibliotheken
5. Schulung der Nutzer zu Sicherheitspraktiken

---

Zuletzt aktualisiert: Mai 2025
