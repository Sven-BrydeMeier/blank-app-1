# Claude Code Memory File - Immobilien-Transaktionsplattform

**Letzte Aktualisierung:** 2025-12-05
**Branch:** `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt`
**Letzter Commit:** `956ba52` - Add comprehensive responsive design system for mobile, tablet and desktop

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
├── streamlit_app.py      # Hauptanwendung (~10000+ Zeilen)
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
| TodoKategorie/TodoPrioritaet | ~1120-1135 | Enums für Käufer-Todos |
| KaeuferTodo | ~1135-1150 | Dataclass für Käufer-Aufgaben |
| HandwerkerKategorie | ~1153-1170 | Enum für Handwerker-Kategorien |
| IdeenKategorie | ~1173-1184 | Enum für Ideenboard-Kategorien |
| Handwerker | ~1187-1203 | Dataclass für Handwerker-Empfehlungen |
| IdeenboardEintrag | ~1206-1222 | Dataclass für Ideenboard-Einträge |
| Session State Init | ~1737-1763 | Inkl. kaeufer_todos, handwerker_empfehlungen, ideenboard |
| **Ausweis-Upload (Vorder/Rückseite)** | ~2650-2990 | render_ausweis_upload mit 3 Tabs |
| Dashboard-Suchfunktionen | ~1840-1940 | render_dashboard_search(), search_matches(), filter_* |
| Käufer-Dashboard | ~5760-5820 | Mit 9 Tabs inkl. Aufgaben und Handwerker |
| Käufer-Aufgaben | ~5920-6250 | Todos, Ideenboard, System-Todos |
| Käufer-Finanzierungsrechner | ~6620-6910 | Umfassender Kreditrechner |
| Notar-Dashboard | ~8190-8250 | Mit 11 Tabs inkl. Handwerker und Einstellungen |
| Notar-Handwerker | ~9010-9150 | Handwerker-Verwaltung für Notar |
| main() | ~10011 | Hauptfunktion mit Responsive Design Injection |

---

## Implementierte Features

### Responsive Design System (NEU)
- [x] **DeviceType Enum** für Geräte-Kategorisierung (mobile, tablet, desktop)
- [x] **CSS Variablen** für konsistentes Design
- [x] **Dark Mode Support** via prefers-color-scheme
- [x] **Media Queries** für:
  - Mobile (< 768px): Volle Breite, Bottom-Navigation, Sticky Header
  - Tablet (768-1024px): 2-Spalten Grid, optimierte Sidebar
  - Desktop (> 1024px): 3-Spalten Grid, volle Features
- [x] **iOS Safe Area Support** für Notch/Home-Indicator
- [x] **Moderne UI-Komponenten:**
  - `render_mobile_header()` - App-Header mit Zurück/Menü
  - `render_mobile_nav()` - Bottom Navigation Bar
  - `render_quick_actions()` - Quick Action Buttons
  - `render_stat_cards()` - Statistik-Karten
  - `render_progress_steps()` - Fortschritts-Steps
  - `render_list_item()` - Listen-Einträge
  - `render_empty_state()` - Leere Zustände
  - `render_status_badge()` - Status-Badges
  - `render_avatar()` - Avatar-Komponente
- [x] **Device Detection** via JavaScript

### Personalausweis-Erfassung mit Vorder- und Rückseite (NEU)
- [x] **3-Tab-Layout:** Vorderseite, Rückseite, Daten übernehmen
- [x] **Fortschrittsanzeige:** Zeigt welche Seiten erfasst wurden
- [x] **OCR für beide Seiten:**
  - Vorderseite: Vorname, Nachname, Geburtsort, Geburtsdatum
  - Rückseite: Adresse, Ausweisnummer, Ablaufdatum
- [x] **Daten-Kombination:** Zusammenführung beider OCR-Ergebnisse
- [x] **Kamera oder Datei-Upload** für jede Seite
- [x] **Verfügbar für Käufer und Verkäufer**

