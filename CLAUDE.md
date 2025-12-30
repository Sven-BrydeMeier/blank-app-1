# ImmoFlow - Projekt-Gedächtnis

## Projektübersicht

**ImmoFlow** ist eine umfassende Streamlit-Webanwendung für die digitale Abwicklung von Immobilientransaktionen. Die App verbindet alle Beteiligten eines Immobilienkaufs: Makler, Käufer, Verkäufer, Finanzierer (Banken) und Notare.

## Technische Details

- **Framework:** Streamlit (Python)
- **Hauptdatei:** `streamlit_app.py` (~37.000+ Zeilen)
- **Design:** Navy-Gold Theme mit Hell/Dunkel-Modus
- **Authentifizierung:** Session-basiert mit Cookie-Speicherung

## Demo-Zugangsdaten

| Rolle | Email | Passwort |
|-------|-------|----------|
| Makler | makler@demo.de | makler123 |
| Interessent | interessent@demo.de | interessent123 |
| Käufer | kaeufer@demo.de | kaeufer123 |
| Verkäufer | verkaeufer@demo.de | verkaeufer123 |
| Finanzierer | finanz@demo.de | finanz123 |
| Notar | notar@demo.de | notar123 |
| Notarfachkraft | notarfachkraft@demo.de | notarfachkraft123 |

## Dashboard-Struktur (Neues Design)

### Alle Rollen haben einheitliches Design mit:

**Fixierte Topbar:**
- Links: Rolle/Dashboard-Name mit Icon
- Mitte: Schnellaktionen
- Rechts: User-Info mit Abmelden-Link

**Sidebar (von oben nach unten):**
1. **Menü** - Navigation (Dashboard, Projekte, Timeline, Nachrichten, Dokumente, Termine, Einstellungen)
2. **Suche & Aktionen** - Suche, Benachrichtigungen, Neu, Design-Wechsel, Abmelden
3. **Aktentasche** - Dokumente sammeln
4. **Benachrichtigungs-Badge**

**Dashboard-Widgets:**
- Heute-Widget (Statistiken mit Badges)
- Aufgaben/Checkliste
- Nachrichten (zuletzt)
- Meine Vorgänge
- Timeline (Auszug)
- Dokumente (relevant)

### Rollen-spezifische Menüpunkte:

**Makler:**
- Dashboard, Projekte, Timeline, Nachrichten, Dokumente, Termine, Beteiligte, Bankenmappe, Einstellungen
- **Interessenten-Verwaltung:** Kann Interessenten als Käufer markieren (einzeln oder als Gruppe/Paar)

**Interessent (Vorstufe zum Käufer):**
- Dashboard, Objekte, Timeline, Dokumente, Termine, Einstellungen
- Hat das gleiche Dashboard wie Käufer, aber ohne Finanzierungs- und Kaufvertragsfunktionen
- Wird zum Käufer befördert, wenn vom Makler/Verkäufer als solcher markiert

**Käufer:**
- Dashboard, Projekte, Timeline, Finanzierung, Nachrichten, Dokumente, Termine, Einstellungen

**Verkäufer:**
- Dashboard, Projekte, Timeline, Preisfindung, Nachrichten, Dokumente, Termine, Einstellungen
- Kann Interessenten als Käufer markieren

**Finanzierer:**
- Dashboard, Projekte, Wirtschaftsdaten, Angebote, Termine, Einstellungen

**Notar:**
- Dashboard + erweitertes Notar-Menü (Akten, Vorgänge, Dokumente, Termine, etc.)
- **WICHTIG:** Beim Notar heißen "Projekte" immer "Akten"
- Kann Mitarbeiter anlegen und Berechtigungen vergeben
- Weist Mitarbeiter Projekten/Akten zu

**Notarfachkraft (Notar-Mitarbeiter):**
- Eingeschränktes Dashboard basierend auf Berechtigungen
- Bearbeitet zugewiesene Projekte/Akten
- Tabs: Timeline, Projekte, Checklisten, Dokumenten-Freigaben, Termine, Finanzierung
- Berechtigungen werden vom Notar festgelegt

### Notar ↔ Notarfachkraft Zusammenarbeit

**Berechtigungssystem:**
| Berechtigung | Beschreibung |
|--------------|--------------|
| kann_checklisten_bearbeiten | Checklisten für Projekte bearbeiten |
| kann_dokumente_freigeben | Dokumente im Namen des Notars freigeben |
| kann_termine_verwalten | Termine anlegen und bearbeiten |
| kann_finanzierung_sehen | Finanzierungsnachweise einsehen |

