import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from moduleAI.parser.text_parser import parse_document
from moduleAI.validator.structure_validator import validate
from moduleAI.detector.ai_detector import detect_ai
from moduleAI.relevance.freshness_checker import check_freshness
from moduleAI.similarity.analogue_finder import find_analogues
from moduleAI.evaluator.quality_evaluator import evaluate_quality
from moduleAI.aggregator import aggregate

app = FastAPI(title="SPS AI Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

def run_pipeline(text: str, doc_type: Optional[str] = None) -> dict:
    struct = validate(text, doc_type=doc_type)
    ai_det = detect_ai(text)
    fresh = check_freshness(text)
    analogs = find_analogues(text)
    quality = evaluate_quality(text, doc_type=doc_type)
    result = aggregate(struct, ai_det, fresh, analogs, quality)
    return result

@app.post("/analyze/file")
async def analyze_file(file: UploadFile = File(...), doc_type: Optional[str] = Form(None)):
    try:
        content = await file.read()
        text = parse_document(file.filename, content)
        return {"status": "done", "result": run_pipeline(text, doc_type)}
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {e}")

@app.post("/analyze/text")
async def analyze_text(text: str = Form(...), doc_type: Optional[str] = Form(None)):
    try:
        return {"status": "done", "result": run_pipeline(text, doc_type)}
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {e}")

@app.get("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run("ai_service:app", host="0.0.0.0", port=8001, reload=False)
