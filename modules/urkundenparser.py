"""
Notar-Parser v1 - LLM-basierte Urkundenanalyse

Dieses Modul extrahiert aus notariellen Vertrags-/Urkundentexten:
1. Strukturierte Textbausteine (Blocks) inkl. Positions-/Variant-Logik
2. Maschinenlesbare Facts (v.a. Fälligkeit/Umschreibung/Vollzug)
3. Ableitbare Tasks mit Dependencies (Workflow)
4. Erkennung genereller Bausteine (vertragstypübergreifend)

Verwendet OpenAI Structured Outputs für Schema-konforme JSON-Ausgaben.
"""

import json
import re
import hashlib
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

# ============================================================================
# ENUMS
# ============================================================================

class BlockType(Enum):
    """Typ eines Textbausteins"""
    FIXED = "FIXED"                 # Fester Baustein, immer vorhanden
    RULED = "RULED"                 # Regel-basiert (bedingt)
    OPTIONAL = "OPTIONAL"           # Optional, standardmäßig inaktiv
    VARIANT_GROUP = "VARIANT_GROUP" # Gruppe von Varianten
    VARIANT_MEMBER = "VARIANT_MEMBER"  # Mitglied einer Variantengruppe
    HEADING = "HEADING"             # Überschrift (triggert keine Facts)


class Stage(Enum):
    """Vollzugsstufen im Notariatsworkflow"""
    MATURITY = "MATURITY"           # Kaufpreisfälligkeit
    REGISTRATION = "REGISTRATION"   # Umschreibung/Eintragung
    POST_CLOSING = "POST_CLOSING"   # Übergabe/Nachlaufpflichten
    OTHER = "OTHER"                 # Sonstiges


class MatchType(Enum):
    """Match-Typen für generelle Bausteine"""
    NONE = "NONE"
    EXACT_HASH = "EXACT_HASH"
    NEAR_TEXT = "NEAR_TEXT"
    EMBEDDING = "EMBEDDING"


class IssueSeverity(Enum):
    """Schweregrad von Parser-Issues"""
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


# ============================================================================
# MASTERPROMPT (SYSTEM)
# ============================================================================

NOTAR_PARSER_SYSTEM_PROMPT = """DU BIST: „Notar-Parser v1".
AUFGABE: Aus einem deutschen notariellen Vertrags-/Urkundentext extrahierst du
(1) strukturierte Textbausteine (Blocks) inkl. Positions-/Variant-Logik,
(2) maschinenlesbare Facts (v.a. Fälligkeit/Umschreibung/Vollzug),
(3) daraus ableitbare Tasks mit Dependencies (Workflow),
(4) eine Einschätzung, welche Blocks „generelle Bausteine" (vertragstypübergreifend) sind.

AUSGABEFORMAT: Du MUSST ausschließlich gültiges JSON liefern, das exakt dem vorgegebenen JSON-Schema entspricht (STRICT). Kein Fließtext.

WICHTIGE GRUNDSÄTZE:
1) Überschriften/Headings dürfen KEINE Facts triggern. Headings sind nur Struktur.
2) Varianten/Alternativen/„ggf.":
   - Wenn ein Abschnitt/Absatz als „Variante", „Alternative", „ggf.", Klammer-Alternative oder Auswahltext erkennbar ist,
     dann ist er VARIANT_MEMBER oder OPTIONAL und gilt standardmäßig als INAKTIV.
   - Facts aus Varianten dürfen nur als „conditional_facts" ausgegeben werden, nicht als aktive facts.
3) Stage-Trennung ist zwingend:
   - MATURITY (Kaufpreisfälligkeit/Fälligkeitsmitteilung)
   - REGISTRATION (Umschreibung/Eintragung)
   - POST_CLOSING (Übergabe/Miete/Kaution/Nachlaufpflichten)
4) Negationen/Overrides sind zwingend:
   - Beispiele: „verzichtet", „nicht Voraussetzung", „mit Ausnahme", „ohne", „keine Vormerkung".
   - In solchen Fällen erzeugst du einen override_fact (z. B. EXCLUDES_VORMERKUNG) und markierst widersprechende Facts als suppressed_by_override.
5) Generelle Bausteine:
   - Ein Block ist „generic_candidate", wenn er typischerweise in vielen Urkunden vorkommt (Formalia, Vollmachten, Grundbuchklauseln, Kosten, Ausfertigungen, Notarhinweise etc.).
   - Wenn dir eine library_reference (Liste bekannter Standardbausteine mit ids + hashes + kurzen Beschreibungen) gegeben ist,
     dann versuchst du einen match (exact_hash oder near_match) und gibst generic_match aus.
   - Wenn keine library_reference gegeben ist, entscheide heuristisch und begründe kurz.

VOLLZUG/WORKFLOW:
- Erzeuge Tasks aus Facts anhand folgender Leitlogik:
  A) MATURITY_GATE_TASK „FAELLIGKEITSMITTEILUNG" ist nur unblocked, wenn alle MATURITY-Voraussetzungen erfüllt sind.
  B) REGISTRATION_GATE_TASK „UMSCHREIBUNG_BETREIBEN" ist nur unblocked, wenn alle REGISTRATION-Voraussetzungen erfüllt sind.
- Jede Task hat: stage, actor, evidence_to_collect, depends_on_task_ids, derived_from_fact_ids.
- Jede Fact muss source_block_id haben, damit UI zum Text springen kann.

INPUTS (im user content):
- contract_text: kompletter Text (bereinigt, ohne Formatcodes)
- context: {contract_type_hint?, property_kind?, parties?, is_rented?, is_condominium? ...}
- library_reference?: bekannte generelle Blocks (optional)

KONFIDENZ:
- Gib confidence 0..1 an. Unter 0.6: set needs_confirmation = true.
- Wenn etwas unklar ist: lege issue an (issues[]), aber bleibe im Schema.

WICHTIGE DOMÄNEN-HINWEISE:
- Bei Immobilien-/NKV-Texten sind typische Facts:
  Vormerkung, Negativzeugnis/Vorkaufsrecht, Löschung/Freigaben/Treuhand, GrESt-Unbedenklichkeit, Kaufpreisnachweis/Verkäuferbestätigung.
- Aber: Beachte stets Ausnahmen im Text (Overrides)."""