**Mitarbeiter-Rollen:**
- `Vollzugriff` - Alle Berechtigungen
- `Sachbearbeiter` - Standard-Bearbeitung (Checklisten, Termine)
- `Checklisten-Verwalter` - Nur Checklisten
- `Nur Lesen` - Lesezugriff ohne Bearbeitungsrechte

**Workflow:**
1. Notar legt Mitarbeiter an (Menü → Mehr → Kontakte → Mitarbeiter)
2. Notar weist Berechtigungen zu
3. Notar weist Projekte/Akten zu
4. Mitarbeiter loggt sich ein und sieht nur zugewiesene Projekte
5. Mitarbeiter bearbeitet Checklisten, gibt Dokumente frei, etc.

### Interessent → Käufer Workflow

1. **Mehrere Interessenten** können sich für ein Projekt interessieren
2. **Makler oder Verkäufer** markiert einen oder mehrere Interessenten als Käufer
3. **Käufer-Paar/Gruppe:** Mehrere Interessenten können gemeinsam als Käufer markiert werden (z.B. Ehepaar, Lebenspartner, GbR)
4. **Rollenänderung:** Bei der Beförderung wird die Rolle automatisch von "Interessent" auf "Käufer" geändert
5. **Benachrichtigung:** Der neue Käufer erhält eine Benachrichtigung über seine Statusänderung

### Notar-Dashboard (4-Quadranten-Layout)

Das Notar-Dashboard ist speziell auf den Notarworkflow zugeschnitten:

**Timeline am oberen Rand:**
- Zeigt Anzahl der Vorgänge pro Status-Kategorie (Vorbereitung, Finanzierung, Beurkundung, Nach Kaufvertrag, Abgeschlossen)

**4-Quadranten-Layout:**

| Links oben: Termine des Tages | Rechts oben: Posteingang |
|-------------------------------|--------------------------|
| - Datum oben angezeigt | - Neue Dokumente der Parteien |
| - Uhrzeit + Aktenzeichen + Kurzbezeichnung | - Datum, Aktenzeichen, Dokument, Absender |
| - Klick → öffnet Akte | - Status: erledigt/offen/dringend + Frist |
| | - Klick auf Dokument → direkt zum Dokument |
| | - Klick auf Aktenzeichen → zur Akte |

| Links unten: Urkundsentwurf erforderlich | Rechts unten: Beurkundete Verträge |
|------------------------------------------|-----------------------------------|
| - Akten mit allen Daten für Entwurf | - 3 Stadien als Tabs |
| - Button: Urkundenassistent (Step-by-Step) | - 1️⃣ Kaufpreisfälligkeit raus? |
| - Button: Urkunde-KI (automatischer Entwurf) | - 2️⃣ Kaufpreis Eingang bestätigt |
| | - 3️⃣ Auflassung/Grundschuld eingetragen |

**Akten-Detailansicht:**
- Zurück-Button zum Dashboard
- Timeline der Akte am oberen Rand
- Ordnerstruktur links: Entwürfe, Urkunden, Grundbuch, Parteien, Korrespondenz, Sonstiges
- Dokumente rechts (aktuell ausgewähltes Dokument wird highlighted)
- Dokumentaktionen: Als erledigt markieren, An Partei senden, In Entwurf übernehmen

**Sidebar-Menü mit Navigation:**
- 🏠 Dashboard (Home-Button) - Zurück zum 4-Quadranten-Dashboard
- 📁 Akten - Akten-Übersichtsseite mit Sortierung und Suche
- 📋 Vorgänge, 💬 Nachrichten, 📄 Dokumente, 📅 Termine, ⚙️ Einstellungen

**Suche in der Sidebar:**
- Echtzeit-Suche nach Aktenzeichen, Namen, Parteien
- Klickbare Suchergebnisse → direkt zur Akte
- 📬 Posteingang-Badge zeigt neue Dokumente an

**Akten-Übersichtsseite:**
- Alle Akten in Tabellenansicht
- Sortierung nach: Aktenzeichen, Datum (neueste/älteste), Status
- Suche nach Aktenzeichen, Name, Status
- 📬 Posteingang-Spalte mit Anzahl neuer Dokumente
- Klick auf 📂 → Akte öffnen
- Klick auf 📬 → Direkt zum Posteingang der Akte

