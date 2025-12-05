# Claude Code Memory File - Immobilien-Transaktionsplattform

**Letzte Aktualisierung:** 2025-12-05
**Branch:** `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt`
**Letzter Commit:** `3a6b8ad` - Add financing/legal gating and Makler recommendation system

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
├── streamlit_app.py      # Hauptanwendung (~5500+ Zeilen)
├── requirements.txt      # Python-Abhängigkeiten
├── CLAUDE_MEMORY.md      # Diese Datei
└── .gitignore
```

---

## Haupt-Datei: streamlit_app.py

### Wichtige Zeilenbereiche (ungefähre Positionen)

| Bereich | Zeilen | Beschreibung |
|---------|--------|--------------|
| Imports & Enums | 1-100 | UserRole, ProjektStatus, PropertyType, NotificationType |
| User Dataclass | ~214-228 | Benutzer mit personal_daten und ausweis_foto |
| **PersonalDaten Dataclass** | ~230-263 | Ausweisdaten (Name, Geburt, Adresse, Ausweisnr, etc.) |
| TimelineEvent | ~265-275 | Timeline-Events |
| Projekt Dataclass | ~240-260 | Projekt mit termine-Liste |
| **TerminTyp/TerminStatus** | ~262-278 | Termin-Enums |
| **Termin Dataclass** | ~280-313 | Termin mit Bestätigungen, Outlook-Integration |
| **TerminVorschlag** | ~315-325 | Notar-Terminvorschläge |
| MaklerAgent/Profile | ~327-350 | Makler-Team |
| **ExposeData Dataclass** | ~352-450 | Exposé mit allen Feldern (Adresse, Nutzungsart, Ausstattung, Entfernungen, Vergleichsobjekte) |
| Session State Init | ~554-590 | init_session_state() mit termine, terminvorschlaege, notar_kalender |
| Demo Users | ~590-700 | create_demo_users(), create_demo_projekt() |
| simulate_ocr | ~720-740 | OCR-Simulation für Wirtschaftsdaten |
| **ocr_personalausweis** | ~741-800 | OCR für Personalausweis/Reisepass (pytesseract oder Simulation) |
| **simulate_personalausweis_ocr** | ~802-862 | Demo-Simulation für Ausweis-OCR |
| **parse_ausweis_ocr_text** | ~864-958 | Extrahiert strukturierte Daten aus OCR-Text |
| **render_ausweis_upload** | ~960-1148 | UI-Komponente für Ausweis-Upload und OCR |
| validate_address_online | ~1380-1425 | Nominatim/OpenStreetMap API Adressvalidierung |
| calculate_price_suggestion | ~1428-1491 | Kaufpreis-Vorschlag basierend auf Objektdaten |
| **TERMIN-FUNKTIONEN** | ~1434-2078 | Alle Termin-Verwaltungsfunktionen |
| render_expose_editor | ~2080-2500 | Exposé-Editor mit allen Feldern |
| makler_dashboard | ~2850-2895 | Makler-Hauptdashboard |
| makler_projekte_view | ~2911-3027 | Projekt-Verwaltung mit Exposé und Terminen |
| notar_dashboard | ~4439-4477 | Notar-Hauptdashboard |
| **notar_termine** | ~4888-5026 | Erweiterte Termin-Verwaltung mit Outlook-Kalender |

---

## Implementierte Features

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

### Sonstige Features
- [x] Financing Offers & Legal Document Gating
- [x] Wirtschaftsdaten-Upload für Käufer
- [x] Notar-Checklisten
- [x] Dokumenten-Anforderungen
- [x] Timeline mit Status-Tracking
- [x] Benachrichtigungssystem
- [x] Notar-Mitarbeiter-System

---

## Wichtige Funktionen

### Termin-Verwaltung

```python
# Termin-Vorschläge erstellen (Notar)
create_termin_vorschlaege(projekt_id, notar_id, termin_typ) -> TerminVorschlag

# Termin aus Vorschlag erstellen
create_termin_from_vorschlag(vorschlag, ausgewaehlter_index, projekt) -> Termin

# Termin bestätigen
bestatige_termin(termin_id, user_id, rolle) -> bool

# Bestätigungsstatus prüfen
check_termin_bestaetigung(termin, projekt) -> Dict

# ICS-Datei generieren
generate_ics_file(termin, projekt) -> str

# E-Mail senden (simuliert)
send_appointment_email(empfaenger, termin, projekt, email_typ)
```

### Exposé

```python
# Adresse validieren
validate_address_online(strasse, hausnummer, plz, ort, land) -> Dict

# Kaufpreis-Vorschlag berechnen
calculate_price_suggestion(expose) -> float

# Exposé-Editor rendern
render_expose_editor(projekt) -> None
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
    # Termin-Koordination
    'termine': Dict[str, Termin],
    'terminvorschlaege': Dict[str, TerminVorschlag],
    'notar_kalender': Dict,  # Simulierter Outlook-Kalender
}
```

---

## Bekannte Issues / TODOs

### Offen
- [ ] Erinnerungs-E-Mail 1 Tag vor Termin (Cronjob/Scheduler nötig)
- [ ] Echte Outlook-Kalender-Integration (Microsoft Graph API)
- [ ] Echte E-Mail-Versendung (SMTP)
- [ ] PDF-Exposé-Generierung (reportlab/weasyprint)
- [ ] Käufer/Verkäufer Dashboard Termin-Ansicht erweitern

### Behoben
- [x] Exposé-Buttons verschwinden nach Speichern (return True entfernt)
- [x] Exposé-Daten erst nach Kurzdaten möglich (jetzt direkt sichtbar)
- [x] Marktanalyse Links nicht klickbar (jetzt mit Markdown-Links)

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
| b449d60 | Add camera capture for mobile devices (iPhone, iPad, Android) |
| 0e445aa | Update memory file with OCR documentation |
| 594094c | Add Personalausweis OCR recognition for Käufer and Verkäufer |
| 047f451 | Add Claude memory file for session continuity |
| 5d76a3c | Add comprehensive appointment coordination system |
| 2194fc5 | Enhance Exposé editor with new features |

---

## Kontext für Fortsetzung

Bei Fortsetzung einer abgebrochenen Session:

1. **Branch prüfen:** `git branch` - sollte auf `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt` sein
2. **Letzten Stand prüfen:** `git log -3 --oneline`
3. **Diese Datei lesen:** `/home/user/blank-app-1/CLAUDE_MEMORY.md`
4. **Hauptdatei:** `/home/user/blank-app-1/streamlit_app.py` (~5500 Zeilen)

### Wichtige Code-Bereiche zum Nachlesen:
- ExposeData: Zeile ~352-450
- Termin Dataclass: Zeile ~280-313
- Termin-Funktionen: Zeile ~1434-2078
- Exposé-Editor: Zeile ~2080-2500
- Notar-Termine: Zeile ~4888-5026

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
