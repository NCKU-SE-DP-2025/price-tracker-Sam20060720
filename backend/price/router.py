# External imports
from fastapi import APIRouter, Query

# Internal imports
from price.service import PriceService

router = APIRouter(prefix="/api/v1/prices", tags=["prices"])

_price_service: PriceService = None


def set_price_dependencies(price_service: PriceService):
    """Set price service (called from main.py)"""
    global _price_service
    _price_service = price_service


@router.get("/necessities-price")
def get_necessities_prices(
    category=Query(None),
    commodity=Query(None)
):
    """Get necessities prices"""
    return _price_service.get_necessities_prices(category, commodity)

