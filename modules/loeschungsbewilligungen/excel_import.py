"""
Excel-Import Service für Löschungsbewilligungen

Ermöglicht den Massenimport von Löschungsbewilligungs-Fällen
aus Excel-Dateien mit:
- Automatischer Spaltenerkennung
- Manueller Spalten-Zuordnung
- Validierung und Fehlerbehandlung
- Vorschau vor dem Import
"""

import io
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple, BinaryIO
from uuid import UUID, uuid4

import pandas as pd

from .models import LBCase, LBCaseStatus


# ==================== SPALTEN-MAPPING ====================

class LBExcelColumn(Enum):
    """Standardspalten für den Excel-Import"""
    # Grundbuch
    GRUNDBUCH = "grundbuch"
    GB_BLATT = "gb_blatt"
    GEMARKUNG = "gemarkung"
    FLUR = "flur"
    FLURSTUECK = "flurstueck"

    # Eigentümer
    VORNAME = "vorname"
    NACHNAME = "nachname"
    FIRMA = "firma"
    STRASSE = "strasse"
    PLZ = "plz"
    ORT = "ort"

    # Recht
    ABTEILUNG = "abteilung"
    LAUFENDE_NUMMER = "laufende_nummer"
    RECHT_ART = "recht_art"
    RECHT_BETRAG = "recht_betrag"
    RECHT_BESCHREIBUNG = "recht_beschreibung"

    # Gläubiger
    GLAEUBIGER_NAME = "glaeubiger_name"
    GLAEUBIGER_STRASSE = "glaeubiger_strasse"
    GLAEUBIGER_PLZ = "glaeubiger_plz"
    GLAEUBIGER_ORT = "glaeubiger_ort"
    GLAEUBIGER_IBAN = "glaeubiger_iban"
    GLAEUBIGER_BIC = "glaeubiger_bic"

    # Meta
    AKTENZEICHEN = "aktenzeichen"
    EXTERNE_REFERENZ = "externe_referenz"
    NOTIZEN = "notizen"
    FRIST_DATUM = "frist_datum"


# Automatische Spaltenerkennung basierend auf Headern
COLUMN_PATTERNS = {
    LBExcelColumn.GRUNDBUCH: ["grundbuch", "gb", "amtsgericht", "grundbuchamt"],
    LBExcelColumn.GB_BLATT: ["blatt", "gb_blatt", "gb-blatt", "blattnummer", "gb nr"],
    LBExcelColumn.GEMARKUNG: ["gemarkung", "gmkg"],
    LBExcelColumn.FLUR: ["flur"],
    LBExcelColumn.FLURSTUECK: ["flurstück", "flurstueck", "flst", "flurstücke"],

    LBExcelColumn.VORNAME: ["vorname", "vname", "v.name"],
    LBExcelColumn.NACHNAME: ["nachname", "name", "familienname", "n.name", "zuname"],
    LBExcelColumn.FIRMA: ["firma", "unternehmen", "gesellschaft", "company"],
    LBExcelColumn.STRASSE: ["straße", "strasse", "str", "adresse", "anschrift"],
    LBExcelColumn.PLZ: ["plz", "postleitzahl", "zip"],
    LBExcelColumn.ORT: ["ort", "stadt", "city", "wohnort"],

    LBExcelColumn.ABTEILUNG: ["abteilung", "abt", "abt."],
    LBExcelColumn.LAUFENDE_NUMMER: ["lfd", "lfd.", "laufende", "laufende nr", "lfd nr"],
    LBExcelColumn.RECHT_ART: ["art", "rechtsart", "belastung", "grundschuld", "hypothek"],
    LBExcelColumn.RECHT_BETRAG: ["betrag", "summe", "höhe", "nennbetrag"],
    LBExcelColumn.RECHT_BESCHREIBUNG: ["beschreibung", "details", "bemerkung"],

    LBExcelColumn.GLAEUBIGER_NAME: ["gläubiger", "glaeubiger", "bank", "kreditgeber"],
    LBExcelColumn.GLAEUBIGER_STRASSE: ["gläubiger straße", "gläubiger str", "bank str"],
    LBExcelColumn.GLAEUBIGER_PLZ: ["gläubiger plz", "bank plz"],
    LBExcelColumn.GLAEUBIGER_ORT: ["gläubiger ort", "bank ort"],
    LBExcelColumn.GLAEUBIGER_IBAN: ["iban", "gläubiger iban"],
    LBExcelColumn.GLAEUBIGER_BIC: ["bic", "swift", "gläubiger bic"],

    LBExcelColumn.AKTENZEICHEN: ["aktenzeichen", "az", "akz", "akte"],
    LBExcelColumn.EXTERNE_REFERENZ: ["referenz", "ref", "externe ref", "ext. ref"],
    LBExcelColumn.NOTIZEN: ["notizen", "anmerkungen", "hinweise", "bemerkungen"],
    LBExcelColumn.FRIST_DATUM: ["frist", "fristdatum", "deadline", "termin"],
}


