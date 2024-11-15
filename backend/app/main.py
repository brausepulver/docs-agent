from dotenv import load_dotenv
load_dotenv()

import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from .utils.docs import create_process_comments, create_process_gdrive
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
import asyncio
from .routers import auth, docs, repos
from datetime import datetime

@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = AsyncIOScheduler()
    stop_event = asyncio.Event()

    process_comments = create_process_comments()
    scheduler.add_job(process_comments, 'cron', second='*/1', args=[stop_event], next_run_time=datetime.now())

    process_gdrive = create_process_gdrive()
    scheduler.add_job(process_gdrive, 'cron', second='*/30', args=[stop_event], next_run_time=datetime.now())

    scheduler.start()

    yield

    stop_event.set()
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv('FRONTEND_URL')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(docs.router)
app.include_router(repos.router)
