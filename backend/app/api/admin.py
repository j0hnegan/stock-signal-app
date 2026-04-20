from fastapi import APIRouter, BackgroundTasks

from app.jobs.quotes import refresh_quotes_job, refresh_universe_job

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/refresh-universe")
def trigger_refresh_universe(background: BackgroundTasks) -> dict[str, str]:
    background.add_task(refresh_universe_job)
    return {"status": "started"}


@router.post("/refresh-quotes")
def trigger_refresh_quotes(background: BackgroundTasks) -> dict[str, str]:
    background.add_task(refresh_quotes_job)
    return {"status": "started"}