### Dashboard-Suche
- [x] Suchleiste in allen 5 Dashboards (Makler, Käufer, Verkäufer, Finanzierer, Notar)
- [x] Wiederverwendbare `render_dashboard_search()` Komponente
- [x] `search_matches()` für flexible Feldsuche
- [x] `filter_projekte_by_search()` - Projekte filtern
- [x] `filter_dokumente_by_search()` - Dokumente filtern
- [x] `filter_angebote_by_search()` - Finanzierungsangebote filtern

### Käufer-Todoliste
- [x] **System-generierte Todos** basierend auf Projekt-Status:
  - Finanzierung: Anfrage stellen, Wirtschaftsdaten hochladen, Angebote prüfen
  - Dokumente: Personalausweis erfassen
  - Kaufvertrag: Rechtsdokumente akzeptieren, Finanzierungszusage, Notartermin
- [x] **Eigene Todos** mit Titel, Beschreibung, Kategorie, Priorität, Fälligkeitsdatum
- [x] Kategorien: Finanzierung, Kaufvertrag, Dokumente, Ausstattung & Ideen, Umzug, Sonstiges
- [x] Prioritäten: Hoch, Mittel, Niedrig
- [x] Überfällig-Warnung bei Fälligkeitsdatum
- [x] Erledigt-Status mit Toggle zum Reaktivieren
- [x] Gruppierung nach Kategorie, Sortierung nach Priorität

### Ideenboard für Käufer
- [x] Kreative Ideen sammeln für neues Objekt
- [x] Kategorien: Einrichtung, Renovierung, Lichtkonzept, Küche, Bad, Garten, Smart Home, Farben, Böden
- [x] Geschätzte Kosten pro Idee
- [x] Inspirationsbilder per URL
- [x] Notizen zu jeder Idee
- [x] Als "umgesetzt" markieren
- [x] Filter nach Kategorie

### Handwerker-Empfehlungen
- [x] **Notar**: Handwerker anlegen mit vollständigen Kontaktdaten
  - Kategorien: Elektriker, Sanitär, Maler, Tischler, Bodenleger, Fliesenleger, etc.
  - Bewertung (1-5 Sterne)
  - Beschreibung & interne Notizen
  - Freigabe/Deaktivierung
- [x] **Käufer**: Vom Notar empfohlene Handwerker einsehen
  - Nur freigegebene Handwerker sichtbar
  - Filter nach Kategorie
  - Kontaktdaten und Webseite

### Exposé-System
- [x] ExposeData Dataclass mit ~50 Feldern
- [x] Adressfelder (Straße, Hausnummer, PLZ, Ort, Land)
- [x] Adressvalidierung via Nominatim/OpenStreetMap API
- [x] Nutzungsart (Ferienvermietung, Dauerwohnen, Zweitwohnung) mit Ja/Nein/Keine Angabe
- [x] Ausstattungsmerkmale (Balkon, Terrasse, Garage, Tiefgarage, Sauna, Schwimmbad, Fahrstuhl, Meerblick, Bergblick, Seeblick, etc.)
- [x] Entfernungen (Strand, Zentrum, Stadt, Supermarkt, Arzt, Flughafen)
- [x] Kaufpreis-Vorschlag basierend auf Objektdaten
- [x] Marktanalyse mit klickbaren Vergleichsobjekt-Links
- [x] Web-Exposé Vorschau (HTML)
- [x] Exposé-Editor direkt sichtbar (ohne Toggle-Button)

### Termin-Koordination
- [x] Termin und TerminVorschlag Dataclasses
- [x] TerminTyp: Besichtigung, Übergabe, Beurkundung, Sonstiges
- [x] TerminStatus: Vorgeschlagen, Angefragt, Ausstehend, Teilweise bestätigt, Bestätigt, Abgesagt, Abgeschlossen
- [x] Termin-Verwaltung in Makler-Dashboard (Tabs für jeden Termintyp)
- [x] Notar Outlook-Kalender-Integration (simuliert)
- [x] 3 automatische Terminvorschläge vom Notar
- [x] Kaufvertragsentwurf-Status-Check vor Beurkundungsterminen
- [x] Bestätigungs-Workflow für alle Parteien
- [x] E-Mail-Benachrichtigungen (simuliert)
- [x] ICS-Kalenderdatei-Export (Google, Apple, Outlook)
- [x] Grünes Lämpchen bei bestätigten Terminen

