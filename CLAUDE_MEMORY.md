# Claude Code Memory File - Immobilien-Transaktionsplattform

**Letzte Aktualisierung:** 2025-12-08
**Branch:** `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt`
**Letzter Commit:** `d2eccfe` - Implement improvement suggestions: price adoption, Makler view, ratings

---

## Projekt-Übersicht

Dies ist eine **Streamlit-basierte Immobilien-Transaktionsplattform**, die die Kommunikation zwischen folgenden Parteien koordiniert:
- **Makler** - Erstellt Projekte, verwaltet Exposés, koordiniert Termine, **kann Ausweise scannen**
- **Käufer** - Lädt Bonitätsunterlagen hoch, akzeptiert Dokumente, bestätigt Termine, **muss Rechtsdokumente akzeptieren**
- **Verkäufer** - Stellt Unterlagen bereit, akzeptiert Dokumente, bestätigt Termine, **muss Rechtsdokumente akzeptieren**
- **Finanzierer** - Prüft Bonität, erstellt Finanzierungsangebote
- **Notar** - Prüft Dokumente, erstellt Kaufvertragsentwürfe, koordiniert Beurkundungstermine, **verwaltet Rechtsdokumente & Handwerker**

**Streamlit App URL:** https://blank-app-1-01jm3ycngfksr1qvslfzhqrz.streamlit.app/

---

## Dateistruktur

