# Claude Code Memory File - Immobilien-Transaktionsplattform

**Letzte Aktualisierung:** 2025-12-05
**Branch:** `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt`
**Letzter Commit:** `f67cad0` - Add Käufer todo list with system-generated and custom tasks

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
├── streamlit_app.py      # Hauptanwendung (~8500+ Zeilen)
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
| TodoKategorie/TodoPrioritaet | ~214-228 | Enums für Käufer-Todos |
| KaeuferTodo | ~229-244 | Dataclass für Käufer-Aufgaben |
| HandwerkerKategorie | ~247-263 | Enum für Handwerker-Kategorien |
| IdeenKategorie | ~266-277 | Enum für Ideenboard-Kategorien |
| Handwerker | ~280-296 | Dataclass für Handwerker-Empfehlungen |
| IdeenboardEintrag | ~299-315 | Dataclass für Ideenboard-Einträge |
| Session State Init | ~830-856 | Inkl. kaeufer_todos, handwerker_empfehlungen, ideenboard |
| Dashboard-Suchfunktionen | ~934-1032 | render_dashboard_search(), search_matches(), filter_* |
| Käufer-Dashboard | ~4851-4914 | Mit 9 Tabs inkl. Aufgaben und Handwerker |
| kaeufer_handwerker_empfehlungen | ~4971-5036 | Handwerker-Ansicht für Käufer |
| generate_system_todos | ~5039-5112 | Generiert automatische Todos |
| kaeufer_aufgaben_view | ~5115-5149 | Aufgaben-Tab mit 4 Untertabs |
| render_ideenboard | ~5366-5487 | Ideenboard für kreative Ideen |
| kaeufer_finanzierungsrechner | ~5712-5999 | Umfassender Kreditrechner |
| Notar-Dashboard | ~7280-7335 | Mit 11 Tabs inkl. Handwerker |
| notar_handwerker_view | ~8105-8244 | Handwerker-Verwaltung für Notar |

---

## Implementierte Features

### Dashboard-Suche (NEU)
- [x] Suchleiste in allen 5 Dashboards (Makler, Käufer, Verkäufer, Finanzierer, Notar)
- [x] Wiederverwendbare `render_dashboard_search()` Komponente
- [x] `search_matches()` für flexible Feldsuche
- [x] `filter_projekte_by_search()` - Projekte filtern
- [x] `filter_dokumente_by_search()` - Dokumente filtern
- [x] `filter_angebote_by_search()` - Finanzierungsangebote filtern

### Käufer-Todoliste (NEU)
- [x] **System-generierte Todos** basierend auf Projekt-Status:
  - Finanzierung: Anfrage stellen, Wirtschaftsdaten hochladen, Angebote prüfen
  - Dokumente: Personalausweis erfassen
  - Kaufvertrag: Rechtsdokumente akzeptieren, Finanzierungszusage, Notartermin
- [x] **Eigene Todos** mit Titel, Beschreibung, Kategorie, Priorität, Fälligkeitsdatum
- [x] Kategorien: Finanzierung, Kaufvertrag, Dokumente, Ausstattung & Ideen, Umzug, Sonstiges
- [x] Prioritäten: Hoch (🔴), Mittel (🟡), Niedrig (🟢)
- [x] Überfällig-Warnung bei Fälligkeitsdatum
- [x] Erledigt-Status mit Toggle zum Reaktivieren
- [x] Gruppierung nach Kategorie, Sortierung nach Priorität

### Ideenboard für Käufer (NEU)
- [x] Kreative Ideen sammeln für neues Objekt
- [x] Kategorien: Einrichtung, Renovierung, Lichtkonzept, Küche, Bad, Garten, Smart Home, Farben, Böden
- [x] Geschätzte Kosten pro Idee
- [x] Inspirationsbilder per URL
- [x] Notizen zu jeder Idee
- [x] Als "umgesetzt" markieren
- [x] Filter nach Kategorie

### Handwerker-Empfehlungen (NEU)
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
```

---

## Letzte Commits

| Commit | Beschreibung |
|--------|--------------|
| (pending) | Add Ideenboard and Handwerker recommendations |
| f67cad0 | Add Käufer todo list with system-generated and custom tasks |
| eccc867 | Add search functionality to all dashboards |
| dacda13 | Add comprehensive financing module with calculator and invitation system |
| a4c5b16 | Add API key configuration to Notar dashboard |
| 6935b68 | Add AI Vision API support for Personalausweis OCR |

---

## Kontext für Fortsetzung

Bei Fortsetzung einer abgebrochenen Session:

1. **Branch prüfen:** `git branch` - sollte auf `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt` sein
2. **Letzten Stand prüfen:** `git log -3 --oneline`
3. **Diese Datei lesen:** `/home/user/blank-app-1/CLAUDE_MEMORY.md`
4. **Hauptdatei:** `/home/user/blank-app-1/streamlit_app.py` (~8500 Zeilen)

### Wichtige Code-Bereiche zum Nachlesen:
- Käufer-Todos: Zeile ~229-244 (Dataclass), ~5039-5350 (Funktionen)
- Ideenboard: Zeile ~299-315 (Dataclass), ~5366-5536 (Funktionen)
- Handwerker: Zeile ~280-296 (Dataclass), ~8105-8244 (Notar), ~4971-5036 (Käufer)
- Dashboard-Suche: Zeile ~934-1032

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