@dataclass
class LBExcelColumnMapping:
    """Zuordnung Excel-Spalte -> Datenfeld"""
    excel_column: str  # Spaltenname in Excel
    target_field: LBExcelColumn  # Zielfeld
    is_auto_detected: bool = False


@dataclass
class LBImportError:
    """Fehler beim Import einer Zeile"""
    row_number: int
    column: Optional[str] = None
    message: str = ""
    severity: str = "error"  # "error", "warning"

    def __str__(self) -> str:
        if self.column:
            return f"Zeile {self.row_number}, Spalte '{self.column}': {self.message}"
        return f"Zeile {self.row_number}: {self.message}"


@dataclass
class LBImportResult:
    """Ergebnis eines Excel-Imports"""
    success: bool = False
    total_rows: int = 0
    imported_count: int = 0
    skipped_count: int = 0
    error_count: int = 0

    cases: List[LBCase] = field(default_factory=list)
    errors: List[LBImportError] = field(default_factory=list)
    warnings: List[LBImportError] = field(default_factory=list)

    mapping_used: Dict[str, str] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class LBExcelImporter:
    """
    Excel-Import Service für Löschungsbewilligungen

    Verwendung:
        importer = LBExcelImporter(organization_id)

        # Excel laden und Spalten erkennen
        preview = importer.preview(file_bytes)

        # Mapping anpassen falls nötig
        importer.set_mapping({
            "Grundbuchamt": "grundbuch",
            "Blatt-Nr": "gb_blatt",
            ...
        })

        # Import durchführen
        result = importer.import_data(file_bytes)
    """

    def __init__(self, organization_id: UUID, created_by: Optional[UUID] = None):
        self.organization_id = organization_id
        self.created_by = created_by
        self.column_mapping: Dict[str, LBExcelColumn] = {}
        self._df: Optional[pd.DataFrame] = None

    def preview(
        self,
        file: BinaryIO,
        sheet_name: Optional[str] = None,
        max_rows: int = 10
    ) -> Dict[str, Any]:
        """
        Lädt Excel-Datei und gibt Vorschau zurück

        Returns:
            Dictionary mit:
            - columns: Liste der Spaltennamen
            - detected_mapping: Automatisch erkannte Zuordnung
            - preview_data: Erste Zeilen als Liste von Dicts
            - sheet_names: Verfügbare Arbeitsblätter
            - total_rows: Gesamtanzahl Zeilen
        """
        # Excel laden
        if sheet_name:
            self._df = pd.read_excel(file, sheet_name=sheet_name)
        else:
            xls = pd.ExcelFile(file)
            sheet_names = xls.sheet_names
            self._df = pd.read_excel(file, sheet_name=0)

        # Spaltennamen normalisieren (Whitespace entfernen)
        self._df.columns = [str(c).strip() for c in self._df.columns]

        # Automatische Spaltenerkennung
        detected_mapping = self._auto_detect_columns()

        # Vorschau erstellen
        preview_df = self._df.head(max_rows)
        preview_data = preview_df.to_dict('records')

        return {
            "columns": list(self._df.columns),
            "detected_mapping": {k: v.value for k, v in detected_mapping.items()},
            "preview_data": preview_data,
            "sheet_names": sheet_names if 'sheet_names' in locals() else [sheet_name or "Sheet1"],
            "total_rows": len(self._df),
        }

    def _auto_detect_columns(self) -> Dict[str, LBExcelColumn]:
        """Erkennt automatisch Spaltenzuordnungen basierend auf Header-Namen"""
        detected = {}

        for col in self._df.columns:
            col_lower = str(col).lower().strip()

            for target_field, patterns in COLUMN_PATTERNS.items():
                for pattern in patterns:
                    if pattern in col_lower or col_lower == pattern:
                        detected[col] = target_field
                        break
                if col in detected:
                    break

        # Mapping speichern
        self.column_mapping = detected
        return detected

    def set_mapping(self, mapping: Dict[str, str]) -> None:
        """
        Setzt manuelles Spalten-Mapping

        Args:
            mapping: Dict von Excel-Spaltenname -> Zielfeld (als String)
        """
        self.column_mapping = {}
        for excel_col, target in mapping.items():
            if target and target != "":
                try:
                    self.column_mapping[excel_col] = LBExcelColumn(target)
                except ValueError:
                    pass  # Ungültiges Zielfeld ignorieren

    def import_data(
        self,
        file: Optional[BinaryIO] = None,
        validate_only: bool = False
    ) -> LBImportResult:
        """
        Importiert Daten aus Excel-Datei

        Args:
            file: Excel-Datei (optional wenn preview() bereits aufgerufen)
            validate_only: Nur validieren, nicht importieren

        Returns:
            LBImportResult mit importierten Cases und Fehlern
        """
        result = LBImportResult()

        # Datei laden falls nicht schon geschehen
        if file is not None:
            self._df = pd.read_excel(file)
            self._df.columns = [str(c).strip() for c in self._df.columns]
            if not self.column_mapping:
                self._auto_detect_columns()

        if self._df is None:
            result.errors.append(LBImportError(
                row_number=0,
                message="Keine Datei geladen. Bitte zuerst preview() aufrufen."
            ))
            return result

        result.total_rows = len(self._df)

        # Keine Pflichtfelder - alle Daten können später ergänzt werden
        # (Grundbuch aus Adresse, GB-Blatt aus Auszug, etc.)

        # Mapping speichern für Ergebnis
        result.mapping_used = {k: v.value for k, v in self.column_mapping.items()}

        # Zeilen verarbeiten
        for idx, row in self._df.iterrows():
            row_num = idx + 2  # Excel-Zeile (1-basiert, +1 für Header)

            try:
                case = self._parse_row(row, row_num, result)
                if case:
                    result.cases.append(case)
                    result.imported_count += 1
                else:
                    result.skipped_count += 1
            except Exception as e:
                result.errors.append(LBImportError(
                    row_number=row_num,
                    message=f"Unerwarteter Fehler: {str(e)}"
                ))
                result.error_count += 1

        result.success = result.error_count == 0
        return result

    def _parse_row(
        self,
        row: pd.Series,
        row_num: int,
        result: LBImportResult
    ) -> Optional[LBCase]:
        """Parst eine Excel-Zeile zu einem LBCase"""

        # Werte aus Mapping extrahieren
        values = {}
        for excel_col, target_field in self.column_mapping.items():
            if excel_col in row.index:
                val = row[excel_col]
                # NaN zu None konvertieren
                if pd.isna(val):
                    val = None
                elif isinstance(val, float) and val == int(val):
                    val = int(val)  # 1.0 -> 1
                values[target_field] = val

        # Alle Felder sind optional - können später ergänzt werden
        # (Grundbuch aus Adresse, GB-Blatt aus Auszug, etc.)
        grundbuch = self._get_string_value(values, LBExcelColumn.GRUNDBUCH)
        gb_blatt = self._get_string_value(values, LBExcelColumn.GB_BLATT)

        # Prüfen ob mindestens ein identifizierendes Merkmal vorhanden ist
        hat_eigentuemer = bool(
            self._get_string_value(values, LBExcelColumn.VORNAME) or
            self._get_string_value(values, LBExcelColumn.NACHNAME) or
            self._get_string_value(values, LBExcelColumn.FIRMA)
        )
        hat_adresse = bool(
            self._get_string_value(values, LBExcelColumn.STRASSE) or
            self._get_string_value(values, LBExcelColumn.ORT)
        )
        hat_grundbuch = bool(grundbuch or gb_blatt)

        if not (hat_eigentuemer or hat_adresse or hat_grundbuch):
            result.warnings.append(LBImportError(
                row_number=row_num,
                message="Zeile übersprungen - keine identifizierenden Daten (Name, Adresse oder Grundbuch).",
                severity="warning"
            ))
            return None

        # Case erstellen
        case = LBCase(
            organization_id=self.organization_id,
            created_by=self.created_by,

            # Grundbuch (beides optional - kann später aus Adresse/Auszug ergänzt werden)
            grundbuch=grundbuch or "",
            gb_blatt=gb_blatt or "",
            gemarkung=self._get_string_value(values, LBExcelColumn.GEMARKUNG),
            flur=self._get_string_value(values, LBExcelColumn.FLUR),
            flurstueck=self._get_string_value(values, LBExcelColumn.FLURSTUECK),

            # Eigentümer
            vorname=self._get_string_value(values, LBExcelColumn.VORNAME),
            nachname=self._get_string_value(values, LBExcelColumn.NACHNAME),
            firma=self._get_string_value(values, LBExcelColumn.FIRMA),
            strasse=self._get_string_value(values, LBExcelColumn.STRASSE),
            plz=self._get_string_value(values, LBExcelColumn.PLZ),
            ort=self._get_string_value(values, LBExcelColumn.ORT),

            # Recht
            abteilung=self._get_string_value(values, LBExcelColumn.ABTEILUNG),
            laufende_nummer=self._get_string_value(values, LBExcelColumn.LAUFENDE_NUMMER),
            recht_art=self._get_string_value(values, LBExcelColumn.RECHT_ART),
            recht_betrag=self._get_decimal_value(values, LBExcelColumn.RECHT_BETRAG, row_num, result),
            recht_beschreibung=self._get_string_value(values, LBExcelColumn.RECHT_BESCHREIBUNG),

            # Gläubiger
            glaeubiger_name=self._get_string_value(values, LBExcelColumn.GLAEUBIGER_NAME),
            glaeubiger_strasse=self._get_string_value(values, LBExcelColumn.GLAEUBIGER_STRASSE),
            glaeubiger_plz=self._get_string_value(values, LBExcelColumn.GLAEUBIGER_PLZ),
            glaeubiger_ort=self._get_string_value(values, LBExcelColumn.GLAEUBIGER_ORT),
            glaeubiger_iban=self._get_string_value(values, LBExcelColumn.GLAEUBIGER_IBAN),
            glaeubiger_bic=self._get_string_value(values, LBExcelColumn.GLAEUBIGER_BIC),

            # Meta
            aktenzeichen=self._get_string_value(values, LBExcelColumn.AKTENZEICHEN),
            externe_referenz=self._get_string_value(values, LBExcelColumn.EXTERNE_REFERENZ),
            notizen=self._get_string_value(values, LBExcelColumn.NOTIZEN),
            frist_datum=self._get_date_value(values, LBExcelColumn.FRIST_DATUM, row_num, result),
        )

        return case

    def _get_string_value(
        self,
        values: Dict[LBExcelColumn, Any],
        field: LBExcelColumn
    ) -> Optional[str]:
        """Extrahiert String-Wert"""
        val = values.get(field)
        if val is None:
            return None
        return str(val).strip() if str(val).strip() else None

    def _get_decimal_value(
        self,
        values: Dict[LBExcelColumn, Any],
        field: LBExcelColumn,
        row_num: int,
        result: LBImportResult
    ) -> Optional[Decimal]:
        """Extrahiert Decimal-Wert"""
        val = values.get(field)
        if val is None:
            return None

        try:
            # Formatierung bereinigen (1.234,56 -> 1234.56)
            if isinstance(val, str):
                val = val.replace(" ", "").replace("€", "").replace("EUR", "")
                # Deutsche Notation: 1.234,56 -> 1234.56
                if "," in val and "." in val:
                    val = val.replace(".", "").replace(",", ".")
                elif "," in val:
                    val = val.replace(",", ".")
            return Decimal(str(val))
        except (InvalidOperation, ValueError) as e:
            result.warnings.append(LBImportError(
                row_number=row_num,
                column=field.value,
                message=f"Ungültiger Betrag: '{val}'",
                severity="warning"
            ))
            return None

    def _get_date_value(
        self,
        values: Dict[LBExcelColumn, Any],
        field: LBExcelColumn,
        row_num: int,
        result: LBImportResult
    ) -> Optional[date]:
        """Extrahiert Date-Wert"""
        val = values.get(field)
        if val is None:
            return None

        try:
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, date):
                return val
            # String parsen
            if isinstance(val, str):
                # Verschiedene Formate probieren
                for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                    try:
                        return datetime.strptime(val.strip(), fmt).date()
                    except ValueError:
                        continue
            result.warnings.append(LBImportError(
                row_number=row_num,
                column=field.value,
                message=f"Ungültiges Datum: '{val}'",
                severity="warning"
            ))
            return None
        except Exception:
            return None