# ============================================================================
# JSON-SCHEMA FÜR STRUCTURED OUTPUTS
# ============================================================================

NOTAR_PARSER_JSON_SCHEMA = {
    "name": "notar_parser_output",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["meta", "blocks", "facts", "tasks", "issues"],
        "properties": {
            "meta": {
                "type": "object",
                "additionalProperties": False,
                "required": ["contract_type_guess", "subtype_guess", "property_kind_guess"],
                "properties": {
                    "contract_type_guess": {"type": "string"},
                    "subtype_guess": {"type": "array", "items": {"type": "string"}},
                    "property_kind_guess": {"type": "string"}
                }
            },
            "blocks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "block_id", "block_type", "outline_path", "anchor", "role_guess",
                        "text_excerpt", "constraints", "generic_candidate", "generic_reason",
                        "variant", "source_ref"
                    ],
                    "properties": {
                        "block_id": {"type": "string"},
                        "block_type": {"type": "string", "enum": ["FIXED", "RULED", "OPTIONAL", "VARIANT_GROUP", "VARIANT_MEMBER", "HEADING"]},
                        "outline_path": {"type": "string"},
                        "anchor": {"type": "string"},
                        "role_guess": {"type": "string"},
                        "text_excerpt": {"type": "string"},
                        "constraints": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["before_roles", "after_roles", "priority"],
                            "properties": {
                                "before_roles": {"type": "array", "items": {"type": "string"}},
                                "after_roles": {"type": "array", "items": {"type": "string"}},
                                "priority": {"type": "integer"}
                            }
                        },
                        "generic_candidate": {"type": "boolean"},
                        "generic_reason": {"type": "string"},
                        "generic_match": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["matched", "match_type", "match_score", "library_id"],
                            "properties": {
                                "matched": {"type": "boolean"},
                                "match_type": {"type": "string", "enum": ["NONE", "EXACT_HASH", "NEAR_TEXT", "EMBEDDING"]},
                                "match_score": {"type": "number"},
                                "library_id": {"type": "string"}
                            }
                        },
                        "variant": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["group_id", "is_active_default"],
                            "properties": {
                                "group_id": {"type": "string"},
                                "is_active_default": {"type": "boolean"}
                            }
                        },
                        "source_ref": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["line_hint"],
                            "properties": {"line_hint": {"type": "string"}}
                        }
                    }
                }
            },
            "facts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "fact_id", "fact_type", "stage", "confidence", "needs_confirmation",
                        "source_block_id", "params", "suppressed_by_override", "conditional_on_variant_group"
                    ],
                    "properties": {
                        "fact_id": {"type": "string"},
                        "fact_type": {"type": "string"},
                        "stage": {"type": "string", "enum": ["MATURITY", "REGISTRATION", "POST_CLOSING", "OTHER"]},
                        "confidence": {"type": "number"},
                        "needs_confirmation": {"type": "boolean"},
                        "source_block_id": {"type": "string"},
                        "params": {"type": "object"},
                        "suppressed_by_override": {"type": "boolean"},
                        "conditional_on_variant_group": {"type": "string"}
                    }
                }
            },
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "task_id", "task_type", "stage", "actor", "description",
                        "evidence_to_collect", "depends_on_task_ids", "derived_from_fact_ids"
                    ],
                    "properties": {
                        "task_id": {"type": "string"},
                        "task_type": {"type": "string"},
                        "stage": {"type": "string", "enum": ["MATURITY", "REGISTRATION", "POST_CLOSING", "OTHER"]},
                        "actor": {"type": "string"},
                        "description": {"type": "string"},
                        "evidence_to_collect": {"type": "array", "items": {"type": "string"}},
                        "depends_on_task_ids": {"type": "array", "items": {"type": "string"}},
                        "derived_from_fact_ids": {"type": "array", "items": {"type": "string"}}
                    }
                }
            },
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["severity", "message", "block_id_hint"],
                    "properties": {
                        "severity": {"type": "string", "enum": ["INFO", "WARN", "ERROR"]},
                        "message": {"type": "string"},
                        "block_id_hint": {"type": "string"}
                    }
                }
            }
        }
    }
}


