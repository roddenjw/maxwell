"""
Share API Routes
Public endpoints for shareable recap cards with Open Graph support
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import base64

from app.database import get_db
from app.models.shareable_recap import ShareableRecap, generate_share_id

router = APIRouter(prefix="/api/share", tags=["share"])


class CreateShareRequest(BaseModel):
    """Request to create a shareable recap"""
    manuscript_id: str
    chapter_id: Optional[str] = None
    recap_type: str = "chapter"  # 'chapter' or 'writing_stats'
    title: str
    description: Optional[str] = None
    template: str = "dark"
    image_data_base64: Optional[str] = None  # Base64 encoded PNG
    recap_content: Optional[dict] = None


class CreateShareResponse(BaseModel):
    """Response with share link"""
    share_id: str
    share_url: str


class ShareStats(BaseModel):
    """Share analytics"""
    share_id: str
    view_count: int
    share_count: int
    created_at: str


@router.post("/create", response_model=CreateShareResponse)
def create_share(request: CreateShareRequest, db: Session = Depends(get_db)):
    """
    Create a shareable recap card

    Returns a short share URL that can be posted on social media
    """
    # Generate unique share ID
    share_id = generate_share_id()

    # Ensure uniqueness
    while db.query(ShareableRecap).filter(ShareableRecap.share_id == share_id).first():
        share_id = generate_share_id()

    # Decode image data if provided
    image_data = None
    if request.image_data_base64:
        try:
            image_data = base64.b64decode(request.image_data_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {e}")

    # Create shareable recap
    shareable = ShareableRecap(
        share_id=share_id,
        manuscript_id=request.manuscript_id,
        chapter_id=request.chapter_id,
        recap_type=request.recap_type,
        title=request.title,
        description=request.description,
        template=request.template,
        image_data=image_data,
        recap_content=request.recap_content
    )

    db.add(shareable)
    db.commit()

    # Build share URL (frontend route)
    share_url = f"/share/{share_id}"

    return CreateShareResponse(share_id=share_id, share_url=share_url)


@router.get("/recap/{share_id}", response_class=HTMLResponse)
def get_share_page(share_id: str, db: Session = Depends(get_db)):
    """
    Get the share page with Open Graph meta tags

    This endpoint returns HTML that social media platforms can scrape
    for rich previews when users share links
    """
    shareable = db.query(ShareableRecap).filter(
        ShareableRecap.share_id == share_id
    ).first()

    if not shareable:
        raise HTTPException(status_code=404, detail="Share not found")

    # Increment view count
    shareable.view_count += 1
    db.commit()

    # Build Open Graph meta tags
    base_url = "http://localhost:8000"  # Should be configurable
    image_url = f"{base_url}/api/share/image/{share_id}.png"

    og_title = shareable.title or "Chapter Recap"
    og_description = shareable.description or "Written in Maxwell"
    og_type = "article"

    # Build UTM tracking parameters
    utm_params = "utm_source=maxwell&utm_medium=recap&utm_campaign=share"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{og_title} - Maxwell</title>

    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{og_description}">
    <meta property="og:image" content="{image_url}?{utm_params}">
    <meta property="og:image:width" content="1080">
    <meta property="og:image:height" content="1920">
    <meta property="og:type" content="{og_type}">
    <meta property="og:url" content="{base_url}/share/{share_id}">
    <meta property="og:site_name" content="Maxwell">

    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{og_title}">
    <meta name="twitter:description" content="{og_description}">
    <meta name="twitter:image" content="{image_url}?{utm_params}">

    <style>
        body {{
            font-family: 'EB Garamond', Georgia, serif;
            background-color: #f5f0e6;
            color: #1a1a2e;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            text-align: center;
        }}
        .recap-image {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        p {{
            color: #666;
            margin-bottom: 2rem;
        }}
        .cta {{
            display: inline-block;
            background-color: #b87333;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            font-weight: 600;
        }}
        .cta:hover {{
            background-color: #996530;
        }}
        .stats {{
            margin-top: 1rem;
            font-size: 0.875rem;
            color: #888;
        }}
    </style>
</head>
<body>
    <div class="container">
        <img src="{image_url}" alt="{og_title}" class="recap-image">
        <h1>{og_title}</h1>
        <p>{og_description}</p>
        <a href="https://maxwell.app?{utm_params}" class="cta">
            Start Writing in Maxwell
        </a>
        <p class="stats">{shareable.view_count} views</p>
    </div>
</body>
</html>"""

    return HTMLResponse(content=html)


@router.get("/image/{share_id}.png")
def get_share_image(share_id: str, db: Session = Depends(get_db)):
    """
    Get the share image as PNG

    This endpoint serves the cached recap card image
    """
    # Remove .png extension if present in ID
    clean_id = share_id.replace('.png', '')

    shareable = db.query(ShareableRecap).filter(
        ShareableRecap.share_id == clean_id
    ).first()

    if not shareable:
        raise HTTPException(status_code=404, detail="Share not found")

    if not shareable.image_data:
        raise HTTPException(status_code=404, detail="Image not available")

    # Return image with appropriate headers
    return Response(
        content=shareable.image_data,
        media_type=shareable.image_content_type or "image/png",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "Content-Disposition": f'inline; filename="{clean_id}.png"'
        }
    )


@router.get("/stats/{share_id}", response_model=ShareStats)
def get_share_stats(share_id: str, db: Session = Depends(get_db)):
    """
    Get analytics for a shared recap
    """
    shareable = db.query(ShareableRecap).filter(
        ShareableRecap.share_id == share_id
    ).first()

    if not shareable:
        raise HTTPException(status_code=404, detail="Share not found")

    return ShareStats(
        share_id=shareable.share_id,
        view_count=shareable.view_count,
        share_count=shareable.share_count,
        created_at=shareable.created_at.isoformat()
    )


@router.post("/track/{share_id}")
def track_share(share_id: str, platform: str = "unknown", db: Session = Depends(get_db)):
    """
    Track when a share link is used

    Called when user clicks a share button
    """
    shareable = db.query(ShareableRecap).filter(
        ShareableRecap.share_id == share_id
    ).first()

    if not shareable:
        raise HTTPException(status_code=404, detail="Share not found")

    shareable.share_count += 1
    db.commit()

    return {"success": True, "share_count": shareable.share_count}
