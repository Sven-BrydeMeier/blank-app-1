"""
Module für spezialisierte Funktionen der Notarplattform

Dieses Paket enthält:
- urkundenparser: LLM-basierte Extraktion von Textbausteinen, Facts und Workflow-Tasks
"""

from .urkundenparser import (
    # Hauptfunktionen
    parse_urkunde,
    segment_paragraphs,
    build_workflow_from_facts,
    match_generic_block,
    normalize_for_hash,
    block_hash,

    # Datenklassen
    ParserMeta,
    ParserBlock,
    BlockConstraints,
    GenericMatch,
    BlockVariant,
    SourceRef,
    ParserFact,
    ParserTask,
    ParserIssue,
    NotarParserOutput,

    # Konstanten
    NOTAR_PARSER_SYSTEM_PROMPT,
    NOTAR_PARSER_JSON_SCHEMA,

    # Enums
    BlockType,
    Stage,
    MatchType,
    IssueSeverity,
)

__all__ = [
    # Hauptfunktionen
    "parse_urkunde",
    "segment_paragraphs",
    "build_workflow_from_facts",
    "match_generic_block",
    "normalize_for_hash",
    "block_hash",

    # Datenklassen
    "ParserMeta",
    "ParserBlock",
    "BlockConstraints",
    "GenericMatch",
    "BlockVariant",
    "SourceRef",
    "ParserFact",
    "ParserTask",
    "ParserIssue",
    "NotarParserOutput",

    # Konstanten
    "NOTAR_PARSER_SYSTEM_PROMPT",
    "NOTAR_PARSER_JSON_SCHEMA",

    # Enums
    "BlockType",
    "Stage",
    "MatchType",
    "IssueSeverity",
]
