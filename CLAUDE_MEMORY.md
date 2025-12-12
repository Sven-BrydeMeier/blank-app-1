# Claude Code Memory File - Immobilien-Transaktionsplattform

**Letzte Aktualisierung:** 2025-12-12
**Branch:** `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt`
**Letzter Commit:** `2b27870` - Feature: Dynamische Unterbereich-Auswahl in Aktenanlage

---

## Projekt-Übersicht

Dies ist eine **Streamlit-basierte Immobilien-Transaktionsplattform** (~25.000+ Zeilen), die die Kommunikation zwischen folgenden Parteien koordiniert:
- **Makler** - Erstellt Projekte, verwaltet Exposés, koordiniert Termine, kann Ausweise scannen, Parteien-Verwaltung
- **Käufer** - Lädt Bonitätsunterlagen hoch, akzeptiert Dokumente, bestätigt Termine, muss Rechtsdokumente akzeptieren
- **Verkäufer** - Stellt Unterlagen bereit, akzeptiert Dokumente, bestätigt Termine, muss Rechtsdokumente akzeptieren
- **Finanzierer** - Prüft Bonität, erstellt Finanzierungsangebote
- **Notar** - Aktenmanagement, Vertragserstellung, Beurkundung, Datenermittlung, Gesellschaften-Verwaltung

**Streamlit App URL:** https://blank-app-1-01jm3ycngfksr1qvslfzhqrz.streamlit.app/

---

## Dateistruktur

```
/home/user/blank-app-1/
├── streamlit_app.py      # Hauptanwendung (~25.000+ Zeilen)
├── requirements.txt      # Python-Abhängigkeiten
├── CLAUDE_MEMORY.md      # Diese Datei
└── .gitignore
```

---

## Kürzlich implementierte Features (2025-12-12)

### 1. Akten-Management mit Gesellschaften
- **Automatische Aktenzeichen-Generierung**: Format `Nummer/Jahr Verkäufer / Käufer`
- **Gesellschaften als Vertragsparteien**: GmbH, UG, AG, KG, OHG, GbR, eG, SE, KGaA
- **Organe/Vertretungsberechtigte**: Geschäftsführer, Vorstand, Prokurist mit Einzelvertretungsbefugnis
- **Handelsregister-Abfrage**: API oder manuelle Eingabe
- **Automatische Akte-Erstellung** bei Projekt-Notar-Verknüpfung
- **Parteien-Verwaltung UI** in Makler- und Notar-Dashboard

### 2. Dynamische Unterbereich-Auswahl in Aktenanlage
- Hauptbereich außerhalb des Formulars für dynamische Aktualisierung
- Unterbereiche werden basierend auf Hauptbereich gefiltert:
  - **Erbrecht**: Einzeltestament, Gemeinschaftliches Testament, Erbvertrag, Erbausschlagung, Erbschein
  - **Zivilrecht**: Not. Kaufvertrag, Überlassungsvertrag, Ehevertrag, Scheidungsfolgenvereinbarung, Vorsorgevertrag
  - **Gesellschaftsrecht**: Gründung, Liquidation, Anteilsverkauf/-abtretung

### 3. Bug-Fixes
- Dataclass-Feldreihenfolge in `Gesellschaft` korrigiert
- Doppelte `AktenStatus` Enum-Definition entfernt und zusammengeführt

---

## Wichtige Datenstrukturen

### Neue Enums (Zeilen ~3758-3786)
```python
class Rechtsform(Enum):
    NATUERLICHE_PERSON, GMBH, UG, AG, KG, OHG, GbR, eG, SE, KGaA, GMBH_CO_KG, STIFTUNG, VEREIN

class OrganTyp(Enum):
    GESCHAEFTSFUEHRER, VORSTAND, PROKURIST, KOMPLEMENTAER, KOMMANDITIST, GESELLSCHAFTER, LIQUIDATOR
```

### Neue Dataclasses (Zeilen ~3788-3921)
```python
@dataclass
class Organ:
    organ_id, gesellschaft_id, name, vorname, geburtsdatum, organ_typ
    einzelvertretungsberechtigt: bool

@dataclass
class HandelsregisterEintrag:
    hr_id, gesellschaft_id, registergericht, registerart, registernummer

@dataclass
class Gesellschaft:
    gesellschaft_id, firma, projekt_id, rechtsform, organe, hr_abfrage_erfolgt

@dataclass
class Partei:
    partei_id, projekt_id, ist_gesellschaft, user_id, gesellschaft_id, rolle

@dataclass
class NotarAktenzeichen:
    notar_id, jahr, letzte_nummer
```

### Erweiterte Projekt-Klasse (Zeilen ~3313-3322)
```python
akte_id: str = ""           # Verweis auf ImportierteAkte beim Notar
aktenzeichen: str = ""      # z.B. "123/2025 Müller / Schmidt"
parteien: List[str]         # Liste der Partei-IDs
gesellschaften: List[str]   # Liste der Gesellschaft-IDs
vertragstyp: str = "Kaufvertrag"
```

### AktenStatus Enum (Zeile ~3713)
```python
class AktenStatus(Enum):
    IMPORTIERT, NEU, IN_BEARBEITUNG, WARTET_AUF_UNTERLAGEN, VOLLSTAENDIG
    BEURKUNDUNG_VORBEREITET, BEURKUNDET, VOLLZUG, ABGESCHLOSSEN, ARCHIVIERT, STORNIERT
```

