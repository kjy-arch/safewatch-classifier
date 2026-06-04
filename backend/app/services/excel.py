import pandas as pd
import openpyxl
from io import BytesIO
from typing import List, Dict, Any


VALID_SOURCE_TYPES = {"언론", "SNS", "커뮤니티", "유튜브"}


def parse_excel(file_bytes: bytes) -> List[Dict[str, Any]]:
    """
    엑셀 파일을 파싱하여 행 목록으로 반환.
    필수 컬럼: text (원문 텍스트)
    선택 컬럼: source_type, source_url
    """
    df = pd.read_excel(BytesIO(file_bytes), dtype=str)
    df = df.fillna("")

    if "text" not in df.columns:
        raise ValueError("엑셀 파일에 'text' 컬럼이 필요합니다.")

    rows = []
    for _, row in df.iterrows():
        text = str(row.get("text", "")).strip()
        if not text:
            continue

        source_type = str(row.get("source_type", "언론")).strip()
        if source_type not in VALID_SOURCE_TYPES:
            source_type = "언론"

        rows.append({
            "text": text,
            "source_type": source_type,
            "source_url": str(row.get("source_url", "")).strip(),
        })

    return rows


def build_result_excel(original_rows: List[Dict], analysis_results: List[Dict]) -> bytes:
    """
    원본 행 + 분석 결과를 합쳐서 엑셀 파일 바이트로 반환.
    """
    records = []
    for row, result in zip(original_rows, analysis_results):
        records.append({
            "원문":           row["text"],
            "출처":           row["source_type"],
            "URL":            row.get("source_url", ""),
            "거짓점수(0-100)": result.get("false_score", ""),
            "거짓척도":        result.get("false_level", ""),
            "판단이유":        result.get("false_reason", ""),
            "의도유형":        result.get("intent_type", ""),
            "내용유형":        result.get("content_type", ""),
            "연관부서":        result.get("department", ""),
        })

    df = pd.DataFrame(records)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="분석결과")
        ws = writer.sheets["분석결과"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)
    return buf.getvalue()
