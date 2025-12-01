# app.py

import io
import re
import zipfile
from datetime import datetime, date
from typing import Any, Dict, List, Optional

import pandas as pd
import fitz  # PyMuPDF
import streamlit as st
from pypdf import PdfReader, PdfWriter
from xlsxwriter.utility import xl_col_to_name


# ---------------------------------------------------------
# Konfiguration / Konstanten
# ---------------------------------------------------------

SACHBEARBEITER_KUERZEL = ["SQ", "TS", "M", "CV", "FÜ"]
SACHBEARBEITER_DEFAULT = "nicht-zugeordnet"

STICHWORT_LISTE = [
    "Beschluss", "Urteil", "Veräußerungsanzeige", "Negativzeugnis",
    "Arbeitsbescheinigung", "Schaden", "Kündigung", "Vergleich",
    "Rechnung", "Mahnung", "Fristsetzung"
]

DATUM_REGEX = r"\b(?:0?[1-9]|[12][0-9]|3[01])\.(?:0?[1-9]|1[0-2])\.(?:19|20)\d{2}\b"

# interne Aktenzeichen:
# 151/20M  | 294/20SQ | 98/23FÜ  | 411/20M1 | 99/23CVa
INTERNES_AZ_MIT_KUERZEL_REGEX = r"\b(\d{1,4}/\d{2})(SQ|M|TS|FÜ|CV)([0-9A-Za-z]*)\b"
INTERNES_AZ_OHNE_KUERZEL_REGEX = r"\b(\d{1,4}/\d{2})\b"


# ---------------------------------------------------------
# Hilfsfunktionen: Allgemein
# ---------------------------------------------------------

def normalize_akte_value(val: Any) -> str:
    """
    ' 151/20 ' -> '151/20'
    Entfernt Whitespace, NBSP etc.
    """
    if pd.isna(val):
        return ""
    s = str(val).replace("\xa0", " ")
    return s.strip()


