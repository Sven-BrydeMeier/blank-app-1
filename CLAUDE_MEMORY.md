# Claude Code Memory File - Immobilien-Transaktionsplattform

**Letzte Aktualisierung:** 2025-12-06
**Branch:** `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt`
**Letzter Commit:** `6f8e544` - Fix AttributeError: projekt.verkaeufer_id changed to verkaeufer_ids

---

## Projekt-Übersicht

Dies ist eine **Streamlit-basierte Immobilien-Transaktionsplattform**, die die Kommunikation zwischen folgenden Parteien koordiniert:
- **Makler** - Erstellt Projekte, verwaltet Exposés, koordiniert Termine
- **Käufer** - Lädt Bonitätsunterlagen hoch, akzeptiert Dokumente, bestätigt Termine
- **Verkäufer** - Stellt Unterlagen bereit, akzeptiert Dokumente, bestätigt Termine
- **Finanzierer** - Prüft Bonität, erstellt Finanzierungsangebote
- **Notar** - Prüft Dokumente, erstellt Kaufvertragsentwürfe, koordiniert Beurkundungstermine

**Streamlit App URL:** https://blank-app-1-01jm3ycngfksr1qvslfzhqrz.streamlit.app/

---

## Dateistruktur

```
/home/user/blank-app-1/
├── streamlit_app.py      # Hauptanwendung (~10800+ Zeilen)
├── requirements.txt      # Python-Abhängigkeiten
├── CLAUDE_MEMORY.md      # Diese Datei
└── .gitignore
```

---

## Haupt-Datei: streamlit_app.py

### Wichtige Zeilenbereiche (ungefähre Positionen)

| Bereich | Zeilen | Beschreibung |
|---------|--------|--------------|
| Imports & Enums | 1-130 | UserRole, ProjektStatus, PropertyType, NotificationType |
| **RESPONSIVE DESIGN** | 19-920 | DeviceType, inject_responsive_css, Helper-Funktionen |
| **SESSION PERSISTENZ** | ~1696-1820 | Cookies/localStorage, inject_session_persistence() |
| TodoKategorie/TodoPrioritaet | ~1220-1235 | Enums für Käufer-Todos |
| KaeuferTodo | ~1235-1250 | Dataclass für Käufer-Aufgaben |
| HandwerkerKategorie | ~1253-1270 | Enum für Handwerker-Kategorien |
| IdeenKategorie | ~1273-1284 | Enum für Ideenboard-Kategorien |
| Handwerker | ~1287-1303 | Dataclass für Handwerker-Empfehlungen |
| IdeenboardEintrag | ~1306-1322 | Dataclass für Ideenboard-Einträge |
| **Projekt-Klasse** | ~1330-1351 | verkaeufer_ids (Liste!), kaeufer_ids (Liste!), makler_id, notar_id |
| Session State Init | ~1809-1878 | Inkl. valid_tokens, API-Keys aus st.secrets |
| OCR-Verfügbarkeitsprüfung | ~2041-2095 | check_ocr_availability() |
| **Ausweis-Upload (Vorder/Rückseite)** | ~2750-3090 | render_ausweis_upload mit 3 Tabs + Rückkamera |
| Dashboard-Suchfunktionen | ~1940-2040 | render_dashboard_search(), search_matches(), filter_* |
| **Login-Seite** | ~5319-5417 | Mit "Angemeldet bleiben" Checkbox, Versionsnummer |
| Käufer-Dashboard | ~5860-5920 | Mit 9 Tabs inkl. Aufgaben und Handwerker |
| Käufer-Aufgaben | ~6020-6350 | Todos, Ideenboard, System-Todos |
| Käufer-Finanzierungsrechner | ~6720-7010 | Umfassender Kreditrechner |
| Notar-Dashboard | ~8290-8350 | Mit 12 Tabs inkl. KI-Kaufvertrag und Einstellungen |
| **KI-Kaufvertragsentwurf** | ~9076-9650 | notar_kaufvertrag_generator() mit 4 Sub-Tabs |
| Notar-Handwerker | ~10110-10250 | Handwerker-Verwaltung für Notar |
| **Notar-Einstellungen** | ~10309-10435 | API-Keys mit Hinweis zu st.secrets |
| main() | ~10860 | Hauptfunktion mit Responsive Design Injection |

