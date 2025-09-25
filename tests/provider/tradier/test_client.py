"""Tests for Tradier API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import os
from src.provider.tradier.client import TradierClient, TradierQuote, TradierHistoricalData


class TestTradierClient:
    """Test suite for TradierClient."""
    
    @pytest.fixture
    def mock_token(self):
        """Mock token for testing."""
        return "test_token_12345"
    
    @pytest.fixture
    def client(self, mock_token):
        """Create a test client with mock token."""
        return TradierClient(access_token=mock_token)
    
    def test_init_with_token(self, mock_token):
        """Test client initialization with explicit token."""
        client = TradierClient(access_token=mock_token)
        assert client.access_token == mock_token
        assert client.base_url == "https://api.tradier.com"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == f"Bearer {mock_token}"
    
    @patch.dict(os.environ, {"TRADIER_ACCESS_TOKEN": "env_token"})
    def test_init_with_env_token(self):
        """Test client initialization with environment token."""
        client = TradierClient()
        assert client.access_token == "env_token"
    
    @patch('src.provider.tradier.client.load_dotenv')
    def test_init_without_token(self, mock_load_dotenv):
        """Test client initialization fails without token."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="TRADIER_ACCESS_TOKEN environment variable is required"):
                TradierClient()
    
    def test_init_with_custom_base_url(self, mock_token):
        """Test client initialization with custom base URL."""
        custom_url = "https://sandbox.tradier.com"
        client = TradierClient(access_token=mock_token, base_url=custom_url)
        assert client.base_url == custom_url
    
    @patch('src.provider.tradier.client.requests.Session.get')
    def test_make_request_get_success(self, mock_get, client):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = client._make_request("GET", "/test", {"param": "value"})
        
        assert result == {"success": True}
        mock_get.assert_called_once_with(
            "https://api.tradier.com/test",
            params={"param": "value"}
        )
    
    @patch('src.provider.tradier.client.requests.Session.post')
    def test_make_request_post_success(self, mock_post, client):
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = client._make_request("POST", "/test", {"param": "value"})
        
        assert result == {"success": True}
        mock_post.assert_called_once_with(
            "https://api.tradier.com/test",
            data={"param": "value"}
        )
    
    def test_make_request_unsupported_method(self, client):
        """Test unsupported HTTP method raises error."""
        with pytest.raises(ValueError, match="Unsupported HTTP method: PUT"):
            client._make_request("PUT", "/test")
    
    @patch('src.provider.tradier.client.requests.Session.get')
    def test_make_request_http_error(self, mock_get, client):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="Tradier API error: 404 Not Found"):
            client._make_request("GET", "/test")
    
    @patch('src.provider.tradier.client.time.sleep')
    @patch.object(TradierClient, '_make_request')
    def test_make_request_with_retry_success_after_retry(self, mock_make_request, mock_sleep, client):
        """Test successful request after retry."""
        mock_make_request.side_effect = [
            Exception("First attempt failed"),
            {"success": True}
        ]
        
        result = client._make_request_with_retry("GET", "/test", max_retries=3)
        
        assert result == {"success": True}
        assert mock_make_request.call_count == 2
        mock_sleep.assert_called_once()
    
    @patch.object(TradierClient, '_make_request')
    def test_make_request_with_retry_max_retries_exceeded(self, mock_make_request, client):
        """Test max retries exceeded."""
        mock_make_request.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            client._make_request_with_retry("GET", "/test", max_retries=2)
        
        assert mock_make_request.call_count == 2
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_get_quotes_single_quote(self, mock_request, client):
        """Test getting quotes for a single symbol."""
        mock_response = {
            "quotes": {
                "quote": {
                    "symbol": "TSLA",
                    "last": 442.79,
                    "change": 16.94,
                    "change_percentage": 3.98,
                    "volume": 93133600,
                    "high": 444.21,
                    "low": 429.03,
                    "open": 429.83,
                    "prevclose": 425.85,
                    "description": "Tesla Inc",
                    "bid": 442.50,
                    "ask": 442.80
                }
            }
        }
        mock_request.return_value = mock_response
        
        quotes = client.get_quotes(["TSLA"])
        
        assert len(quotes) == 1
        quote = quotes[0]
        assert isinstance(quote, TradierQuote)
        assert quote.symbol == "TSLA"
        assert quote.last == 442.79
        assert quote.change == 16.94
        assert quote.change_percentage == 3.98
        assert quote.volume == 93133600
        assert quote.description == "Tesla Inc"
        
        mock_request.assert_called_once_with(
            "GET", 
            "/v1/markets/quotes", 
            {"symbols": "TSLA", "greeks": "false"}
        )
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_get_quotes_multiple_quotes(self, mock_request, client):
        """Test getting quotes for multiple symbols."""
        mock_response = {
            "quotes": {
                "quote": [
                    {
                        "symbol": "TSLA",
                        "last": 442.79,
                        "description": "Tesla Inc"
                    },
                    {
                        "symbol": "AAPL",
                        "last": 150.25,
                        "description": "Apple Inc"
                    }
                ]
            }
        }
        mock_request.return_value = mock_response
        
        quotes = client.get_quotes(["TSLA", "AAPL"])
        
        assert len(quotes) == 2
        assert quotes[0].symbol == "TSLA"
        assert quotes[1].symbol == "AAPL"
        
        mock_request.assert_called_once_with(
            "GET",
            "/v1/markets/quotes",
            {"symbols": "TSLA,AAPL", "greeks": "false"}
        )
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_get_quotes_with_greeks(self, mock_request, client):
        """Test getting quotes with greeks data."""
        mock_response = {
            "quotes": {
                "quote": {
                    "symbol": "TSLA210618C00700000",
                    "last": 5.20,
                    "underlying": "TSLA",
                    "strike": 700.0,
                    "expiration_date": "2021-06-18",
                    "option_type": "call",
                    "greeks": {
                        "delta": 0.52,
                        "gamma": 0.003,
                        "theta": -0.15,
                        "vega": 1.25,
                        "rho": 0.18
                    }
                }
            }
        }
        mock_request.return_value = mock_response
        
        quotes = client.get_quotes(["TSLA210618C00700000"], include_greeks=True)
        
        assert len(quotes) == 1
        quote = quotes[0]
        assert quote.greeks is not None
        assert quote.greeks["delta"] == 0.52
        assert quote.greeks["gamma"] == 0.003
        
        mock_request.assert_called_once_with(
            "GET",
            "/v1/markets/quotes",
            {"symbols": "TSLA210618C00700000", "greeks": "true"}
        )
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_get_quotes_empty_response(self, mock_request, client):
        """Test handling empty quotes response."""
        mock_response = {"quotes": {}}
        mock_request.return_value = mock_response
        
        quotes = client.get_quotes(["INVALID"])
        
        assert quotes == []
    
    def test_get_quotes_empty_symbols(self, client):
        """Test get_quotes with empty symbols list."""
        quotes = client.get_quotes([])
        assert quotes == []
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_get_company_info_success(self, mock_request, client):
        """Test successful company info retrieval."""
        mock_response = [
            {
                "type": "Company",
                "tables": {
                    "company_profile": {
                        "company_name": "Tesla Inc",
                        "sector": "Consumer Discretionary"
                    }
                }
            }
        ]
        mock_request.return_value = mock_response
        
        info = client.get_company_info("TSLA")
        
        assert info == mock_response[0]
        mock_request.assert_called_once_with(
            "GET",
            "/beta/markets/fundamentals/company",
            {"symbols": "TSLA"}
        )
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_get_company_info_empty_response(self, mock_request, client):
        """Test company info with empty response."""
        mock_request.return_value = []
        
        info = client.get_company_info("INVALID")
        
        assert info == {}
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_get_company_info_exception(self, mock_request, client):
        """Test company info with exception."""
        mock_request.side_effect = Exception("API Error")
        
        info = client.get_company_info("TSLA")
        
        assert info == {}
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_get_ratios_success(self, mock_request, client):
        """Test successful ratios retrieval."""
        mock_response = [
            {
                "tables": {
                    "valuation_ratios": {
                        "pe_ratio": 65.4,
                        "pb_ratio": 12.3
                    }
                }
            }
        ]
        mock_request.return_value = mock_response
        
        ratios = client.get_ratios("TSLA")
        
        assert ratios == mock_response[0]
        mock_request.assert_called_once_with(
            "GET",
            "/markets/fundamentals/ratios",
            {"symbols": "TSLA"}
        )
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_get_ratios_exception(self, mock_request, client):
        """Test ratios with exception."""
        mock_request.side_effect = Exception("API Error")
        
        ratios = client.get_ratios("TSLA")
        
        assert ratios == {}
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_search_securities(self, mock_request, client):
        """Test securities search."""
        mock_response = {
            "securities": {
                "security": [
                    {
                        "symbol": "TSLA",
                        "description": "Tesla Inc",
                        "exchange": "NASDAQ"
                    }
                ]
            }
        }
        mock_request.return_value = mock_response
        
        results = client.search_securities("Tesla")
        
        assert len(results) == 1
        assert results[0]["symbol"] == "TSLA"
        mock_request.assert_called_once_with(
            "GET",
            "/v1/markets/search",
            {"q": "Tesla", "indexes": "false"}
        )
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_get_historical_data(self, mock_request, client):
        """Test historical data retrieval."""
        mock_response = {
            "history": {
                "day": [
                    {
                        "date": "2023-01-03",
                        "open": 108.10,
                        "high": 123.18,
                        "low": 101.81,
                        "close": 122.42,
                        "volume": 359480200
                    }
                ]
            }
        }
        mock_request.return_value = mock_response
        
        data = client.get_historical_data("TSLA", "2023-01-01", "2023-01-31")
        
        assert len(data) == 1
        assert isinstance(data[0], TradierHistoricalData)
        assert data[0].date == "2023-01-03"
        assert data[0].close == 122.42
        
        mock_request.assert_called_once_with(
            "GET",
            "/v1/markets/history",
            {
                "symbol": "TSLA",
                "interval": "daily",
                "start": "2023-01-01",
                "end": "2023-01-31",
                "session_filter": "all"
            }
        )
    
    @patch.object(TradierClient, '_make_request_with_retry')
    def test_get_historical_data_empty_response(self, mock_request, client):
        """Test historical data with empty response."""
        mock_response = {"history": {}}
        mock_request.return_value = mock_response
        
        data = client.get_historical_data("INVALID", "2023-01-01", "2023-01-31")
        
        assert data == []


