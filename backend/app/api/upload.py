from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from io import BytesIO
from app.core.database import supabase
from app.services.excel import parse_excel, build_result_excel
from app.services.analyzer import analyze_batch

router = APIRouter(prefix="/batches", tags=["upload"])


@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.")

    content = await file.read()

    try:
        rows = parse_excel(content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not rows:
        raise HTTPException(status_code=422, detail="분석할 행이 없습니다. 'text' 컬럼을 확인해주세요.")

    # batches 테이블에 배치 생성
    batch = supabase.table("batches").insert({
        "file_name": file.filename,
        "total_rows": len(rows),
        "analyzed_rows": 0,
    }).execute().data[0]

    # articles 테이블에 원문 저장 (분석 전)
    articles_to_insert = [
        {
            "batch_id": batch["id"],
            "original_text": row["text"],
            "source_type": row["source_type"],
            "source_url": row["source_url"] or None,
        }
        for row in rows
    ]
    supabase.table("articles").insert(articles_to_insert).execute()

    return {
        "batch_id": batch["id"],
        "file_name": file.filename,
        "total_rows": len(rows),
        "message": f"{len(rows)}행 업로드 완료. /api/batches/{batch['id']}/analyze 로 분석을 시작하세요.",
    }


@router.post("/{batch_id}/analyze")
def start_analyze(batch_id: str, background_tasks: BackgroundTasks):
    batch = supabase.table("batches").select("id").eq("id", batch_id).execute().data
    if not batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다.")
    background_tasks.add_task(analyze_batch, batch_id)
    return {"message": "분석 시작됨. 잠시 후 결과를 확인하세요.", "batch_id": batch_id}


@router.get("")
def list_batches():
    result = supabase.table("batches").select("*").order("created_at", desc=True).execute()
    return result.data


@router.get("/{batch_id}")
def get_batch(batch_id: str):
    batch = supabase.table("batches").select("*").eq("id", batch_id).execute().data
    if not batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다.")

    articles = supabase.table("articles").select("*").eq("batch_id", batch_id).order("created_at").execute().data

    return {"batch": batch[0], "articles": articles}


@router.get("/{batch_id}/download")
def download_result(batch_id: str):
    batch = supabase.table("batches").select("*").eq("id", batch_id).execute().data
    if not batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다.")

    articles = supabase.table("articles").select("*, departments(name)").eq("batch_id", batch_id).order("created_at").execute().data

    original_rows = [{"text": a["original_text"], "source_type": a["source_type"], "source_url": a.get("source_url", "")} for a in articles]
    analysis_results = [
        {
            "false_score":  a.get("false_score"),
            "false_level":  a.get("false_level"),
            "false_reason": a.get("false_reason"),
            "intent_type":  a.get("intent_type", ""),
            "content_type": a.get("content_type", ""),
            "department":   a.get("departments", {}).get("name", "") if a.get("departments") else "",
        }
        for a in articles
    ]

    excel_bytes = build_result_excel(original_rows, analysis_results)
    filename = f"result_{batch[0]['file_name']}"

    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