### Personalausweis-Erfassung (OCR)
- [x] PersonalDaten Dataclass für Ausweisdaten
- [x] OCR mit pytesseract (oder Simulation als Fallback)
- [x] **AI Vision OCR** mit OpenAI GPT-4 Vision API
- [x] API-Key Konfiguration im Notar-Dashboard
- [x] Regex-Parser für deutsche Ausweisdaten
- [x] **Kamera-Aufnahme für Mobilgeräte** (st.camera_input)
- [x] Datei-Upload als Alternative
- [x] Bearbeitbares Formular nach OCR
- [x] Validierung (Pflichtfelder, Ablaufdatum)
- [x] Integration in Käufer- und Verkäufer-Dashboard
- [x] **Vorder- und Rückseite** separat erfassen

### Makler-Empfehlungssystem
- [x] MaklerEmpfehlung Dataclass für Einladungen
- [x] MaklerEmpfehlungStatus Enum (Eingeladen, Daten eingegeben, Freigegeben, Abgelehnt, Deaktiviert)
- [x] Notar: Makler per E-Mail einladen mit Onboarding-Token
- [x] Notar: Makler freigeben/ablehnen/deaktivieren
- [x] Verkäufer: "Makler finden" Tab mit freigegebenen Maklern
- [x] Verkäufer: Filter nach Region und Spezialisierung
- [x] Verkäufer: Kontaktformular für Makleranfragen
- [x] Makler-Onboarding-Seite via URL-Token (?token=xxx)
- [x] Makler: Eingabe von Bürodaten, Konditionen, AGB, Widerrufsbelehrung

### API-Key Konfiguration (Notar-Dashboard)
- [x] Neuer Tab "Einstellungen" im Notar-Dashboard
- [x] OpenAI API-Key eingeben und speichern
- [x] Anthropic API-Key eingeben und speichern
- [x] Status-Anzeige für konfigurierte API-Keys
- [x] OCR-Funktionen prüfen zuerst Session State, dann Secrets, dann Umgebungsvariablen

### Erweitertes Finanzierungsmodul (Käufer)
- [x] Finanzierung anfragen Tab mit Kaufpreis/Eigenkapital-Eingabe
- [x] Finanzierer per E-Mail einladen mit Onboarding-Token
- [x] Dokumente-Zugriff von Verkäufer/Makler/Notar
- [x] Wirtschaftsdaten-Upload für Finanzierer freigeben
- [x] Umfassender Kreditrechner mit Tilgungsplan
  - Finanzierungsbetrag, Eigenkapital, Zinssatz
  - Tilgung als Prozent oder monatlicher Betrag
  - Sondertilgung (Prozent p.a. oder Festbetrag, jährlich/monatlich)
  - Volltilger-Darlehen Option
  - Sollzinsbindung
  - Monatliche/Jährliche Tilgungsplan-Anzeige
  - Restschuld nach Laufzeit

### Erweitertes Finanzierungsmodul (Finanzierer)
- [x] Mehrere Angebote pro Projekt erstellen
- [x] Produktname für Angebote
- [x] Befristung mit Gültigkeitsdatum
- [x] Automatisches Löschen nach Ablauf (optional)
- [x] Sondertilgung, Effektivzins, Bereitstellungszeit
- [x] Angebote zurückziehen und reaktivieren
- [x] Angebote löschen
- [x] Status-Tracking (Gesendet, Entwurf, Angenommen, Zurückgezogen, Abgelaufen)