# ============================================================================
# DATENKLASSEN
# ============================================================================

@dataclass
class BlockConstraints:
    """Positionierungsconstraints für einen Block"""
    before_roles: List[str] = field(default_factory=list)
    after_roles: List[str] = field(default_factory=list)
    priority: int = 0


@dataclass
class GenericMatch:
    """Match-Information gegen die Bausteinbibliothek"""
    matched: bool = False
    match_type: str = MatchType.NONE.value
    match_score: float = 0.0
    library_id: str = ""


@dataclass
class BlockVariant:
    """Varianten-Informationen für einen Block"""
    group_id: str = ""
    is_active_default: bool = True


@dataclass
class SourceRef:
    """Quellenverweis im Originaltext"""
    line_hint: str = ""


@dataclass
class ParserBlock:
    """Ein extrahierter Textbaustein"""
    block_id: str
    block_type: str
    outline_path: str
    anchor: str
    role_guess: str
    text_excerpt: str
    constraints: BlockConstraints
    generic_candidate: bool
    generic_reason: str
    generic_match: GenericMatch
    variant: BlockVariant
    source_ref: SourceRef

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "outline_path": self.outline_path,
            "anchor": self.anchor,
            "role_guess": self.role_guess,
            "text_excerpt": self.text_excerpt,
            "constraints": asdict(self.constraints),
            "generic_candidate": self.generic_candidate,
            "generic_reason": self.generic_reason,
            "generic_match": asdict(self.generic_match),
            "variant": asdict(self.variant),
            "source_ref": asdict(self.source_ref),
        }


@dataclass
class ParserFact:
    """Ein extrahierter Fact (Voraussetzung/Bedingung)"""
    fact_id: str
    fact_type: str
    stage: str
    confidence: float
    needs_confirmation: bool
    source_block_id: str
    params: Dict[str, Any]
    suppressed_by_override: bool
    conditional_on_variant_group: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParserTask:
    """Eine abgeleitete Workflow-Task"""
    task_id: str
    task_type: str
    stage: str
    actor: str
    description: str
    evidence_to_collect: List[str]
    depends_on_task_ids: List[str]
    derived_from_fact_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParserIssue:
    """Ein Issue/Problem bei der Analyse"""
    severity: str
    message: str
    block_id_hint: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParserMeta:
    """Metadaten über den erkannten Vertragstyp"""
    contract_type_guess: str
    subtype_guess: List[str]
    property_kind_guess: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NotarParserOutput:
    """Vollständige Ausgabe des Notar-Parsers"""
    meta: ParserMeta
    blocks: List[ParserBlock]
    facts: List[ParserFact]
    tasks: List[ParserTask]
    issues: List[ParserIssue]

    # Zusätzliche Metadaten
    parsed_at: datetime = field(default_factory=datetime.now)
    parser_version: str = "1.0"
    source_document_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta": self.meta.to_dict(),
            "blocks": [b.to_dict() for b in self.blocks],
            "facts": [f.to_dict() for f in self.facts],
            "tasks": [t.to_dict() for t in self.tasks],
            "issues": [i.to_dict() for i in self.issues],
            "parsed_at": self.parsed_at.isoformat(),
            "parser_version": self.parser_version,
            "source_document_hash": self.source_document_hash,
        }


