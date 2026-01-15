"""
Dokumentgenerierung Service für Löschungsbewilligungen

Generiert DOCX-Dokumente aus Templates mit Platzhalter-Ersetzung
basierend auf docxtpl.

Features:
- Template-basierte Generierung
- Automatische Platzhalter-Extraktion
- Mehrfach-Generierung für Batch-Verarbeitung
- PDF-Konvertierung (optional)
"""

import io
import re
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, BinaryIO
from uuid import UUID, uuid4

try:
    from docxtpl import DocxTemplate
    DOCXTPL_AVAILABLE = True
except ImportError:
    DOCXTPL_AVAILABLE = False

from .models import (
    LBCase,
    LBDocument,
    LBDocumentType,
    LBOrganization,
    STANDARD_PLATZHALTER,
)


# ==================== DATACLASSES ====================

@dataclass
class LBPlaceholder:
    """Definition eines Platzhalters"""
    name: str  # z.B. "$Grundbuch"
    description: str  # Beschreibung
    value: Optional[str] = None  # Aktueller Wert
    is_required: bool = False


@dataclass
class LBGenerationResult:
    """Ergebnis einer Dokumentgenerierung"""
    success: bool = False
    document_bytes: Optional[bytes] = None
    file_name: str = ""

    # Verwendete Platzhalter
    placeholders_used: Dict[str, str] = field(default_factory=dict)
    placeholders_missing: List[str] = field(default_factory=list)

    # Fehler
    error_message: Optional[str] = None

    # Metadaten
    generated_at: datetime = field(default_factory=datetime.now)
    case_id: Optional[UUID] = None


