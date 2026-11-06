"""UI served inside Agent Server; threads and runs use native LangGraph APIs."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

FRONTEND = Path(__file__).resolve().parent / "frontend"
app = FastAPI(title="Hỗ trợ tâm lý", docs_url=None, openapi_url=None)


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
