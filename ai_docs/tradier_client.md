Tradier Client Reference Implementation

```python
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests


@dataclass
class TradierQuote:
    symbol: str
    last: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    volume: Optional[int]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    change: Optional[float]
    change_percentage: Optional[float]
    prevclose: Optional[float]
    description: Optional[str] = None
    underlying: Optional[str] = None
    strike: Optional[float] = None
    expiration_date: Optional[str] = None
    option_type: Optional[str] = None
    open_interest: Optional[int] = None
    greeks: Optional[Dict[str, float]] = None


@dataclass
class TradierHistoricalData:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class TradierClient:
    def __init__(self, access_token: str = None, base_url: str = "https://api.tradier.com"):
        self.access_token = access_token or os.getenv("TRADIER_ACCESS_TOKEN")
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}", "Accept": "application/json"})

        if not self.access_token:
            raise ValueError("Tradier access token is required")

    def _make_request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, data=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Tradier API error: {str(e)}")

    def get_quotes(self, symbols: List[str], include_greeks: bool = False) -> List[TradierQuote]:
        symbols_str = ",".join(symbols)
        params = {"symbols": symbols_str, "greeks": "true" if include_greeks else "false"}

        data = self._make_request("GET", "/v1/markets/quotes", params)
        quotes_data = data.get("quotes", {})

        if "quote" not in quotes_data:
            return []

        quote_list = quotes_data["quote"]
        if not isinstance(quote_list, list):
            quote_list = [quote_list]

        quotes = []
        for quote_data in quote_list:
            greeks_data = quote_data.get("greeks")
            greeks = None
            if greeks_data:
                greeks = {
                    "delta": greeks_data.get("delta"),
                    "gamma": greeks_data.get("gamma"),
                    "theta": greeks_data.get("theta"),
                    "vega": greeks_data.get("vega"),
                    "rho": greeks_data.get("rho"),
                    "phi": greeks_data.get("phi"),
                    "bid_iv": greeks_data.get("bid_iv"),
                    "mid_iv": greeks_data.get("mid_iv"),
                    "ask_iv": greeks_data.get("ask_iv"),
                    "smv_vol": greeks_data.get("smv_vol"),
                }

            quote = TradierQuote(
                symbol=quote_data.get("symbol"),
                last=quote_data.get("last"),
                bid=quote_data.get("bid"),
                ask=quote_data.get("ask"),
                volume=quote_data.get("volume"),
                open=quote_data.get("open"),
                high=quote_data.get("high"),
                low=quote_data.get("low"),
                change=quote_data.get("change"),
                change_percentage=quote_data.get("change_percentage"),
                prevclose=quote_data.get("prevclose"),
                description=quote_data.get("description"),
                underlying=quote_data.get("underlying"),
                strike=quote_data.get("strike"),
                expiration_date=quote_data.get("expiration_date"),
                option_type=quote_data.get("option_type"),
                open_interest=quote_data.get("open_interest"),
                greeks=greeks,
            )
            quotes.append(quote)

        return quotes

    def get_option_chain(self, symbol: str, expiration: str = None, include_greeks: bool = True) -> List[TradierQuote]:
        params = {"symbol": symbol, "greeks": "true" if include_greeks else "false"}

        if expiration:
            params["expiration"] = expiration

        data = self._make_request("GET", "/v1/markets/options/chains", params)
        options_data = data.get("options", {})

        if "option" not in options_data:
            return []

        option_list = options_data["option"]
        if not isinstance(option_list, list):
            option_list = [option_list]

        options = []
        for option_data in option_list:
            greeks_data = option_data.get("greeks")
            greeks = None
            if greeks_data:
                greeks = {
                    "delta": greeks_data.get("delta"),
                    "gamma": greeks_data.get("gamma"),
                    "theta": greeks_data.get("theta"),
                    "vega": greeks_data.get("vega"),
                    "rho": greeks_data.get("rho"),
                    "phi": greeks_data.get("phi"),
                    "bid_iv": greeks_data.get("bid_iv"),
                    "mid_iv": greeks_data.get("mid_iv"),
                    "ask_iv": greeks_data.get("ask_iv"),
                    "smv_vol": greeks_data.get("smv_vol"),
                }

            option = TradierQuote(
                symbol=option_data.get("symbol"),
                last=option_data.get("last"),
                bid=option_data.get("bid"),
                ask=option_data.get("ask"),
                volume=option_data.get("volume"),
                open=option_data.get("open"),
                high=option_data.get("high"),
                low=option_data.get("low"),
                change=option_data.get("change"),
                change_percentage=option_data.get("change_percentage"),
                prevclose=option_data.get("prevclose"),
                description=option_data.get("description"),
                underlying=option_data.get("underlying"),
                strike=option_data.get("strike"),
                expiration_date=option_data.get("expiration_date"),
                option_type=option_data.get("option_type"),
                open_interest=option_data.get("open_interest"),
                greeks=greeks,
            )
            options.append(option)

        return options

    def get_option_expirations(self, symbol: str, include_all_roots: bool = True) -> List[str]:
        params = {"symbol": symbol, "includeAllRoots": "true" if include_all_roots else "false"}

        data = self._make_request("GET", "/v1/markets/options/expirations", params)
        expirations_data = data.get("expirations", {})

        if "date" not in expirations_data:
            return []

        date_list = expirations_data["date"]
        if not isinstance(date_list, list):
            date_list = [date_list]

        return date_list

    def get_historical_data(
        self, symbol: str, start_date: str, end_date: str, interval: str = "daily"
    ) -> List[TradierHistoricalData]:
        params = {"symbol": symbol, "interval": interval, "start": start_date, "end": end_date, "session_filter": "all"}

        data = self._make_request("GET", "/v1/markets/history", params)
        history_data = data.get("history", {})

        if "day" not in history_data:
            return []

        day_list = history_data["day"]
        if not isinstance(day_list, list):
            day_list = [day_list]

        historical_data = []
        for day_data in day_list:
            historical_point = TradierHistoricalData(
                date=day_data.get("date"),
                open=day_data.get("open"),
                high=day_data.get("high"),
                low=day_data.get("low"),
                close=day_data.get("close"),
                volume=day_data.get("volume"),
            )
            historical_data.append(historical_point)

        return historical_data

    def search_securities(self, query: str, include_indices: bool = False) -> List[Dict]:
        params = {"q": query, "indexes": "true" if include_indices else "false"}

        data = self._make_request("GET", "/v1/markets/search", params)
        securities_data = data.get("securities", {})

        if "security" not in securities_data:
            return []

        security_list = securities_data["security"]
        if not isinstance(security_list, list):
            security_list = [security_list]

        return security_list

    def get_company_info(self, symbol: str) -> Dict:
        params = {"symbols": symbol}

        try:
            data = self._make_request("GET", "/beta/markets/fundamentals/company", params)
            if data and len(data) > 0:
                return data[0]
            return {}
        except Exception:
            return {}

    def get_corporate_calendar(self, symbol: str) -> Dict:
        """Get corporate calendar information including earnings dates for a security"""
        params = {"symbols": symbol}

        try:
            data = self._make_request("GET", "/beta/markets/fundamentals/calendars", params)
            if data and len(data) > 0:
                return data[0]
            return {}
        except Exception as e:
            raise Exception(f"Error fetching corporate calendar for {symbol}: {str(e)}")
```
