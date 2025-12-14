# Claude Code Memory File - Immobilien-Transaktionsplattform

**Letzte Aktualisierung:** 2025-12-14
**Branch:** `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt`
**Letzter Commit:** Fix AttributeError: Use rolle instead of role in main() dashboard routing
**Code-Umfang:** ~32.000 Zeilen

---

## Projekt-Übersicht

Dies ist eine **Streamlit-basierte Immobilien-Transaktionsplattform** (~32.000 Zeilen), die die Kommunikation zwischen folgenden Parteien koordiniert:
- **Makler** - Erstellt Projekte, verwaltet Exposés, koordiniert Termine, kann Ausweise scannen, Parteien-Verwaltung
- **Käufer** - Lädt Bonitätsunterlagen hoch, akzeptiert Dokumente, bestätigt Termine, muss Rechtsdokumente akzeptieren
- **Verkäufer** - Stellt Unterlagen bereit, akzeptiert Dokumente, bestätigt Termine, muss Rechtsdokumente akzeptieren
- **Finanzierer** - Prüft Bonität, erstellt Finanzierungsangebote
- **Notar** - Aktenmanagement, Vertragserstellung, Beurkundung, Datenermittlung, Gesellschaften-Verwaltung
- **Notar-Mitarbeiter** - Spezialisierter Zugang mit eingeschränkten Berechtigungen

**Streamlit App URL:** https://blank-app-1-01jm3ycngfksr1qvslfzhqrz.streamlit.app/

---

## Dateistruktur

```
/home/user/blank-app-1/
├── streamlit_app.py              # Hauptanwendung (~32.000 Zeilen)
├── requirements.txt              # Python-Abhängigkeiten
├── CLAUDE_MEMORY.md              # Diese Datei
├── KOMMUNIKATION_ERWEITERUNGEN.md # Kommunikations-Feature-Dokumentation
├── README.md                     # Setup-Anleitung
├── .gitignore
└── database/                     # Datenbank-Layer
    ├── __init__.py               # Package-Exports
    ├── models.py                 # SQLAlchemy-Modelle
    ├── connection.py             # Verbindungsmanagement
    └── services.py               # High-Level Datenbank-Services
```

---

## Konsistenz-Status (2025-12-14)

### Geprüft und OK:
- **User.rolle**: Konsistent in allen ~40 Verwendungen (nicht `role`)
- **AktenStatus Enum**: Einmalig definiert (Zeile ~3713)
- **AktenOrdner Dataclass**: Einmalig definiert (Zeile ~4799)
- **GatingPruefung Dataclass**: Einmalig definiert (Zeile ~4090)
- **Python-Syntax**: Kompiliert fehlerfrei (`py_compile`)
- **Dashboard-Routing**: Korrekt in `main()` (Zeilen 31895-31967)

### Bekannte Lösungen:
1. **role -> rolle**: Geändert in Commit 110d9a6
2. **Doppelte Klassen**: Bereinigt in Commit 7940c34
3. **Null-Checks**: Hinzugefügt in Commit 33ff5b7

---

## Implementierte Features

### Datenermittlung (Notar-Dashboard Tab 3)
- **Flurkarten-Anfrage**: Anfrage beim zuständigen Katasteramt
- **Elektronisches Grundbuch**: EGVP/SolumSTAR je nach Bundesland
- **Baulastenverzeichnis**: Anfrage beim zuständigen Bauamt
- **Steuer-ID-Abfrage**: BZSt-Anfrage für Käufer/Verkäufer
- **Grunderwerbsteuer-Meldung**: Anzeige ans zuständige Finanzamt
- **Vorkaufsrecht**: Anfrage bei der Gemeinde

### Vorhandene Behörden-Strukturen (NOCH MANUELL)
```python
@dataclass GrundbuchAnfrage:
    amtsgericht: str
    grundbuchbezirk: str
    grundbuchblatt: str

@dataclass BaulastenAnfrage:
    bauamt_name: str
    bauamt_adresse: str

@dataclass SteuerIdAbfrage:
    finanzamt_name: str
    finanzamt_adresse: str

@dataclass GrunderwersteuerMeldung:
    finanzamt_name: str
    finanzamt_aktenzeichen: str
```