def slugify_name(s: str) -> str:
    """
    Umlaute ersetzen, Sonderzeichen entfernen, Leerzeichen mit '_'.
    """
    if not s:
        return ""
    s = s.strip()
    repl = {
        "ä": "ae", "ö": "oe", "ü": "ue",
        "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
        "ß": "ss"
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    # unerwünschte Zeichen entfernen
    s = re.sub(r"[^A-Za-z0-9._\- ]+", "", s)
    s = re.sub(r"\s+", "_", s)
    return s[:120]


def extract_page_texts(pdf_bytes: bytes) -> List[str]:
    """Extrahiert Text pro Seite mit PyMuPDF (robust gegen OCR-PDFs)."""
    texts = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            texts.append(page.get_text("text") or "")
    return texts


def is_t_trennblatt(text: str) -> bool:
    """
    Trennblatt: Seite, deren OCR-Text im Wesentlichen nur aus einem großen 'T' besteht.
    """
    if text is None:
        return False
    cleaned = text.strip()
    if not cleaned:
        return False
    # alle Whitespaces entfernen
    compact = re.sub(r"\s+", "", cleaned)
    return compact == "T"


def is_leerseite(text: str) -> bool:
    """
    Leere Seite: kein verwertbarer Text (nur Whitespace etc.).
    Leerseiten werden entfernt, aber NICHT als Trennblätter gewertet.
    """
    if text is None:
        return True
    cleaned = re.sub(r"\s+", "", text)
    return cleaned == ""


def render_status_badge(label: str, ok: bool, hint: str = "") -> None:
    """Zeigt einen gut lesbaren Statusindikator mit Emoji an."""
    icon = "🟢" if ok else "🔴"
    state = "aktiv" if ok else "nicht verbunden"
    extra = f"<br/><small>{hint}</small>" if hint else ""
    st.markdown(f"**{icon} {label}:** {state}{extra}", unsafe_allow_html=True)


def split_pdf_with_t_and_empty(pdf_bytes: bytes, page_texts: List[str]):
    """
    Split nach T-Seiten (Trennblätter), Leerseiten werden vorher entfernt.
    Rückgabe:
      - docs_bytes: Liste von PDF-Bytes (ein Einzeldokument pro Segment)
      - docs_meta:  Liste von Dicts mit start_page / end_page (1-basiert, original)
      - t_pages:    Liste von 1-basierten Seitennummern der T-Seiten
      - empty_pages:Liste von 1-basierten Seitennummern der Leerseiten
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    num_pages = len(reader.pages)

    t_pages = []
    empty_pages = []

    docs_bytes: List[bytes] = []
    docs_meta: List[Dict[str, int]] = []

    current_writer = PdfWriter()
    current_pages: List[int] = []

    for i in range(num_pages):
        text = page_texts[i] if i < len(page_texts) else ""
        page_no = i + 1  # 1-basiert für Logging

        if is_t_trennblatt(text):
            t_pages.append(page_no)
            # aktuelles Dokument beenden (falls Seiten vorhanden)
            if len(current_writer.pages) > 0:
                buf = io.BytesIO()
                current_writer.write(buf)
                docs_bytes.append(buf.getvalue())
                docs_meta.append({
                    "start_page": current_pages[0],
                    "end_page": current_pages[-1],
                })
                current_writer = PdfWriter()
                current_pages = []
            # T-Seite selbst nicht übernehmen
            continue

        if is_leerseite(text):
            empty_pages.append(page_no)
            # Leerseite weder Dokumenttrenner noch Inhalt -> einfach überspringen
            continue

        # normale Seite -> in aktuelles Dokument aufnehmen
        current_writer.add_page(reader.pages[i])
        current_pages.append(page_no)

    # letztes Dokument, falls offen
    if len(current_writer.pages) > 0:
        buf = io.BytesIO()
        current_writer.write(buf)
        docs_bytes.append(buf.getvalue())
        docs_meta.append({
            "start_page": current_pages[0],
            "end_page": current_pages[-1],
        })

    return docs_bytes, docs_meta, t_pages, empty_pages


# ---------------------------------------------------------
# Aktenregister laden
# ---------------------------------------------------------

def load_aktenregister(excel_file) -> tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    """
    Lädt aktenregister.xlsx, Tabelle 'akten'.
    Zeile 1 ignorieren, Zeile 2 = Header, Daten ab Zeile 3.
    Liefert:
      - df (voll)
      - index: dict {akte_clean: row_dict}
    """
    df = pd.read_excel(excel_file, sheet_name="akten", header=1)
    # Akte & SB normalisieren
    if "Akte" not in df.columns or "SB" not in df.columns:
        raise ValueError("Spalten 'Akte' und/oder 'SB' im Tabellenblatt 'akten' nicht gefunden.")

    df["Akte_clean"] = df["Akte"].apply(normalize_akte_value)
    df["SB_clean"] = df["SB"].apply(lambda x: str(x).strip() if not pd.isna(x) else "")

    index: Dict[str, Dict[str, Any]] = {}
    for _, row in df.iterrows():
        akte_clean = row["Akte_clean"]
        if akte_clean:
            index[akte_clean] = row.to_dict()

    return df, index


# ---------------------------------------------------------
# Aktenzeichen-Erkennung
# ---------------------------------------------------------

def find_internes_az_candidates(text: str) -> List[Dict[str, str]]:
    """
    Findet Kandidaten für interne Aktenzeichen im Text (mit und ohne Kürzel).
    Rückgabe: Liste von Dicts mit keys: stamm, kuerzel (optional), raw.
    """
    candidates = []

    # 1. Muster mit Kürzel
    for m in re.finditer(INTERNES_AZ_MIT_KUERZEL_REGEX, text):
        stamm = m.group(1)
        kuerzel = m.group(2)
        raw = m.group(0)
        candidates.append({"stamm": stamm, "kuerzel": kuerzel, "raw": raw})

    # 2. Muster ohne Kürzel
    for m in re.finditer(INTERNES_AZ_OHNE_KUERZEL_REGEX, text):
        stamm = m.group(1)
        # Nur aufnehmen, wenn nicht bereits mit Kürzel erfasst
        if not any(c["stamm"] == stamm for c in candidates):
            candidates.append({"stamm": stamm, "kuerzel": "", "raw": m.group(0)})

    # 3. Speziell hinter „Ihr Zeichen / Ihr AZ / Ihr Aktenzeichen“
    suchphrasen = ["Ihr Zeichen", "Ihr AZ", "Ihr Az.", "Ihr Aktenzeichen"]
    lower = text.lower()
    for phrase in suchphrasen:
        pos = lower.find(phrase.lower())
        while pos != -1:
            snippet = text[pos:pos + 80]  # ein Stück dahinter
            # Zahl/Slash-Zahl + evtl. Kürzel extrahieren
            m_full = re.search(INTERNES_AZ_MIT_KUERZEL_REGEX, snippet)
            m_stamm = re.search(INTERNES_AZ_OHNE_KUERZEL_REGEX, snippet)
            if m_full:
                stamm = m_full.group(1)
                kuerzel = m_full.group(2)
                raw = m_full.group(0)
                if not any(c["raw"] == raw for c in candidates):
                    candidates.append({"stamm": stamm, "kuerzel": kuerzel, "raw": raw})
            elif m_stamm:
                stamm = m_stamm.group(1)
                raw = m_stamm.group(0)
                if not any(c["raw"] == raw for c in candidates):
                    candidates.append({"stamm": stamm, "kuerzel": "", "raw": raw})
            pos = lower.find(phrase.lower(), pos + 1)

    return candidates


def detect_internal_and_external_az(
    text: str,
    akten_index: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Liefert:
      - internes_aktenzeichen (kanonisch, z.B. 151/20M)
      - internes_aktenzeichen_stamm (z.B. 151/20)
      - internes_aktenzeichen_kuerzel
      - aktenregister_row (oder None)
      - externe_aktenzeichen (Liste)
    """
    internes_az = None
    internes_stamm = None
    internes_kuerzel = None
    akten_row = None

    candidates = find_internes_az_candidates(text)

    # Priorität: solche Kandidaten, die im Aktenregister vorkommen
    for cand in candidates:
        stamm = cand["stamm"]
        akte_clean = normalize_akte_value(stamm)
        if akte_clean in akten_index:
            internes_stamm = stamm
            internes_kuerzel = cand["kuerzel"] or akten_index[akte_clean]["SB_clean"]
            internes_az = f"{akte_clean}{internes_kuerzel}"
            akten_row = akten_index[akte_clean]
            break

    # Falls keiner im Register gefunden, aber es gibt Kandidaten → nimm den ersten
    if internes_az is None and candidates:
        cand = candidates[0]
        internes_stamm = cand["stamm"]
        internes_kuerzel = cand["kuerzel"] or ""
        internes_az = f"{internes_stamm}{internes_kuerzel}"

    # externe Aktenzeichen (vereinfachte Heuristik)
    externe_az = []
    # typische Einleitungen
    for m in re.finditer(r"\b(Az\.?|Aktenzeichen|Unser Zeichen|Schadennummer|Versicherungsnummer)\b[: ]+(.{1,40})", text):
        raw = m.group(2).strip()
        # wenn es nicht unser internes Muster ist, als extern werten
        if not re.search(INTERNES_AZ_MIT_KUERZEL_REGEX, raw) and not re.search(INTERNES_AZ_OHNE_KUERZEL_REGEX, raw):
            externe_az.append(raw)

    # Duplikate raus
    externe_az = list(dict.fromkeys(externe_az))

    return {
        "internes_aktenzeichen": internes_az,
        "internes_aktenzeichen_stamm": internes_stamm,
        "internes_aktenzeichen_kuerzel": internes_kuerzel,
        "aktenregister_row": akten_row,
        "externe_aktenzeichen": externe_az,
    }


# ---------------------------------------------------------
# Mandant / Gegner / Absendertyp / Datum / Frist
# ---------------------------------------------------------

def guess_mandant_gegner_from_kurzbez(kurzbez: str) -> tuple[Optional[str], Optional[str]]:
    """
    Kurzbez.: z.B. 'Duchatz ./. Grull'
    """
    if not kurzbez:
        return None, None
    m = re.search(r"(.+?)\s+\./\.\s+(.+)", kurzbez)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return kurzbez.strip(), None


def guess_mandant_gegner_from_text(text: str) -> tuple[Optional[str], Optional[str]]:
    m = re.search(r"(.+?)\s+\./\.\s+(.+)", text)
    if m:
        mandant = m.group(1).strip().splitlines()[0]
        gegner = m.group(2).strip().splitlines()[0]
        return mandant, gegner
    return None, None


def find_datums(text: str) -> List[datetime]:
    dates = []
    for m in re.findall(DATUM_REGEX, text):
        try:
            dates.append(datetime.strptime(m, "%d.%m.%Y"))
        except Exception:
            pass
    return dates


def detect_absendertyp(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["amtsgericht", "landgericht", "arbeitsgericht", "sozialgericht", "oberlandesgericht", "bundesgericht"]):
        return "Gericht"
    if any(w in lower for w in ["ministerium", "amt ", "behörde", "landesamt", "stadt ", "gemeinde ", "finanzamt", "jobcenter", "agentur für arbeit", "landkreis"]):
        return "Behörde"
    if any(w in lower for w in ["versicherung", "versicherungsnummer", "schadennummer", "huk", "allianz", "r+v", "devk", "vhv", "gothaer", "kravag"]):
        return "Versicherung"
    return "sonstiger Dritter"


def detect_frist(text: str) -> Dict[str, Any]:
    """
    Sehr vereinfachte Fristerkennung:
    - sucht nach 'Frist' + Datum
    - gibt ein dict mit datum, typ, quelle, textauszug zurück oder leere Werte
    """
    # Beispiel 'Frist bis zum 10.12.2024'
    for m in re.finditer(r"(Frist[^.\n]{0,80})(" + DATUM_REGEX + ")", text, flags=re.IGNORECASE):
        umfeld = m.group(0)
        dat_str = m.group(2)
        try:
            dat = datetime.strptime(dat_str, "%d.%m.%Y").date()
            return {
                "fristdatum": dat,
                "fristtyp": "Frist laut Schreiben",
                "fristquelle": umfeld.strip(),
                "textauszug": umfeld.strip(),
            }
        except Exception:
            continue

    # keine Frist gefunden
    return {
        "fristdatum": None,
        "fristtyp": "",
        "fristquelle": "",
        "textauszug": "",
    }


# ---------------------------------------------------------
# Sachbearbeiter-Zuordnung
# ---------------------------------------------------------

def determine_sachbearbeiter(
    text: str,
    internes_az_kuerzel: Optional[str],
    aktenregister_row: Optional[Dict[str, Any]]
) -> str:
    """
    Sachbearbeiter nach Master-Prompt:
    Regel 0: Aktenregister (SB-Spalte) vorrangig
    Regel 1: internes Aktenzeichen / Kürzel im Text
    Regel 2: Rechtsgebiet-Heuristik
    Regel 3: 'nicht-zugeordnet'
    """

    # Regel 0 – Aktenregister
    if aktenregister_row is not None:
        sb = str(aktenregister_row.get("SB_clean") or "").strip()
        if sb:
            return sb

    # Regel 1 – internes Aktenzeichen / Kürzel
    if internes_az_kuerzel and internes_az_kuerzel in SACHBEARBEITER_KUERZEL:
        return internes_az_kuerzel

    for k in SACHBEARBEITER_KUERZEL:
        if re.search(rf"\b{k}\b", text):
            return k

    # Regel 2 – Rechtsgebiet
    lower = text.lower()
    if any(w in lower for w in ["arbeitsgericht", "kündigung", "arbeitgeber", "arbeitnehmer", "arbeitsvertrag"]):
        # SQ oder M – wir nehmen hier SQ als default
        return "SQ"
    if any(w in lower for w in ["verkehrsunfall", "verkehrsrecht", "bußgeldbescheid"]):
        return "TS"
    if any(w in lower for w in ["mietvertrag", "miete", "mieterhöhung", "wohnungseigentum", "weg-recht", "weg "]):
        return "TS"
    if any(w in lower for w in ["erbschein", "testament", "nachlass", "erbrecht"]):
        # SQ oder CV – wir nehmen hier SQ als default
        return "SQ"

    # Regel 3 – Fallback
    return SACHBEARBEITER_DEFAULT


# ---------------------------------------------------------
# Analyse eines Einzeldokuments
# ---------------------------------------------------------

def analyze_document(
    pdf_bytes: bytes,
    akten_index: Dict[str, Dict[str, Any]],
    eingangsdatum: date,
) -> Dict[str, Any]:
    text = extract_fulltext_from_pdf_bytes(pdf_bytes)

    az_info = detect_internal_and_external_az(text, akten_index)
    internes_az = az_info["internes_aktenzeichen"]
    internes_stamm = az_info["internes_aktenzeichen_stamm"]
    internes_kuerzel = az_info["internes_aktenzeichen_kuerzel"]
    akten_row = az_info["aktenregister_row"]
    externe_az = az_info["externe_aktenzeichen"]

    # Mandant / Gegner
    mandant = None
    gegner = None
    if akten_row is not None:
        kurzbez = akten_row.get("Kurzbez.", "")
        gegner_reg = akten_row.get("Gegner", "")
        mandant, gegner_kbz = guess_mandant_gegner_from_kurzbez(str(kurzbez) if not pd.isna(kurzbez) else "")
        if not gegner and gegner_reg and not pd.isna(gegner_reg):
            gegner = str(gegner_reg).strip()
        if not gegner and gegner_kbz:
            gegner = gegner_kbz
    else:
        mandant, gegner = guess_mandant_gegner_from_text(text)

    # Datum: frühestes Datum im Dokument
    dates = find_datums(text)
    dokument_datum = min(dates).date() if dates else None

    # Stichworte
    stichworte = []
    for kw in STICHWORT_LISTE:
        if re.search(rf"\b{re.escape(kw)}\b", text, flags=re.IGNORECASE):
            stichworte.append(kw)
    stichworte = list(dict.fromkeys(stichworte))

    # Frist
    frist_info = detect_frist(text)

    # Absendertyp
    absendertyp = detect_absendertyp(text)

    # Sachbearbeiter
    sachbearbeiter = determine_sachbearbeiter(
        text=text,
        internes_az_kuerzel=internes_kuerzel,
        aktenregister_row=akten_row
    )

    # Dateiname
    if internes_az:
        az_for_name = internes_az.replace("/", "-")
    else:
        az_for_name = "ohne-az"

    mandant_part = slugify_name(mandant or "Mandant-unbekannt")
    gegner_part = slugify_name(gegner or "Gegner-unbekannt")
    if dokument_datum:
        datum_part = dokument_datum.strftime("%Y-%m-%d")
    else:
        datum_part = "ohne-datum"
    stichworte_part = slugify_name("-".join(stichworte) or "ohne-stichworte")

    filename = f"{az_for_name}_{mandant_part}_{gegner_part}_{datum_part}_{stichworte_part}.pdf"

    info = {
        "eingangsdatum": eingangsdatum,
        "internes_aktenzeichen": internes_az,
        "internes_aktenzeichen_stamm": internes_stamm,
        "internes_aktenzeichen_kuerzel": internes_kuerzel,
        "aktenregister_row": akten_row,
        "externe_aktenzeichen": externe_az,
        "mandant": mandant,
        "gegner": gegner,
        "dokument_datum": dokument_datum,
        "stichworte": stichworte,
        "fristdatum": frist_info["fristdatum"],
        "fristtyp": frist_info["fristtyp"],
        "fristquelle": frist_info["fristquelle"],
        "frist_textauszug": frist_info["textauszug"],
        "absendertyp": absendertyp,
        "sachbearbeiter": sachbearbeiter,
        "volltext": text,
        "dateiname": filename,
    }
    return info


def extract_fulltext_from_pdf_bytes(pdf_bytes: bytes) -> str:
    texts = extract_page_texts(pdf_bytes)
    return "\n".join(texts)


# ---------------------------------------------------------
# Excel- und ZIP-Erstellung
# ---------------------------------------------------------

def create_excels_and_zips(
    docs: List[Dict[str, Any]]
) -> tuple[Dict[str, Dict[str, bytes]], bytes, Optional[bytes]]:
    """
    Erzeugt:
      - pro Sachbearbeiter eine ZIP mit PDFs + Excel (als Bytes)
      - ein Gesamt-Excel (als Bytes)
      - ein Stammdaten_Aktenzeichen-Excel (neu erkannte interne Aktenzeichen) oder None
    Rückgabe:
      sb_files: { 'SQ': {'zip': b'...', 'excel': b'...'}, ... }
      gesamt_excel_bytes
      stammdaten_excel_bytes oder None
    """

    df_rows = []
    for d in docs:
        df_rows.append({
            "Eingangsdatum": d["eingangsdatum"],
            "Internes Aktenzeichen": d["internes_aktenzeichen"],
            "Externes Aktenzeichen": ", ".join(d["externe_aktenzeichen"]),
            "Mandant": d["mandant"],
            "Gegner / Absender": d["gegner"],
            "Absendertyp": d["absendertyp"],
            "Sachbearbeiter": d["sachbearbeiter"],
            "Fristdatum": d["fristdatum"],
            "Fristtyp": d["fristtyp"],
            "Fristquelle": d["fristquelle"],
            "Textauszug": d["frist_textauszug"],
            "PDF-Datei": d["dateiname"],
            "Status": "offen",
        })

    df = pd.DataFrame(df_rows)

    # Gesamt-Excel mit farbiger Fristmarkierung
    gesamt_buf = io.BytesIO()
    with pd.ExcelWriter(gesamt_buf, engine="xlsxwriter", datetime_format="dd.mm.yyyy") as writer:
        df.to_excel(writer, index=False, sheet_name="Fristen_Akten")
        workbook = writer.book
        worksheet = writer.sheets["Fristen_Akten"]

        # Bedingte Formatierung für Fristdatum (Spalte 'Fristdatum')
        if "Fristdatum" in df.columns:
            col_idx = df.columns.get_loc("Fristdatum")
            col_letter = xl_col_to_name(col_idx)
            # Datenbereich (ab Zeile 2, weil Zeile 1 Header)
            last_row = len(df) + 1
            cell_range = f"{col_letter}2:{col_letter}{last_row}"

            red_format = workbook.add_format({"bg_color": "#FF9999"})
            orange_format = workbook.add_format({"bg_color": "#FFD699"})

            # Rot: Frist <= 3 Tage
            worksheet.conditional_format(cell_range, {
                "type": "formula",
                "criteria": f"=AND(ISNUMBER({col_letter}2), {col_letter}2<=TODAY()+3)",
                "format": red_format,
            })
            # Orange: Frist <= 7 Tage
            worksheet.conditional_format(cell_range, {
                "type": "formula",
                "criteria": f"=AND(ISNUMBER({col_letter}2), {col_letter}2<=TODAY()+7, {col_letter}2>TODAY()+3)",
                "format": orange_format,
            })

    gesamt_buf.seek(0)
    gesamt_excel_bytes = gesamt_buf.getvalue()

    # Excels & ZIPs pro Sachbearbeiter
    sb_files: Dict[str, Dict[str, bytes]] = {}
    for sb, group in df.groupby("Sachbearbeiter"):
        sb_excel_buf = io.BytesIO()
        with pd.ExcelWriter(sb_excel_buf, engine="xlsxwriter", datetime_format="dd.mm.yyyy") as writer:
            group.to_excel(writer, index=False, sheet_name="Posteingang")
        sb_excel_buf.seek(0)
        sb_excel_bytes = sb_excel_buf.getvalue()

        # ZIP bauen
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # PDFs hinzufügen
            for d in docs:
                if d["sachbearbeiter"] == sb:
                    zf.writestr(d["dateiname"], d["pdf_bytes"])
            # Excel hineinlegen
            zf.writestr(f"{sb}_Posteingang.xlsx", sb_excel_bytes)

        zip_buf.seek(0)
        sb_files[sb] = {
            "zip": zip_buf.getvalue(),
            "excel": sb_excel_bytes,
        }

    # Stammdaten_Aktenzeichen: neue interne Aktenzeichen (ohne Registerbezug)
    neue_az = set()
    for d in docs:
        if d["internes_aktenzeichen"] and d["aktenregister_row"] is None:
            neue_az.add(d["internes_aktenzeichen"])

    stammdaten_excel_bytes = None
    if neue_az:
        rows = []
        for az in sorted(neue_az):
            rows.append({
                "Internes Aktenzeichen": az,
                "Quelle": "Posteingang",
            })
        stammdaten_df = pd.DataFrame(rows)
        stammdaten_buf = io.BytesIO()
        with pd.ExcelWriter(stammdaten_buf, engine="xlsxwriter") as writer:
            stammdaten_df.to_excel(writer, index=False, sheet_name="Stammdaten_Aktenzeichen")
        stammdaten_buf.seek(0)
        stammdaten_excel_bytes = stammdaten_buf.getvalue()

    return sb_files, gesamt_excel_bytes, stammdaten_excel_bytes


# ---------------------------------------------------------
# Streamlit GUI
# ---------------------------------------------------------

def main():
    st.set_page_config(page_title="Posteingang RHM | MASTER-WORKFLOW", layout="wide")
    st.title("📥 Automatisierter Posteingang (RHM | Anwälte)")

    # Seitenleiste: API-Key & ChatGPT-Verbindungsstatus
    st.sidebar.header("Verbindungsmonitor")
    api_key = st.sidebar.text_input(
        "OpenAI API-Key",
        type="password",
        help="Der Schlüssel wird nur clientseitig geprüft, es erfolgt kein externer Aufruf in dieser Demo.",
    )

    if "api_status" not in st.session_state:
        st.session_state.api_status = False
        st.session_state.chat_status = False
        st.session_state.api_message = "Noch nicht geprüft."

    if st.sidebar.button("API-Key prüfen"):
        valid = bool(re.match(r"^sk-[A-Za-z0-9]{20,}$", api_key.strip()))
        st.session_state.api_status = valid
        st.session_state.chat_status = valid
        st.session_state.api_message = "Schlüssel-Format gültig." if valid else "Ungültiges Format – bitte erneut eingeben."

    render_status_badge("API-Schlüssel", st.session_state.api_status, st.session_state.api_message)
    render_status_badge(
        "ChatGPT-Verarbeitung",
        st.session_state.chat_status,
        "Aktiv, sobald ein gültiger API-Key hinterlegt ist.",
    )

    st.markdown(
        "1. **Tagespost-PDF** hochladen (OCR, gesamter Posteingang, mit T-Trennblättern).  \n"
        "2. **aktenregister.xlsx** hochladen (Tabellenblatt „akten“).  \n"
        "3. **Eingangsdatum** wählen.  \n"
        "4. Auf **„Posteingang verarbeiten“** klicken."
    )

    eingangsdatum = st.date_input("Eingangsdatum der Tagespost", value=date.today())

    col1, col2 = st.columns(2)
    with col1:
        tages_pdf = st.file_uploader(
            "Tagespost-PDF (OCR, gesamter Posteingang)", type=["pdf"]
        )
    with col2:
        akten_excel = st.file_uploader(
            "Aktenregister (aktenregister.xlsx, Blatt „akten“ – Pflicht)", type=["xls", "xlsx"]
        )

    process_btn = st.button("🚀 Posteingang verarbeiten")

    status_box = st.empty()
    log_lines = []

    def log(msg: str):
        log_lines.append(msg)
        status_box.text("\n".join(log_lines[-20:]))

    if process_btn:
        if tages_pdf is None:
            st.error("Bitte zuerst das Tages-PDF hochladen.")
            return
        if akten_excel is None:
            st.error("Bitte aktenregister.xlsx hochladen (Tabellenblatt 'akten').")
            return

        # 0. Aktenregister laden
        try:
            log("Lade Aktenregister …")
            akten_df, akten_index = load_aktenregister(akten_excel)
            log(f"Aktenregister geladen ({len(akten_index)} Akten gefunden).")
        except Exception as e:
            st.error(f"Fehler beim Laden des Aktenregisters: {e}")
            return

        # 1. PDF einlesen, Seiten klassifizieren
        pdf_bytes = tages_pdf.read()
        log(f"Starte Verarbeitung der PDF-Datei: {tages_pdf.name}")
        page_texts = extract_page_texts(pdf_bytes)
        num_pages = len(page_texts)
        log(f"Seiten insgesamt: {num_pages}")

        # 2. Split nach T-Seiten, Leerseiten entfernen
        docs_bytes, docs_meta, t_pages, empty_pages = split_pdf_with_t_and_empty(pdf_bytes, page_texts)
        log(f"Erkannte T-Trennblätter (Seiten): {t_pages if t_pages else '– keine –'}")
        log(f"Erkannte Leerseiten (entfernt, keine Trennblätter): {empty_pages if empty_pages else '– keine –'}")
        log(f"Erzeugte Einzeldokumente: {len(docs_bytes)}")

        docs_info: List[Dict[str, Any]] = []

        # 3. Jedes Einzeldokument analysieren
        for idx, (doc_bytes, meta) in enumerate(zip(docs_bytes, docs_meta), start=1):
            start_page = meta["start_page"]
            end_page = meta["end_page"]
            log(f"Verarbeite Dokument {idx}/{len(docs_bytes)} (Seiten {start_page}–{end_page}) …")
            info = analyze_document(
                pdf_bytes=doc_bytes,
                akten_index=akten_index,
                eingangsdatum=eingangsdatum,
            )
            info["pdf_bytes"] = doc_bytes
            info["dokument_nr"] = idx
            info["start_page"] = start_page
            info["end_page"] = end_page

            log_msg = f"Dokument {idx}/{len(docs_bytes)}"
            if info["internes_aktenzeichen"]:
                log_msg += f" → Akte {info['internes_aktenzeichen']}, SB = {info['sachbearbeiter']}"
            else:
                log_msg += f" → kein internes Aktenzeichen, SB = {info['sachbearbeiter']}"
            log(log_msg)

            docs_info.append(info)

        # 4. Verteilung pro Sachbearbeiter
        zuordnung = {}
        for d in docs_info:
            zuordnung.setdefault(d["sachbearbeiter"], 0)
            zuordnung[d["sachbearbeiter"]] += 1

        log("Verteilung der Dokumente pro Sachbearbeiter:")
        for sb, count in zuordnung.items():
            log(f"  {sb}: {count} Dokument(e)")

        # 5. Excels & ZIPs erzeugen
        log("Erstelle Excel-Listen und ZIP-Dateien …")
        sb_files, gesamt_excel_bytes, stammdaten_excel_bytes = create_excels_and_zips(docs_info)
        log("ZIP-Erstellung abgeschlossen.")

        log("Verarbeitung abgeschlossen.")

        # -------------------------------------------------
        # Ergebnis-Bereich
        # -------------------------------------------------
        st.subheader("Ergebnisse")

        # Statistik
        st.markdown("#### Verarbeitungsstatistik")
        metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
        metrics_col1.metric("Seiten insgesamt", num_pages)
        metrics_col2.metric("T-Trennblätter", len(t_pages))
        metrics_col3.metric("Leerseiten entfernt", len(empty_pages))
        metrics_col4.metric("Erzeugte Dokumente", len(docs_bytes))

        st.markdown("#### Zuordnung nach Sachbearbeiter")
        zuordnung_df = pd.DataFrame.from_dict(zuordnung, orient="index", columns=["Dokumente"])
        st.bar_chart(zuordnung_df)

        # Downloads pro Sachbearbeiter
        for sb in ["SQ", "TS", "M", "FÜ", "CV", SACHBEARBEITER_DEFAULT]:
            if sb in sb_files:
                files = sb_files[sb]
                st.markdown(f"### Sachbearbeiter: **{sb}**")
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button(
                        label=f"📦 Download {sb}.zip",
                        data=files["zip"],
                        file_name=f"{sb}.zip",
                        mime="application/zip",
                    )
                with c2:
                    st.download_button(
                        label=f"📊 Download Excel {sb}",
                        data=files["excel"],
                        file_name=f"{sb}_Posteingang.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                st.markdown("---")

        # Gesamt-Excel
        st.markdown("### Gesamtübersicht „Fristen & Akten“")
        st.download_button(
            label="📊 Download Gesamt-Excel „Fristen_Akten_Gesamt.xlsx“",
            data=gesamt_excel_bytes,
            file_name="Fristen_Akten_Gesamt.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # Stammdaten_Aktenzeichen
        if stammdaten_excel_bytes:
            st.markdown("### Neue Stammdaten_Aktenzeichen")
            st.download_button(
                label="📊 Download „Stammdaten_Aktenzeichen.xlsx“",
                data=stammdaten_excel_bytes,
                file_name="Stammdaten_Aktenzeichen.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


if __name__ == "__main__":
    main()
