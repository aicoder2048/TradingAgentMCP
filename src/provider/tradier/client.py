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
    
    # ==================== CSP Strategy Enhancement Methods ====================
    
    def get_options_by_delta_range(
        self,
        symbol: str,
        expiration: str,
        option_type: str,
        delta_min: float,
        delta_max: float
    ) -> List[OptionContract]:
        """
        获取指定Delta范围内的期权合约。
        专为CSP策略选择优化。
        
        Args:
            symbol: 股票代码
            expiration: 到期日 (YYYY-MM-DD)
            option_type: 期权类型 ("call" 或 "put")
            delta_min: 最小Delta值
            delta_max: 最大Delta值
            
        Returns:
            符合Delta范围的期权合约列表
        """
        # 获取完整期权链
        all_options = self.get_option_chain_enhanced(symbol, expiration, include_greeks=True)
        
        # 过滤指定类型和Delta范围的期权
        filtered_options = []
        for option in all_options:
            if option.option_type != option_type:
                continue
                
            if not option.greeks:
                continue
                
            delta = option.greeks.get("delta", 0)
            if delta_min <= delta <= delta_max:
                filtered_options.append(option)
        
        # 按Delta值排序
        filtered_options.sort(key=lambda x: x.greeks.get("delta", 0))
        return filtered_options
    
    def get_next_expiration_by_duration(
        self,
        symbol: str,
        duration: str  # "1w", "2w", "1m", "3m", "6m", "1y"
    ) -> Optional[str]:
        """
        根据持续时间获取下一个合适的到期日。
        处理周度/月度期权和交易日计算。
        
        Args:
            symbol: 股票代码
            duration: 持续时间 ("1w", "2w", "1m", "3m", "6m", "1y")
            
        Returns:
            最适合的到期日 (YYYY-MM-DD) 或 None
        """
        from datetime import datetime, timedelta
        import calendar
        
        # 持续时间映射到天数范围
        duration_mappings = {
            "1w": {"min_days": 5, "max_days": 9, "preferred": "weekly"},
            "2w": {"min_days": 10, "max_days": 18, "preferred": "weekly"},
            "1m": {"min_days": 25, "max_days": 35, "preferred": "monthly"},
            "3m": {"min_days": 80, "max_days": 100, "preferred": "monthly"},
            "6m": {"min_days": 170, "max_days": 190, "preferred": "monthly"},
            "1y": {"min_days": 350, "max_days": 380, "preferred": "leaps"}
        }
        
        if duration not in duration_mappings:
            raise ValueError(f"Unsupported duration: {duration}")
        
        mapping = duration_mappings[duration]
        min_days = mapping["min_days"]
        max_days = mapping["max_days"]
        preferred_type = mapping["preferred"]
        
        # 获取所有可用到期日
        expirations = self.get_option_expirations(symbol, include_all_roots=True)
        
        today = datetime.now().date()
        candidates = []
        
        for exp in expirations:
            exp_date = datetime.strptime(exp.date, "%Y-%m-%d").date()
            days_to_exp = (exp_date - today).days
            
            if min_days <= days_to_exp <= max_days:
                # 判断是否为周度期权 (周五到期)
                is_weekly = exp_date.weekday() == 4  # 周五
                
                # 判断是否为月度期权 (第三个周五)
                third_friday = self._get_third_friday(exp_date.year, exp_date.month)
                is_monthly = exp_date == third_friday
                
                candidates.append({
                    "date": exp.date,
                    "days_to_exp": days_to_exp,
                    "is_weekly": is_weekly,
                    "is_monthly": is_monthly,
                    "exp_type": exp.expiration_type
                })
        
        if not candidates:
            return None
        
        # 根据偏好选择最佳到期日
        if preferred_type == "weekly":
            # 优先选择周度期权
            weekly_options = [c for c in candidates if c["is_weekly"]]
            if weekly_options:
                # 选择最接近中位天数的
                target_days = (min_days + max_days) / 2
                best = min(weekly_options, key=lambda x: abs(x["days_to_exp"] - target_days))
                return best["date"]
        
        elif preferred_type == "monthly":
            # 优先选择月度期权
            monthly_options = [c for c in candidates if c["is_monthly"]]
            if monthly_options:
                # 选择最接近中位天数的
                target_days = (min_days + max_days) / 2
                best = min(monthly_options, key=lambda x: abs(x["days_to_exp"] - target_days))
                return best["date"]
        
        # 如果没有找到偏好类型，选择最接近中位天数的
        target_days = (min_days + max_days) / 2
        best = min(candidates, key=lambda x: abs(x["days_to_exp"] - target_days))
        return best["date"]
    
    def calculate_implied_volatility_surface(
        self,
        symbol: str,
        expiration_dates: List[str]
    ) -> Dict[str, Dict[float, float]]:
        """
        构建隐含波动率曲面用于波动率分析。
        
        Args:
            symbol: 股票代码
            expiration_dates: 到期日列表
            
        Returns:
            波动率曲面字典 {expiration: {strike: iv}}
        """
        iv_surface = {}
        
        for expiration in expiration_dates:
            try:
                options = self.get_option_chain_enhanced(symbol, expiration, include_greeks=True)
                
                # 按执行价组织隐含波动率数据
                strikes_iv = {}
                for option in options:
                    if not option.greeks or not option.strike:
                        continue
                    
                    iv = option.greeks.get("mid_iv")
                    if iv and iv > 0:
                        strikes_iv[option.strike] = iv
                
                if strikes_iv:
                    iv_surface[expiration] = strikes_iv
                    
            except Exception as e:
                print(f"Error getting IV data for {expiration}: {e}")
                continue
        
        return iv_surface
    
    def get_atm_implied_volatility(self, symbol: str) -> Optional[float]:
        """
        获取最近到期的平值期权隐含波动率。
        
        Args:
            symbol: 股票代码
            
        Returns:
            平值隐含波动率或None
        """
        try:
            # 获取当前股价
            quotes = self.get_quotes([symbol])
            if not quotes:
                return None
            
            current_price = quotes[0].last
            if not current_price:
                return None
            
            # 获取最近的到期日
            expirations = self.get_option_expirations(symbol)
            if not expirations:
                return None
            
            # 选择最近的到期日（但不是今天）
            from datetime import datetime, timedelta
            today = datetime.now().date()
            min_exp = today + timedelta(days=1)
            
            valid_expirations = [
                exp for exp in expirations
                if datetime.strptime(exp.date, "%Y-%m-%d").date() >= min_exp
            ]
            
            if not valid_expirations:
                return None
            
            # 按日期排序，选择最近的
            valid_expirations.sort(key=lambda x: x.date)
            nearest_exp = valid_expirations[0].date
            
            # 获取该到期日的期权链
            options = self.get_option_chain_enhanced(symbol, nearest_exp, include_greeks=True)
            
            # 找到最接近平值的期权
            closest_strike = None
            min_distance = float('inf')
            
            for option in options:
                if not option.strike or not option.greeks:
                    continue
                
                distance = abs(option.strike - current_price)
                if distance < min_distance:
                    min_distance = distance
                    closest_strike = option.strike
            
            if not closest_strike:
                return None
            
            # 获取该执行价的平均隐含波动率
            call_iv = None
            put_iv = None
            
            for option in options:
                if option.strike == closest_strike and option.greeks:
                    iv = option.greeks.get("mid_iv")
                    if iv and iv > 0:
                        if option.option_type == "call":
                            call_iv = iv
                        elif option.option_type == "put":
                            put_iv = iv
            
            # 返回Call和Put的平均隐含波动率
            if call_iv and put_iv:
                return (call_iv + put_iv) / 2
            elif call_iv:
                return call_iv
            elif put_iv:
                return put_iv
            
            return None
            
        except Exception as e:
            print(f"Error getting ATM IV for {symbol}: {e}")
            return None
    
    def get_option_liquidity_metrics(
        self,
        symbol: str,
        expiration: str
    ) -> Dict[str, Any]:
        """
        获取期权流动性指标。
        
        Args:
            symbol: 股票代码
            expiration: 到期日
            
        Returns:
            流动性指标字典
        """
        options = self.get_option_chain_enhanced(symbol, expiration, include_greeks=True)
        
        total_volume = 0
        total_oi = 0
        valid_options = 0
        spreads = []
        
        for option in options:
            if option.bid and option.ask and option.bid > 0 and option.ask > 0:
                valid_options += 1
                spread_pct = (option.ask - option.bid) / ((option.ask + option.bid) / 2)
                spreads.append(spread_pct)
                
                if option.volume:
                    total_volume += option.volume
                if option.open_interest:
                    total_oi += option.open_interest
        
        avg_spread = sum(spreads) / len(spreads) if spreads else 0
        
        return {
            "total_volume": total_volume,
            "total_open_interest": total_oi,
            "valid_options_count": valid_options,
            "average_bid_ask_spread": avg_spread,
            "liquidity_score": min(100, (total_volume / 100 + total_oi / 1000) * 10)  # 简化评分
        }
    
    def _get_third_friday(self, year: int, month: int) -> 'datetime.date':
        """获取指定年月的第三个周五（月度期权到期日）"""
        import calendar
        from datetime import date
        
        # 找到该月第一个周五
        first_day = date(year, month, 1)
        first_friday = first_day
        while first_friday.weekday() != 4:  # 4 = Friday
            first_friday = first_friday.replace(day=first_friday.day + 1)
        
        # 第三个周五
        third_friday = first_friday.replace(day=first_friday.day + 14)
        
        # 确保没有超出该月
        last_day = calendar.monthrange(year, month)[1]
        if third_friday.day > last_day:
            # 如果超出，返回倒数第一个周五
            last_date = date(year, month, last_day)
            while last_date.weekday() != 4:
                last_date = last_date.replace(day=last_date.day - 1)
            return last_date
        
        return third_friday