**Notar-spezifische Funktionen:**
- `notar_dashboard()` - Hauptfunktion, rendert immer das neue Sidebar-Menü
- `_render_notar_dashboard_home()` - Haupt-Dashboard mit 4-Quadranten
- `_render_notar_akten_uebersicht()` - Akten-Übersicht mit Sortierung/Suche
- `_render_notar_vorgaenge_view()` - Vorgänge mit Timeline
- `_render_notar_nachrichten_view()` - Nachrichten/Kommunikationszentrale
- `_render_notar_dokumente_view()` - Dokumente (Aktenverwaltung, Anforderungen, Freigaben)
- `_render_notar_termine_view()` - Termine-Kalender
- `_render_notar_einstellungen_view()` - Einstellungen (Profil, Mitarbeiter, DSGVO, Papierkorb)
- `_render_notar_termine_widget()` - Termine des Tages (klickbar)
- `_render_notar_posteingang_widget()` - Posteingang (klickbar)
- `_render_notar_entwurf_widget()` - Urkundsentwurf-Akten (klickbar)
- `_render_notar_beurkundete_widget()` - Beurkundete Verträge nach 3 Stadien
- `_render_notar_akte_detail()` - Akten-Detailansicht mit Ordnerstruktur
- `_render_urkunden_assistent()` - Step-by-Step Urkundenerstellung
- `_render_urkunden_ki()` - KI-gestützte Urkundenerstellung
- `_suche_notar_akten()` - Suche in Akten/Projekten mit Posteingang-Info

## Wichtige Funktionen

### Akten-Import (PDF)
- PDF-Upload mit OCR-Extraktion
- Aktenvorblatt-Parser für strukturierte Daten
- Zuordnung zu Projekten möglich
- PDF-Bytes werden im Session State gespeichert

### Design-System
- `inject_new_dashboard_css()` - Haupt-CSS für neues Design
- `render_dashboard_header()` - Header mit Titel, Suche, Profil
- `render_sidebar_menu()` - Sidebar-Menü mit aktiver Markierung
- `render_heute_widget()` - Tagesstatistiken
- `render_aufgaben_widget()` - Checkliste
- `render_nachrichten_widget()` - Nachrichten
- `render_vorgaenge_widget()` - Vorgänge
- `render_timeline_widget()` - Timeline
- `render_dokumente_widget()` - Dokumentenstatus

### Topbar-System
- `render_fixed_topbar()` - Fixierte Menüleiste oben
- `render_topbar_actions()` - Schnellaktionen in Sidebar (Suche, Design-Wechsel, Abmelden)

## Bekannte Einschränkungen

- JavaScript in `st.markdown()` wird nicht ausgeführt - alle Interaktionen müssen über native Streamlit-Komponenten laufen
- Suche und Aktionen in der HTML-Topbar sind nur visuell - echte Funktionalität über Sidebar-Buttons

## Code-Konventionen

- Deutsche Variablennamen und Kommentare
- Funktionspräfixe: `render_`, `_render_` (privat), `_get_` (Datenhelfer)
- Session State für alle persistenten Daten
- CSS-Injection via `st.markdown(unsafe_allow_html=True)`

## Neue Grundbuch-OCR & Workflow-Funktionen

### Grundbuch-Abteilungen II/III Extraktion
- **OCR-Analyse:** PDF-Upload mit KI-gestützter Extraktion (OpenAI/Anthropic)
- **Abteilung II:** Lasten und Beschränkungen (Wegerechte, Leitungsrechte, Wohnrechte, Nießbrauch, etc.)
- **Abteilung III:** Hypotheken, Grundschulden, Rentenschulden
- Automatische Erkennung von Gläubigern und Beträgen

### Löschungs-ToDo-System
- **Automatische ToDo-Erstellung** für jede Belastung in Abt. III
- **Prioritäts-Stufen:** Hoch (>50.000€), Mittel (10.000-50.000€), Niedrig (<10.000€)
- **Status-Tracking:** Offen → Angefragt → Bewilligung erhalten → Gelöscht
- **Gläubiger-Verwaltung:** Adresse, E-Mail, IBAN für Ablösung
- **Dokument-Upload:** Löschungsbewilligungen hochladen

### Käufer-Abfrage zu Belastungen
- **Entscheidungs-Dialog:** Käufer wählt "Übernehmen" oder "Löschen" für jede Belastung
- **Benachrichtigungs-System:** Automatische Benachrichtigung bei offenen Entscheidungen
- **Status-Anzeige:** Farbcodierte Anzeige (🔴 Offen, 🟡 In Bearbeitung, 🟢 Erledigt)

