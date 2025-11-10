# External imports
import requests

class PriceService:
    """Wrapper for price-related external APIs."""

    @staticmethod
    def get_necessities_prices(category=None, commodity=None):
        return requests.get(
            "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
            params={"CategoryName": category, "Name": commodity},
        ).json()