---

## Implementierte Features

### Session-Persistenz (NEU - 2025-12-06)
- [x] **"Angemeldet bleiben" Checkbox** auf Login-Seite (standardmäßig aktiviert)
- [x] **localStorage-basierte Session-Speicherung** via JavaScript
- [x] **Session-Token-System** für sichere Wiederherstellung
- [x] **URL-Parameter-basierte Session-Wiederherstellung**
- [x] **Automatisches Laden von API-Keys aus st.secrets** beim Start
- [x] **Logout löscht Session** aus Browser und Server

### Versionsnummer auf Login-Seite (NEU)
- [x] Format: `JJ.MMTT.HH:MM` (z.B. 25.126.13:26)
- [x] Dynamisch generiert bei jedem Seitenaufruf

### KI-Kaufvertragsentwurf Generator (NEU)
- [x] **Notar-Dashboard Tab** "KI-Kaufvertrag"
- [x] **4 Sub-Tabs:**
  - Datenübersicht: Alle Projekt-/Teilnehmer-Daten
  - KI-Vertrag generieren: Mit Optionen und Vorschau
  - Vertrag bearbeiten: Editor für generierten Text
  - Vertrag versenden: An alle Parteien
- [x] **KI-Integration:** OpenAI GPT-4 oder Anthropic Claude
- [x] **Datensammlung:** Verkäufer, Käufer, Makler, Objekt, Exposé
- [x] **Optionen:** Auflassungsvormerkung, Räumungsfrist, Finanzierungsvollmacht, etc.

### OCR-Verbesserungen (NEU)
- [x] **check_ocr_availability()** - Prüft ob OCR verfügbar ist
- [x] **Klare Status-Anzeige** wenn OCR nicht verfügbar (Demo-Modus)
- [x] **Rückkamera-Präferenz** für mobile Geräte via JavaScript
- [x] **Priorität:** Claude Vision → OpenAI Vision → pytesseract → Demo-Daten

### Responsive Design System
- [x] **DeviceType Enum** für Geräte-Kategorisierung (mobile, tablet, desktop)
- [x] **CSS Variablen** für konsistentes Design
- [x] **Dark Mode Support** via prefers-color-scheme
- [x] **Media Queries** für:
  - Mobile (< 768px): Volle Breite, Bottom-Navigation, Sticky Header
  - Tablet (768-1024px): 2-Spalten Grid, optimierte Sidebar
  - Desktop (> 1024px): 3-Spalten Grid, volle Features
- [x] **iOS Safe Area Support** für Notch/Home-Indicator
- [x] **Sidebar funktioniert** auf allen Geräten (Fix vom 2025-12-06)

### Personalausweis-Erfassung mit Vorder- und Rückseite
- [x] **3-Tab-Layout:** Vorderseite, Rückseite, Daten übernehmen
- [x] **Fortschrittsanzeige:** Zeigt welche Seiten erfasst wurden
- [x] **OCR für beide Seiten:**
  - Vorderseite: Vorname, Nachname, Geburtsort, Geburtsdatum
  - Rückseite: Adresse, Ausweisnummer, Ablaufdatum
- [x] **Daten-Kombination:** Zusammenführung beider OCR-Ergebnisse
- [x] **Kamera oder Datei-Upload** für jede Seite
- [x] **Rückkamera-Präferenz** auf Mobilgeräten
- [x] **Verfügbar für Käufer und Verkäufer**

### Dashboard-Suche
- [x] Suchleiste in allen 5 Dashboards (Makler, Käufer, Verkäufer, Finanzierer, Notar)
- [x] Wiederverwendbare `render_dashboard_search()` Komponente
- [x] `search_matches()` für flexible Feldsuche

### Käufer-Todoliste
- [x] **System-generierte Todos** basierend auf Projekt-Status
- [x] **Eigene Todos** mit Titel, Beschreibung, Kategorie, Priorität, Fälligkeitsdatum
- [x] Kategorien: Finanzierung, Kaufvertrag, Dokumente, Ausstattung & Ideen, Umzug, Sonstiges
- [x] Prioritäten: Hoch, Mittel, Niedrig
- [x] Überfällig-Warnung bei Fälligkeitsdatum

