import pandas as pd
import openpyxl
from io import BytesIO
from typing import List, Dict, Any


VALID_SOURCE_TYPES = {"언론", "SNS", "커뮤니티", "유튜브"}

# 컬럼명 자동 인식 매핑 (한글/영문 모두 지원)
TEXT_ALIASES = {
    "text", "내용", "텍스트", "본문", "기사내용", "기사본문",
    "게시글", "댓글", "내용물", "원문", "제목", "타이틀"
}
SOURCE_TYPE_ALIASES = {
    "source_type", "출처", "출처유형", "유형", "구분", "type", "분류"
}
SOURCE_URL_ALIASES = {
    "source_url", "url", "링크", "주소", "출처링크", "기사링크", "원문링크"
}


def _find_col(columns, aliases):
    """컬럼명 목록에서 aliases 중 일치하는 첫 번째 컬럼명 반환."""
    cols_lower = {c.strip().lower(): c for c in columns}
    for alias in aliases:
        if alias.lower() in cols_lower:
            return cols_lower[alias.lower()]
    return None


def parse_excel(file_bytes: bytes) -> List[Dict[str, Any]]:
    df = pd.read_excel(BytesIO(file_bytes), dtype=str)
    df = df.fillna("")

    cols = list(df.columns)

    # 컬럼명 자동 인식
    text_col = _find_col(cols, TEXT_ALIASES)
    source_type_col = _find_col(cols, SOURCE_TYPE_ALIASES)
    source_url_col = _find_col(cols, SOURCE_URL_ALIASES)

    # 인식된 컬럼이 없으면 순서 기반으로 처리 (첫 번째 컬럼 = 원문)
    if not text_col:
        text_col = cols[0] if cols else None

    if not text_col:
        raise ValueError("엑셀에서 텍스트 컬럼을 찾을 수 없습니다.")

    rows = []
    for _, row in df.iterrows():
        text = str(row[text_col]).strip()
        if not text or text == "nan":
            continue

        source_type = str(row[source_type_col]).strip() if source_type_col else "언론"
        if source_type not in VALID_SOURCE_TYPES:
            source_type = "언론"

        source_url = str(row[source_url_col]).strip() if source_url_col else ""

        rows.append({
            "text": text,
            "source_type": source_type,
            "source_url": source_url,
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
