"""Tradier API client for stock data retrieval."""

import os
import time
import random
import requests
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv


@dataclass
class TradierQuote:
    """Tradier quote data structure."""
    # Basic price information
    symbol: str
    last: Optional[float] = None          # Latest price
    bid: Optional[float] = None           # Bid price
    ask: Optional[float] = None           # Ask price
    open: Optional[float] = None          # Open price
    high: Optional[float] = None          # High price
    low: Optional[float] = None           # Low price
    prevclose: Optional[float] = None     # Previous close
    change: Optional[float] = None        # Price change
    change_percentage: Optional[float] = None  # Percentage change

    # Trading data
    volume: Optional[int] = None          # Trading volume
    average_volume: Optional[int] = None  # Average volume
    last_volume: Optional[int] = None     # Last trade volume
    
    # Exchange and type information
    exch: Optional[str] = None            # Exchange
    type: Optional[str] = None            # Security type
    
    # Additional price data
    close: Optional[float] = None         # Close price (can differ from last)
    week_52_high: Optional[float] = None  # 52-week high
    week_52_low: Optional[float] = None   # 52-week low
    
    # Bid/Ask details
    bidsize: Optional[int] = None         # Bid size
    asksize: Optional[int] = None         # Ask size
    bidexch: Optional[str] = None         # Bid exchange
    askexch: Optional[str] = None         # Ask exchange
    bid_date: Optional[int] = None        # Bid timestamp
    ask_date: Optional[int] = None        # Ask timestamp
    
    # Trade timing
    trade_date: Optional[int] = None      # Trade timestamp
    
    # Additional attributes for options
    description: Optional[str] = None     # Company description
    underlying: Optional[str] = None      # Underlying symbol (for options)
    strike: Optional[float] = None        # Strike price (for options)
    expiration_date: Optional[str] = None # Expiration date (for options)
    option_type: Optional[str] = None     # Option type (call/put)
    open_interest: Optional[int] = None   # Open interest (for options)
    root_symbols: Optional[str] = None    # Root symbols
    greeks: Optional[Dict[str, float]] = None  # Greeks data (for options)


