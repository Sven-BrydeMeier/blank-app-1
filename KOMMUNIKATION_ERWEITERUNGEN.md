# Vorschläge für Kommunikations-Erweiterungen

**Erstellt:** 2025-12-12
**Status:** Planungsphase

---

## Übersicht der geplanten Erweiterungen

1. [Kommunikationszentrale](#1-kommunikationszentrale)
2. [Intelligente Ordnerstruktur](#2-intelligente-ordnerstruktur)
3. [Such-, Filter- und Sortierfunktionen](#3-such--filter--und-sortierfunktionen)
4. [Sichere Kommunikation](#4-sichere-kommunikation)
5. [Briefkopf-Administration](#5-briefkopf-administration)
6. [E-Mail-Signaturen](#6-e-mail-signaturen)
7. [Makler-Mitarbeiterverwaltung](#7-makler-mitarbeiterverwaltung)

---

## 1. Kommunikationszentrale

### 1.1 Zentraler Posteingang pro Rolle

```
📬 Kommunikationszentrale
├── 📥 Posteingang
│   ├── Ungelesen (Badge mit Anzahl)
│   ├── Wichtig / Markiert
│   └── Alle Nachrichten
├── 📤 Postausgang
│   ├── Gesendet
│   └── Entwürfe
├── 📎 Anlagen
│   ├── Nach Projekt sortiert
│   ├── Nach Typ (PDF, Bild, Dokument)
│   └── Nach Datum
└── 🗂️ Archiv
```

### 1.2 Nachrichten-Struktur

| Feld | Beschreibung |
|------|--------------|
| `nachricht_id` | Eindeutige ID |
| `projekt_id` | Zugehöriges Projekt |
| `absender_id` | Sender |
| `empfaenger_ids` | Liste der Empfänger |
| `betreff` | Betreffzeile |
| `inhalt` | Nachrichtentext (HTML/Markdown) |
| `anlagen` | Liste von Anlage-IDs |
| `prioritaet` | Normal, Hoch, Dringend |
| `kategorie` | Anfrage, Information, Dokument, Termin |
| `gelesen_von` | Liste der User-IDs die gelesen haben |
| `ist_vertraulich` | Boolean für sensible Inhalte |
| `erstellt_am` | Timestamp |
| `aktenzeichen` | Verknüpfung zur Akte |

### 1.3 Anlagen-Verwaltung (gesondert)

```python
@dataclass
class KommunikationsAnlage:
    anlage_id: str
    nachricht_id: str
    projekt_id: str
    dateiname: str
    dateityp: str  # PDF, DOCX, JPG, etc.
    dateigroesse: int
    hochgeladen_von: str
    hochgeladen_am: datetime
    beschreibung: str = ""
    ist_vertraulich: bool = False
    ordner_pfad: str = ""  # z.B. "/Kaufvertrag/Entwürfe"
```

**Anlagen-Ansicht:**
- Separate Liste aller Anlagen eines Projekts
- Gruppierung nach Kommunikation oder nach Typ
- Vorschau-Funktion für PDFs und Bilder
- Download einzeln oder als ZIP

---

## 2. Intelligente Ordnerstruktur

### 2.1 Notar-Aktenstruktur

```
📁 Akte: 123/2025 Müller / Schmidt
├── 📂 01_Stammdaten
│   ├── Personalausweise
│   ├── Handelsregisterauszüge
│   └── Vollmachten
├── 📂 02_Kaufgegenstand
│   ├── Grundbuchauszug
│   ├── Flurkarte
│   ├── Baulastenverzeichnis
│   └── Exposé
├── 📂 03_Finanzierung
│   ├── Finanzierungsbestätigung
│   ├── Grundschuldbestellung
│   └── Bankkorrespondenz
├── 📂 04_Vertragsentwürfe
│   ├── Entwurf_V1.pdf
│   ├── Entwurf_V2_mit_Änderungen.pdf
│   └── Finale_Version.pdf
├── 📂 05_Korrespondenz
│   ├── Eingehend/
│   │   ├── 2025-01-15_Makler_Anfrage.pdf
│   │   └── 2025-01-20_Käufer_Rückfrage.pdf
│   └── Ausgehend/
│       ├── 2025-01-16_An_Makler.pdf
│       └── 2025-01-22_An_Käufer.pdf
├── 📂 06_Beurkundung
│   ├── Beurkundungsprotokoll
│   └── Unterschriebener_Vertrag
├── 📂 07_Vollzug
│   ├── Grundbuchanmeldung
│   ├── Finanzamtsmeldung
│   └── Fälligkeitsmitteilung
└── 📂 08_Abrechnung
    ├── Kostenrechnung
    └── Zahlungseingang
```

### 2.2 Ordner-Templates pro Aktentyp

| Aktentyp | Standard-Ordner |
|----------|-----------------|
| **Kaufvertrag** | Stammdaten, Kaufgegenstand, Finanzierung, Entwürfe, Korrespondenz, Beurkundung, Vollzug, Abrechnung |
| **Testament** | Stammdaten, Verfügungen, Entwürfe, Korrespondenz, Beurkundung, Verwahrung |
| **Gesellschaftsgründung** | Stammdaten, Gesellschaftsvertrag, Handelsregister, Korrespondenz, Beurkundung |
| **Erbvertrag** | Stammdaten, Vermögensübersicht, Entwürfe, Korrespondenz, Beurkundung |

### 2.3 Automatische Einordnung

```python
DOKUMENT_ZUORDNUNG = {
    "Personalausweis": "01_Stammdaten",
    "Reisepass": "01_Stammdaten",
    "Handelsregisterauszug": "01_Stammdaten",
    "Grundbuchauszug": "02_Kaufgegenstand",
    "Flurkarte": "02_Kaufgegenstand",
    "Finanzierungsbestätigung": "03_Finanzierung",
    "Kaufvertrag": "04_Vertragsentwürfe",
    # ... weitere Zuordnungen
}
```

---

## 3. Such-, Filter- und Sortierfunktionen

### 3.1 Globale Suche

```
🔍 Suche: [________________________] [Suchen]

Suchergebnisse in:
☑️ Akten          ☑️ Nachrichten    ☑️ Dokumente
☑️ Projekte       ☑️ Personen       ☑️ Notizen
```

### 3.2 Erweiterte Filteroptionen

| Filter | Optionen |
|--------|----------|
| **Zeitraum** | Heute, Diese Woche, Dieser Monat, Benutzerdefiniert |
| **Status** | Offen, In Bearbeitung, Abgeschlossen, Archiviert |
| **Priorität** | Normal, Hoch, Dringend |
| **Absender/Empfänger** | Dropdown mit allen Beteiligten |
| **Dokumenttyp** | PDF, Word, Bild, E-Mail, Sonstige |
| **Projekt** | Dropdown aller Projekte |
| **Aktenzeichen** | Texteingabe mit Autovervollständigung |
| **Vertraulichkeit** | Alle, Nur vertrauliche, Nur öffentliche |

### 3.3 Sortieroptionen

```
Sortieren nach: [Datum ▼]  [Aufsteigend ○ Absteigend ●]

Optionen:
- Datum (Neueste/Älteste zuerst)
- Absender (A-Z / Z-A)
- Betreff (A-Z / Z-A)
- Priorität (Höchste/Niedrigste zuerst)
- Aktenzeichen
- Projekt
- Ungelesen zuerst
```

### 3.4 Gespeicherte Suchen

```python
@dataclass
class GespeicherteSuche:
    suche_id: str
    user_id: str
    name: str  # z.B. "Offene Kaufverträge 2025"
    filter_kriterien: Dict
    sortierung: str
    erstellt_am: datetime
    ist_standard: bool = False  # Als Standard-Ansicht
```

---

## 4. Sichere Kommunikation

### 4.1 Sicherheitsstufen

| Stufe | Symbol | Beschreibung | Maßnahmen |
|-------|--------|--------------|-----------|
| **Öffentlich** | 🟢 | Allgemeine Informationen | Standard-Verschlüsselung |
| **Intern** | 🟡 | Projektbezogene Daten | + Zugriffsbeschränkung |
| **Vertraulich** | 🟠 | Sensible persönliche Daten | + Logging, keine Weiterleitung |
| **Streng vertraulich** | 🔴 | Rechtlich geschützt | + Wasserzeichen, Ablaufdatum |

### 4.2 Sicherheits-Features

```python
@dataclass
class SicherheitEinstellungen:
    # Verschlüsselung
    verschluesselung_aktiv: bool = True
    verschluesselungs_methode: str = "AES-256"

    # Zugriffskontrolle
    zwei_faktor_auth: bool = False
    session_timeout_minuten: int = 30
    max_login_versuche: int = 5

    # Audit
    audit_logging: bool = True
    zugriffe_protokollieren: bool = True

    # Dokumente
    wasserzeichen_bei_download: bool = True
    ablaufdatum_fuer_links: int = 7  # Tage
    download_bestaetigung: bool = True
```

### 4.3 Audit-Trail

```
📋 Aktivitätsprotokoll - Akte 123/2025

| Datum/Zeit | Benutzer | Aktion | Details |
|------------|----------|--------|---------|
| 12.12.25 14:32 | Notar Schmidt | Dokument angesehen | Kaufvertrag_V2.pdf |
| 12.12.25 14:30 | Käufer Müller | Nachricht gesendet | Betreff: Rückfrage... |
| 12.12.25 10:15 | Makler Weber | Dokument hochgeladen | Exposé.pdf |
```

---

## 5. Briefkopf-Administration

### 5.1 Briefkopf-Struktur

```python
@dataclass
class Briefkopf:
    briefkopf_id: str
    inhaber_id: str  # User oder Firma
    inhaber_typ: str  # "user", "firma", "kanzlei"

    # Logo
    logo_data: bytes = None
    logo_position: str = "links"  # links, rechts, zentriert
    logo_groesse: int = 100  # Pixel Höhe

    # Kopfdaten
    firmenname: str = ""
    zusatz: str = ""  # z.B. "Notariat", "Immobilienmakler"
    inhaber_name: str = ""

    # Adresse
    strasse: str = ""
    plz: str = ""
    ort: str = ""
    land: str = "Deutschland"

    # Kontakt
    telefon: str = ""
    fax: str = ""
    email: str = ""
    website: str = ""

    # Rechtliches
    steuernummer: str = ""
    ust_id: str = ""
    handelsregister: str = ""

    # Bankverbindung
    bank_name: str = ""
    iban: str = ""
    bic: str = ""

    # Design
    schriftart: str = "Arial"
    primaerfarbe: str = "#000000"
    sekundaerfarbe: str = "#666666"

    # Fußzeile
    fusszeile_text: str = ""
    fusszeile_zeile2: str = ""

    ist_aktiv: bool = True
    erstellt_am: datetime = field(default_factory=datetime.now)
```

### 5.2 Briefkopf-Vorschau

```
┌─────────────────────────────────────────────────────────────┐
│  [LOGO]     Notariat Dr. Schmidt                            │
│             Rechtsanwalt und Notar                          │
│                                                             │
│             Musterstraße 123 · 12345 Musterstadt            │
│             Tel: 0123-456789 · Fax: 0123-456780             │
│             E-Mail: kanzlei@notar-schmidt.de                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [DOKUMENTINHALT]                                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Bankverbindung: Sparkasse Musterstadt                      │
│  IBAN: DE89 3704 0044 0532 0130 00 · BIC: COBADEFFXXX       │
│  Steuernummer: 123/456/78901 · USt-IdNr.: DE123456789       │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Administration in Einstellungen

```
⚙️ Einstellungen > 📝 Briefkopf

┌─ Briefkopf-Verwaltung ─────────────────────────────────────┐
│                                                            │
│  🖼️ Logo hochladen: [Datei auswählen] [Hochladen]          │
│  Position: ○ Links  ● Rechts  ○ Zentriert                  │
│                                                            │
│  ─── Firmendaten ───                                       │
│  Firmenname:    [Notariat Dr. Schmidt____________]         │
│  Zusatz:        [Rechtsanwalt und Notar__________]         │
│  Inhaber:       [Dr. Max Schmidt_________________]         │
│                                                            │
│  ─── Adresse ───                                           │
│  Straße:        [Musterstraße 123________________]         │
│  PLZ/Ort:       [12345] [Musterstadt_____________]         │
│                                                            │
│  ─── Kontakt ───                                           │
│  Telefon:       [0123-456789____] Fax: [0123-456780]       │
│  E-Mail:        [kanzlei@notar-schmidt.de________]         │
│  Website:       [www.notar-schmidt.de____________]         │
│                                                            │
│  [💾 Speichern]  [👁️ Vorschau]  [📄 Test-PDF]              │
└────────────────────────────────────────────────────────────┘
```

---

## 6. E-Mail-Signaturen

### 6.1 Signatur-Struktur

```python
@dataclass
class EmailSignatur:
    signatur_id: str
    user_id: str
    name: str  # z.B. "Standard", "Formal", "Kurz"

    # Inhalt
    text_signatur: str  # Plaintext-Version
    html_signatur: str  # HTML-Version mit Formatierung

    # Optionen
    bild_einbetten: bool = True
    visitenkarte_anhaengen: bool = False

    # Verwendung
    ist_standard: bool = False
    fuer_neue_nachrichten: bool = True
    fuer_antworten: bool = True

    erstellt_am: datetime = field(default_factory=datetime.now)
```

### 6.2 Signatur-Editor

```
✉️ E-Mail-Signaturen

┌─ Meine Signaturen ──────────────────────────────────────────┐
│                                                             │
│  [+ Neue Signatur]                                          │
│                                                             │
│  ☑️ Standard-Signatur (wird automatisch verwendet)          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Mit freundlichen Grüßen                             │    │
│  │                                                     │    │
│  │ Dr. Max Schmidt                                     │    │
│  │ Notar                                               │    │
│  │                                                     │    │
│  │ Notariat Dr. Schmidt                                │    │
│  │ Musterstraße 123, 12345 Musterstadt                 │    │
│  │ Tel: 0123-456789 | Fax: 0123-456780                 │    │
│  │ E-Mail: m.schmidt@notar-schmidt.de                  │    │
│  │                                                     │    │
│  │ Diese E-Mail kann vertrauliche Informationen       │    │
│  │ enthalten. Sollten Sie nicht der beabsichtigte...  │    │
│  └─────────────────────────────────────────────────────┘    │
│  [✏️ Bearbeiten]  [📋 Duplizieren]  [🗑️ Löschen]            │
│                                                             │
│  ○ Kurz-Signatur                                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ MfG, Dr. Schmidt | Notar | Tel: 0123-456789         │    │
│  └─────────────────────────────────────────────────────┘    │
│  [✏️ Bearbeiten]  [📋 Duplizieren]  [🗑️ Löschen]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─ Mitarbeiter-Signaturen verwalten ──────────────────────────┐
│  (Nur für Kanzlei-/Firmeninhaber)                           │
│                                                             │
│  Mitarbeiter: [Frau Müller (Sekretariat) ▼]                 │
│                                                             │
│  ☑️ Darf eigene Signaturen erstellen                        │
│  ☑️ Muss Kanzlei-Briefkopf verwenden                        │
│  ☐ Kann im Namen des Notars signieren                       │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Variablen für Signaturen

```
Verfügbare Platzhalter:
{{name}}           - Vollständiger Name
{{vorname}}        - Vorname
{{nachname}}       - Nachname
{{titel}}          - Titel (Dr., Prof., etc.)
{{position}}       - Position/Rolle
{{telefon}}        - Telefonnummer
{{email}}          - E-Mail-Adresse
{{firma}}          - Firmenname
{{adresse}}        - Vollständige Adresse
{{datum}}          - Aktuelles Datum
{{projekt}}        - Aktueller Projektname (falls im Kontext)
{{aktenzeichen}}   - Aktenzeichen (falls im Kontext)
```

---

## 7. Makler-Mitarbeiterverwaltung

### 7.1 Mitarbeiter-Struktur

```python
@dataclass
class MaklerMitarbeiter:
    mitarbeiter_id: str
    makler_id: str  # Büro-Inhaber
    user_id: str    # Verknüpfter User-Account

    # Persönliche Daten
    name: str
    vorname: str
    email: str
    telefon: str = ""

    # Rolle und Berechtigungen
    rolle: str = "Mitarbeiter"  # Mitarbeiter, Teamleiter, Partner
    berechtigungen: List[str] = field(default_factory=list)

    # Projektzuordnung
    projekt_ids: List[str] = field(default_factory=list)
    kann_alle_projekte_sehen: bool = False

    # Status
    ist_aktiv: bool = True
    eingestellt_am: datetime = field(default_factory=datetime.now)

    # Kommunikation
    kann_im_namen_kommunizieren: bool = False  # Im Namen des Maklers
    eigene_signatur: bool = True
```

### 7.2 Berechtigungssystem

```python
class MaklerBerechtigung(Enum):
    # Projekte
    PROJEKTE_ANSEHEN = "Projekte ansehen"
    PROJEKTE_ERSTELLEN = "Projekte erstellen"
    PROJEKTE_BEARBEITEN = "Projekte bearbeiten"
    PROJEKTE_LOESCHEN = "Projekte löschen"

    # Kommunikation
    NACHRICHTEN_SENDEN = "Nachrichten senden"
    NACHRICHTEN_LESEN = "Alle Nachrichten lesen"
    IM_NAMEN_KOMMUNIZIEREN = "Im Namen des Maklers kommunizieren"

    # Dokumente
    DOKUMENTE_HOCHLADEN = "Dokumente hochladen"
    DOKUMENTE_LOESCHEN = "Dokumente löschen"
    EXPOSE_ERSTELLEN = "Exposés erstellen"

    # Teilnehmer
    TEILNEHMER_EINLADEN = "Teilnehmer einladen"
    TEILNEHMER_VERWALTEN = "Teilnehmer verwalten"

    # Termine
    TERMINE_ERSTELLEN = "Termine erstellen"
    TERMINE_BESTAETIGEN = "Termine bestätigen"

    # Finanzen
    PREISE_SEHEN = "Preise sehen"
    PREISE_VERHANDELN = "Preisverhandlungen führen"

    # Administration
    MITARBEITER_VERWALTEN = "Mitarbeiter verwalten"
    EINSTELLUNGEN_AENDERN = "Einstellungen ändern"
```

### 7.3 Mitarbeiter-Dashboard (Makler-Einstellungen)

```
⚙️ Einstellungen > 👥 Mitarbeiter

┌─ Mitarbeiter-Übersicht ─────────────────────────────────────┐
│                                                             │
│  [+ Neuen Mitarbeiter hinzufügen]                           │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 👤 Anna Weber                                          │ │
│  │    Rolle: Teamleiterin | Status: ✅ Aktiv              │ │
│  │    E-Mail: a.weber@makler-schmidt.de                   │ │
│  │    Zugewiesene Projekte: 5                             │ │
│  │    [✏️ Bearbeiten] [📋 Projekte] [🔑 Rechte] [🗑️]      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 👤 Thomas Müller                                       │ │
│  │    Rolle: Mitarbeiter | Status: ✅ Aktiv               │ │
│  │    E-Mail: t.mueller@makler-schmidt.de                 │ │
│  │    Zugewiesene Projekte: 3                             │ │
│  │    [✏️ Bearbeiten] [📋 Projekte] [🔑 Rechte] [🗑️]      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─ Neuen Mitarbeiter hinzufügen ──────────────────────────────┐
│                                                             │
│  Name:      [________________] Vorname: [________________]  │
│  E-Mail:    [________________________________]              │
│  Telefon:   [________________]                              │
│                                                             │
│  Rolle:     [Mitarbeiter ▼]                                 │
│             ○ Mitarbeiter - Standardrechte                  │
│             ○ Teamleiter - Erweiterte Rechte                │
│             ○ Partner - Volle Rechte                        │
│                                                             │
│  ─── Berechtigungen ───                                     │
│  ☑️ Projekte ansehen                                        │
│  ☑️ Projekte bearbeiten                                     │
│  ☐ Projekte erstellen                                       │
│  ☑️ Nachrichten senden                                      │
│  ☐ Im Namen des Maklers kommunizieren                       │
│  ☑️ Dokumente hochladen                                     │
│  ☑️ Teilnehmer einladen                                     │
│  ☑️ Termine erstellen                                       │
│  ☐ Preisverhandlungen führen                                │
│                                                             │
│  [📧 Einladung senden]  [❌ Abbrechen]                       │
└─────────────────────────────────────────────────────────────┘
```

### 7.4 Projekt-Zuweisung

```
📋 Projekte > Mitarbeiter zuweisen

┌─ Projekt: Musterwohnung München ────────────────────────────┐
│                                                             │
│  Hauptverantwortlicher: [Max Makler (Inhaber) ▼]            │
│                                                             │
│  Zugewiesene Mitarbeiter:                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ ☑️ Anna Weber (Teamleiterin)                        │    │
│  │    Rolle im Projekt: [Projektleitung ▼]             │    │
│  │    Benachrichtigungen: ☑️ Alle  ☐ Nur wichtige      │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ ☑️ Thomas Müller (Mitarbeiter)                      │    │
│  │    Rolle im Projekt: [Assistenz ▼]                  │    │
│  │    Benachrichtigungen: ☐ Alle  ☑️ Nur wichtige      │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ ☐ Lisa Schmidt (Mitarbeiter)                        │    │
│  │    (Nicht zugewiesen)                               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  [💾 Speichern]                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementierungsreihenfolge (Vorschlag)

### Phase 1: Grundlagen (Priorität: Hoch)
1. ✅ Briefkopf-Datenstruktur und Administration
2. ✅ E-Mail-Signaturen für alle Benutzer
3. ✅ Makler-Mitarbeiterverwaltung

### Phase 2: Kommunikation (Priorität: Hoch)
4. ✅ Erweiterte Nachrichten-Struktur mit Anlagen
5. ✅ Kommunikationszentrale mit Posteingang/Postausgang
6. ✅ Anlagen-Verwaltung (gesonderte Ansicht)

### Phase 3: Organisation (Priorität: Mittel)
7. ✅ Intelligente Ordnerstruktur für Notar-Akten
8. ✅ Ordner-Templates pro Aktentyp
9. ✅ Automatische Dokumenten-Einordnung

### Phase 4: Suche & Filter (Priorität: Mittel)
10. ✅ Globale Suchfunktion
11. ✅ Erweiterte Filteroptionen
12. ✅ Sortieroptionen und gespeicherte Suchen

### Phase 5: Sicherheit (Priorität: Hoch)
13. ✅ Sicherheitsstufen für Dokumente
14. ✅ Audit-Trail und Aktivitätsprotokoll
15. ✅ Vertraulichkeitsmarkierungen

---

## Geschätzter Aufwand

| Komponente | Komplexität | Geschätzte Arbeit |
|------------|-------------|-------------------|
| Briefkopf-Administration | Mittel | ⭐⭐⭐ |
| E-Mail-Signaturen | Niedrig | ⭐⭐ |
| Makler-Mitarbeiter | Hoch | ⭐⭐⭐⭐ |
| Kommunikationszentrale | Hoch | ⭐⭐⭐⭐⭐ |
| Intelligente Ordner | Mittel | ⭐⭐⭐ |
| Such- & Filterfunktionen | Mittel | ⭐⭐⭐ |
| Sicherheitsfeatures | Hoch | ⭐⭐⭐⭐ |

---

## Nächste Schritte

1. **Priorisierung bestätigen** - Welche Features zuerst?
2. **Design-Abstimmung** - UI/UX für neue Bereiche
3. **Technische Spezifikation** - Detaillierte Datenstrukturen
4. **Implementierung** - Schrittweise Umsetzung
5. **Testing** - Funktions- und Sicherheitstests