### Bundesländer mit elektronischem Grundbuch (Zeile ~2996)
```python
ELEKTRONISCHES_GRUNDBUCH_SUPPORT = {
    "Baden-Württemberg": {"egvp": True, "solum_star": True},
    "Bayern": {"egvp": True, "solum_star": True},
    "Berlin": {"egvp": True, "solum_star": True},
    # ... alle 16 Bundesländer
}
```

---

## Fehlende Features (Vorschläge)

### 1. Automatische Behördenerkennung (HÖCHSTE PRIORITÄT)

**Problem:** Behördendaten werden aktuell manuell eingegeben.

**Lösung:** Automatische Ermittlung zuständiger Behörden basierend auf PLZ/Adresse:

```python
@dataclass
class ZustaendigkeitsInfo:
    """Automatisch ermittelte zuständige Behörden"""
    # Grundbuch
    amtsgericht_name: str
    amtsgericht_adresse: str
    amtsgericht_plz: str
    amtsgericht_ort: str
    grundbuchbezirk: str

    # Bauamt (Untere Bauaufsichtsbehörde)
    bauamt_name: str
    bauamt_adresse: str
    bauamt_plz: str
    bauamt_ort: str
    bauamt_telefon: str
    bauamt_email: str

    # Finanzamt (Grunderwerbsteuer)
    finanzamt_name: str
    finanzamt_adresse: str
    finanzamt_plz: str
    finanzamt_ort: str
    finanzamt_nummer: str  # Behördenkennzahl

    # Katasteramt (Vermessungsamt)
    katasteramt_name: str
    katasteramt_adresse: str

    # Gemeinde (Vorkaufsrecht)
    gemeinde_name: str
    gemeinde_plz: str
    gemeinde_verwaltung: str

    # Metadaten
    ermittelt_am: datetime
    quelle: str  # "API", "Datenbank", "Manuell"
    konfidenz: float  # 0-1

# Datenquellen:
# 1. Amtsgerichtsbezirke: destatis.de oder justiz-portale der Länder
# 2. Finanzämter: bzst.de (Finanzamtsliste nach PLZ)
# 3. Bauämter: Landratsämter/Kreise nach PLZ
# 4. Gemeinden: Gemeindeverzeichnis (AGS)
```

**Implementierungs-Ansätze:**
1. **Statische Datenbank**: JSON/CSV mit PLZ -> Behörden-Mapping
2. **API-Integration**: DESTATIS, OpenStreetMap Nominatim, Google Places
3. **Hybrid**: Lokale Datenbank + API-Fallback

### 2. PLZ-Datenbank für Deutschland

```python
PLZ_BEHOERDEN_MAPPING = {
    "80331": {  # München Innenstadt
        "bundesland": "Bayern",
        "landkreis": "München (Stadt)",
        "amtsgericht": "Amtsgericht München",
        "ag_adresse": "Pacellistraße 5, 80333 München",
        "finanzamt_grest": "Finanzamt München Grunderwerbsteuer",
        "fa_adresse": "Deroystraße 20, 80335 München",
        "fa_nummer": "9143",
        "bauamt": "Lokalbaukommission München",
        "katasteramt": "Amt für Digitalisierung, Breitband und Vermessung München",
    },
    # ... weitere PLZ
}
```

### 3. Weitere logische Feature-Vorschläge

| Feature | Beschreibung | Priorität |
|---------|--------------|-----------|
| **AGS-Integration** | Amtlicher Gemeindeschlüssel für Behördenzuordnung | Hoch |
| **Handelsregister-API** | Echte API-Anbindung (Bundesanzeiger, Handelsregister.de) | Hoch |
| **Notarsuche** | Automatische Notar-Empfehlung nach Bezirk | Mittel |
| **Grundbuch-Online** | SolumSTAR/EGVP API-Integration | Hoch |
| **Steuer-ID-Abfrage** | BZSt-API für automatische Abfrage | Mittel |
| **E-Signatur** | qualifizierte elektronische Signatur (QES) | Hoch |
| **PDF-Export** | Akten/Verträge als PDF mit digitalem Siegel | Mittel |
| **E-Mail-Integration** | SMTP/IMAP für echte E-Mails | Mittel |
| **Videokonferenz** | WebRTC für Online-Beurkundung | Niedrig |