### Ideenboard für Käufer
- [x] Kreative Ideen sammeln für neues Objekt
- [x] Kategorien: Einrichtung, Renovierung, Lichtkonzept, Küche, Bad, Garten, Smart Home, Farben, Böden
- [x] Geschätzte Kosten pro Idee
- [x] Inspirationsbilder per URL

### Handwerker-Empfehlungen
- [x] **Notar**: Handwerker anlegen mit vollständigen Kontaktdaten
- [x] **Käufer**: Vom Notar empfohlene Handwerker einsehen

### Exposé-System
- [x] ExposeData Dataclass mit ~50 Feldern
- [x] Adressvalidierung via Nominatim/OpenStreetMap API
- [x] Kaufpreis-Vorschlag basierend auf Objektdaten
- [x] Marktanalyse mit klickbaren Vergleichsobjekt-Links
- [x] Web-Exposé Vorschau (HTML)

### Termin-Koordination
- [x] Termin und TerminVorschlag Dataclasses
- [x] TerminTyp: Besichtigung, Übergabe, Beurkundung, Sonstiges
- [x] Bestätigungs-Workflow für alle Parteien
- [x] ICS-Kalenderdatei-Export (Google, Apple, Outlook)
- [x] **Fix:** Duplicate Key Error in Termin-Cards behoben (context Parameter)

### API-Key Konfiguration (Notar-Dashboard)
- [x] Neuer Tab "Einstellungen" im Notar-Dashboard
- [x] OpenAI API-Key eingeben und speichern
- [x] Anthropic API-Key eingeben und speichern
- [x] **NEU:** Hinweis zur permanenten Speicherung in Streamlit Secrets
- [x] **NEU:** Automatisches Laden aus st.secrets beim Start

### Erweitertes Finanzierungsmodul
- [x] Finanzierung anfragen Tab mit Kaufpreis/Eigenkapital-Eingabe
- [x] Finanzierer per E-Mail einladen mit Onboarding-Token
- [x] Umfassender Kreditrechner mit Tilgungsplan

---

## Wichtige Datenklassen

### Projekt (Zeile ~1330)
```python
@dataclass
class Projekt:
    projekt_id: str
    name: str
    makler_id: str = ""           # SINGULAR - Ein Makler
    kaeufer_ids: List[str] = []   # LISTE - Mehrere Käufer möglich
    verkaeufer_ids: List[str] = [] # LISTE - Mehrere Verkäufer möglich
    notar_id: str = ""            # SINGULAR - Ein Notar
    finanzierer_ids: List[str] = [] # LISTE - Mehrere Finanzierer
```

**WICHTIG:** `verkaeufer_ids` und `kaeufer_ids` sind Listen! Nicht `verkaeufer_id` (singular) verwenden!

---

## Session State Struktur

```python
st.session_state = {
    'initialized': bool,
    'current_user': User,
    'users': Dict[str, User],
    'projekte': Dict[str, Projekt],
    'legal_documents': Dict,
    'financing_offers': Dict,
    'wirtschaftsdaten': Dict,
    'notifications': Dict,
    'timeline_events': Dict[str, TimelineEvent],
    'makler_profiles': Dict,
    'expose_data': Dict[str, ExposeData],
    'termine': Dict[str, Termin],
    'terminvorschlaege': Dict[str, TerminVorschlag],
    'kaeufer_todos': Dict[str, KaeuferTodo],
    'handwerker_empfehlungen': Dict[str, Handwerker],
    'ideenboard': Dict[str, IdeenboardEintrag],
    # Session-Persistenz (NEU)
    'valid_tokens': Dict[str, str],  # email -> token
    # API-Keys (vom Notar konfigurierbar, aus st.secrets geladen)
    'api_keys': {'openai': str, 'anthropic': str},
    # Device Detection
    'device_type': str,  # mobile, tablet, desktop
}
```

---

## Bekannte Issues / TODOs

### Offen
- [ ] Erinnerungs-E-Mail 1 Tag vor Termin (Cronjob/Scheduler nötig)
- [ ] Echte Outlook-Kalender-Integration (Microsoft Graph API)
- [ ] Echte E-Mail-Versendung (SMTP)
- [ ] PDF-Exposé-Generierung (reportlab/weasyprint)