# ==================== HILFSFUNKTIONEN ====================

def get_available_fields() -> List[Tuple[str, str]]:
    """Gibt Liste aller verfügbaren Import-Felder zurück"""
    return [(col.value, col.name.replace("_", " ").title()) for col in LBExcelColumn]


def create_import_template() -> bytes:
    """Erstellt eine leere Excel-Vorlage für den Import"""
    columns = [
        "Grundbuch",
        "Blatt",
        "Gemarkung",
        "Flur",
        "Flurstück",
        "Vorname",
        "Nachname",
        "Firma",
        "Straße",
        "PLZ",
        "Ort",
        "Abteilung",
        "Lfd. Nr.",
        "Art des Rechts",
        "Betrag",
        "Beschreibung",
        "Gläubiger Name",
        "Gläubiger Straße",
        "Gläubiger PLZ",
        "Gläubiger Ort",
        "Gläubiger IBAN",
        "Gläubiger BIC",
        "Aktenzeichen",
        "Externe Referenz",
        "Notizen",
        "Frist",
    ]

    # Beispieldaten
    sample_data = {
        "Grundbuch": ["Amtsgericht München", "Amtsgericht München"],
        "Blatt": ["12345", "12346"],
        "Gemarkung": ["München", "München"],
        "Flur": ["1", "2"],
        "Flurstück": ["100/1", "200/2"],
        "Vorname": ["Max", "Anna"],
        "Nachname": ["Mustermann", "Beispiel"],
        "Firma": ["", "Beispiel GmbH"],
        "Straße": ["Musterstraße 1", "Beispielweg 2"],
        "PLZ": ["80331", "80333"],
        "Ort": ["München", "München"],
        "Abteilung": ["III", "III"],
        "Lfd. Nr.": ["1", "2"],
        "Art des Rechts": ["Grundschuld", "Hypothek"],
        "Betrag": ["100.000,00", "50.000,00"],
        "Beschreibung": ["ohne Brief", ""],
        "Gläubiger Name": ["Sparkasse München", "Volksbank München"],
        "Gläubiger Straße": ["Bankstraße 1", "Bankweg 2"],
        "Gläubiger PLZ": ["80331", "80333"],
        "Gläubiger Ort": ["München", "München"],
        "Gläubiger IBAN": ["DE89370400440532013000", "DE89370400440532013001"],
        "Gläubiger BIC": ["COBADEFFXXX", "GENODEF1M01"],
        "Aktenzeichen": ["2024/001", "2024/002"],
        "Externe Referenz": ["EXT-001", "EXT-002"],
        "Notizen": ["Beispiel-Eintrag", "Weiterer Eintrag"],
        "Frist": ["31.12.2024", ""],
    }

    df = pd.DataFrame(sample_data)

    # Zu BytesIO schreiben
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Löschungsbewilligungen', index=False)

        # Spaltenbreiten anpassen
        worksheet = writer.sheets['Löschungsbewilligungen']
        for i, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).str.len().max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + i)].width = min(max_len, 30)

    output.seek(0)
    return output.getvalue()