```
/home/user/blank-app-1/
├── streamlit_app.py      # Hauptanwendung (~13200 Zeilen)
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
| **VERTRAGSARCHIV ENUMS** | ~1732-1782 | VertragsTyp, TextbausteinKategorie, TextbausteinStatus |
| **VERTRAGSARCHIV DATACLASSES** | ~1783-1957 | Textbaustein, VertragsDokument, VertragsVorlage, Vertragsentwurf |
| **SESSION PERSISTENZ** | ~1959-2030 | Cookies/localStorage, inject_session_persistence() |
| TodoKategorie/TodoPrioritaet | ~1220-1235 | Enums für Käufer-Todos |
| KaeuferTodo | ~1235-1250 | Dataclass für Käufer-Aufgaben |
| HandwerkerKategorie | ~1253-1270 | Enum für Handwerker-Kategorien |
| IdeenKategorie | ~1273-1284 | Enum für Ideenboard-Kategorien |
| Handwerker | ~1287-1303 | Dataclass für Handwerker-Empfehlungen |
| IdeenboardEintrag | ~1306-1322 | Dataclass für Ideenboard-Einträge |
| **Projekt-Klasse** | ~1330-1351 | verkaeufer_ids (Liste!), kaeufer_ids (Liste!), makler_id, notar_id |
| Session State Init | ~1809-1903 | Inkl. valid_tokens, API-Keys, rechtsdokument_akzeptanzen |
| **Demo-Daten Handwerker** | ~2003-2080 | create_demo_handwerker() |
| **Demo-Daten Rechtsdokumente** | ~2081-2145 | create_demo_notar_rechtsdokumente() |
| OCR-Verfügbarkeitsprüfung | ~2150-2200 | check_ocr_availability() |
| **Ausweis-Upload (Vorder/Rückseite)** | ~3004-3200 | render_ausweis_upload mit context-Parameter |
| ICS-Kalender-Export | ~4164-4180 | fix: beschreibung_ics Variable statt inline |
| Dashboard-Suchfunktionen | ~1940-2040 | render_dashboard_search(), search_matches(), filter_* |
| **Login-Seite** | ~5319-5417 | Mit "Angemeldet bleiben" Checkbox, Versionsnummer |
| **Makler-Dashboard** | ~5621-5658 | Mit neuem Tab "🪪 Ausweisdaten erfassen" |
| **Makler Ausweis-Erfassung** | ~6227-6300 | makler_ausweis_erfassung() |
| **Käufer-Dashboard** | ~6421-6490 | Mit Pflicht-Akzeptanz Check, 9 Tabs |
| Käufer-Handwerker (gefiltert) | ~6455-6520 | kaeufer_handwerker_empfehlungen() nach Notar gefiltert |
| Käufer-Aufgaben | ~6550-6750 | Todos, Ideenboard, System-Todos |
| Käufer-Finanzierungsrechner | ~7000-7300 | Umfassender Kreditrechner |
| **Verkäufer-Dashboard** | ~8123-8170 | Mit Pflicht-Akzeptanz Check |
| **Notar-Dashboard** | ~10398-10478 | Mit 17 Tabs inkl. Vertragsarchiv & Vertragserstellung |
| **VERTRAGSARCHIV FUNKTIONEN** | ~10641-11447 | notar_vertragsarchiv_view() mit 5 Sub-Tabs |
| **VERTRAGSERSTELLUNG FUNKTIONEN** | ~11449-11946 | notar_vertragserstellung_view() mit 5 Sub-Tabs |
| **KI-Kaufvertragsentwurf** | ~9200-9750 | notar_kaufvertrag_generator() mit 4 Sub-Tabs |
| Notar-Handwerker | ~10200-10400 | Handwerker-Verwaltung für Notar |
| **Notar Ausweis-Erfassung** | ~10566-10646 | notar_ausweis_erfassung() |
| **Notar Rechtsdokumente** | ~10649-10751 | notar_rechtsdokumente_view(), render_rechtsdokument_editor() |
| **Rechtsdokument Akzeptanz-Status** | ~10754-10827 | render_rechtsdokument_akzeptanz_status() |
| **Pflicht-Akzeptanz Funktionen** | ~10830-10953 | get_user_notar_ids(), check_rechtsdokumente_akzeptiert(), render_rechtsdokumente_akzeptanz_pflicht() |
| **Notar-Einstellungen** | ~10956-11050 | API-Keys mit Hinweis zu st.secrets |
| **Preisverhandlung Helper** | ~2361-2517 | kann_preisverhandlung_fuehren(), create_preisangebot(), respond_to_preisangebot() |
| **Käufer Preisverhandlung UI** | ~7059-7168 | In kaeufer_projekte_view() |
| **Verkäufer Preisverhandlung UI** | ~9188-9297 | In verkaeufer_projekte_view() |
| main() | ~12500 | Hauptfunktion mit Responsive Design Injection |

---

## Implementierte Features

### Vertragsarchiv & Textbausteine (NEU - 2025-12-08)
- [x] **Vertragsarchiv-Tab im Notar-Dashboard** mit 5 Sub-Tabs
  - Upload: DOCX, PDF, Bilder mit Text-Extraktion
  - Textbausteine: Übersicht aller Klauseln mit Filter
  - Hochgeladene Dokumente: Zerlegung in Bausteine
  - Freigaben: Notar-Workflow für neue Bausteine
  - Updates suchen: KI-gestützte Aktualisierungsprüfung
- [x] **Datenstrukturen:**
  - `VertragsTyp` Enum (Kaufvertrag, Erbvertrag, Schenkungsvertrag, etc.)
  - `TextbausteinKategorie` Enum (21 Kategorien: Vertragsparteien, Kaufpreis, Auflassung, etc.)
  - `TextbausteinStatus` Enum (Entwurf, Freigegeben, Update verfügbar, etc.)
  - `Textbaustein` Dataclass mit KI-Metadaten, Versionierung, Duplikaterkennung
  - `VertragsDokument` Dataclass für hochgeladene Verträge
  - `VertragsVorlage` Dataclass für wiederverwendbare Vorlagen
  - `Vertragsentwurf` Dataclass für konkrete Entwürfe mit Workflow
- [x] **KI-Funktionen:**
  - `ki_analysiere_textbaustein()`: Titel, Zusammenfassung, Kategorie automatisch
  - `ki_zerlege_vertrag_in_bausteine()`: Vertrag in einzelne Klauseln splitten
  - `ki_suche_updates()`: Updates für Klauseln via ChatGPT
- [x] **Vertragserstellung-Tab im Notar-Dashboard** mit 5 Sub-Tabs
  - Neuer Vertrag: Projekt wählen, Methode auswählen
  - Aus Bausteinen: Modulare Zusammenstellung
  - KI-Entwurf: Automatische Vertragsgenerierung mit Käufer/Verkäufer-Wünschen
  - Vorlagen: Vertragsvorlagen verwalten
  - Entwürfe: Bearbeiten, freigeben, versenden
- [x] **Duplikaterkennung** mit Text-Hash und Jaccard-Ähnlichkeit
- [x] **Freigabe-Workflow:** Notar prüft alle neuen Bausteine
- [x] **Versand an Beteiligte:** Per Notification an Käufer, Verkäufer, Makler

### Preisverhandlung zwischen Käufer/Verkäufer (NEU - 2025-12-06)
- [x] **Preisangebot-System** mit Status: Offen, Angenommen, Abgelehnt, Gegenangebot, Zurückgezogen
- [x] **Ohne Makler:** Preisverhandlung immer erlaubt
- [x] **Mit Makler:** Nur wenn `preisverhandlung_erlaubt = True` im Projekt
- [x] **Käufer-Dashboard:** Preisangebot abgeben, Verkäufer-Angebote annehmen/ablehnen/Gegenangebot
- [x] **Verkäufer-Dashboard:** Preisvorschlag senden, Käufer-Angebote annehmen/ablehnen/Gegenangebot
- [x] **Verhandlungsverlauf:** Alle Angebote chronologisch mit Status-Icons
- [x] **Benachrichtigungen:** Bei neuem Angebot, Annahme, Ablehnung, Gegenangebot

### Benachrichtigungen bei Rechtsdokument-Akzeptanz (NEU - 2025-12-06)
- [x] **Käufer/Verkäufer erhält Bestätigung** in Posteingang nach Akzeptanz
- [x] **Notar wird informiert** wenn Käufer/Verkäufer Dokumente akzeptiert

### Optionale Rechtsdokument-Pflicht (NEU - 2025-12-06)
- [x] **Makler-Einstellung:** `rechtsdokumente_erforderlich` beim Projekt-Erstellen
- [x] **Projekt-Editor:** Toggle für bestehende Projekte
- [x] Wenn deaktiviert: Käufer/Verkäufer können ohne Akzeptanz auf Dashboard zugreifen

### Druckfunktionen (NEU - 2025-12-06)
- [x] **Handwerker-Steckbrief:** Druckbares HTML mit Kontaktdaten, Bewertung, Beschreibung
- [x] **Exposé-Druckversion:** Professionelles HTML mit CSS Grid, Print-optimiert
- [x] Download-Buttons für beide Dokumenttypen

### Demo-Modus Toggle (NEU - 2025-12-06)
- [x] **Notar-Einstellungen:** Toggle für Demo-Modus AN/AUS
- [x] AN = Volle Funktionalität mit Demo-Daten
- [x] AUS = Produktionsmodus (Hinweis auf echte API-Keys)

### Erweiterte Handwerker-Kategorien (NEU - 2025-12-06)
- [x] **Umzugsunternehmen** hinzugefügt (HandwerkerKategorie.UMZUG)
- [x] **Reinigungsservice** hinzugefügt (HandwerkerKategorie.REINIGUNG)
- [x] Demo-Handwerker für beide Kategorien

### Rechtsdokumente & Pflicht-Akzeptanz (NEU - 2025-12-06)
- [x] **Notar: Rechtsdokumente-Verwaltung** (Datenschutz, AGB, Widerrufsbelehrung)
  - Neuer Tab "📜 Rechtsdokumente" im Notar-Dashboard
  - Editor für Titel, Inhalt, Version, Gültigkeitsdatum, Pflicht-Flag
  - Akzeptanz-Status-Übersicht aller Käufer/Verkäufer pro Projekt
- [x] **Käufer/Verkäufer: Pflicht-Akzeptanz vor Dashboard-Zugang**
  - Prüfung beim Dashboard-Laden via `check_alle_rechtsdokumente_akzeptiert()`
  - Scrollbarer Dokumenteninhalt mit Checkbox-Bestätigung
  - Akzeptanz wird mit Timestamp und Version gespeichert
  - Dashboard erst nach Akzeptanz aller Pflicht-Dokumente zugänglich

### Personalausweis-Scan für Makler/Notar (NEU - 2025-12-06)
- [x] **Makler-Dashboard:** Neuer Tab "🪪 Ausweisdaten erfassen"
- [x] **Notar-Dashboard:** Neuer Tab "🪪 Ausweisdaten"
- [x] **Context-Parameter** für render_ausweis_upload() - unique Widget-Keys
- [x] Auswahl des Projekts und der Person (Käufer/Verkäufer)

### Handwerker-Empfehlungen verbessert (NEU - 2025-12-06)
- [x] **Demo-Handwerker erstellt** (Elektriker, Sanitär, Maler, Schreiner)
- [x] **Käufer sehen nur Handwerker vom Notar ihrer Projekte**
- [x] Filterung via `get_user_notar_ids()` und `meine_notar_ids`

### Session-Persistenz (2025-12-06)
- [x] **"Angemeldet bleiben" Checkbox** auf Login-Seite (standardmäßig aktiviert)
- [x] **localStorage-basierte Session-Speicherung** via JavaScript
- [x] **Session-Token-System** für sichere Wiederherstellung
- [x] **URL-Parameter-basierte Session-Wiederherstellung**
- [x] **Automatisches Laden von API-Keys aus st.secrets** beim Start
- [x] **Logout löscht Session** aus Browser und Server

### Versionsnummer auf Login-Seite
- [x] Format: `JJ.MMTT.HH:MM` (z.B. 25.126.13:26)
- [x] Dynamisch generiert bei jedem Seitenaufruf

### KI-Kaufvertragsentwurf Generator
- [x] **Notar-Dashboard Tab** "KI-Kaufvertrag"
- [x] **4 Sub-Tabs:**
  - Datenübersicht: Alle Projekt-/Teilnehmer-Daten
  - KI-Vertrag generieren: Mit Optionen und Vorschau
  - Vertrag bearbeiten: Editor für generierten Text
  - Vertrag versenden: An alle Parteien
- [x] **KI-Integration:** OpenAI GPT-4 oder Anthropic Claude
- [x] **Datensammlung:** Verkäufer, Käufer, Makler, Objekt, Exposé
- [x] **Optionen:** Auflassungsvormerkung, Räumungsfrist, Finanzierungsvollmacht, etc.

### OCR-Verbesserungen
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
- [x] **Sidebar funktioniert** auf allen Geräten

### Personalausweis-Erfassung mit Vorder- und Rückseite
- [x] **3-Tab-Layout:** Vorderseite, Rückseite, Daten übernehmen
- [x] **Fortschrittsanzeige:** Zeigt welche Seiten erfasst wurden
- [x] **OCR für beide Seiten:**
  - Vorderseite: Vorname, Nachname, Geburtsort, Geburtsdatum
  - Rückseite: Adresse, Ausweisnummer, Ablaufdatum
- [x] **Daten-Kombination:** Zusammenführung beider OCR-Ergebnisse
- [x] **Kamera oder Datei-Upload** für jede Seite
- [x] **Rückkamera-Präferenz** auf Mobilgeräten
- [x] **Verfügbar für Käufer, Verkäufer, Makler und Notar**

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
- [x] **Käufer**: Vom Notar empfohlene Handwerker einsehen (gefiltert nach Projekt-Notar)

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
- [x] Hinweis zur permanenten Speicherung in Streamlit Secrets
- [x] Automatisches Laden aus st.secrets beim Start

### Erweitertes Finanzierungsmodul
- [x] Finanzierung anfragen Tab mit Kaufpreis/Eigenkapital-Eingabe
- [x] Finanzierer per E-Mail einladen mit Onboarding-Token
- [x] Umfassender Kreditrechner mit Tilgungsplan

---

## Wichtige Datenklassen

### Projekt (Zeile ~1352)
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
    rechtsdokumente_erforderlich: bool = True  # NEU: Pflicht-Akzeptanz
    preisverhandlung_erlaubt: bool = False     # NEU: Preisverhandlung
```

