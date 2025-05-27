# Medical Spytool - Neue Projektstruktur

**Version:** 2.0 (nach Cleanup)  
**Stand:** 27. Mai 2025

## 📁 Übersicht der Projektstruktur

```
medical-spytool/
├── 📄 main.py                   # WSGI Entry Point für Production
├── 📄 manage.py                 # Development Management Interface  
├── 📄 requirements.txt          # Python Dependencies
├── 📄 README.md                 # Haupt-Dokumentation
├── 📄 Dockerfile               # Container Configuration
├── 📄 docker-compose.yml       # Docker Compose Setup
├── 📄 Makefile                 # Build Automation
├── 📄 .env                     # Environment Configuration
├── 📄 .env.example             # Environment Template
├── 📄 .gitignore               # Git Ignore Rules
├── 📄 CONTRIBUTING.md          # Contribution Guidelines
├── 📄 pyproject.toml           # Python Project Configuration
├── 📄 babel.cfg                # Internationalization Config
├── 📄 uv.lock                  # UV Lock File
├── 📄 generated-icon.png       # Application Icon
│
├── 📂 backend/                 # 🔥 CORE APPLICATION
│   ├── 📄 app.py               # Flask Application Factory
│   ├── 📄 config.py            # Application Configuration  
│   ├── 📄 models.py            # Database Models
│   ├── 📄 search.py            # Search Engine Logic
│   ├── 📄 utils.py             # Utility Functions
│   ├── 📄 constants.py         # Application Constants
│   ├── 📄 csrf_config.py       # CSRF Protection Config
│   ├── 📄 export_utils.py      # Export Functionality
│   ├── 📄 api_utils.py         # API Utilities
│   ├── 📄 i18n.py             # Internationalization
│   ├── 📄 connectors_module.py # Database Connectors
│   │
│   ├── 📂 blueprints/          # Flask Blueprints
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main.py          # Main Routes
│   │   ├── 📄 search.py        # Search Routes  
│   │   ├── 📄 auth.py          # Authentication
│   │   ├── 📄 persons.py       # Person Management
│   │   ├── 📄 export.py        # Export Routes
│   │   ├── 📄 analysis.py      # Analysis Features
│   │   ├── 📄 logs.py          # Logging Routes
│   │   └── 📄 search_status_endpoint.py
│   │
│   ├── 📂 connectors/          # Database Connectors Package
│   │   ├── 📄 __init__.py
│   │   └── 📄 utils.py
│   │
│   ├── 📂 static/              # Static Assets (CSS, JS, Images)
│   ├── 📂 templates/           # Jinja2 Templates
│   ├── 📂 translations/        # i18n Translation Files
│   └── 📂 instance/            # Instance-specific Files
│
├── 📂 tests/                   # 🧪 TEST SUITE
│   ├── 📄 __init__.py
│   ├── 📄 conftest.py          # Test Configuration
│   ├── 📄 test_app.py          # Application Tests
│   ├── 📄 test_config.py       # Configuration Tests
│   ├── 📄 test_connectors.py   # Connector Tests
│   ├── 📄 test_csrf.py         # CSRF Tests
│   ├── 📄 test_models.py       # Model Tests
│   └── 📄 test_quick_search.py # Search Tests
│
├── 📂 docs/                    # 📚 DOCUMENTATION
│   ├── 📂 guides/              # User and Setup Guides
│   │   ├── 📄 USER_GUIDE.md
│   │   ├── 📄 QUICK_START.md
│   │   ├── 📄 SETUP_GUIDE.md
│   │   ├── 📄 TEST_GUIDE.md
│   │   └── 📄 BROWSER_TEST_GUIDE.md
│   │
│   ├── 📂 summaries/           # Development Summaries
│   │   ├── 📄 CSRF_FIX_COMPLETION_SUMMARY.md
│   │   ├── 📄 DNB_CONNECTOR_FIX_SUMMARY.md  
│   │   ├── 📄 TROUBLESHOOTING_SUMMARY.md
│   │   ├── 📄 SYSTEM_READY_REPORT.md
│   │   ├── 📄 VERIFICATION_FINAL_REPORT.md
│   │   ├── 📄 search_functionality_fix_summary.md
│   │   └── 📄 search_functionality_test_report.md
│   │
│   └── 📂 technical/           # Technical Documentation
│       ├── 📄 API_DOCS.md
│       ├── 📄 TROUBLESHOOTING.md
│       ├── 📄 LOCAL_DEVELOPMENT.md
│       ├── 📄 OPTIMIZATIONS.md
│       └── 📄 THEME_FIX_DOCUMENTATION.md
│
├── 📂 scripts/                 # 🔧 UTILITY SCRIPTS
│   ├── 📄 backup_database.py
│   ├── 📄 check_dependencies.py
│   ├── 📄 check_indentation.py
│   ├── 📄 generate_api_docs.py
│   ├── 📄 health_check.py
│   ├── 📄 setup_database.py
│   └── 📄 setup_dev_env.py
│
├── 📂 tools/                   # 🛠️ DEVELOPMENT TOOLS
│   ├── 📄 accessibility_audit.py
│   ├── 📄 csrf_test.py
│   ├── 📄 search_functionality_test_fixed.py
│   └── 📄 search_functionality_test.py
│
├── 📂 utils/                   # 🔄 SHARED UTILITIES
│   └── 📄 path_helper.py
│
├── 📂 migrations/              # 🗄️ DATABASE MIGRATIONS
│   ├── 📄 alembic.ini
│   ├── 📄 env.py
│   ├── 📄 README
│   └── 📄 script.py.mako
│
├── 📂 instance/                # 💾 RUNTIME DATA
│   ├── 📄 medicalspy.db        # SQLite Database
│   ├── 📄 test.db             # Test Database
│   ├── 📂 flask_session/       # Session Storage
│   └── 📂 sessions/           # Additional Sessions
│
├── 📂 logs/                    # 📋 APPLICATION LOGS
│   ├── 📄 medicalspymanager_20250526.log
│   └── 📄 medicalspymanager_20250527.log
│
├── 📂 output/                  # 📤 EXPORT OUTPUT
├── 📂 person_lists/            # 👥 PERSON DATA
├── 📂 backups/                 # 💾 DATABASE BACKUPS
│   ├── 📄 medicalspy_20250516_113321.db
│   ├── 📄 medicalspy_backup_20250516.db
│   └── 📂 sessions_20250521_112018/
│
├── 📂 attached_assets/         # 📎 ATTACHED DOCUMENTS
│   └── ... (Analyse-PDFs)
│
├── 📂 app/                     # 📱 LEGACY APP STRUCTURE
│   ├── 📄 config.py
│   └── 📂 main/
│       └── 📄 errors.py
│
└── 📂 .git/                    # 🔄 VERSION CONTROL
```