---

## Dashboard-Struktur

### Notar-Dashboard (20 Tabs, Zeile ~17510)
| Tab | Inhalt |
|-----|--------|
| 0 | Timeline |
| 1 | Projekte (mit Parteien-Verwaltung) |
| 2 | Aktenmanagement |
| 3 | Datenermittlung (Flurkarten, Grundbuch, Baulasten) |
| 4 | Preiseinigungen |
| 5 | Vertragsarchiv |
| 6 | Vertragserstellung |
| 7 | Checklisten |
| 8 | Dokumentenanforderungen |
| 9 | Mitarbeiter |
| 10 | Finanzierungsnachweise |
| 11 | Dokumenten-Freigaben |
| 12 | Kaufvertrag |
| 13 | Termine |
| 14 | Maklerempfehlung |
| 15 | Handwerker |
| 16 | Ausweisdaten |
| 17 | Rechtsdokumente |
| 18 | Aktenimport |
| 19 | Einstellungen |

### Makler-Dashboard (11 Tabs, Zeile ~10983)
| Tab | Inhalt |
|-----|--------|
| 0-2 | Timeline, Projekte (mit Parteien-Verwaltung), Kommunikation |
| 3-5 | Preisverhandlung, Finanzierungsübersicht, Teilnehmer-Status |
| 6-8 | Einladungen, Aktentasche, Profil |
| 9 | Dokumenten-Freigaben |
| 10 | Termin-Übersicht |

---

## Session State Strukturen (Zeilen ~4740-4747)

```python
st.session_state.users = {}              # User-ID -> User
st.session_state.projekte = {}           # Projekt-ID -> Projekt
st.session_state.akten = {}              # Akte-ID -> Akte
st.session_state.importierte_akten = {}  # Akte-ID -> ImportierteAkte
st.session_state.gesellschaften = {}     # Gesellschaft-ID -> Gesellschaft
st.session_state.organe = {}             # Organ-ID -> Organ
st.session_state.hr_eintraege = {}       # HR-ID -> HandelsregisterEintrag
st.session_state.parteien = {}           # Partei-ID -> Partei
st.session_state.aktenzeichen_zaehler = {}  # "notar_id_jahr" -> Nummer
```

---

## Wichtige Funktionen

### Aktenzeichen-Generierung (Zeilen ~22812-22993)
```python
def generiere_aktenzeichen(notar_id: str) -> str
def erstelle_aktenbezeichnung(projekt: Projekt) -> str
def erstelle_akte_fuer_projekt(projekt: Projekt, notar_id: str) -> ImportierteAkte
def verknuepfe_projekt_mit_notar(projekt_id: str, notar_id: str) -> ImportierteAkte
def aktualisiere_aktenbezeichnung(projekt: Projekt) -> None
```

### Parteien-Verwaltung (Zeilen ~23005-23300)
```python
def render_parteien_verwaltung(projekt: Projekt, user_rolle: str)
def render_partei_sektion(projekt: Projekt, rolle: str, user_rolle: str)
def render_neue_partei_formular(projekt: Projekt, rolle: str)
def render_gesellschaft_formular(projekt: Projekt, rolle: str)
def render_gesellschaft_details(gesellschaft: Gesellschaft)
def render_handelsregister_abfrage(gesellschaft: Gesellschaft)
def render_organ_verwaltung(gesellschaft: Gesellschaft)
```

### Akten-Untertypen (Zeile ~5673)
```python
def get_verfuegbare_untertypen(hauptbereich: str, notar_id: str) -> List[str]
```

---

## Bekannte Probleme & Lösungen

### 1. Dataclass-Feldreihenfolge
Felder ohne Default-Wert MÜSSEN vor Feldern mit Default-Wert stehen:
```python
# RICHTIG:
@dataclass
class Foo:
    required: str           # Ohne Default zuerst
    optional: str = ""      # Mit Default danach
```

### 2. Doppelte Tab-Indices
Streamlit erfordert eindeutige Keys bei `with tabs[X]:` - keine doppelten Indices!

### 3. Doppelte Enum-Definitionen
Enum-Klassen nur einmal definieren, sonst überschreibt die zweite die erste.

### 4. Dynamische Auswahl in Formularen
Selectboxen innerhalb von `st.form()` aktualisieren sich nicht dynamisch.
Lösung: Abhängige Selectboxen AUSSERHALB des Formulars platzieren.

---

## Git-Workflow

```bash
# Entwicklungs-Branch
git checkout claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt

# Push
git push -u origin claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt
```

---

## Letzte Commits

| Hash | Beschreibung |
|------|--------------|
| 2b27870 | Feature: Dynamische Unterbereich-Auswahl in Aktenanlage |
| 26cf550 | Fix: Doppelte AktenStatus Enum-Definition entfernt |
| d05f658 | Fix: Gesellschaft Dataclass-Feldreihenfolge korrigiert |
| 3ca1d0b | Feature: Akten-Management mit Gesellschaften und Parteien-Verwaltung |
| a86ccc0 | Fix: Doppelte Tab-Indices in Dashboards korrigiert |

---

## Nächste mögliche Schritte

1. Integration echter Handelsregister-API
2. PDF-Export für Akten und Verträge
3. E-Mail-Benachrichtigungen
4. Erweiterte Suchfunktionen
5. Berichtswesen und Statistiken
6. Finanzierungs-Gating (Legal-Prüfung vor Finanzierung)