**WICHTIG:** `verkaeufer_ids` und `kaeufer_ids` sind Listen! Nicht `verkaeufer_id` (singular) verwenden!

### Preisangebot (Zeile ~1325)
```python
class PreisangebotStatus(Enum):
    OFFEN = "Offen"
    ANGENOMMEN = "Angenommen"
    ABGELEHNT = "Abgelehnt"
    GEGENANGEBOT = "Gegenangebot"
    ZURUECKGEZOGEN = "Zurückgezogen"

@dataclass
class Preisangebot:
    angebot_id: str
    projekt_id: str
    von_user_id: str  # Wer das Angebot macht
    von_rolle: str    # "Käufer" oder "Verkäufer"
    betrag: float     # Angebotener Preis
    nachricht: str = ""
    status: str = PreisangebotStatus.OFFEN.value
    erstellt_am: datetime
    beantwortet_am: Optional[datetime] = None
```

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
    'preisangebote': Dict[str, Preisangebot],  # NEU: Preisverhandlung
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
    # Session-Persistenz
    'valid_tokens': Dict[str, str],  # email -> token
    # API-Keys (vom Notar konfigurierbar, aus st.secrets geladen)
    'api_keys': {'openai': str, 'anthropic': str},
    # Device Detection
    'device_type': str,  # mobile, tablet, desktop
    # NEU: Rechtsdokumente
    'rechtsdokument_akzeptanzen': Dict[str, Dict[str, Dict[str, Any]]],  # user_id -> notar_id -> doc_type -> {akzeptiert_am, version}
    'notar_rechtsdokumente': Dict[str, Dict[str, Dict]],  # notar_id -> doc_type -> {titel, inhalt, version, pflicht, ...}
    # NEU: Vertragsarchiv & Textbausteine (2025-12-08)
    'textbausteine': Dict[str, Textbaustein],      # baustein_id -> Textbaustein
    'vertragsdokumente': Dict[str, VertragsDokument],  # dokument_id -> VertragsDokument
    'vertragsvorlagen': Dict[str, VertragsVorlage],   # vorlage_id -> VertragsVorlage
    'vertragsentwuerfe': Dict[str, Vertragsentwurf],  # entwurf_id -> Vertragsentwurf
}
```

---

## Bekannte Issues / TODOs

### Offen
- [ ] Erinnerungs-E-Mail 1 Tag vor Termin (Cronjob/Scheduler nötig)
- [ ] Echte Outlook-Kalender-Integration (Microsoft Graph API)
- [ ] Echte E-Mail-Versendung (SMTP)
- [ ] PDF-Exposé-Generierung (reportlab/weasyprint)

### Verbesserungsvorschläge (NEU - 2025-12-06)
- [ ] **Preisübernahme:** Vereinbarter Preis automatisch als neuer kaufpreis im Projekt setzen
- [ ] **E-Mail-Benachrichtigungen:** Für Preisangebote, Rechtsdokument-Akzeptanz, Termine
- [ ] **Makler-Einsicht:** Preisverhandlungsverlauf für Makler lesend einsehbar
- [ ] **PDF-Export:** Handwerker-Steckbrief und Exposé als PDF (WeasyPrint/ReportLab)
- [ ] **Automatische Ablehnung:** Offene Angebote bei Kaufpreisänderung als "veraltet" markieren
- [ ] **Notar-Preisübersicht:** Tab für Preiseinigungen zur Beurkundungsvorbereitung
- [ ] **Handwerker-Bewertung:** Käufer können nach Abschluss Handwerker bewerten
- [ ] **Terminvorschlag nach Einigung:** Nach Preiseinigung automatischer Notartermin-Vorschlag

### Behoben (2025-12-06 - Aktuelle Session)
- [x] **Preisverhandlung:** Käufer/Verkäufer können Preise verhandeln (ohne Makler immer, mit Makler nur wenn erlaubt)
- [x] **Benachrichtigungen:** Bei Rechtsdokument-Akzeptanz (User + Notar)
- [x] **Druckfunktionen:** Handwerker-Steckbrief + Exposé als HTML downloadbar
- [x] **Demo-Modus Toggle:** In Notar-Einstellungen AN/AUS
- [x] **Optionale Rechtsdokument-Pflicht:** Makler kann pro Projekt entscheiden
- [x] **Umzug/Reinigung:** Neue Handwerker-Kategorien mit Demo-Daten
- [x] **Handwerker nicht sichtbar für Käufer:** → Filterung nach Notar + Demo-Daten
- [x] **Makler/Notar können keine Ausweise scannen:** → Neue Tabs in beiden Dashboards
- [x] **Keine Rechtsdokumente-Verwaltung:** → Notar-Tab mit Editor und Akzeptanz-Status
- [x] **Keine Pflicht-Akzeptanz:** → Käufer/Verkäufer müssen vor Dashboard-Zugang akzeptieren
- [x] **ICS Syntax-Fehler:** → beschreibung_ics Variable statt inline f-string

### Behoben (2025-12-06 - Frühere Session)
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
| (neu) | Add contract archive and text building blocks system (Vertragsarchiv) |
| d2eccfe | Implement improvement suggestions: price adoption, Makler view, ratings |
| 391643e | Fix: RangeError Invalid time value in Ausweis date parsing |
| 473ba6b | Add price negotiation, notifications, print functions, and demo mode |
| e6612d1 | Add financing/legal gating features for Käufer/Verkäufer |
| 1015ebd | Add session persistence and API key improvements |
| 6f8e544 | Fix AttributeError: projekt.verkaeufer_id changed to verkaeufer_ids |

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
4. **Hauptdatei:** `/home/user/blank-app-1/streamlit_app.py` (~11100 Zeilen)

### Wichtige Code-Bereiche zum Nachlesen:
- Session-Persistenz: Zeile ~1696-1820
- Login-Seite mit "Angemeldet bleiben": Zeile ~5319-5417
- Makler Ausweis-Erfassung: Zeile ~6227-6300
- Käufer-Dashboard (mit Pflicht-Akzeptanz): Zeile ~6421-6490
- Verkäufer-Dashboard (mit Pflicht-Akzeptanz): Zeile ~8123-8170
- Notar Rechtsdokumente: Zeile ~10649-10827
- Pflicht-Akzeptanz Funktionen: Zeile ~10830-10953
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
- **Datenschutzerklärung** = Privacy policy
- **AGB** = Terms and conditions (Allgemeine Geschäftsbedingungen)
- **Widerrufsbelehrung** = Cancellation policy
- **Pflicht-Akzeptanz** = Mandatory acceptance