### Grundbuchstand im Kaufvertrag
- **Template-Generierung:** Automatisch formatierter Grundbuchstand-Abschnitt
- **Integration von Käufer-Entscheidungen:** [wird übernommen] / [zur Löschung vorgesehen]
- **Funktion:** `generiere_grundbuchstand_text(projekt_id)`

### Bank-Grundschuld-Auswahl
- **Bank-Erfassung:** Name, Adresse, BIC, Ansprechpartner
- **Grundschuld-Details:** Betrag, Zinsen, Buchgrundschuld/Briefgrundschuld
- **Workflow:** Entwurf anfordern → Entwurf hochladen → Beurkundung
- **Automatische Vorausfüllung** aus Finanzierungsangeboten

### Workflow-Benachrichtigungen
- **Automatische Benachrichtigung** nach jedem Workflow-Schritt
- **Empfänger-Auswahl:** Käufer, Verkäufer, Makler, Alle
- **Abwahl-Option:** Empfänger können Benachrichtigungen abwählen
- **Funktion:** `sende_workflow_benachrichtigung(projekt_id, ...)`

### Neue Notar-Menüstruktur (Workflow-orientiert)
```
📁 AKTE
├── 📥 Neue Akte
├── 📋 Meine Akten
└── 📤 Akten-Import (PDF)

📚 GRUNDBUCH
├── 🔍 Grundbuchauszug anfordern
├── 📖 Abteilungen prüfen
├── ⚠️ Löschungsanforderungen (ToDos)
└── ❓ Käufer-Abfrage (Übernehmen/Löschen)

👥 PARTEIEN
├── 📝 Käufer/Verkäufer
├── 🪪 Ausweisdaten (OCR)
└── 🆔 Steuer-IDs

💰 FINANZIERUNG
├── 🏦 Bank-Auswahl (Grundschuld)
├── ✅ Finanzierungsbestätigung
└── 💵 Auszahlungsbedingungen

📜 KAUFVERTRAG
├── ⚙️ Vertragsdaten
├── 🏠 Grundbuchstand einfügen
├── 🤖 KI-Entwurf erstellen
├── ✍️ Entwurf bearbeiten
└── 📤 An Parteien versenden

📅 BEURKUNDUNG
├── 📆 Termin planen
├── 📋 Checkliste
├── 🔊 Vorlesen-Modus
└── ✅ Beurkundung durchführen

⚡ VOLLZUG
├── 📊 Status-Übersicht
├── 🏛️ Grunderwerbsteuer-Anzeige
├── 📜 Auflassungsvormerkung
├── 💸 Kaufpreisfälligkeit
└── 📖 Eigentumsumschreibung

📬 KOMMUNIKATION
├── ✉️ Nachrichten
├── 🔔 Benachrichtigungen
└── 📋 Dokumentenfreigaben
```

### Neue Dataclasses
- `GrundbuchBelastung` - Einzelne Belastung aus Grundbuch
- `LoeschungsAnforderung` - ToDo für Löschungsbewilligung
- `KaeuferBelastungsAbfrage` - Käufer-Entscheidung zu Belastung
- `BankGrundschuldInfo` - Finanzierende Bank für Grundschuld
- `MietverhaeltnisInfo` - Mietverhältnisse im Objekt
- `WorkflowBenachrichtigung` - Automatische Benachrichtigungen

### Neue Funktionen
- `ocr_grundbuch_mit_ki()` - KI-gestützte Grundbuch-OCR
- `erstelle_belastungen_aus_ocr()` - Belastungen aus OCR-Ergebnis erstellen
- `erstelle_loeschungs_todos_aus_belastungen()` - Automatische ToDo-Erstellung
- `generiere_grundbuchstand_text()` - Kaufvertrag-Abschnitt generieren
- `sende_workflow_benachrichtigung()` - Workflow-Benachrichtigung senden
- `notar_bank_grundschuld()` - Bank-Grundschuld-Verwaltung
- `_render_grundbuch_belastungen()` - UI für Belastungen-Anzeige
- `_render_loeschungs_todos()` - UI für Löschungs-ToDos
- `_run_grundbuch_ocr()` - OCR-Analyse durchführen

## Erklärungs-Modus für Verträge

