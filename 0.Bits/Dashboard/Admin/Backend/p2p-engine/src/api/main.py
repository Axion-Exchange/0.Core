"""
FastAPI Application
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.api.auth import verify_api_key

app = FastAPI(
    title="P2P Automation API",
    description="API for P2P crypto trading automation",
    version="1.0.0",
)

# CORS — restrict to trusted origins (update ALLOWED_ORIGINS in production)
import os
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All /api routes require API key authentication
app.include_router(router, dependencies=[Depends(verify_api_key)])


@app.get("/")
async def root():
    """Root endpoint - health check (unauthenticated)."""
    return {"status": "ok", "service": "p2p-automation"}


@app.get("/heartbeat")
async def heartbeat():
    """
    FIX C8: Deadman's switch heartbeat endpoint (unauthenticated).
    External monitors should alert if seconds_since_last_poll > threshold.
    """
    from datetime import datetime
    try:
        from src.services.order_orchestrator import orchestrator
        last_poll = getattr(orchestrator, '_last_poll_time', None)
        active_orders = len([o for o in orchestrator.state._orders.values()
                           if o.state.value not in ('completed', 'cancelled', 'expired', 'refunded')])
        return {
            "status": "alive",
            "last_poll_utc": last_poll.isoformat() if last_poll else None,
            "seconds_since_last_poll": (datetime.utcnow() - last_poll).total_seconds() if last_poll else None,
            "active_orders": active_orders,
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}




# ── Dashboard ──
from fastapi.responses import HTMLResponse as _HTMLResponse
import os as _os

@app.get('/dashboard', response_class=_HTMLResponse, include_in_schema=False)
async def _serve_dashboard():
    _path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'dashboard.html')
    with open(_path, 'r') as _f:
        return _f.read()
