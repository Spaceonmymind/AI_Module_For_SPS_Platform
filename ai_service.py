import os
import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

app = FastAPI(title="SPS AI Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

# ---------- Fallback parser (txt/docx/pdf) ----------
def _fallback_parse_document(filename: str, content: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".docx"):
        try:
            from docx import Document  # python-docx
            import io
            doc = Document(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            raise RuntimeError(f"DOCX parse error: {e}")
    if name.endswith(".pdf"):
        try:
            from io import BytesIO
            from pdfminer.high_level import extract_text
            return extract_text(BytesIO(content))
        except Exception as e:
            raise RuntimeError(f"PDF parse error: {e}")
    # TXT/прочее
    try:
        return content.decode("utf-8", errors="ignore")
    except Exception:
        return content.decode("latin-1", errors="ignore")

def _parse_document(filename: str, content: bytes) -> str:
    # 1) попытка использовать твой парсер, если он есть
    try:
        from moduleAI.parser.text_parser import parse_document  # type: ignore
        return parse_document(filename, content)
    except Exception:
        pass
    try:
        from moduleAI.parser.text_parser import parse_file  # type: ignore
        return parse_file(filename, content)
    except Exception:
        pass
    try:
        from moduleAI.parser.text_parser import parse_text  # type: ignore
        txt = content.decode("utf-8", errors="ignore")
        return parse_text(txt)
    except Exception:
        pass
    # 2) фолбэк
    return _fallback_parse_document(filename, content)

def _run_pipeline(text: str, doc_type: Optional[str]) -> dict:
    # Импортируем подпроцессы «лениво», чтобы сервис стартовал даже при частичных проблемах
    try:
        from moduleAI.validator.structure_validator import validate
    except Exception as e:
        raise HTTPException(500, f"Import error: structure_validator.validate — {e}")
    try:
        from moduleAI.detector.ai_detector import detect_ai
    except Exception as e:
        raise HTTPException(500, f"Import error: detector.ai_detector.detect_ai — {e}")
    try:
        from moduleAI.relevance.freshness_checker import check_freshness
    except Exception as e:
        raise HTTPException(500, f"Import error: relevance.freshness_checker.check_freshness — {e}")
    try:
        from moduleAI.similarity.analogue_finder import find_analogues
    except Exception as e:
        raise HTTPException(500, f"Import error: similarity.analogue_finder.find_analogues — {e}")
    try:
        from moduleAI.evaluator.quality_evaluator import evaluate_quality
    except Exception as e:
        raise HTTPException(500, f"Import error: evaluator.quality_evaluator.evaluate_quality — {e}")

    # Агрегатор — если есть твой
    try:
        from moduleAI.aggregator.result_builder import aggregate_result
        use_custom_agg = True
    except Exception:
        use_custom_agg = False

    struct = validate(text, doc_type=doc_type)
    ai_det = detect_ai(text)
    fresh = check_freshness(text)
    analogs = find_analogues(text)
    quality = evaluate_quality(text, doc_type=doc_type)

    if use_custom_agg:
        return aggregate_result(struct, ai_det, fresh, analogs, quality, {"doc_type": doc_type})

    return {
        "structure_validation": struct,
        "ai_detection": ai_det,
        "freshness_check": fresh,
        "similar_ideas": analogs,
        "quality": quality,
        "verdict": {
            "ai_score": ai_det.get("score") if isinstance(ai_det, dict) else None,
            "is_ai": (isinstance(ai_det, dict) and ai_det.get("verdict") in (True, "ai", 1, "likely_ai")),
            "quality_score": quality.get("score") if isinstance(quality, dict) else None,
            "is_recent": fresh.get("is_recent") if isinstance(fresh, dict) else None,
        },
        "_schema_version": "0.9-fallback"
    }

@app.post("/analyze/file")
async def analyze_file(file: UploadFile = File(...), doc_type: Optional[str] = Form(None)):
    try:
        content = await file.read()
        text = _parse_document(file.filename, content)
        return {"status": "done", "result": _run_pipeline(text, doc_type)}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Analyze error")
        raise HTTPException(500, f"Analyze error: {e}")

class AnalyzeInput(BaseModel):
    file_path: str
    doc_type: Optional[str] = None

@app.post("/analyze")
async def analyze_path(inp: AnalyzeInput):
    """
    Основной эндпоинт для SPS_Platform.
    Получает путь к файлу и тип документа.
    """
    file_path = inp.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Файл не найден: {file_path}")

    try:
        with open(file_path, "rb") as f:
            content = f.read()
        text = _parse_document(file_path, content)
        result = _run_pipeline(text, inp.doc_type)
        return {"status": "done", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Analyze error (file_path)")
        raise HTTPException(status_code=500, detail=f"Analyze error: {e}")



if __name__ == "__main__":
    uvicorn.run("ai_service:app", host="0.0.0.0", port=5005, workers=1)
