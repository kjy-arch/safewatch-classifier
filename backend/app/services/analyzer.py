import json
from google import genai
from app.core.config import settings
from app.core.database import supabase
from app.services.doc_service import find_relevant_docs

client = genai.Client(api_key=settings.GEMINI_API_KEY)

SYSTEM_PROMPT = """당신은 병무청 언론 모니터링 전문 분석관입니다.
주어진 텍스트를 아래 4가지 기준으로 분석하여 반드시 JSON만 반환하세요.

반환 형식:
{
  "false_score": 0~100 정수 (0=완전한 사실, 100=완전한 거짓/허위),
  "false_level": "낮음" | "중간" | "높음",
  "false_reason": 거짓 여부 판단 이유 한 줄 (40자 이내),
  "intent_type": 아래 중 하나,
  "content_type": 아래 중 하나,
  "department_name": 아래 부서 목록 중 가장 관련 있는 부서명 (없으면 null)
}

[의도 유형 - intent_type]
- "악의적 유포": 허위 사실을 의도적으로 퍼뜨리는 경우
- "단순 오해": 사실을 잘못 이해하거나 잘못 전달한 경우
- "풍자/비판": 과장이나 풍자를 통한 비판적 표현
- "사실 보도": 실제 사실에 근거한 보도나 제보
- "불명확": 의도를 파악하기 어려운 경우

[내용 유형 - content_type]
- "사실관계 오류": 구체적인 사실이 틀린 경우
- "과장/왜곡": 사실을 부풀리거나 맥락을 왜곡한 경우
- "출처 불명": 근거나 출처가 없는 주장
- "맥락 누락": 일부 사실만 발췌하여 전체 맥락을 흐리는 경우
- "문제없음": 내용상 허위나 왜곡이 없는 경우

[거짓점수 기준]
- 0~33: false_level = "낮음" (사실에 가까움)
- 34~66: false_level = "중간" (사실 여부 불분명)
- 67~100: false_level = "높음" (허위 가능성 높음)"""


def analyze_batch(batch_id: str):
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
            result = _analyze_single(
                article["original_text"],
                article["source_type"],
                departments,
            )
            dept_id = _find_dept_id(result.get("department_name"), departments)

            supabase.table("articles").update({
                "false_score":  result["false_score"],
                "false_level":  result["false_level"],
                "false_reason": result["false_reason"],
                "intent_type":  result["intent_type"],
                "content_type": result["content_type"],
                "department_id": dept_id,
            }).eq("id", article["id"]).execute()

            analyzed += 1
        except Exception:
            continue

    supabase.table("batches").update({"analyzed_rows": analyzed}).eq("id", batch_id).execute()
    return {"analyzed": analyzed, "total": len(articles)}


def _find_dept_id(dept_name: str | None, departments: list) -> str | None:
    if not dept_name:
        return None
    for d in departments:
        if d["name"] == dept_name:
            return d["id"]
    # 정확히 일치하지 않으면 부분 일치 시도
    for d in departments:
        if dept_name in d["name"] or d["name"] in dept_name:
            return d["id"]
    return None


def _analyze_single(text: str, source_type: str, departments: list) -> dict:
    source_label = {
        "언론": "언론 기사",
        "SNS": "SNS 게시물",
        "커뮤니티": "커뮤니티 게시물",
        "유튜브": "유튜브 댓글",
    }.get(source_type, "텍스트")

    dept_list = "\n".join(f"- {d['name']}" for d in departments)

    relevant_docs = find_relevant_docs(text)
    doc_section = ""
    if relevant_docs:
        doc_section = "\n\n[병무청 공식 자료 참고]\n" + "\n---\n".join(relevant_docs)

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"[분류 가능한 부서 목록]\n{dept_list}"
        f"{doc_section}\n\n"
        f"출처: {source_label}\n"
        f"텍스트: {text}"
    )

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
    score = max(0, min(100, int(data.get("false_score", 50))))

    if score <= 33:
        level = "낮음"
    elif score <= 66:
        level = "중간"
    else:
        level = "높음"

    return {
        "false_score":     score,
        "false_level":     level,
        "false_reason":    str(data.get("false_reason", ""))[:100],
        "intent_type":     str(data.get("intent_type", "불명확")),
        "content_type":    str(data.get("content_type", "불명확")),
        "department_name": data.get("department_name"),
    }