## 🚀 Entry Points

### Development (Lokal)
```bash
python manage.py run      # Startet Development Server
python manage.py setup    # Setup und Initialisierung  
python manage.py test     # Führt Tests aus
```

### Production (WSGI)
```bash
gunicorn main:app         # WSGI App über main.py
```

### Docker
```bash
docker-compose up         # Container-basiertes Setup
```

## 📝 Wichtige Dateien

| Datei | Zweck | Verwendung |
|-------|-------|------------|
| `manage.py` | **Management Interface** | Lokale Entwicklung, Setup, Tests |
| `main.py` | **WSGI Entry Point** | Production Deployment |
| `backend/app.py` | **Flask App Factory** | Anwendungslogik |
| `backend/config.py` | **Konfiguration** | App-Einstellungen |
| `requirements.txt` | **Dependencies** | Paket-Installation |
| `.env` | **Environment** | Umgebungsvariablen |

## 🔧 Development Workflow

### 1. Erste Einrichtung
```bash
git clone <repo>
cd medical-spytool
pip install -r requirements.txt
python manage.py setup --full
```

### 2. Development Server starten
```bash
python manage.py run
```

### 3. Tests ausführen
```bash
python manage.py test
# oder spezifisch:
python -m pytest tests/
```

### 4. Datenbank-Management
```bash
python manage.py db init       # Erstmalige Migration
python manage.py db migrate    # Schema-Änderungen
python manage.py db upgrade    # Anwenden der Migrationen
```

## 📚 Dokumentation Navigation

### Für Benutzer
- `README.md` - Erste Anlaufstelle
- `docs/guides/QUICK_START.md` - Schnelleinstieg
- `docs/guides/USER_GUIDE.md` - Vollständiges Benutzerhandbuch

### Für Entwickler  
- `CONTRIBUTING.md` - Beitragsleitfaden
- `docs/technical/LOCAL_DEVELOPMENT.md` - Entwicklung Setup
- `docs/technical/API_DOCS.md` - API Dokumentation

### Für System-Administratoren
- `docs/guides/SETUP_GUIDE.md` - Installation & Konfiguration
- `docs/technical/TROUBLESHOOTING.md` - Problemlösung

## 🔒 Sicherheitshinweise

### Niemals committen:
- `.env` (lokale Umgebungsvariablen)
- `instance/` Inhalte (Datenbanken, Sessions)  
- `logs/` Inhalte (Log-Dateien)
- `__pycache__/` (kompilierte Python-Dateien)

### Immer prüfen vor Deployment:
- `requirements.txt` aktuell
- Datenbank-Migrationen angewendet
- Tests erfolgreich
- Environment-Variablen gesetzt

---

**Ergebnis:** Klare, wartbare und professionelle Projektstruktur! 🎯
