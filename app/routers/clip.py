from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from app.models import ClipRequest, ClipJobStatus, ClipResult
from app.services.downloader import downloader
from app.services.transcriber import transcriber
from app.services.clip_finder import clip_finder
from app.services.video_processor import video_processor
from app.auth import get_current_user
from app.database import User
import uuid
import asyncio
import os
import shutil
from typing import Dict
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

jobs: Dict[str, ClipJobStatus] = {}
CLIP_TTL_SECONDS = int(os.environ.get("CLIPPER_CLIP_TTL", "600"))
COOKIES_PATH = os.environ.get("CLIPPER_COOKIES_FILE", "/app/data/cookies.txt")


def _delete_quietly(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


async def _schedule_ttl_deletion(path: str, ttl: int = CLIP_TTL_SECONDS):
    try:
        await asyncio.sleep(ttl)
        _delete_quietly(path)
    except asyncio.CancelledError:
        _delete_quietly(path)


@router.post("/clip/create", response_model=ClipJobStatus)
async def create_clip_job(
    request: ClipRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    job_id = str(uuid.uuid4())[:8]

    jobs[job_id] = ClipJobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Job created, waiting to start"
    )

    background_tasks.add_task(process_clip_job, job_id, request)

    return jobs[job_id]


@router.get("/clip/status/{job_id}", response_model=ClipJobStatus)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@router.get("/clip/download/{clip_id}")
async def download_clip(
    clip_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    output_path = f"/tmp/youtube-clipper/output/{clip_id}.mp4"
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Clip not found (already downloaded or expired)")

    background_tasks.add_task(_delete_quietly, output_path)

    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=f"clip_{clip_id}.mp4"
    )


@router.post("/clip/cookies")
async def upload_cookies(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload cookies.txt untuk bypass deteksi bot YouTube."""
    if file.content_type != "text/plain" and not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="File harus berformat .txt (cookies.txt)")
    
    # Pastikan directory ada
    os.makedirs(os.path.dirname(COOKIES_PATH), exist_ok=True)
    
    # Simpan file
    contents = await file.read()
    with open(COOKIES_PATH, "wb") as f:
        f.write(contents)
    
    logger.info(f"Cookies uploaded by {current_user.username} to {COOKIES_PATH}")
    
    return {"message": "Cookies berhasil diupload", "path": COOKIES_PATH}


@router.get("/clip/cookies/status")
async def cookies_status(current_user: User = Depends(get_current_user)):
    """Cek apakah cookies.txt tersedia."""
    exists = os.path.exists(COOKIES_PATH)
    size = os.path.getsize(COOKIES_PATH) if exists else 0
    return {
        "exists": exists,
        "size_bytes": size,
        "path": COOKIES_PATH if exists else None
    }


async def process_clip_job(job_id: str, request: ClipRequest):
    """Background task to process video, render clips, and schedule their deletion."""
    rendered_paths = []
    video_id = None
    srt_paths = []
    
    try:
        jobs[job_id].status = "downloading"
        jobs[job_id].message = "Downloading video from YouTube..."
        jobs[job_id].progress = 10
        
        video_info = downloader.download(request.youtube_url)
        video_id = video_info["video_id"]
        
        jobs[job_id].status = "transcribing"
        jobs[job_id].message = "Transcribing audio..."
        jobs[job_id].progress = 30
        
        transcript = transcriber.transcribe(video_info["audio_path"], language=None)
        
        jobs[job_id].status = "analyzing"
        jobs[job_id].message = "Finding interesting moments..."
        jobs[job_id].progress = 50
        
        clips = clip_finder.find_clips(
            transcript=transcript["text"],
            segments=transcript["segments"],
            max_clips=request.max_clips,
            min_duration=request.min_clip_duration,
            max_duration=request.max_clip_duration,
            language=request.subtitle_language.value
        )
        
        jobs[job_id].status = "processing"
        jobs[job_id].message = f"Generating {len(clips)} clips..."
        jobs[job_id].progress = 60
        
        full_srt = transcriber.get_srt(transcript["segments"])
        
        results = []
        total_clips = len(clips)
        
        for i, clip in enumerate(clips):
            clip_id = f"{job_id}_{i+1}"
            
            segment_srt = video_processor.extract_segment_srt(
                full_srt,
                clip["start_time"],
                clip["end_time"]
            )
            
            srt_path = f"/tmp/youtube-clipper/{clip_id}.srt"
            with open(srt_path, "w") as f:
                f.write(segment_srt)
            srt_paths.append(srt_path)
            
            result = video_processor.process_clip(
                audio_path=video_info["audio_path"],
                start_time=clip["start_time"],
                end_time=clip["end_time"],
                subtitle_path=srt_path,
                aspect_ratio=request.aspect_ratio.value,
                subtitle_language=request.subtitle_language.value,
                clip_id=clip_id
            )
            
            rendered_paths.append(result["output_path"])
            _delete_quietly(srt_path)
            
            results.append(ClipResult(
                clip_id=clip_id,
                original_url=request.youtube_url,
                start_time=clip["start_time"],
                end_time=clip["end_time"],
                duration=result["duration"],
                aspect_ratio=request.aspect_ratio.value,
                subtitle_language=request.subtitle_language.value,
                download_url=f"/api/clip/download/{clip_id}",
            ))
            
            jobs[job_id].progress = 60 + int((i + 1) / total_clips * 35)
            jobs[job_id].message = f"Processed clip {i+1}/{total_clips}"
        
        downloader.cleanup(video_id)
        
        jobs[job_id].status = "completed"
        jobs[job_id].progress = 100
        jobs[job_id].message = "All clips generated — download within 10 minutes"
        jobs[job_id].clips = results
        
        for p in rendered_paths:
            asyncio.create_task(_schedule_ttl_deletion(p))
        
    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        jobs[job_id].status = "error"
        jobs[job_id].message = f"Error: {str(e)}"
        jobs[job_id].error = str(e)
        
        for p in rendered_paths:
            _delete_quietly(p)
        for p in srt_paths:
            _delete_quietly(p)
        if video_id:
            downloader.cleanup(video_id)