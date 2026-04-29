from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.schemas import DataEnvelope, ListEnvelope, RunDetailRead
from app.services import get_latest_run, get_run_by_id, list_runs


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="News Scraper Backend", lifespan=lifespan)


@app.get("/health", response_model=DataEnvelope)
def healthcheck() -> DataEnvelope:
    return DataEnvelope(data={"status": "ok"})


@app.get("/api/runs", response_model=ListEnvelope)
def get_runs(session: Session = Depends(get_db)) -> ListEnvelope:
    runs = list_runs(session)
    return ListEnvelope(data=runs, meta={"total": len(runs)})


@app.get("/api/runs/latest", response_model=DataEnvelope)
def latest_run(session: Session = Depends(get_db)) -> DataEnvelope:
    run = get_latest_run(session)
    if run is None:
        raise HTTPException(status_code=404, detail="No runs available")
    return DataEnvelope(data=RunDetailRead.model_validate(run))


@app.get("/api/runs/{run_id}", response_model=DataEnvelope)
def run_by_id(run_id: int, session: Session = Depends(get_db)) -> DataEnvelope:
    run = get_run_by_id(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return DataEnvelope(data=RunDetailRead.model_validate(run))