---

## Dashboard-Struktur

### Notar-Dashboard (21 Tabs)
| Tab | Inhalt |
|-----|--------|
| 0 | Timeline |
| 1 | Projekte (mit Parteien-Verwaltung) |
| 2 | Aktenmanagement |
| 3 | **Datenermittlung** (Flurkarten, Grundbuch, Baulasten, Steuer-ID, Grunderwerbsteuer) |
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
| 19 | Nachrichten |
| 20 | Einstellungen |

### Makler-Dashboard (13 Tabs)
| Tab | Inhalt |
|-----|--------|
| 0-2 | Timeline, Projekte, Marktanalyse |
| 3-5 | Profil, Bankenmappe, Rechtliche Dokumente |
| 6-8 | Teilnehmer-Status, Einladungen, Kommentare |
| 9 | Ausweisdaten erfassen |
| 10 | Termine |
| 11 | Mitarbeiter |
| 12 | Nachrichten |

### Käufer-Dashboard (14 Tabs)
| Tab | Inhalt |
|-----|--------|
| 0-4 | Portal, Timeline, Projekte, Preisfindung, Maklerfinder |
| 5-8 | Ausweis/Pass, Dokumente, Dokumentenanfragen, Nachrichten |
| 9-10 | Eigenkosten, Vertragsvergleich |
| 11-13 | Termine, Papierkorb, Text-to-Speech |

---

## Session State Strukturen

```python
# Kern-Daten
st.session_state.users = {}              # User-ID -> User
st.session_state.projekte = {}           # Projekt-ID -> Projekt
st.session_state.akten = {}              # Akte-ID -> Akte
st.session_state.importierte_akten = {}  # Akte-ID -> ImportierteAkte
st.session_state.gesellschaften = {}     # Gesellschaft-ID -> Gesellschaft
st.session_state.parteien = {}           # Partei-ID -> Partei

# Kommunikation
st.session_state.briefkoepfe = {}        # Briefkopf-ID -> Briefkopf
st.session_state.email_signaturen = {}   # Signatur-ID -> EmailSignatur
st.session_state.nachrichten = {}        # Nachricht-ID -> KommunikationsNachricht

# Datenermittlung
st.session_state.grundbuch_anfragen = {} # ID -> GrundbuchAnfrage
st.session_state.baulasten_anfragen = {} # ID -> BaulastenAnfrage
st.session_state.steuer_id_abfragen = {} # ID -> SteuerIdAbfrage

# Behörden (NEU - zu implementieren)
st.session_state.zustaendigkeiten = {}   # PLZ -> ZustaendigkeitsInfo
```

---

## Bekannte Probleme & Lösungen

### 1. Dataclass-Feldreihenfolge
```python
# RICHTIG:
@dataclass
class Foo:
    required: str           # Ohne Default zuerst
    optional: str = ""      # Mit Default danach
```

### 2. Doppelte Tab-Indices
Streamlit erfordert eindeutige Keys bei `with tabs[X]:` - keine doppelten Indices!

### 3. Dynamische Auswahl in Formularen
Selectboxen innerhalb von `st.form()` aktualisieren sich nicht dynamisch.
Lösung: Abhängige Selectboxen AUSSERHALB des Formulars platzieren.

### 4. User-Attribut: rolle (nicht role)
Immer `user.rolle` verwenden, nicht `user.role`!

---

## Letzte Commits

| Hash | Beschreibung |
|------|--------------|
| 110d9a6 | Fix AttributeError: Use rolle instead of role in main() |
| 068f73a | Fix AttributeError: Rename User.role to User.rolle |
| 33ff5b7 | Fix: Add null-check for user in form |
| 7940c34 | Fix TypeError: duplicate AktenOrdner class |
| 1d4e30f | Feature: DSGVO Nachweis-Dokument Pflicht für Löschungen |
| 85a93e2 | Feature: DSGVO-compliant data management |
| c114f01 | Feature: Trash system & text-to-speech |

---

## Git-Workflow

```bash
# Entwicklungs-Branch
git checkout claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt

# Push
git push -u origin claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt
```
