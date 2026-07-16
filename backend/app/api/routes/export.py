"""
Export endpoints: turn an AnalysisResponse into downloadable deliverable formats.

The client sends back the exact AnalysisResponse JSON it got from
/api/analysis/run (rather than the server re-running the analysis), so
exports are cheap, instant, and reflect exactly what the user saw on screen.
"""
import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.export.pptx_export import build_deck
from app.models.schemas import AnalysisResponse

router = APIRouter()


@router.post("/pptx")
def export_pptx(analysis: AnalysisResponse):
    deck_bytes = build_deck(analysis)
    filename = "strategy-copilot-deck.pptx"
    return StreamingResponse(
        io.BytesIO(deck_bytes),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
