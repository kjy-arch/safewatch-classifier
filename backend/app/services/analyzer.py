import json
from google import genai
from app.core.config import settings
from app.core.database import supabase
from app.services.doc_service import find_relevant_docs

client = genai.Client(api_key=settings.GEMINI_API_KEY)

SYSTEM_PROMPT = """당신은 병무청 언론 분류 전문가입니다.
주어진 텍스트를 분석하여 아래 항목을 JSON 형식으로 반환하세요.

반환 형식 (반드시 이 JSON만 반환):
{
  "false_score": 0~100 사이의 정수 (0=완전한 사실, 100=완전한 거짓),
  "false_level": "낮음" | "중간" | "높음",
  "false_reason": 판단 이유 한 줄 (30자 이내),
  "department_keyword": 연관 부서를 나타내는 핵심 키워드 하나
}

판단 기준:
- false_score 0~33 → false_level: 낮음
- false_score 34~66 → false_level: 중간
- false_score 67~100 → false_level: 높음
- 병무청에 불리하거나 허위일 가능성이 높을수록 점수를 높게 부여
- department_keyword는 텍스트에서 추출한 핵심 업무 키워드 (예: 신체검사, 사회복무, 입영 등)"""


def _match_department(keyword: str, departments: list) -> str | None:
    """키워드를 부서 keywords 배열과 매칭하여 부서 ID 반환."""
    if not keyword:
        return None
    keyword_lower = keyword.lower()
    for dept in departments:
        for kw in dept.get("keywords", []):
            if kw in keyword_lower or keyword_lower in kw:
                return dept["id"]
    return None


def analyze_batch(batch_id: str):
    """배치 내 모든 articles를 Gemini로 분석하고 결과를 Supabase에 저장."""
    articles = (
        supabase.table("articles")
        .select("id, original_text, source_type")
        .eq("batch_id", batch_id)
        .execute()
        .data
    )
    departments = supabase.table("departments").select("id, name, keywords").execute().data

    analyzed = 0
    for article in articles:
        try:
            result = _analyze_single(article["original_text"], article["source_type"])
            dept_id = _match_department(result.get("department_keyword", ""), departments)

            supabase.table("articles").update({
                "false_score": result["false_score"],
                "false_level": result["false_level"],
                "false_reason": result["false_reason"],
                "department_id": dept_id,
            }).eq("id", article["id"]).execute()

            analyzed += 1
        except Exception:
            continue

    supabase.table("batches").update({"analyzed_rows": analyzed}).eq("id", batch_id).execute()
    return {"analyzed": analyzed, "total": len(articles)}


def _analyze_single(text: str, source_type: str) -> dict:
    source_label = {
        "언론": "언론 기사",
        "SNS": "SNS 게시물",
        "커뮤니티": "커뮤니티 게시물",
        "유튜브": "유튜브 댓글",
    }.get(source_type, "텍스트")

    # 관련 공식 문서 검색 (있을 경우 프롬프트에 삽입)
    relevant_docs = find_relevant_docs(text)
    if relevant_docs:
        doc_section = "\n\n[병무청 공식 자료 참고]\n" + "\n---\n".join(relevant_docs)
        prompt = f"{SYSTEM_PROMPT}{doc_section}\n\n출처: {source_label}\n텍스트: {text}"
    else:
        prompt = f"{SYSTEM_PROMPT}\n\n출처: {source_label}\n텍스트: {text}"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)
    score = int(data.get("false_score", 50))
    score = max(0, min(100, score))

    if score <= 33:
        level = "낮음"
    elif score <= 66:
        level = "중간"
    else:
        level = "높음"

    return {
        "false_score": score,
        "false_level": level,
        "false_reason": str(data.get("false_reason", ""))[:100],
        "department_keyword": str(data.get("department_keyword", "")),
    }
