from fastapi import Depends, FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

import yfinance as yf

app = FastAPI()

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/info")
async def get_info(ticker_name: str):
    tick = yf.Ticker(ticker_name)
    return tick.info

@app.get("/history")
async def get_history(ticker_name: str, period: str):
    tick = yf.Ticker(ticker_name)
    try:
        hist = tick.history(period=period)
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream error")
    if hist is None or hist.empty:
        # TODO: Delete Ticker so next time it isn't included in this process
        raise HTTPException(status_code=404, detail="Ticker Not Found")
    return hist.to_dict()


    