class LBDocumentGenerator:
    """
    DOCX-Dokumentgenerierung mit Template-Engine

    Verwendung:
        generator = LBDocumentGenerator()

        # Template laden
        generator.load_template(template_bytes)

        # Platzhalter anzeigen
        placeholders = generator.get_placeholders()

        # Dokument generieren
        result = generator.generate(case, organization)
    """

    def __init__(self):
        self._template: Optional[DocxTemplate] = None
        self._template_placeholders: List[str] = []

        if not DOCXTPL_AVAILABLE:
            raise ImportError(
                "docxtpl ist nicht installiert. "
                "Bitte installieren mit: pip install docxtpl"
            )

    def load_template(self, template_file: BinaryIO) -> List[str]:
        """
        Lädt ein DOCX-Template und extrahiert Platzhalter

        Args:
            template_file: Template-Datei (BytesIO oder File)

        Returns:
            Liste der gefundenen Platzhalter
        """
        self._template = DocxTemplate(template_file)
        self._template_placeholders = self._extract_placeholders()
        return self._template_placeholders

    def load_template_bytes(self, template_bytes: bytes) -> List[str]:
        """Lädt Template aus Bytes"""
        return self.load_template(io.BytesIO(template_bytes))

    def _extract_placeholders(self) -> List[str]:
        """
        Extrahiert alle Platzhalter aus dem Template

        Unterstützt zwei Formate:
        - $Platzhalter (Dollar-Format)
        - {{ platzhalter }} (Jinja2-Format)
        """
        if not self._template:
            return []

        placeholders = set()

        # XML des Dokuments durchsuchen
        for part in self._template.docx.parts.values():
            if hasattr(part, 'blob'):
                content = part.blob.decode('utf-8', errors='ignore')

                # Dollar-Format: $Platzhalter
                dollar_matches = re.findall(r'\$([A-Za-zäöüÄÖÜß][A-Za-z0-9äöüÄÖÜß_]*)', content)
                for match in dollar_matches:
                    placeholders.add(f"${match}")

                # Jinja2-Format: {{ platzhalter }}
                jinja_matches = re.findall(r'\{\{\s*([a-z_][a-z0-9_]*)\s*\}\}', content)
                for match in jinja_matches:
                    placeholders.add(match)

        return sorted(list(placeholders))

    def get_placeholders(self) -> List[LBPlaceholder]:
        """
        Gibt Liste der Platzhalter mit Beschreibungen zurück
        """
        standard_dict = {p[0]: p[1] for p in STANDARD_PLATZHALTER}
        result = []

        for ph in self._template_placeholders:
            desc = standard_dict.get(ph, "Benutzerdefiniert")
            result.append(LBPlaceholder(name=ph, description=desc))

        return result

    def generate(
        self,
        case: LBCase,
        organization: Optional[LBOrganization] = None,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> LBGenerationResult:
        """
        Generiert Dokument aus Template mit Case-Daten

        Args:
            case: Löschungsbewilligungs-Fall
            organization: Organisation (für Notar-Daten)
            extra_context: Zusätzliche Platzhalter-Werte

        Returns:
            LBGenerationResult mit Dokument-Bytes
        """
        result = LBGenerationResult(case_id=case.id)

        if not self._template:
            result.error_message = "Kein Template geladen"
            return result

        try:
            # Kontext aufbauen
            context = self._build_context(case, organization, extra_context)
            result.placeholders_used = {k: str(v) if v else "" for k, v in context.items()}

            # Fehlende Platzhalter ermitteln
            for ph in self._template_placeholders:
                # Dollar-Format zu Kontext-Key konvertieren
                key = ph.lstrip("$")
                if key not in context or context.get(key) is None:
                    result.placeholders_missing.append(ph)

            # Dokument generieren
            self._template.render(context)

            # Zu Bytes konvertieren
            output = io.BytesIO()
            self._template.save(output)
            output.seek(0)

            result.document_bytes = output.getvalue()
            result.success = True

            # Dateiname generieren
            result.file_name = self._generate_filename(case)

        except Exception as e:
            result.error_message = f"Fehler bei Generierung: {str(e)}"

        return result

    def _build_context(
        self,
        case: LBCase,
        organization: Optional[LBOrganization] = None,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Baut Platzhalter-Kontext aus Case-Daten"""

        context = {
            # Grundbuch
            "Grundbuch": case.grundbuch,
            "GBBlatt": case.gb_blatt,
            "Gemarkung": case.gemarkung or "",
            "Flur": case.flur or "",
            "Flurstueck": case.flurstueck or "",

            # Eigentümer
            "Vorname": case.vorname or "",
            "Nachname": case.nachname or "",
            "Firma": case.firma or "",
            "Strasse": case.strasse or "",
            "PLZ": case.plz or "",
            "Ort": case.ort or "",

            # Vollständige Adresse
            "EmpfaengerName": case.empfaenger_name,
            "EmpfaengerAdresse": case.empfaenger_adresse,

            # Recht
            "Abteilung": case.abteilung or "",
            "LfdNr": case.laufende_nummer or "",
            "RechtArt": case.recht_art or "",
            "RechtBetrag": self._format_currency(case.recht_betrag, case.recht_waehrung),
            "RechtBeschreibung": case.recht_beschreibung or "",
            "RechtFormatiert": case.recht_formatiert,

            # Gläubiger
            "GlaeubigerName": case.glaeubiger_name or "",
            "GlaeubigerStrasse": case.glaeubiger_strasse or "",
            "GlaeubigerPLZ": case.glaeubiger_plz or "",
            "GlaeubigerOrt": case.glaeubiger_ort or "",
            "GlaeubigerIBAN": case.glaeubiger_iban or "",
            "GlaeubigerBIC": case.glaeubiger_bic or "",

            # Ablösung
            "Abloesebetrag": self._format_currency(case.abloesebetrag),
            "AbloeseDatum": self._format_date(case.abloese_datum),

            # Meta
            "Aktenzeichen": case.aktenzeichen or "",
            "Datum": self._format_date(date.today()),
            "DatumLang": self._format_date_long(date.today()),
            "GrundbuchBezeichnung": case.grundbuch_bezeichnung,
        }

        # Organisation/Notar
        if organization:
            context.update({
                "NotarName": organization.notar_name or "",
                "NotarAmtssitz": organization.amtssitz or "",
                "KanzleiName": organization.name or "",
                "KanzleiStrasse": organization.strasse or "",
                "KanzleiPLZ": organization.plz or "",
                "KanzleiOrt": organization.ort or "",
                "KanzleiTelefon": organization.telefon or "",
                "KanzleiEmail": organization.email or "",
            })

        # Extra-Kontext
        if extra_context:
            context.update(extra_context)

        # Auch Kleinbuchstaben-Varianten für Jinja2
        lowercase_context = {k.lower(): v for k, v in context.items()}
        context.update(lowercase_context)

        return context

    def _format_currency(
        self,
        amount: Optional[Decimal],
        currency: str = "EUR"
    ) -> str:
        """Formatiert Betrag als Währung"""
        if amount is None:
            return ""
        # Deutsche Formatierung: 1.234,56 €
        formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted} {currency}"

    def _format_date(self, d: Optional[date]) -> str:
        """Formatiert Datum als DD.MM.YYYY"""
        if d is None:
            return ""
        return d.strftime("%d.%m.%Y")

    def _format_date_long(self, d: Optional[date]) -> str:
        """Formatiert Datum als 'TT. Monat JJJJ'"""
        if d is None:
            return ""
        months = [
            "Januar", "Februar", "März", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Dezember"
        ]
        return f"{d.day}. {months[d.month - 1]} {d.year}"

    def _generate_filename(self, case: LBCase) -> str:
        """Generiert Dateinamen für das Dokument"""
        parts = ["Loeschungsbewilligung"]

        if case.aktenzeichen:
            # Sonderzeichen entfernen
            az_clean = re.sub(r'[^\w\-]', '_', case.aktenzeichen)
            parts.append(az_clean)

        if case.empfaenger_name:
            name_clean = re.sub(r'[^\w\-]', '_', case.empfaenger_name)
            parts.append(name_clean[:30])  # Maximal 30 Zeichen

        parts.append(datetime.now().strftime("%Y%m%d"))

        return "_".join(parts) + ".docx"


# ==================== BATCH-GENERIERUNG ====================

def generate_batch(
    cases: List[LBCase],
    template_bytes: bytes,
    organization: Optional[LBOrganization] = None
) -> List[LBGenerationResult]:
    """
    Generiert Dokumente für mehrere Fälle

    Args:
        cases: Liste der Fälle
        template_bytes: Template als Bytes
        organization: Organisation

    Returns:
        Liste von GenerationResults
    """
    results = []

    for case in cases:
        generator = LBDocumentGenerator()
        generator.load_template_bytes(template_bytes)
        result = generator.generate(case, organization)
        results.append(result)

    return results


# ==================== STANDARD-TEMPLATES ====================

def get_standard_template_eigentuemer() -> str:
    """
    Gibt Standard-Template-Text für Eigentümer-Anschreiben zurück

    Hinweis: Dies ist nur der Text-Inhalt. Das eigentliche DOCX-Template
    muss separat erstellt werden.
    """
    return """
Notariat {{ NotarName }}
{{ KanzleiStrasse }}
{{ KanzleiPLZ }} {{ KanzleiOrt }}

{{ EmpfaengerName }}
{{ Strasse }}
{{ PLZ }} {{ Ort }}

{{ DatumLang }}

Betreff: Löschungsbewilligung
Grundbuch {{ Grundbuch }}, Blatt {{ GBBlatt }}
{% if Aktenzeichen %}Aktenzeichen: {{ Aktenzeichen }}{% endif %}

Sehr geehrte Damen und Herren,

im Rahmen einer notariellen Angelegenheit bitten wir Sie um Erteilung einer
Löschungsbewilligung für folgende im Grundbuch eingetragene Belastung:

Abteilung {{ Abteilung }}, lfd. Nr. {{ LfdNr }}:
{{ RechtArt }}{% if RechtBetrag %} über {{ RechtBetrag }}{% endif %}
{% if RechtBeschreibung %}{{ RechtBeschreibung }}{% endif %}

Bitte übersenden Sie uns die Löschungsbewilligung in notariell beglaubigter
Form an obige Adresse.

Für Rückfragen stehen wir Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen


{{ NotarName }}
Notar
""".strip()


def get_standard_template_bank() -> str:
    """Standard-Template-Text für Bank-Anschreiben"""
    return """
Notariat {{ NotarName }}
{{ KanzleiStrasse }}
{{ KanzleiPLZ }} {{ KanzleiOrt }}

{{ GlaeubigerName }}
{{ GlaeubigerStrasse }}
{{ GlaeubigerPLZ }} {{ GlaeubigerOrt }}

{{ DatumLang }}

Betreff: Anforderung Löschungsbewilligung
Grundbuch {{ Grundbuch }}, Blatt {{ GBBlatt }}
{% if Aktenzeichen %}Aktenzeichen: {{ Aktenzeichen }}{% endif %}

Sehr geehrte Damen und Herren,

im Rahmen einer bevorstehenden Immobilientransaktion bitten wir um
Übersendung einer Löschungsbewilligung für folgende zu Ihren Gunsten
eingetragene Grundschuld/Hypothek:

Abteilung {{ Abteilung }}, lfd. Nr. {{ LfdNr }}:
{{ RechtArt }} über {{ RechtBetrag }}
{% if RechtBeschreibung %}{{ RechtBeschreibung }}{% endif %}

Bitte teilen Sie uns den aktuellen Ablösebetrag mit und übersenden Sie
uns nach Eingang des Ablösebetrags die Löschungsbewilligung in
notariell beglaubigter Form.

{% if GlaeubigerIBAN %}
Ihre Bankverbindung:
IBAN: {{ GlaeubigerIBAN }}
{% if GlaeubigerBIC %}BIC: {{ GlaeubigerBIC }}{% endif %}
{% endif %}

Für Rückfragen stehen wir Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen


{{ NotarName }}
Notar
""".strip()