### Behoben (2025-12-06)
- [x] **Session-Persistenz:** Login bei Reload verloren → "Angemeldet bleiben" implementiert
- [x] **API-Keys vergessen:** → Automatisches Laden aus st.secrets
- [x] **verkaeufer_id AttributeError:** → Alle Referenzen zu verkaeufer_ids korrigiert
- [x] **Sidebar auf Mobile:** → CSS-Fix, funktioniert jetzt korrekt
- [x] **Duplicate Key Error in Termin-Cards:** → context Parameter hinzugefügt
- [x] **OCR nutzt Demo-Daten:** → check_ocr_availability() mit Status-Anzeige
- [x] **Frontkamera statt Rückkamera:** → JavaScript für facingMode: 'environment'

### Behoben (früher)
- [x] Exposé-Buttons verschwinden nach Speichern
- [x] Marktanalyse Links nicht klickbar
- [x] Dashboard-Suche implementiert

---

## Git-Workflow

```bash
# Aktueller Branch
git checkout claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt

# Änderungen committen
git add streamlit_app.py
git commit -m "Beschreibung"

# Pushen
git push -u origin claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt

# WICHTIG: Nach Push muss User auf GitHub PR erstellen und nach main mergen!
```

---

## Letzte Commits

| Commit | Beschreibung |
|--------|--------------|
| 6f8e544 | Fix AttributeError: projekt.verkaeufer_id changed to verkaeufer_ids |
| 859075a | Add OCR availability check and rear camera preference |
| (pending) | Add session persistence and API key improvements |
| 07d64c1 | Fix sidebar visibility on mobile devices |
| 03e713b | Add version number to login page |
| 0cef74f | Add comprehensive responsive design system |
| b6ea8d2 | Add front and back ID card upload with OCR combination |

---

## Deployment-Hinweis

**WICHTIG:** Streamlit Cloud deployed von `main` Branch!

Nach jedem Push auf den Feature-Branch muss der User:
1. Auf GitHub gehen
2. Pull Request erstellen: Feature-Branch -> main
3. PR mergen (Merge oder Squash)
4. Streamlit App redeployen oder warten (auto-redeploy)

### API-Keys in Streamlit Cloud konfigurieren:
1. Gehen Sie zu [share.streamlit.io](https://share.streamlit.io)
2. App auswählen → Settings → Secrets
3. Hinzufügen:
```toml
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
```
4. Save klicken

---

## Kontext für Fortsetzung

Bei Fortsetzung einer abgebrochenen Session:

1. **Branch prüfen:** `git branch` - sollte auf `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt` sein
2. **Letzten Stand prüfen:** `git log -3 --oneline`
3. **Diese Datei lesen:** `/home/user/blank-app-1/CLAUDE_MEMORY.md`
4. **Hauptdatei:** `/home/user/blank-app-1/streamlit_app.py` (~10800 Zeilen)

### Wichtige Code-Bereiche zum Nachlesen:
- Session-Persistenz: Zeile ~1696-1820
- Login-Seite mit "Angemeldet bleiben": Zeile ~5319-5417
- KI-Kaufvertragsentwurf: Zeile ~9076-9650
- Notar-Einstellungen (API-Keys): Zeile ~10309-10435
- Projekt-Klasse (verkaeufer_ids!): Zeile ~1330-1351

---

## Benutzer-Anforderungen (Deutsch)

Der Benutzer (Sven-BrydeMeier) arbeitet an einer deutschen Immobilien-Transaktionsplattform. Wichtige Begriffe:

- **Exposé** = Property listing/brochure
- **Beurkundung** = Notarization
- **Kaufvertrag** = Purchase contract
- **Notar** = Notary
- **Makler** = Real estate agent
- **Käufer** = Buyer
- **Verkäufer** = Seller
- **Finanzierer** = Financing party/bank
- **Besichtigung** = Property viewing
- **Übergabe** = Handover
- **Handwerker** = Craftsmen/tradespeople
- **Ideenboard** = Idea board for creative planning
- **Vorderseite/Rückseite** = Front/back (of ID card)
- **Angemeldet bleiben** = Stay logged in / Remember me
