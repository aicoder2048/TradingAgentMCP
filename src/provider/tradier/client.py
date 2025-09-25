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
    contract_size: Optional[int] = None   # Contract size (for options)
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


@dataclass
class OptionContract:
    """期权合约数据结构。"""
    symbol: str
    strike: float
    expiration_date: str
    option_type: str  # "call" or "put"
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    underlying: Optional[str] = None
    change: Optional[float] = None
    change_percentage: Optional[float] = None
    greeks: Optional[Dict[str, float]] = None
    
    # 新增重要字段
    description: Optional[str] = None  # 期权描述 "AAPL Apr 16 2021 $125.00 Call"
    open: Optional[float] = None       # 开盘价
    high: Optional[float] = None       # 最高价  
    low: Optional[float] = None        # 最低价
    close: Optional[float] = None      # 收盘价
    prevclose: Optional[float] = None  # 前收盘价
    average_volume: Optional[int] = None     # 平均成交量
    last_volume: Optional[int] = None        # 最新成交量
    week_52_high: Optional[float] = None     # 52周最高价
    week_52_low: Optional[float] = None      # 52周最低价
    bidsize: Optional[int] = None            # 买盘量
    asksize: Optional[int] = None            # 卖盘量
    trade_date: Optional[int] = None         # 交易时间戳
    bid_date: Optional[int] = None           # 买价时间戳
    ask_date: Optional[int] = None           # 卖价时间戳
    contract_size: Optional[int] = None      # 合约规模 (通常是100)
    root_symbol: Optional[str] = None        # 根符号
    
    # 计算字段
    mid_price: Optional[float] = None
    intrinsic_value: Optional[float] = None
    time_value: Optional[float] = None
    moneyness: Optional[float] = None
    days_to_expiration: Optional[int] = None
    in_the_money: Optional[bool] = None


@dataclass
class OptionExpiration:
    """期权到期日数据结构。"""
    date: str
    contract_size: int
    expiration_type: str
    strikes: List[float]


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

    def get_option_expirations(self, symbol: str, include_all_roots: bool = True, 
                                include_strikes: bool = False, include_details: bool = False) -> List[OptionExpiration]:
        """获取期权到期日信息。

        Args:
            symbol: 股票代码
            include_all_roots: 包含所有期权根符号
            include_strikes: 包含执行价格信息
            include_details: 包含详细信息（合约大小、到期类型等）

        Returns:
            OptionExpiration 对象列表
        """
        params = {
            "symbol": symbol,
            "includeAllRoots": "true" if include_all_roots else "false"
        }
        
        if include_strikes:
            params["strikes"] = "true"
        if include_details:
            params["contractSize"] = "true"
            params["expirationType"] = "true"

        data = self._make_request_with_retry("GET", "/v1/markets/options/expirations", params)
        expirations_data = data.get("expirations", {})

        if "expiration" in expirations_data:
            # 详细格式响应
            exp_list = expirations_data["expiration"]
            if not isinstance(exp_list, list):
                exp_list = [exp_list]
            
            expirations = []
            for exp_data in exp_list:
                strikes = []
                if "strikes" in exp_data and "strike" in exp_data["strikes"]:
                    strikes_data = exp_data["strikes"]["strike"]
                    if isinstance(strikes_data, list):
                        strikes = strikes_data
                    else:
                        strikes = [strikes_data]
                
                expiration = OptionExpiration(
                    date=exp_data.get("date", ""),
                    contract_size=exp_data.get("contract_size", 100),
                    expiration_type=exp_data.get("expiration_type", "standard"),
                    strikes=strikes
                )
                expirations.append(expiration)
            return expirations
        
        elif "date" in expirations_data:
            # 简单格式响应
            date_list = expirations_data["date"]
            if not isinstance(date_list, list):
                date_list = [date_list]
            
            return [OptionExpiration(
                date=date,
                contract_size=100,
                expiration_type="standard", 
                strikes=[]
            ) for date in date_list]
        
        return []

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

    def get_option_strikes(self, symbol: str, expiration: str, include_all_roots: bool = True) -> List[float]:
        """获取指定到期日的期权执行价格。

        Args:
            symbol: 股票代码
            expiration: 到期日 (YYYY-MM-DD 格式)
            include_all_roots: 包含所有期权根符号

        Returns:
            执行价格列表
        """
        params = {
            "symbol": symbol,
            "expiration": expiration,
            "includeAllRoots": "true" if include_all_roots else "false"
        }

        data = self._make_request_with_retry("GET", "/v1/markets/options/strikes", params)
        strikes_data = data.get("strikes", {})

        if "strike" not in strikes_data:
            return []

        strike_list = strikes_data["strike"]
        if not isinstance(strike_list, list):
            strike_list = [strike_list]

        return [float(strike) for strike in strike_list]
    
    def get_option_chain_enhanced(self, symbol: str, expiration: str, 
                                include_greeks: bool = True) -> List[OptionContract]:
        """获取增强的期权链数据，返回 OptionContract 对象。

        Args:
            symbol: 股票代码
            expiration: 到期日 (YYYY-MM-DD 格式) 
            include_greeks: 是否包含希腊字母

        Returns:
            OptionContract 对象列表
        """
        # 使用现有的 get_option_chain 方法获取数据
        tradier_quotes = self.get_option_chain(symbol, expiration, include_greeks)
        
        option_contracts = []
        for quote in tradier_quotes:
            # 计算中间价格
            mid_price = None
            if quote.bid is not None and quote.ask is not None and quote.bid > 0 and quote.ask > 0:
                mid_price = (quote.bid + quote.ask) / 2
            
            contract = OptionContract(
                symbol=quote.symbol,
                strike=quote.strike,
                expiration_date=quote.expiration_date,
                option_type=quote.option_type,
                bid=quote.bid,
                ask=quote.ask,
                last=quote.last,
                volume=quote.volume,
                open_interest=quote.open_interest,
                underlying=quote.underlying,
                change=quote.change,
                change_percentage=quote.change_percentage,
                greeks=quote.greeks,
                mid_price=mid_price,
                # 新增的重要字段
                description=quote.description,
                open=quote.open,
                high=quote.high,
                low=quote.low,
                close=quote.close,
                prevclose=quote.prevclose,
                average_volume=quote.average_volume,
                last_volume=quote.last_volume,
                week_52_high=quote.week_52_high,
                week_52_low=quote.week_52_low,
                bidsize=quote.bidsize,
                asksize=quote.asksize,
                trade_date=quote.trade_date,
                bid_date=quote.bid_date,
                ask_date=quote.ask_date,
                contract_size=quote.contract_size,
                root_symbol=quote.root_symbols
            )
            option_contracts.append(contract)
        
        return option_contracts