class TestTradierQuote:
    """Test suite for TradierQuote dataclass."""
    
    def test_quote_creation_minimal(self):
        """Test creating quote with minimal data."""
        quote = TradierQuote(symbol="TSLA")
        assert quote.symbol == "TSLA"
        assert quote.last is None
        assert quote.volume is None
    
    def test_quote_creation_full(self):
        """Test creating quote with full data."""
        quote = TradierQuote(
            symbol="TSLA",
            last=442.79,
            bid=442.50,
            ask=442.80,
            volume=93133600,
            high=444.21,
            low=429.03,
            open=429.83,
            prevclose=425.85,
            change=16.94,
            change_percentage=3.98,
            description="Tesla Inc"
        )
        
        assert quote.symbol == "TSLA"
        assert quote.last == 442.79
        assert quote.change_percentage == 3.98
        assert quote.description == "Tesla Inc"


class TestTradierHistoricalData:
    """Test suite for TradierHistoricalData dataclass."""
    
    def test_historical_data_creation(self):
        """Test creating historical data."""
        data = TradierHistoricalData(
            date="2023-01-03",
            open=108.10,
            high=123.18,
            low=101.81,
            close=122.42,
            volume=359480200
        )
        
        assert data.date == "2023-01-03"
        assert data.close == 122.42
        assert data.volume == 359480200