### Übersicht
Der Erklärungs-Modus ermöglicht es Käufern, Verkäufern und Maklern, Kaufverträge und Grundschuldbestellungsurkunden mit verständlichen, nicht-juristischen Erklärungen zu lesen.

### Funktionsweise
- **Split-View:** Links der Originaltext, rechts die verständliche Erklärung
- **Abschnitts-Navigation:** Klick auf einen Vertragsabschnitt zeigt dessen Erklärung
- **Standard-Erklärungen:** Vordefinierte Erklärungen für typische Vertragsabschnitte (Präambel, Kaufpreis, Zahlung, Besitzübergang, etc.)

### Rollen-spezifische Funktionen

| Rolle | Erklärungs-Modus | Einstellung |
|-------|------------------|-------------|
| Käufer | Standardmäßig aktiv | Nicht einstellbar |
| Verkäufer | Standardmäßig aktiv | Nicht einstellbar |
| Makler | Einstellbar | Toggle in Profil-Einstellungen |

### Vertragsabschnitt-Typen
- `PRAEAMBEL` - Vertragsparteien und Grundstück
- `KAUFPREIS` - Der vereinbarte Kaufpreis
- `ZAHLUNG` - Zahlungsmodalitäten und Fälligkeit
- `BESITZUEBERGANG` - Wirtschaftlicher Übergang
- `LASTEN` - Lasten und Beschränkungen im Grundbuch
- `GEWAEHRLEISTUNG` - Sachmängelhaftung
- `KOSTEN` - Kosten und Steuern
- `GRUNDSCHULD` - Grundschuldbestellung (bei Finanzierung)
- `AUFLASSUNG` - Eigentumsübergang
- `VOLLMACHTEN` - Belastungsvollmacht etc.
- `SCHLUSSBESTIMMUNGEN` - Formale Regelungen

### Neue Dataclasses
- `VertragsAbschnittTyp` (Enum) - Typen von Vertragsabschnitten
- `VertragsAbschnitt` - Einzelner Abschnitt mit Originaltext
- `VertragsErklaerung` - Erklärung zu einem Abschnitt
- `VertragMitErklaerungen` - Vertragsdokument mit allen Abschnitten

### Neue Funktionen
- `render_erklaerungsmodus_splitview()` - Split-View Komponente
- `render_erklaerungsmodus_toggle()` - Toggle für Makler-Einstellungen
- `erstelle_demo_vertrag_mit_erklaerungen()` - Demo-Vertrag erstellen
- `render_dokument_mit_erklaerungsmodus()` - Wrapper für Dokumentansicht
- `kaeufer_dokumente_view()` - Erweitert um Erklärungs-Modus Tab
- `verkaeufer_erklaerungsmodus_view()` - Erklärungs-Modus für Verkäufer
- `makler_erklaerungsmodus_view()` - Erklärungs-Modus für Makler

### Session State Variablen
- `st.session_state.vertrags_abschnitte` - Alle Vertragsabschnitte
- `st.session_state.vertrags_erklaerungen` - Alle Erklärungen
- `st.session_state.vertraege_mit_erklaerungen` - Verträge mit Erklärungen
- `st.session_state.aktiver_erklaerungsmodus_vertrag` - Aktuell angezeigter Vertrag

## Letzte Änderungen

1. **Grundbuch-OCR mit KI** - Automatische Extraktion von Abt. II und III aus PDFs
2. **Löschungs-ToDo-System** - Automatische ToDos für Grundschulden/Hypotheken
3. **Käufer-Abfrage-Dialog** - Entscheidung über Übernahme/Löschung von Rechten
4. **Bank-Grundschuld-Modul** - Erfassung der finanzierenden Bank
5. **Workflow-Benachrichtigungen** - Automatische Benachrichtigungen an Parteien
6. **Notar-Menü workflow-orientiert** - Neue Menüstruktur nach Notarablauf
7. **Grundbuchstand im Kaufvertrag** - Automatisch generierter Abschnitt mit allen Belastungen
8. **Notar-Dashboard komplett überarbeitet** - 4-Quadranten-Layout mit klickbaren Widgets
9. **Sidebar-Suche funktional** - Echtzeit-Suche mit klickbaren Ergebnissen
10. **Alle Interaktionen klickbar** - Native Streamlit-Buttons statt HTML-only
11. **Erklärungs-Modus für Verträge** - Split-View mit verständlichen Erklärungen für Käufer/Verkäufer/Makler