@dataclass
class TradierHistoricalData:
    """Tradier historical data structure."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class TradierClient:
    """Tradier API client with comprehensive error handling and retry logic."""

    def __init__(self, access_token: str = None, base_url: str = "https://api.tradier.com"):
        """Initialize Tradier client.

        Args:
            access_token: Tradier API access token (can be None to use env var)
            base_url: Tradier API base URL
        """
        # Load environment variables from .env file in current working directory
        load_dotenv()

        self.access_token = access_token or os.getenv("TRADIER_ACCESS_TOKEN")
        self.base_url = base_url

        print(f"🔑 TRADIER_ACCESS_TOKEN: {'***' + str(self.access_token)[-4:] if self.access_token else 'NOT SET'}")

        if not self.access_token:
            raise ValueError("TRADIER_ACCESS_TOKEN environment variable is required")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        })

    def _make_request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """Make a single API request.

        Args:
            method: HTTP method (GET/POST)
            endpoint: API endpoint
            params: Request parameters

        Returns:
            JSON response as dictionary

        Raises:
            Exception: On API errors
        """
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

    def _make_request_with_retry(self, method: str, endpoint: str, params: Dict = None, max_retries: int = 3) -> Dict:
        """Make API request with exponential backoff retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Request parameters
            max_retries: Maximum retry attempts

        Returns:
            JSON response as dictionary
        """
        for attempt in range(max_retries):
            try:
                return self._make_request(method, endpoint, params)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise

                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)

    def get_quotes(self, symbols: List[str], include_greeks: bool = False) -> List[TradierQuote]:
        """Get stock quotes for given symbols.

        Args:
            symbols: List of stock symbols
            include_greeks: Whether to include options greeks data

        Returns:
            List of TradierQuote objects
        """
        if not symbols:
            return []

        symbols_str = ",".join(symbols)
        params = {
            "symbols": symbols_str,
            "greeks": "true" if include_greeks else "false"
        }

        data = self._make_request_with_retry("GET", "/v1/markets/quotes", params)
        quotes_data = data.get("quotes", {})

        if "quote" not in quotes_data:
            return []

        quote_list = quotes_data["quote"]
        if not isinstance(quote_list, list):
            quote_list = [quote_list]

        quotes = []
        for quote_data in quote_list:
            # Process greeks data if available
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
                open=quote_data.get("open"),
                high=quote_data.get("high"),
                low=quote_data.get("low"),
                close=quote_data.get("close"),
                prevclose=quote_data.get("prevclose"),
                change=quote_data.get("change"),
                change_percentage=quote_data.get("change_percentage"),
                volume=quote_data.get("volume"),
                average_volume=quote_data.get("average_volume"),
                last_volume=quote_data.get("last_volume"),
                week_52_high=quote_data.get("week_52_high"),
                week_52_low=quote_data.get("week_52_low"),
                exch=quote_data.get("exch"),
                type=quote_data.get("type"),
                bidsize=quote_data.get("bidsize"),
                asksize=quote_data.get("asksize"),
                bidexch=quote_data.get("bidexch"),
                askexch=quote_data.get("askexch"),
                bid_date=quote_data.get("bid_date"),
                ask_date=quote_data.get("ask_date"),
                trade_date=quote_data.get("trade_date"),
                root_symbols=quote_data.get("root_symbols"),
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

    def get_company_info(self, symbol: str) -> Dict:
        """Get company fundamental information.

        Args:
            symbol: Stock symbol

        Returns:
            Company information dictionary
        """
        params = {"symbols": symbol}

        try:
            data = self._make_request_with_retry("GET", "/beta/markets/fundamentals/company", params)
            if data and len(data) > 0:
                return data[0]
            return {}
        except Exception:
            # Company info is optional, return empty dict on failure
            return {}

    def get_ratios(self, symbol: str) -> Dict:
        """Get financial ratios for a company.

        Args:
            symbol: Stock symbol

        Returns:
            Financial ratios dictionary
        """
        params = {"symbols": symbol}

        try:
            data = self._make_request_with_retry("GET", "/markets/fundamentals/ratios", params)
            if data and len(data) > 0:
                return data[0]
            return {}
        except Exception:
            # Ratios are optional, return empty dict on failure
            return {}

    def get_corporate_calendar(self, symbol: str) -> Dict:
        """Get corporate calendar information including earnings dates.

        Args:
            symbol: Stock symbol

        Returns:
            Corporate calendar dictionary
        """
        params = {"symbols": symbol}

        try:
            data = self._make_request_with_retry("GET", "/beta/markets/fundamentals/calendars", params)
            if data and len(data) > 0:
                return data[0]
            return {}
        except Exception as e:
            raise Exception(f"Error fetching corporate calendar for {symbol}: {str(e)}")

    def get_option_chain(self, symbol: str, expiration: str = None, include_greeks: bool = True) -> List[TradierQuote]:
        """Get option chain for a symbol.

        Args:
            symbol: Stock symbol
            expiration: Specific expiration date
            include_greeks: Whether to include greeks data

        Returns:
            List of option TradierQuote objects
        """
        params = {
            "symbol": symbol,
            "greeks": "true" if include_greeks else "false"
        }

        if expiration:
            params["expiration"] = expiration

        data = self._make_request_with_retry("GET", "/v1/markets/options/chains", params)
        options_data = data.get("options", {})

        if "option" not in options_data:
            return []

        option_list = options_data["option"]
        if not isinstance(option_list, list):
            option_list = [option_list]

        options = []
        for option_data in option_list:
            # Process greeks data if available
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
        """Get option expiration dates for a symbol.

        Args:
            symbol: Stock symbol
            include_all_roots: Include all option roots

        Returns:
            List of expiration date strings
        """
        params = {
            "symbol": symbol,
            "includeAllRoots": "true" if include_all_roots else "false"
        }

        data = self._make_request_with_retry("GET", "/v1/markets/options/expirations", params)
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
        """Get historical pricing data.

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (daily, weekly, monthly)

        Returns:
            List of TradierHistoricalData objects
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "start": start_date,
            "end": end_date,
            "session_filter": "all"
        }

        data = self._make_request_with_retry("GET", "/v1/markets/history", params)
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
        """Search for securities by name or symbol.

        Args:
            query: Search query
            include_indices: Include market indices in results

        Returns:
            List of security dictionaries
        """
        params = {
            "q": query,
            "indexes": "true" if include_indices else "false"
        }

        data = self._make_request_with_retry("GET", "/v1/markets/search", params)
        securities_data = data.get("securities", {})

        if "security" not in securities_data:
            return []

        security_list = securities_data["security"]
        if not isinstance(security_list, list):
            security_list = [security_list]

        return security_list
