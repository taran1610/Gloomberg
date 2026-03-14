"""Market & dashboard API."""
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(request: Request):
    """Global indices, gainers, losers, sectors, crypto."""
    svc = request.app.state.market_data
    return await svc.get_dashboard()


@router.get("/indices")
async def get_indices(request: Request):
    svc = request.app.state.market_data
    data = await svc.get_dashboard()
    return data.get("indices", [])


@router.get("/gainers")
async def get_gainers(request: Request):
    svc = request.app.state.market_data
    data = await svc.get_dashboard()
    return data.get("gainers", [])


@router.get("/losers")
async def get_losers(request: Request):
    svc = request.app.state.market_data
    data = await svc.get_dashboard()
    return data.get("losers", [])


@router.get("/sectors")
async def get_sectors(request: Request):
    svc = request.app.state.market_data
    data = await svc.get_dashboard()
    return data.get("sectors", [])


@router.get("/crypto")
async def get_crypto(request: Request):
    svc = request.app.state.market_data
    data = await svc.get_dashboard()
    return data.get("crypto", [])