# ============================================================================
# SEGMENTIERUNG
# ============================================================================

# Regex für Paragraphen-Überschriften
HEADING_RE = re.compile(r"^\s*(§\s*\d+|[IVXLCDM]+\.)\s+.+$", re.IGNORECASE)


def segment_paragraphs(text: str) -> List[str]:
    """
    Segmentiert einen Urkundentext in Paragraph-Chunks.

    Vor dem LLM-Call sollte der Text segmentiert werden, damit das Modell
    weniger „rate-segmentieren" muss und weniger Variant-Fehler macht.

    Args:
        text: Der zu segmentierende Urkundentext

    Returns:
        Liste von Paragraph-Chunks
    """
    # Split by blank lines
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    out = []
    i = 0
    while i < len(parts):
        # Merge headings with following paragraph
        if HEADING_RE.match(parts[i]) and i + 1 < len(parts):
            out.append(parts[i] + "\n" + parts[i + 1])
            i += 2
        else:
            out.append(parts[i])
            i += 1

    return out


# ============================================================================
# HASH & NORMALISIERUNG FÜR GENERELLE BAUSTEINE
# ============================================================================

def normalize_for_hash(text: str) -> str:
    """
    Normalisiert Text für Hash-Berechnung.

    Neutralisiert variable Elemente wie Datum, Beträge, Urkundsnummern,
    damit gleiche Bausteine mit unterschiedlichen konkreten Werten
    denselben Hash ergeben.

    Args:
        text: Der zu normalisierende Text

    Returns:
        Normalisierter Text
    """
    t = text.lower()
    t = re.sub(r"\s+", " ", t).strip()

    # Platzhalter für variable Elemente
    # Datum (z.B. 01.01.2024, 1.1.24)
    t = re.sub(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b", "${DATE}", t)
    # Beträge (z.B. 100.000,00 oder 100000,00)
    t = re.sub(r"\b\d[\d\.]*,\d{2}\b", "${AMOUNT}", t)
    # Urkundsnummern (z.B. UR-Nr. 123/2024)
    t = re.sub(r"ur[.-]?\s*nr[.\s:]*\d+/\d+", "${UR_NR}", t, flags=re.IGNORECASE)
    # Aktenzeichen (z.B. 333/24)
    t = re.sub(r"\b\d{1,4}/\d{2,4}\b", "${AKT_NR}", t)

    return t


def block_hash(text: str) -> str:
    """
    Berechnet einen normalisierten Hash für einen Textbaustein.

    Args:
        text: Der Baustein-Text

    Returns:
        SHA256-Hash des normalisierten Textes
    """
    norm = normalize_for_hash(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def match_generic_block(block_text: str, library: List[Dict[str, Any]]) -> GenericMatch:
    """
    Matched einen Block gegen die Bibliothek bekannter genereller Bausteine.

    Args:
        block_text: Der Text des zu matchenden Blocks
        library: Liste von bekannten Bausteinen mit {"id": ..., "hash": ..., "description": ...}

    Returns:
        GenericMatch mit Match-Informationen
    """
    h = block_hash(block_text)

    for lib_block in library:
        if lib_block.get("hash") == h:
            return GenericMatch(
                matched=True,
                match_type=MatchType.EXACT_HASH.value,
                match_score=1.0,
                library_id=lib_block.get("id", "")
            )

    # TODO: Implementiere NEAR_TEXT und EMBEDDING Matching
    # Für Near-Text: Levenshtein-Distanz oder ähnliches
    # Für Embedding: Vektorähnlichkeit mit OpenAI Embeddings

    return GenericMatch(
        matched=False,
        match_type=MatchType.NONE.value,
        match_score=0.0,
        library_id=""
    )


# ============================================================================
# LLM-EXTRAKTION
# ============================================================================

def call_notar_parser(
    contract_text: str,
    context: Dict[str, Any],
    library_reference: Optional[List[Dict[str, Any]]] = None,
    model: str = "gpt-4o-2024-11-20",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ruft den LLM-Parser mit Structured Outputs auf.

    Args:
        contract_text: Der zu parsende Vertragstext
        context: Kontext-Informationen {contract_type_hint, property_kind, parties, ...}
        library_reference: Optional - bekannte generelle Bausteine für Matching
        model: OpenAI-Modell (Snapshot empfohlen für Stabilität)
        api_key: Optional - OpenAI API Key (sonst aus Environment)

    Returns:
        Strukturierte Parser-Ausgabe als Dict
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("OpenAI-Paket nicht installiert. Bitte 'pip install openai' ausführen.")

    client = OpenAI(api_key=api_key) if api_key else OpenAI()

    # User-Payload zusammenstellen
    user_payload = {
        "contract_text": contract_text,
        "context": context,
    }

    if library_reference:
        user_payload["library_reference"] = library_reference

    # API-Call mit Structured Outputs
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": NOTAR_PARSER_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": NOTAR_PARSER_JSON_SCHEMA
        },
        temperature=0.0  # Deterministisch für Reproduzierbarkeit
    )

    content = response.choices[0].message.content
    return json.loads(content)


def parse_llm_response(raw_response: Dict[str, Any]) -> NotarParserOutput:
    """
    Konvertiert die rohe LLM-Antwort in typisierte Datenklassen.

    Args:
        raw_response: Die rohe JSON-Antwort vom LLM

    Returns:
        NotarParserOutput mit typisierten Objekten
    """
    # Meta
    meta = ParserMeta(
        contract_type_guess=raw_response["meta"]["contract_type_guess"],
        subtype_guess=raw_response["meta"]["subtype_guess"],
        property_kind_guess=raw_response["meta"]["property_kind_guess"]
    )

    # Blocks
    blocks = []
    for b in raw_response.get("blocks", []):
        blocks.append(ParserBlock(
            block_id=b["block_id"],
            block_type=b["block_type"],
            outline_path=b["outline_path"],
            anchor=b["anchor"],
            role_guess=b["role_guess"],
            text_excerpt=b["text_excerpt"],
            constraints=BlockConstraints(
                before_roles=b["constraints"]["before_roles"],
                after_roles=b["constraints"]["after_roles"],
                priority=b["constraints"]["priority"]
            ),
            generic_candidate=b["generic_candidate"],
            generic_reason=b["generic_reason"],
            generic_match=GenericMatch(
                matched=b["generic_match"]["matched"],
                match_type=b["generic_match"]["match_type"],
                match_score=b["generic_match"]["match_score"],
                library_id=b["generic_match"]["library_id"]
            ),
            variant=BlockVariant(
                group_id=b["variant"]["group_id"],
                is_active_default=b["variant"]["is_active_default"]
            ),
            source_ref=SourceRef(
                line_hint=b["source_ref"]["line_hint"]
            )
        ))

    # Facts
    facts = []
    for f in raw_response.get("facts", []):
        facts.append(ParserFact(
            fact_id=f["fact_id"],
            fact_type=f["fact_type"],
            stage=f["stage"],
            confidence=f["confidence"],
            needs_confirmation=f["needs_confirmation"],
            source_block_id=f["source_block_id"],
            params=f.get("params", {}),
            suppressed_by_override=f["suppressed_by_override"],
            conditional_on_variant_group=f["conditional_on_variant_group"]
        ))

    # Tasks
    tasks = []
    for t in raw_response.get("tasks", []):
        tasks.append(ParserTask(
            task_id=t["task_id"],
            task_type=t["task_type"],
            stage=t["stage"],
            actor=t["actor"],
            description=t["description"],
            evidence_to_collect=t["evidence_to_collect"],
            depends_on_task_ids=t["depends_on_task_ids"],
            derived_from_fact_ids=t["derived_from_fact_ids"]
        ))

    # Issues
    issues = []
    for i in raw_response.get("issues", []):
        issues.append(ParserIssue(
            severity=i["severity"],
            message=i["message"],
            block_id_hint=i["block_id_hint"]
        ))

    return NotarParserOutput(
        meta=meta,
        blocks=blocks,
        facts=facts,
        tasks=tasks,
        issues=issues
    )


# ============================================================================
# DETERMINISTISCHER RULE-PLANNER (Facts → Tasks)
# ============================================================================

def mk_task(
    task_type: str,
    stage: str,
    actor: str,
    description: str,
    evidence: List[str],
    derived_fact_ids: List[str]
) -> ParserTask:
    """Erstellt eine neue Task mit generierter UUID."""
    return ParserTask(
        task_id=str(uuid.uuid4()),
        task_type=task_type,
        stage=stage,
        actor=actor,
        description=description,
        evidence_to_collect=evidence,
        depends_on_task_ids=[],
        derived_from_fact_ids=derived_fact_ids
    )


def build_workflow_from_facts(facts: List[ParserFact]) -> List[ParserTask]:
    """
    Baut einen Workflow (Tasks + Dependencies) aus den extrahierten Facts.

    Wendet Overrides an und erzeugt Gate-Tasks für Fälligkeit und Umschreibung.

    Args:
        facts: Liste der extrahierten Facts

    Returns:
        Liste von Tasks mit Dependencies
    """
    # 1) Overrides sammeln
    overrides = {
        f.fact_type for f in facts
        if not f.suppressed_by_override and f.fact_type.startswith("EXCLUDES_")
    }

    def is_suppressed(f: ParserFact) -> bool:
        # Beispiel: EXCLUDES_VORMERKUNG unterdrückt REQUIRES_VORMERKUNG_FOR_MATURITY
        if "EXCLUDES_VORMERKUNG" in overrides and f.fact_type == "REQUIRES_VORMERKUNG_FOR_MATURITY":
            return True
        if "EXCLUDES_NEGATIVZEUGNIS" in overrides and f.fact_type == "REQUIRES_NEGATIVZEUGNIS":
            return True
        return False

    active_facts = [f for f in facts if not is_suppressed(f) and not f.suppressed_by_override]

    tasks = []
    task_by_type: Dict[str, ParserTask] = {}

    # 2) Tasks aus Facts ableiten
    for f in active_facts:
        ft = f.fact_type
        fid = f.fact_id

        # MATURITY Stage Tasks
        if ft == "REQUIRES_VORMERKUNG_FOR_MATURITY":
            t = mk_task(
                "VORMERKUNG_BEANTRAGEN", Stage.MATURITY.value, "NOTAR",
                "Auflassungsvormerkung beantragen und Eintragung überwachen.",
                ["VORMERKUNG_EINTRAGUNG"], [fid]
            )
            task_by_type["VORMERKUNG_BEANTRAGEN"] = t
            tasks.append(t)

        if ft == "REQUIRES_NEGATIVZEUGNIS":
            t = mk_task(
                "NEGATIVZEUGNIS_ANFORDERN", Stage.MATURITY.value, "NOTAR",
                "Negativzeugnis (BauGB) bei Gemeinde anfordern.",
                ["NEGATIVZEUGNIS_BAUGB"], [fid]
            )
            task_by_type["NEGATIVZEUGNIS_ANFORDERN"] = t
            tasks.append(t)

        if ft == "REQUIRES_DELETION_CLEARANCES":
            t = mk_task(
                "LOESCHUNGSUNTERLAGEN_EINHOLEN", Stage.MATURITY.value, "NOTAR",
                "Löschungsbewilligungen/Freigaben einholen (ggf. Bank).",
                ["LOESCHUNGSBEWILLIGUNG"], [fid]
            )
            task_by_type["LOESCHUNGSUNTERLAGEN_EINHOLEN"] = t
            tasks.append(t)

        if ft == "REQUIRES_TREUHAND":
            t = mk_task(
                "TREUHANDKONTO_EINRICHTEN", Stage.MATURITY.value, "NOTAR",
                "Treuhandkonto einrichten und Zahlungsanweisungen vorbereiten.",
                ["TREUHANDKONTO_BESTAETIGUNG"], [fid]
            )
            task_by_type["TREUHANDKONTO_EINRICHTEN"] = t
            tasks.append(t)

        # REGISTRATION Stage Tasks
        if ft == "REQUIRES_TAX_CLEARANCE_FOR_REGISTRATION":
            t = mk_task(
                "UNBEDENKLICHKEIT_ANFORDERN", Stage.REGISTRATION.value, "NOTAR",
                "Unbedenklichkeitsbescheinigung (GrESt) überwachen.",
                ["UNBEDENKLICHKEIT_GRESt"], [fid]
            )
            task_by_type["UNBEDENKLICHKEIT_ANFORDERN"] = t
            tasks.append(t)

        if ft == "REQUIRES_PAYMENT_EVIDENCE_FOR_REGISTRATION":
            t = mk_task(
                "ZAHLUNGSNACHWEIS_EINHOLEN", Stage.REGISTRATION.value, "NOTAR",
                "Verkäuferbestätigung + Kontoauszug zum Kaufpreiseingang einholen.",
                ["ZAHLUNGSBESTAETIGUNG_VERKAEUFER", "KONTOAUSZUG"], [fid]
            )
            task_by_type["ZAHLUNGSNACHWEIS_EINHOLEN"] = t
            tasks.append(t)

        if ft == "REQUIRES_MORTGAGE_CANCELLATION":
            t = mk_task(
                "GRUNDSCHULD_LOESCHUNG", Stage.REGISTRATION.value, "NOTAR",
                "Löschung der Grundschuld beantragen.",
                ["LOESCHUNGSBEWILLIGUNG_GRUNDSCHULD"], [fid]
            )
            task_by_type["GRUNDSCHULD_LOESCHUNG"] = t
            tasks.append(t)

        # POST_CLOSING Stage Tasks
        if ft == "REQUIRES_HANDOVER":
            t = mk_task(
                "UEBERGABE_KOORDINIEREN", Stage.POST_CLOSING.value, "NOTAR",
                "Übergabetermin koordinieren und Übergabeprotokoll vorbereiten.",
                ["UEBERGABEPROTOKOLL"], [fid]
            )
            task_by_type["UEBERGABE_KOORDINIEREN"] = t
            tasks.append(t)

        if ft == "REQUIRES_RENT_DEPOSIT_TRANSFER":
            t = mk_task(
                "KAUTION_UEBERTRAGEN", Stage.POST_CLOSING.value, "KAEUFER",
                "Mietkaution vom Verkäufer übernehmen.",
                ["KAUTION_UEBERTRAGUNGSBESTAETIGUNG"], [fid]
            )
            task_by_type["KAUTION_UEBERTRAGEN"] = t
            tasks.append(t)

        if ft == "REQUIRES_TENANT_NOTIFICATION":
            t = mk_task(
                "MIETER_BENACHRICHTIGEN", Stage.POST_CLOSING.value, "KAEUFER",
                "Mieter über Eigentümerwechsel informieren.",
                ["MIETER_MITTEILUNG"], [fid]
            )
            task_by_type["MIETER_BENACHRICHTIGEN"] = t
            tasks.append(t)

    # 3) Gate-Tasks erstellen
    gate_maturity = mk_task(
        "FAELLIGKEITSMITTEILUNG", Stage.MATURITY.value, "NOTAR",
        "Fälligkeitsmitteilung erstellen/versenden (erst nach Voraussetzungen).",
        ["FAELLIGKEITSMITTEILUNG_VERSENDET"], ["GATE"]
    )

    gate_registration = mk_task(
        "UMSCHREIBUNG_BETREIBEN", Stage.REGISTRATION.value, "NOTAR",
        "Umschreibung betreiben (erst nach Eintragungsvoraussetzungen).",
        ["UMSCHREIBUNG_BEANTRAGT"], ["GATE"]
    )

    # 4) Dependencies dynamisch setzen
    # Alle MATURITY-Tasks müssen vor FAELLIGKEITSMITTEILUNG fertig sein
    for t in tasks:
        if t.stage == Stage.MATURITY.value and t.task_type != "FAELLIGKEITSMITTEILUNG":
            gate_maturity.depends_on_task_ids.append(t.task_id)

    # FAELLIGKEITSMITTEILUNG muss vor REGISTRATION-Tasks kommen
    for t in tasks:
        if t.stage == Stage.REGISTRATION.value:
            t.depends_on_task_ids.append(gate_maturity.task_id)
            gate_registration.depends_on_task_ids.append(t.task_id)

    # Gate-Tasks hinzufügen
    tasks.append(gate_maturity)
    tasks.append(gate_registration)

    return tasks


# ============================================================================
# HAUPT-API
# ============================================================================

def parse_urkunde(
    contract_text: str,
    context: Optional[Dict[str, Any]] = None,
    library_reference: Optional[List[Dict[str, Any]]] = None,
    model: str = "gpt-4o-2024-11-20",
    api_key: Optional[str] = None,
    use_deterministic_planner: bool = True
) -> NotarParserOutput:
    """
    Hauptfunktion: Parst eine Urkunde vollständig.

    Workflow:
    1. Text segmentieren
    2. LLM-Extraktion mit Structured Outputs
    3. Optional: Deterministischen Rule-Planner anwenden
    4. Hash für Deduplikation berechnen

    Args:
        contract_text: Der zu parsende Vertragstext
        context: Optional - Kontext-Informationen
        library_reference: Optional - bekannte generelle Bausteine
        model: OpenAI-Modell
        api_key: Optional - OpenAI API Key
        use_deterministic_planner: Ob der deterministische Planner die LLM-Tasks überschreiben soll

    Returns:
        NotarParserOutput mit allen extrahierten Daten

    Raises:
        ImportError: Wenn OpenAI nicht installiert ist
        Exception: Bei API-Fehlern
    """
    if context is None:
        context = {}

    # 1) Segmentierung (optional, verbessert LLM-Qualität)
    segments = segment_paragraphs(contract_text)

    # 2) LLM-Extraktion
    raw_response = call_notar_parser(
        contract_text=contract_text,
        context=context,
        library_reference=library_reference,
        model=model,
        api_key=api_key
    )

    # 3) In typisierte Objekte konvertieren
    output = parse_llm_response(raw_response)

    # 4) Optional: Deterministischen Planner anwenden
    if use_deterministic_planner and output.facts:
        output.tasks = build_workflow_from_facts(output.facts)

    # 5) Dokument-Hash berechnen
    output.source_document_hash = hashlib.sha256(
        contract_text.encode("utf-8")
    ).hexdigest()

    return output


# ============================================================================
# VALIDIERUNG (Optional, für zusätzliche Sicherheit)
# ============================================================================

def validate_parser_output(data: Dict[str, Any]) -> bool:
    """
    Validiert die Parser-Ausgabe gegen das Schema.

    Structured Outputs reduziert den Bedarf an Retries drastisch,
    aber zusätzliche Validierung ist für kritische Anwendungen sinnvoll.

    Args:
        data: Die zu validierende Parser-Ausgabe

    Returns:
        True wenn valide

    Raises:
        jsonschema.ValidationError: Bei Schema-Verletzung
    """
    try:
        from jsonschema import validate
        validate(instance=data, schema=NOTAR_PARSER_JSON_SCHEMA["schema"])
        return True
    except ImportError:
        # jsonschema nicht installiert, überspringen
        return True


# ============================================================================
# HILFSFUNKTIONEN FÜR STREAMLIT-INTEGRATION
# ============================================================================

def get_blocks_by_type(output: NotarParserOutput, block_type: BlockType) -> List[ParserBlock]:
    """Filtert Blocks nach Typ."""
    return [b for b in output.blocks if b.block_type == block_type.value]


def get_facts_by_stage(output: NotarParserOutput, stage: Stage) -> List[ParserFact]:
    """Filtert Facts nach Stage."""
    return [f for f in output.facts if f.stage == stage.value]


def get_tasks_by_stage(output: NotarParserOutput, stage: Stage) -> List[ParserTask]:
    """Filtert Tasks nach Stage."""
    return [t for t in output.tasks if t.stage == stage.value]


def get_generic_candidates(output: NotarParserOutput) -> List[ParserBlock]:
    """Gibt alle Blocks zurück, die als generelle Bausteine erkannt wurden."""
    return [b for b in output.blocks if b.generic_candidate]


def get_issues_by_severity(output: NotarParserOutput, severity: IssueSeverity) -> List[ParserIssue]:
    """Filtert Issues nach Schweregrad."""
    return [i for i in output.issues if i.severity == severity.value]


def get_high_confidence_facts(output: NotarParserOutput, threshold: float = 0.8) -> List[ParserFact]:
    """Gibt Facts mit hoher Konfidenz zurück."""
    return [f for f in output.facts if f.confidence >= threshold]


def get_facts_needing_confirmation(output: NotarParserOutput) -> List[ParserFact]:
    """Gibt Facts zurück, die eine manuelle Bestätigung benötigen."""
    return [f for f in output.facts if f.needs_confirmation]


def get_task_dependencies_graph(tasks: List[ParserTask]) -> Dict[str, List[str]]:
    """
    Erstellt einen Abhängigkeitsgraphen für die Tasks.

    Returns:
        Dict mit task_id -> [abhängige task_ids]
    """
    graph: Dict[str, List[str]] = {}
    for t in tasks:
        graph[t.task_id] = t.depends_on_task_ids
    return graph


def get_unblocked_tasks(tasks: List[ParserTask], completed_task_ids: List[str]) -> List[ParserTask]:
    """
    Gibt alle Tasks zurück, deren Dependencies erfüllt sind.

    Args:
        tasks: Alle Tasks
        completed_task_ids: IDs der bereits abgeschlossenen Tasks

    Returns:
        Liste der jetzt ausführbaren Tasks
    """
    completed_set = set(completed_task_ids)
    unblocked = []

    for t in tasks:
        if t.task_id in completed_set:
            continue  # Bereits erledigt
        if all(dep in completed_set for dep in t.depends_on_task_ids):
            unblocked.append(t)

    return unblocked