### Sonstige Features
- [x] Financing Offers & Legal Document Gating
- [x] Wirtschaftsdaten-Upload für Käufer
- [x] Notar-Checklisten
- [x] Dokumenten-Anforderungen
- [x] Timeline mit Status-Tracking
- [x] Benachrichtigungssystem
- [x] Notar-Mitarbeiter-System

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
    'comments': Dict,
    'invitations': Dict,
    'timeline_events': Dict[str, TimelineEvent],
    'makler_profiles': Dict,
    'expose_data': Dict[str, ExposeData],
    'document_requests': Dict,
    'notar_checklists': Dict,
    'bank_folders': Dict,
    'notar_mitarbeiter': Dict,
    'verkaeufer_dokumente': Dict,
    'makler_empfehlungen': Dict,  # Makler-Empfehlungssystem
    # Termin-Koordination
    'termine': Dict[str, Termin],
    'terminvorschlaege': Dict[str, TerminVorschlag],
    'notar_kalender': Dict,  # Simulierter Outlook-Kalender
    # Finanzierung
    'finanzierer_einladungen': Dict,  # Einladungen für Finanzierer
    'finanzierungsanfragen': Dict,  # Anfragen vom Käufer
    # Käufer-Features
    'kaeufer_todos': Dict[str, KaeuferTodo],  # Todo-Liste
    'handwerker_empfehlungen': Dict[str, Handwerker],  # Vom Notar verwaltet
    'ideenboard': Dict[str, IdeenboardEintrag],  # Kreative Ideen
    # API-Keys (vom Notar konfigurierbar)
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

### Behoben
- [x] Exposé-Buttons verschwinden nach Speichern (return True entfernt)
- [x] Exposé-Daten erst nach Kurzdaten möglich (jetzt direkt sichtbar)
- [x] Marktanalyse Links nicht klickbar (jetzt mit Markdown-Links)
- [x] Dashboard-Suche implementiert
- [x] Features nicht sichtbar nach Deploy (Branch-Mismatch behoben)

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
| 956ba52 | Add comprehensive responsive design system for mobile, tablet and desktop |
| 219ed33 | Add front and back ID card upload with OCR combination |
| 5aee548 | Add Ideenboard and Handwerker recommendations for Käufer |
| f67cad0 | Add Käufer todo list with system-generated and custom tasks |
| eccc867 | Add search functionality to all dashboards |
| dacda13 | Add comprehensive financing module with calculator and invitation system |
| a4c5b16 | Add API key configuration to Notar dashboard |
| 6935b68 | Add AI Vision API support for Personalausweis OCR |

---

## Deployment-Hinweis

**WICHTIG:** Streamlit Cloud deployed von `main` Branch!

Nach jedem Push auf den Feature-Branch muss der User:
1. Auf GitHub gehen
2. Pull Request erstellen: Feature-Branch -> main
3. PR mergen (Merge oder Squash)
4. Streamlit App redeployen oder warten (auto-redeploy)

---

## Kontext für Fortsetzung

Bei Fortsetzung einer abgebrochenen Session:

1. **Branch prüfen:** `git branch` - sollte auf `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt` sein
2. **Letzten Stand prüfen:** `git log -3 --oneline`
3. **Diese Datei lesen:** `/home/user/blank-app-1/CLAUDE_MEMORY.md`
4. **Hauptdatei:** `/home/user/blank-app-1/streamlit_app.py` (~10000 Zeilen)

### Wichtige Code-Bereiche zum Nachlesen:
- Responsive Design: Zeile ~19-920
- Ausweis-Upload (Vorder/Rückseite): Zeile ~2650-2990
- Käufer-Todos: Zeile ~1135-1150 (Dataclass), ~5920-6250 (Funktionen)
- Ideenboard: Zeile ~1206-1222 (Dataclass), ~6270-6440 (Funktionen)
- Handwerker: Zeile ~1187-1203 (Dataclass), ~9010-9150 (Notar), ~5880-5920 (Käufer)
- Dashboard-Suche: Zeile ~1840-1940

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
