"""
Export API Routes
Endpoints for exporting manuscripts to various formats
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.services.export_service import ExportService

router = APIRouter(prefix="/api/export", tags=["export"])


class ExportRequest(BaseModel):
    """Request model for export"""
    chapter_ids: Optional[List[str]] = None
    include_folders: bool = False


@router.get("/preview/{manuscript_id}")
async def get_export_preview(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """
    Get export preview with manuscript metadata

    Args:
        manuscript_id: ID of the manuscript

    Returns:
        Export preview data including chapter list and word count
    """
    try:
        service = ExportService(db)
        preview = await service.get_export_preview(manuscript_id)

        return {
            "success": True,
            "data": preview
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Export preview error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")


@router.post("/docx/{manuscript_id}")
async def export_to_docx(
    manuscript_id: str,
    request: ExportRequest = ExportRequest(),
    db: Session = Depends(get_db)
):
    """
    Export manuscript to DOCX format

    Args:
        manuscript_id: ID of the manuscript to export
        request: Export configuration (chapter selection, options)

    Returns:
        DOCX file as streaming response
    """
    try:
        service = ExportService(db)

        # Get manuscript title for filename
        preview = await service.get_export_preview(manuscript_id)
        filename = f"{preview['title'].replace(' ', '_')}.docx"

        # Generate DOCX
        buffer = await service.export_to_docx(
            manuscript_id,
            include_folders=request.include_folders,
            chapter_ids=request.chapter_ids
        )

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"DOCX export error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to export to DOCX: {str(e)}")


@router.post("/pdf/{manuscript_id}")
async def export_to_pdf(
    manuscript_id: str,
    request: ExportRequest = ExportRequest(),
    db: Session = Depends(get_db)
):
    """
    Export manuscript to PDF format

    Args:
        manuscript_id: ID of the manuscript to export
        request: Export configuration (chapter selection, options)

    Returns:
        PDF file as streaming response
    """
    try:
        service = ExportService(db)

        # Get manuscript title for filename
        preview = await service.get_export_preview(manuscript_id)
        filename = f"{preview['title'].replace(' ', '_')}.pdf"

        # Generate PDF
        buffer = await service.export_to_pdf(
            manuscript_id,
            include_folders=request.include_folders,
            chapter_ids=request.chapter_ids
        )

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"PDF export error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to export to PDF: {str(e)}")
