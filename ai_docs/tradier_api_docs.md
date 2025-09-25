# Tradier Market Data API
- Realtime data is available to all Tradier Brokerage account holders for US-based stocks and options. If you are not a Tradier Brokerage account holder we are unable to provide you with any realtime data solution.
- Fetch quotes, chains and historical data via REST and streaming APIs.

## Get Quotes (Get)
Get a list of symbols using a keyword lookup on the symbols description. Results are in descending order by average volume of the security. This can be used for simple search functions.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/quotes',
    params={'symbols': 'AAPL,VXX190517P00016000', 'greeks': 'false'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)

```

### JSON Response
```json
{
  "quotes": {
    "quote": [
      {
        "symbol": "AAPL",
        "description": "Apple Inc",
        "exch": "Q",
        "type": "stock",
        "last": 208.21,
        "change": -3.54,
        "volume": 25288395,
        "open": 204.29,
        "high": 208.71,
        "low": 203.5,
        "close": null,
        "bid": 208.19,
        "ask": 208.21,
        "change_percentage": -1.68,
        "average_volume": 27215269,
        "last_volume": 100,
        "trade_date": 1557168406000,
        "prevclose": 211.75,
        "week_52_high": 233.47,
        "week_52_low": 142.0,
        "bidsize": 12,
        "bidexch": "Q",
        "bid_date": 1557168406000,
        "asksize": 1,
        "askexch": "Y",
        "ask_date": 1557168406000,
        "root_symbols": "AAPL"
      },
      {
        "symbol": "VXX190517P00016000",
        "description": "VXX May 17 2019 $16.00 Put",
        "exch": "Z",
        "type": "option",
        "last": null,
        "change": null,
        "volume": 0,
        "open": null,
        "high": null,
        "low": null,
        "close": null,
        "bid": 0.0,
        "ask": 0.01,
        "underlying": "VXX",
        "strike": 16.0,
        "change_percentage": null,
        "average_volume": 0,
        "last_volume": 0,
        "trade_date": 0,
        "prevclose": null,
        "week_52_high": 0.0,
        "week_52_low": 0.0,
        "bidsize": 0,
        "bidexch": "I",
        "bid_date": 1557167321000,
        "asksize": 618,
        "askexch": "Z",
        "ask_date": 1557168367000,
        "open_interest": 10,
        "contract_size": 100,
        "expiration_date": "2019-05-17",
        "expiration_type": "standard",
        "option_type": "put",
        "root_symbol": "VXX"
      }
    ]
  }
}
```
## Get Quotes (Post)
Get a list of symbols using a keyword lookup on the symbols description. Results are in descending order by average volume of the security. This can be used for simple search functions.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.post('https://api.tradier.com/v1/markets/quotes',
    data={'symbols': 'AAPL,VXX190517P00016000', 'greeks': 'false'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "quotes": {
    "quote": [
      {
        "symbol": "AAPL",
        "description": "Apple Inc",
        "exch": "Q",
        "type": "stock",
        "last": 208.21,
        "change": -3.54,
        "volume": 25288395,
        "open": 204.29,
        "high": 208.71,
        "low": 203.5,
        "close": null,
        "bid": 208.19,
        "ask": 208.21,
        "change_percentage": -1.68,
        "average_volume": 27215269,
        "last_volume": 100,
        "trade_date": 1557168406000,
        "prevclose": 211.75,
        "week_52_high": 233.47,
        "week_52_low": 142.0,
        "bidsize": 12,
        "bidexch": "Q",
        "bid_date": 1557168406000,
        "asksize": 1,
        "askexch": "Y",
        "ask_date": 1557168406000,
        "root_symbols": "AAPL"
      },
      {
        "symbol": "VXX190517P00016000",
        "description": "VXX May 17 2019 $16.00 Put",
        "exch": "Z",
        "type": "option",
        "last": null,
        "change": null,
        "volume": 0,
        "open": null,
        "high": null,
        "low": null,
        "close": null,
        "bid": 0.0,
        "ask": 0.01,
        "underlying": "VXX",
        "strike": 16.0,
        "change_percentage": null,
        "average_volume": 0,
        "last_volume": 0,
        "trade_date": 0,
        "prevclose": null,
        "week_52_high": 0.0,
        "week_52_low": 0.0,
        "bidsize": 0,
        "bidexch": "I",
        "bid_date": 1557167321000,
        "asksize": 618,
        "askexch": "Z",
        "ask_date": 1557168367000,
        "open_interest": 10,
        "contract_size": 100,
        "expiration_date": "2019-05-17",
        "expiration_type": "standard",
        "option_type": "put",
        "root_symbol": "VXX"
      }
    ]
  }
}
```
## Get an option chain
Get all quotes in an option chain. Greek and IV data is included courtesy of ORATS. Please check out their APIs for more in-depth options data.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/options/chains',
    params={'symbol': 'VXX', 'expiration': '2019-05-17', 'greeks': 'true'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "options": {
    "option": [
      {
        "symbol": "VXX190517P00016000",
        "description": "VXX May 17 2019 $16.00 Put",
        "exch": "Z",
        "type": "option",
        "last": null,
        "change": null,
        "volume": 0,
        "open": null,
        "high": null,
        "low": null,
        "close": null,
        "bid": 0.0,
        "ask": 0.01,
        "underlying": "VXX",
        "strike": 16.0,
        "change_percentage": null,
        "average_volume": 0,
        "last_volume": 0,
        "trade_date": 0,
        "prevclose": null,
        "week_52_high": 0.0,
        "week_52_low": 0.0,
        "bidsize": 0,
        "bidexch": "J",
        "bid_date": 1557171657000,
        "asksize": 611,
        "askexch": "Z",
        "ask_date": 1557172096000,
        "open_interest": 10,
        "contract_size": 100,
        "expiration_date": "2019-05-17",
        "expiration_type": "standard",
        "option_type": "put",
        "root_symbol": "VXX",
        "greeks": {
          "delta": 1.0,
          "gamma": 1.95546E-10,
          "theta": -0.00204837,
          "vega": 3.54672E-9,
          "rho": 0.106077,
          "phi": -0.28801,
          "bid_iv": 0.0,
          "mid_iv": 0.0,
          "ask_iv": 0.0,
          "smv_vol": 0.380002,
          "updated_at": "2019-08-29 14:59:08"
        }
      },
      {
        "symbol": "VXX190517C00016000",
        "description": "VXX May 17 2019 $16.00 Call",
        "exch": "Z",
        "type": "option",
        "last": null,
        "change": null,
        "volume": 0,
        "open": null,
        "high": null,
        "low": null,
        "close": null,
        "bid": 10.85,
        "ask": 11.0,
        "underlying": "VXX",
        "strike": 16.0,
        "change_percentage": null,
        "average_volume": 0,
        "last_volume": 0,
        "trade_date": 0,
        "prevclose": null,
        "week_52_high": 0.0,
        "week_52_low": 0.0,
        "bidsize": 55,
        "bidexch": "C",
        "bid_date": 1557172097000,
        "asksize": 80,
        "askexch": "E",
        "ask_date": 1557172135000,
        "open_interest": 0,
        "contract_size": 100,
        "expiration_date": "2019-05-17",
        "expiration_type": "standard",
        "option_type": "call",
        "root_symbol": "VXX",
        "greeks": {
          "delta": 1.0,
          "gamma": 1.95546E-10,
          "theta": -0.00204837,
          "vega": 3.54672E-9,
          "rho": 0.106077,
          "phi": -0.28801,
          "bid_iv": 0.0,
          "mid_iv": 0.0,
          "ask_iv": 0.0,
          "smv_vol": 0.380002,
          "updated_at": "2019-08-29 14:59:08"
        }
      },
      {
        "symbol": "VXX190517P00017000",
        "description": "VXX May 17 2019 $17.00 Put",
        "exch": "Z",
        "type": "option",
        "last": null,
        "change": null,
        "volume": 0,
        "open": null,
        "high": null,
        "low": null,
        "close": null,
        "bid": 0.0,
        "ask": 0.01,
        "underlying": "VXX",
        "strike": 17.0,
        "change_percentage": null,
        "average_volume": 0,
        "last_volume": 0,
        "trade_date": 0,
        "prevclose": null,
        "week_52_high": 0.0,
        "week_52_low": 0.0,
        "bidsize": 0,
        "bidexch": "J",
        "bid_date": 1557172023000,
        "asksize": 380,
        "askexch": "Z",
        "ask_date": 1557172096000,
        "open_interest": 0,
        "contract_size": 100,
        "expiration_date": "2019-05-17",
        "expiration_type": "standard",
        "option_type": "put",
        "root_symbol": "VXX",
        "greeks": {
          "delta": 1.0,
          "gamma": 1.95546E-10,
          "theta": -0.00204837,
          "vega": 3.54672E-9,
          "rho": 0.106077,
          "phi": -0.28801,
          "bid_iv": 0.0,
          "mid_iv": 0.0,
          "ask_iv": 0.0,
          "smv_vol": 0.380002,
          "updated_at": "2019-08-29 14:59:08"
        }
      }
      ...
    ]
  }
}
```

## Get an option’s strike prices
Get an options strike prices for a specified expiration date.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/options/strikes',
    params={'symbol': 'VXX', 'expiration': '2019-05-17', 'includeAllRoots': 'true'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "strikes": {
    "strike": [
      22.5,
      25.0,
      27.5,
      30.0,
      32.5,
      35.0,
      37.5,
      40.0,
      42.5,
      45.0,
      47.5,
      50.0,
      52.5,
      55.0,
      57.5,
      60.0,
      62.5,
      65.0,
      67.5,
      70.0,
      72.5,
      75.0,
      80.0,
      85.0,
      90.0
    ]
  }
}
```

## Get an option’s expiration dates
Get expiration dates for a particular underlying.

Note that some underlying securities use a different symbol for their weekly options (RUT/RUTW, SPX/SPXW). To make sure you see all expirations, make sure to send the includeAllRoots parameter. This will also ensure any unique options due to corporate actions (AAPL1) are returned.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/options/expirations',
    params={'symbol': 'VXX', 'includeAllRoots': 'true', 'strikes': 'true', 'contractSize': 'true', 'expirationType': 'true'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "expirations":  {
    "expiration": [
      {
        "date": "2023-11-10",
        "contract_size": 100,
        "expiration_type": "weeklys",
        "strikes": {
          "strike": [12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 25.0, 25.5, 26.0, 26.5, 27.0, 27.5, 28.0, 28.5, 29.0, 29.5, 30.0, 31.0, 32.0, 33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0, 48.0, 49.0, 50.0, 51.0, 52.0, 53.0, 54.0]
        }
      },
      {
        "date": "2023-11-17",
        "contract_size": 100,
        "expiration_type": "standard",
        "strikes": {
          "strike": [9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 25.0, 25.5, 26.0, 26.5, 27.0, 27.5, 28.0, 28.5, 29.0, 29.5, 30.0, 31.0, 32.0, 33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0, 48.0, 49.0, 50.0, 51.0, 52.0, 53.0, 54.0]
        }
      },
      {
        "date": "2023-12-29",
        "contract_size": 100,
        "expiration_type": "quarterlys",
        "strikes": {
          "strike": [12.0, 13.0, 14.0, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 25.0, 25.5, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0]
        }
      }
    ]
  }
}
```

## Lookup options symbols

Get all options symbols for the given underlying. This will include additional option roots (ex. SPXW, RUTW) if applicable.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/options/lookup',
    params={'underlying': 'SPY'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "symbols": [
    {
      "rootSymbol": "SPY"
      "options": [
        "SPY210331C00300000",
        "SPY200702P00252000",
        "SPY200930C00334000",
        "SPY210115C00305000",
        "SPY200622C00288000"
      ]
    }
  ]
}
```
## Get Historical Pricing
Get historical pricing for a security. This data will usually cover the entire lifetime of the company if sending reasonable start/end times. You can fetch historical pricing for options by passing the OCC option symbol (ex. AAPL220617C00270000) as the symbol.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/history',
    params={'symbol': 'AAPL', 'interval': 'daily', 'start': '2019-05-04', 'end': '2019-05-04', 'session_filter': 'all'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "history": {
    "day": [
      {
        "date": "2019-01-02",
        "open": 154.89,
        "high": 158.85,
        "low": 154.23,
        "close": 157.92,
        "volume": 37039737
      },
      {
        "date": "2019-01-03",
        "open": 143.98,
        "high": 145.72,
        "low": 142.0,
        "close": 142.19,
        "volume": 91312195
      },
      {
        "date": "2019-01-04",
        "open": 144.53,
        "high": 148.5499,
        "low": 143.8,
        "close": 148.26,
        "volume": 58607070
      }
      ...
    ]
  }
}
```
## Get Time and Sales
Time and Sales (timesales) is typically used for charting purposes. It captures pricing across a time slice at predefined intervals.

Tick data is also available through this endpoint. This results in a very large data set for high-volume symbols, so the time slice needs to be much smaller to keep downloads time reasonable.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/timesales',
    params={'symbol': 'AAPL', 'interval': '1min', 'start': '2019-05-04 09:30', 'end': '2019-05-04 16:00', 'session_filter': 'all'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "series": {
    "data": [
      {
        "time": "2019-05-09T09:30:00",
        "timestamp": 1557408600,
        "price": 199.64499999999998,
        "open": 200.46,
        "high": 200.53,
        "low": 198.76,
        "close": 200.1154,
        "volume": 1273841,
        "vwap": 199.77806
      },
      {
        "time": "2019-05-09T09:31:00",
        "timestamp": 1557408660,
        "price": 200.2,
        "open": 200.15,
        "high": 200.54,
        "low": 199.86,
        "close": 200.49,
        "volume": 228068,
        "vwap": 200.17588
      },
      {
        "time": "2019-05-09T09:32:00",
        "timestamp": 1557408720,
        "price": 200.445,
        "open": 200.51,
        "high": 200.75,
        "low": 200.14,
        "close": 200.2,
        "volume": 277041,
        "vwap": 200.44681
      },
      ...
    ]
  }
}
```

## Get the ETB List
The ETB list contains securities that are able to be sold short with a Tradier Brokerage account. The list is quite comprehensive and can result in a long download response time.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/etb',
    params={},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "securities": {
    "security": [
      {
        "symbol": "SCS",
        "exchange": "N",
        "type": "stock",
        "description": "Steelcase Inc"
      },
      {
        "symbol": "EXAS",
        "exchange": "Q",
        "type": "stock",
        "description": "Exact Sciences Corp"
      },
      {
        "symbol": "BBL",
        "exchange": "N",
        "type": "stock",
        "description": "BHP Group PlcSponsored ADR"
      },
      {
        "symbol": "WLH",
        "exchange": "N",
        "type": "stock",
        "description": "William Lyon Homes"
      },
      {
        "symbol": "IBKC",
        "exchange": "Q",
        "type": "stock",
        "description": "IBERIABANK Corp"
      },
      {
        "symbol": "BBT",
        "exchange": "N",
        "type": "stock",
        "description": "BB&T Corp"
      }
    ]
  }
}
```
## Get the intraday status
Get the intraday market status. This call will change and return information pertaining to the current day. If programming logic on whether the market is open/closed – this API call should be used to determine the current state.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/clock',
    params={'delayed': 'true'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "clock": {
    "date": "2019-05-06",
    "description": "Market is open from 09:30 to 16:00",
    "state": "open",
    "timestamp": 1557156988,
    "next_change": "16:00",
    "next_state": "postmarket"
  }
}
```

## Get the market calendar
Get the market calendar for the current or given month. This can be used to plan ahead regarding strategies. However, the Get Intraday Status should be used to determine the current status of the market.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/calendar',
    params={'month': '02', 'year': '2019'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "calendar": {
    "month": 4,
    "year": 2019,
    "days": {
      "day": [
        {
          "date": "2019-04-01",
          "status": "open",
          "description": "Market is open",
          "premarket": {
            "start": "07:00",
            "end": "09:24"
          },
          "open": {
            "start": "09:30",
            "end": "16:00"
          },
          "postmarket": {
            "start": "16:00",
            "end": "20:00"
          }
        },
        {
          "date": "2019-04-02",
          "status": "open",
          "description": "Market is open",
          "premarket": {
            "start": "07:00",
            "end": "09:24"
          },
          "open": {
            "start": "09:30",
            "end": "16:00"
          },
          "postmarket": {
            "start": "16:00",
            "end": "20:00"
          }
        },
        {
          "date": "2019-04-03",
          "status": "open",
          "description": "Market is open",
          "premarket": {
            "start": "07:00",
            "end": "09:24"
          },
          "open": {
            "start": "09:30",
            "end": "16:00"
          },
          "postmarket": {
            "start": "16:00",
            "end": "20:00"
          }
        }
        ...
      ]
    }
  }
}
```

## Search for Symbols
Get a list of symbols using a keyword lookup on the symbols description. Results are in descending order by average volume of the security. This can be used for simple search functions.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/search',
    params={'q': 'alphabet', 'indexes': 'false'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "securities": {
    "security": [
      {
        "symbol": "GOOGL",
        "exchange": "Q",
        "type": "stock",
        "description": "Alphabet Inc"
      },
      {
        "symbol": "GOOG",
        "exchange": "Q",
        "type": "stock",
        "description": "Alphabet Inc. - Class C Capital Stock"
      }
    ]
  }
}
```

## Search for Symbols
Search for a symbol using the ticker symbol or partial symbol. Results are in descending order by average volume of the security. This can be used for simple search functions.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/v1/markets/lookup',
    params={'q': 'goog', 'exchanges': 'Q,N', 'types': 'stock, option, etf, index'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
{
  "securities": {
    "security": [
      {
        "symbol": "GOOGL",
        "exchange": "Q",
        "type": "stock",
        "description": "Alphabet Inc"
      },
      {
        "symbol": "GOOG",
        "exchange": "Q",
        "type": "stock",
        "description": "Alphabet Inc. - Class C Capital Stock"
      }
    ]
  }
}
```
## Get Company Information
Get company fundamental information.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/beta/markets/fundamentals/company',
    params={'symbols': 'MSFT'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
[
  {
    "request": "MSFT",
    "type": "Symbol",
    "results": [
      {
        "type": "Company",
        "id": "0C000008EC",
        "tables": {
          "company_profile": {
            "company_id": "0C000008EC",
            "average_employee_number": 0,
            "contact_email": "msft@microsoft.com",
            "headquarter": {
              "address_line1": "One Microsoft Way",
              "city": "Redmond",
              "country": "USA",
              "fax": "+1 425 706-7329",
              "homepage": "http://www.microsoft.com",
              "phone": "+1 425 882-8080",
              "postal_code": "98052-6399",
              "province": "WA"
            },
            "is_head_office_same_with_registered_office_flag": false,
            "total_employee_number": 131000,
            "TotalEmployeeNumber.asOfDate": "2018-06-30"
          },
          "asset_classification": {
            "company_id": "0C000008EC",
            "c_a_n_n_a_i_c_s": 0,
            "financial_health_grade": "A",
            "FinancialHealthGrade.asOfDate": "2019-05-08",
            "growth_grade": "C",
            "GrowthGrade.asOfDate": "2019-04-30",
            "growth_score": 60.55918,
            "morningstar_economy_sphere_code": 3,
            "morningstar_industry_code": 31165134,
            "morningstar_industry_group_code": 31165,
            "morningstar_sector_code": 311,
            "n_a_c_e": 62.09,
            "n_a_i_c_s": 511210,
            "profitability_grade": "C",
            "ProfitabilityGrade.asOfDate": "2019-04-30",
            "s_i_c": 7372,
            "size_score": 398.87,
            "stock_type": 2,
            "StockType.asOfDate": "2019-04-30",
            "style_box": 3,
            "StyleBox.asOfDate": "2019-04-30",
            "style_score": 317.62,
            "value_score": 48.75043
          },
          "historical_asset_classification": {
            "company_id": "0C000008EC",
            "as_of_date": "2019-05-01",
            "financial_health_grade": "A",
            "growth_score": 60.55918,
            "morningstar_economy_sphere_code": 3,
            "morningstar_industry_code": 31165134,
            "morningstar_industry_group_code": 31165,
            "morningstar_sector_code": 311,
            "profitability_grade": "A+",
            "size_score": 398.87,
            "stock_type": 0,
            "style_box": 0,
            "style_score": 317.62,
            "value_score": 48.75043
          },
          "long_descriptions": "Microsoft develops and licenses consumer and enterprise software. It is known for its Windows operating systems and Office productivity suite. The company is organized into three overarching segments: productivity and business processes (legacy Microsoft Office, cloud-based Office 365, Exchange, SharePoint, Skype, LinkedIn, Dynamics), intelligence cloud (infrastructure- and platform-as-a-service offerings Azure, Windows Server OS, SQL Server), and more personal computing (Windows Client, Xbox, Bing search, display advertising, and Surface laptops, tablets, and desktops). Through acquisitions, Microsoft owns Xamarin, LinkedIn, and GitHub. It reports revenue in product and service and other revenue on its income statement."
        }
      }
      ...
    ]
  }
]
```

## Get Corporate Calendars
Get corporate calendar information for securities. This does not include dividend information.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/beta/markets/fundamentals/calendars',
    params={'symbols': 'MSFT'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
[
  {
    "request": "MSFT",
    "type": "Symbol",
    "results": [
      {
        "type": "Company",
        "id": "0C000008EC",
        "tables": {
          "corporate_calendars": [
            {
              "company_id": "0C000008EC",
              "begin_date_time": "2013-01-24",
              "end_date_time": "2013-01-24",
              "event_type": 8,
              "estimated_date_for_next_event": "1970-01-01",
              "event": "Microsoft Fiscal Year 2013 Second Quarter Earnings",
              "event_fiscal_year": 2013,
              "event_status": "Confirmed",
              "time_zone": "1970-01-01"
            },
            {
              "company_id": "0C000008EC",
              "begin_date_time": "2015-01-26",
              "end_date_time": "2015-01-26",
              "event_type": 13,
              "estimated_date_for_next_event": "1970-01-01",
              "event": "Microsoft Corp Second quarter earnings Conference Call in 2015",
              "event_fiscal_year": 2015,
              "event_status": "Confirmed",
              "time_zone": "1969-12-31"
            }
            ...
          ]
        }
      }
    ]
  }
]
```
## Get Dividends
Get dividend information for a security. This will include previous dividends as well as formally announced future dividend dates.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/beta/markets/fundamentals/dividends',
    params={'symbols': 'MSFT'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
[
  {
    "request": "MSFT",
    "type": "Symbol",
    "results": [
      {
        "type": "Stock",
        "id": "0P000003MH",
        "tables": {
          "cash_dividends": [
            {
              "share_class_id": "0P000003MH",
              "dividend_type": "CD",
              "ex_date": "2014-02-18",
              "cash_amount": 0.28,
              "currency_i_d": "USD",
              "declaration_date": "2013-11-19",
              "frequency": 4,
              "pay_date": "2014-03-13",
              "record_date": "2014-02-20"
            },
            {
              "share_class_id": "0P000003MH",
              "dividend_type": "CD",
              "ex_date": "2015-11-17",
              "cash_amount": 0.36,
              "currency_i_d": "USD",
              "declaration_date": "2015-09-15",
              "frequency": 4,
              "pay_date": "2015-12-10",
              "record_date": "2015-11-19"
            },
            {
              "share_class_id": "0P000003MH",
              "dividend_type": "CD",
              "ex_date": "2010-02-16",
              "cash_amount": 0.13,
              "currency_i_d": "USD",
              "declaration_date": "2009-12-10",
              "frequency": 4,
              "pay_date": "2010-03-11",
              "record_date": "2010-02-18"
            }
            ...
          ]
        }
      }
    ]
  }
]
```
## Get Corporate Action Information
Retrieve corporate action information. This will include both historical and scheduled future actions.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/beta/markets/fundamentals/corporate_actions',
    params={'symbols': 'MSFT'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
[
  {
    "request": "MSFT",
    "type": "Symbol",
    "results": [
      {
        "type": "Company",
        "id": "0C000008EC",
        "tables": {
          "mergers_and_acquisitions": {
            "acquired_company_id": "0C00008KGV",
            "parent_company_id": "0C000008EC",
            "cash_amount": 196.0,
            "currency_id": "USD",
            "effective_date": "2016-12-08",
            "notes": "http://blogs.microsoft.com/blog/2016/12/08/microsoft-and-linkedin-begin-journey-to-empower-professionals-around-the-world-to-achieve-more/#sm.000424kd7jadd7a11se14ljr6qdp6"
          }
        }
      },
      {
        "type": "Stock",
        "id": "0P000003MH",
        "tables": {
          "stock_splits": {
            "1987-09-21": {
              "share_class_id": "0P000003MH",
              "ex_date": "1987-09-21",
              "adjustment_factor": 2.0,
              "split_from": 1.0,
              "split_to": 2.0,
              "split_type": "SS"
            },
            "1990-04-16": {
              "share_class_id": "0P000003MH",
              "ex_date": "1990-04-16",
              "adjustment_factor": 2.0,
              "split_from": 1.0,
              "split_to": 2.0,
              "split_type": "SS"
            },
            "1991-06-27": {
              "share_class_id": "0P000003MH",
              "ex_date": "1991-06-27",
              "adjustment_factor": 1.5,
              "split_from": 2.0,
              "split_to": 3.0,
              "split_type": "SS"
            },
            "1992-06-15": {
              "share_class_id": "0P000003MH",
              "ex_date": "1992-06-15",
              "adjustment_factor": 1.5,
              "split_from": 2.0,
              "split_to": 3.0,
              "split_type": "SS"
            },
            "1994-05-23": {
              "share_class_id": "0P000003MH",
              "ex_date": "1994-05-23",
              "adjustment_factor": 2.0,
              "split_from": 1.0,
              "split_to": 2.0,
              "split_type": "SS"
            },
            "1996-12-09": {
              "share_class_id": "0P000003MH",
              "ex_date": "1996-12-09",
              "adjustment_factor": 2.0,
              "split_from": 1.0,
              "split_to": 2.0,
              "split_type": "SS"
            },
            "1998-02-23": {
              "share_class_id": "0P000003MH",
              "ex_date": "1998-02-23",
              "adjustment_factor": 2.0,
              "split_from": 1.0,
              "split_to": 2.0,
              "split_type": "SS"
            },
            "1999-03-29": {
              "share_class_id": "0P000003MH",
              "ex_date": "1999-03-29",
              "adjustment_factor": 2.0,
              "split_from": 1.0,
              "split_to": 2.0,
              "split_type": "SS"
            },
            "2003-02-18": {
              "share_class_id": "0P000003MH",
              "ex_date": "2003-02-18",
              "adjustment_factor": 2.0,
              "split_from": 1.0,
              "split_to": 2.0,
              "split_type": "SS"
            }
          }
        }
      }
    ]
  }
]
```

## Get Ratios
Get standard financial ratios for a company.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/beta/markets/fundamentals/ratios',
    params={'symbols': 'MSFT'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
[
  {
    "request": "MSFT",
    "type": "Symbol",
    "results": [
      {
        "type": "Company",
        "id": "0C000008EC",
        "tables": {
          "operation_ratios_restate": [
            {
              "period_1y": {
                "company_id": "0C000008EC",
                "as_of_date": "2019-03-31",
                "fiscal_year_end": "6",
                "period": "1Y",
                "report_type": "TTM",
                "assets_turnover": 0.48041,
                "cap_ex_sales_ratio": 0.113361,
                "capital_expenditureto_e_b_i_t_d_a": -0.248569,
                "cash_conversion_cycle": 6.375441,
                "days_in_inventory": 17.433416,
                "days_in_payment": 65.52977,
                "days_in_sales": 54.471795,
                "e_b_i_t_d_a_margin": 0.456056,
                "e_b_i_t_margin": 0.363805,
                "f_c_f_net_income_ratio": 0.963208,
                "f_c_f_sales_ratio": 0.27527,
                "f_c_fto_c_f_o": 0.708306,
                "fix_assets_turonver": 3.969372,
                "gross_margin": 0.654368,
                "interest_coverage": 16.534399,
                "inventory_turnover": 20.936803,
                "net_incomes_per_employee": 266610.687023,
                "net_margin": 0.285784,
                "normalized_net_profit_margin": 0.261668,
                "normalized_r_o_i_c": 0.211043,
                "operation_margin": 0.334937,
                "payment_turnover": 5.569987,
                "pretax_margin": 0.341802,
                "receivable_turnover": 6.700716,
                "r_o_a": 0.137294,
                "r_o_e": 0.401211,
                "r_o_i_c": 0.229216,
                "sales_per_employee": 932908.396947,
                "tax_rate": 0.16389,
                "working_capital_turnover_ratio": 1.128699
              }
            },
            {
              "period_3m": {
                "company_id": "0C000008EC",
                "as_of_date": "2019-03-31",
                "fiscal_year_end": "6",
                "period": "3M",
                "report_type": "P",
                "cash_ratio": 2.443661,
                "cashto_total_assets": 0.499915,
                "common_equity_to_assets": 0.360315,
                "current_ratio": 2.968512,
                "debtto_assets": 0.27765,
                "e_b_i_t_d_a_margin": 0.433973,
                "e_b_i_t_margin": 0.338262,
                "financial_leverage": 2.775352,
                "gross_margin": 0.667332,
                "long_term_debt_equity_ratio": 0.7019,
                "long_term_debt_total_capital_ratio": 0.412421,
                "net_incomes_per_employee": 67244.274809,
                "net_margin": 0.288149,
                "normalized_net_profit_margin": 0.288149,
                "operation_margin": 0.338262,
                "pretax_margin": 0.343005,
                "quick_ratio": 2.801415,
                "sales_per_employee": 233366.412214,
                "tax_rate": 0.159928,
                "total_debt_equity_ratio": 0.770577
              },
              "period_9m": {
                "company_id": "0C000008EC",
                "as_of_date": "2019-03-31",
                "fiscal_year_end": "6",
                "period": "9M",
                "report_type": "P",
                "e_b_i_t_d_a_margin": 0.42672,
                "e_b_i_t_margin": 0.331654,
                "gross_margin": 0.647244,
                "net_incomes_per_employee": 198877.862595,
                "net_margin": 0.282797,
                "normalized_net_profit_margin": 0.282797,
                "operation_margin": 0.331654,
                "pretax_margin": 0.337494,
                "sales_per_employee": 703251.908397,
                "tax_rate": 0.162067
              }
            },
            {
              "period_3m": {
                "company_id": "0C000008EC",
                "as_of_date": "2019-03-31",
                "fiscal_year_end": "6",
                "period": "3M",
                "report_type": "R",
                "assets_turnover": 0.117099,
                "cash_conversion_cycle": 7.905167,
                "cash_ratio": 2.443661,
                "cashto_total_assets": 0.499915,
                "common_equity_to_assets": 0.360315,
                "current_ratio": 2.968512,
                "days_in_inventory": 17.550147,
                "days_in_payment": 67.773537,
                "days_in_sales": 58.128557,
                "debtto_assets": 0.27765,
                "e_b_i_t_d_a_margin": 0.460665,
                "e_b_i_t_margin": 0.364954,
                "financial_leverage": 2.775352,
                "fix_assets_turonver": 0.921299,
                "gross_margin": 0.667332,
                "interest_coverage": 16.627422,
                "inventory_turnover": 5.199387,
                "long_term_debt_equity_ratio": 0.7019,
                "long_term_debt_total_capital_ratio": 0.412421,
                "net_income_cont_ops_growth": 0.186557,
                "net_income_growth": 0.186557,
                "net_incomes_per_employee": 67244.274809,
                "net_margin": 0.288149,
                "normalized_net_profit_margin": 0.266167,
                "normalized_r_o_i_c": 0.052215,
                "operation_income_growth": 0.247106,
                "operation_margin": 0.338262,
                "operation_revenue_growth3_month_avg": 0.139901,
                "payment_turnover": 1.346396,
                "pretax_margin": 0.343005,
                "quick_ratio": 2.801415,
                "receivable_turnover": 1.569796,
                "revenue_growth": 0.139901,
                "r_o_a": 0.033742,
                "r_o_e": 0.094218,
                "r_o_i_c": 0.056248,
                "sales_per_employee": 233366.412214,
                "tax_rate": 0.159928,
                "total_debt_equity_ratio": 0.770577,
                "working_capital_turnover_ratio": 0.287616
              },
              "period_9m": {
                "company_id": "0C000008EC",
                "as_of_date": "2019-03-31",
                "fiscal_year_end": "6",
                "period": "9M",
                "report_type": "R",
                "e_b_i_t_d_a_margin": 0.454454,
                "e_b_i_t_margin": 0.359388,
                "gross_margin": 0.647244,
                "interest_coverage": 16.414973,
                "net_income_cont_ops_growth": 2.384386,
                "net_income_growth": 2.384386,
                "net_incomes_per_employee": 198877.862595,
                "net_margin": 0.282797,
                "normalized_net_profit_margin": 0.260085,
                "operation_income_growth": 0.238057,
                "operation_margin": 0.331654,
                "operation_revenue_growth3_month_avg": 0.14763,
                "pretax_margin": 0.337494,
                "revenue_growth": 0.14763,
                "sales_per_employee": 703251.908397,
                "tax_rate": 0.162067
              }
            }
          ],
          "operation_ratios_a_o_r": [
            {
              "period_1y": {
                "company_id": "0C000008EC",
                "as_of_date": "2019-03-31",
                "fiscal_year_end": "6",
                "period": "1Y",
                "report_type": "TTM",
                "assets_turnover": 0.48041,
                "cap_ex_sales_ratio": 0.113361,
                "capital_expenditureto_e_b_i_t_d_a": -0.248569,
                "cash_conversion_cycle": 6.375441,
                "days_in_inventory": 17.433416,
                "days_in_payment": 65.52977,
                "days_in_sales": 54.471795,
                "e_b_i_t_d_a_margin": 0.456056,
                "e_b_i_t_margin": 0.363805,
                "f_c_f_net_income_ratio": 0.963208,
                "f_c_f_sales_ratio": 0.27527,
                "f_c_fto_c_f_o": 0.708306,
                "fix_assets_turonver": 3.969372,
                "gross_margin": 0.654368,
                "interest_coverage": 16.534399,
                "inventory_turnover": 20.936803,
                "net_incomes_per_employee": 266610.687023,
                "net_margin": 0.285784,
                "normalized_net_profit_margin": 0.261668,
                "normalized_r_o_i_c": 0.211043,
                "operation_margin": 0.334937,
                "payment_turnover": 5.569987,
                "pretax_margin": 0.341802,
                "receivable_turnover": 6.700716,
                "r_o_a": 0.137294,
                "r_o_e": 0.401211,
                "r_o_i_c": 0.229216,
                "sales_per_employee": 932908.396947,
                "tax_rate": 0.16389,
                "working_capital_turnover_ratio": 1.128699
              }
            },
            {
              "period_3m": {
                "company_id": "0C000008EC",
                "as_of_date": "2019-03-31",
                "fiscal_year_end": "6",
                "period": "3M",
                "report_type": "P",
                "cash_ratio": 2.443661,
                "cashto_total_assets": 0.499915,
                "common_equity_to_assets": 0.360315,
                "current_ratio": 2.968512,
                "debtto_assets": 0.27765,
                "e_b_i_t_d_a_margin": 0.433973,
                "e_b_i_t_margin": 0.338262,
                "financial_leverage": 2.775352,
                "gross_margin": 0.667332,
                "long_term_debt_equity_ratio": 0.7019,
                "long_term_debt_total_capital_ratio": 0.412421,
                "net_incomes_per_employee": 67244.274809,
                "net_margin": 0.288149,
                "normalized_net_profit_margin": 0.288149,
                "operation_margin": 0.338262,
                "pretax_margin": 0.343005,
                "quick_ratio": 2.801415,
                "sales_per_employee": 233366.412214,
                "tax_rate": 0.159928,
                "total_debt_equity_ratio": 0.770577
              },
              "period_9m": {
                "company_id": "0C000008EC",
                "as_of_date": "2019-03-31",
                "fiscal_year_end": "6",
                "period": "9M",
                "report_type": "P",
                "e_b_i_t_d_a_margin": 0.42672,
                "e_b_i_t_margin": 0.331654,
                "gross_margin": 0.647244,
                "net_incomes_per_employee": 198877.862595,
                "net_margin": 0.282797,
                "normalized_net_profit_margin": 0.282797,
                "operation_margin": 0.331654,
                "pretax_margin": 0.337494,
                "sales_per_employee": 703251.908397,
                "tax_rate": 0.162067
              }
            },
            {
              "period_3m": {
                "company_id": "0C000008EC",
                "as_of_date": "2019-03-31",
                "fiscal_year_end": "6",
                "period": "3M",
                "report_type": "A",
                "assets_turnover": 0.117099,
                "cash_conversion_cycle": 7.905167,
                "cash_ratio": 2.443661,
                "cashto_total_assets": 0.499915,
                "common_equity_to_assets": 0.360315,
                "current_ratio": 2.968512,
                "days_in_inventory": 17.550147,
                "days_in_payment": 67.773537,
                "days_in_sales": 58.128557,
                "debtto_assets": 0.27765,
                "e_b_i_t_d_a_margin": 0.460665,
                "e_b_i_t_margin": 0.364954,
                "financial_leverage": 2.775352,
                "fix_assets_turonver": 0.921299,
                "gross_margin": 0.667332,
                "interest_coverage": 16.627422,
                "inventory_turnover": 5.199387,
                "long_term_debt_equity_ratio": 0.7019,
                "long_term_debt_total_capital_ratio": 0.412421,
                "net_income_cont_ops_growth": 0.0462,
                "net_income_growth": 0.0462,
                "net_incomes_per_employee": 67244.274809,
                "net_margin": 0.288149,
                "normalized_net_profit_margin": 0.266167,
                "normalized_r_o_i_c": 0.052215,
                "operation_income_growth": 0.008091,
                "operation_margin": 0.338262,
                "operation_revenue_growth3_month_avg": -0.058514,
                "payment_turnover": 1.346396,
                "pretax_margin": 0.343005,
                "quick_ratio": 2.801415,
                "receivable_turnover": 1.569796,
                "revenue_growth": -0.058514,
                "r_o_a": 0.033742,
                "r_o_e": 0.094218,
                "r_o_i_c": 0.056248,
                "sales_per_employee": 233366.412214,
                "tax_rate": 0.159928,
                "total_debt_equity_ratio": 0.770577,
                "working_capital_turnover_ratio": 0.287616
              },
              "period_9m": {
                "company_id": "0C000008EC",
                "as_of_date": "2019-03-31",
                "fiscal_year_end": "6",
                "period": "9M",
                "report_type": "A",
                "e_b_i_t_d_a_margin": 0.454454,
                "e_b_i_t_margin": 0.359388,
                "gross_margin": 0.647244,
                "interest_coverage": 16.414973,
                "net_incomes_per_employee": 198877.862595,
                "net_margin": 0.282797,
                "normalized_net_profit_margin": 0.260085,
                "operation_margin": 0.331654,
                "pretax_margin": 0.337494,
                "sales_per_employee": 703251.908397,
                "tax_rate": 0.162067
              },
              "period_5y": {
                "company_id": "0C000008EC",
                "as_of_date": "2019-03-31",
                "fiscal_year_end": "6",
                "period": "5Y",
                "report_type": "A",
                "regression_growth_operating_revenue5_years": 0.060558
              }
            }
          ]
        }
      },
      {
        "type": "Stock",
        "id": "0P000003MH",
        "tables": {
          "earning_ratios_restate": {
            "period_3m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-03-31",
              "fiscal_year_end": "6",
              "period": "3M",
              "report_type": "R",
              "diluted_cont_e_p_s_growth": 0.2,
              "diluted_e_p_s_growth": 0.2,
              "d_p_s_growth": 0.095238,
              "normalized_basic_e_p_s_growth": 0.25789,
              "normalized_diluted_e_p_s_growth": 0.25981
            },
            "period_9m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-03-31",
              "fiscal_year_end": "6",
              "period": "9M",
              "report_type": "R",
              "diluted_cont_e_p_s_growth": 2.393939,
              "diluted_e_p_s_growth": 2.393939,
              "d_p_s_growth": 0.089431,
              "normalized_basic_e_p_s_growth": 2.557041,
              "normalized_diluted_e_p_s_growth": 2.560722
            }
          },
          "valuation_ratios": {
            "share_class_id": "0P000003MH",
            "as_of_date": "2019-05-09",
            "1st_year_estimated_e_p_s_growth": 0.2365,
            "2nd_year_estimated_e_p_s_growth": 0.1639,
            "2_years_forward_earning_yield": 0.0473,
            "2_years_forward_p_e_ratio": 21.1636,
            "2_yrs_e_v_to_forward_e_b_i_t": 15.5282,
            "2_yrs_e_v_to_forward_e_b_i_t_d_a": 12.0161,
            "book_value_per_share": 12.3798,
            "book_value_yield": 0.0986,
            "buy_back_yield": 0.0168,
            "c_a_p_e_ratio": 47.362,
            "cash_return": 0.0372,
            "c_f_o_per_share": 6.1167,
            "c_f_yield": 0.0487,
            "dividend_rate": 1.84,
            "dividend_yield": 0.014,
            "div_yield5_year": 0.0221,
            "earning_yield": 0.0359,
            "e_vto_e_b_i_t": 21.5522,
            "e_v_to_e_b_i_t_d_a": 16.9832,
            "e_vto_f_c_f": 26.8472,
            "e_v_to_forward_e_b_i_t": 18.6879,
            "e_v_to_forward_e_b_i_t_d_a": 14.6195,
            "e_v_to_forward_revenue": 6.5328,
            "e_vto_pre_tax_income": 21.6213,
            "e_vto_revenue": 7.3902,
            "e_vto_total_assets": 3.4304,
            "expected_dividend_growth_rate": 0.0455,
            "f_c_f_per_share": 4.3325,
            "f_c_f_ratio": 28.966919,
            "f_c_f_yield": 0.0345,
            "forward_calculation_style": "Annual",
            "forward_dividend_yield": 0.0147,
            "forward_earning_yield": 0.0406,
            "forward_p_e_ratio": 24.6305,
            "forward_r_o_a": 0.1483,
            "forward_r_o_e": 0.4116,
            "normalized_p_e_ratio": 27.888889,
            "payout_ratio": 0.3911,
            "p_b_ratio": 10.137498,
            "p_b_ratio10_year_growth": 0.080398,
            "p_b_ratio3_yr_avg": 10.31312,
            "p_cash_ratio3_yr_avg": 7.433207,
            "p_c_f_ratio": 20.517447,
            "p_e_g_payback": 11.4072,
            "p_e_g_ratio": 2.1702,
            "p_e_ratio": 27.888889,
            "p_e_ratio10_year_average": 16.56723,
            "p_e_ratio10_year_growth": 0.095906,
            "p_e_ratio10_year_high": 29.022222,
            "p_e_ratio10_year_low": 11.103448,
            "p_e_ratio1_year_average": 28.372037,
            "p_e_ratio1_year_high": 29.022222,
            "p_e_ratio1_year_low": 27.78,
            "p_e_ratio3_yr_avg": 28.372037,
            "p_e_ratio5_year_average": 28.372037,
            "p_e_ratio5_year_high": 29.022222,
            "p_e_ratio5_year_low": 27.78,
            "p_f_c_f_ratio10_year_growth": 0.099825,
            "p_f_c_f_ratio3_yr_avg": 29.496171,
            "price_change1_m": 0.960949,
            "priceto_cash_ratio": 7.306627,
            "priceto_e_b_i_t_d_a": 17.484097,
            "p_s_ratio": 7.973719,
            "p_s_ratio10_year_growth": 0.106779,
            "p_s_ratio3_yr_avg": 8.111855,
            "ratio_p_e5_year_average": 28.372037,
            "sales_per_share": 15.7392,
            "sales_yield": 0.1254,
            "sustainable_growth_rate": 0.2443,
            "tangible_book_value_per_share": 5.8595,
            "tangible_b_v_per_share3_yr_avg": 5.8879,
            "tangible_b_v_per_share5_yr_avg": 6.4777,
            "total_asset_per_share": 34.3582,
            "total_yield": 0.0308,
            "working_capital_per_share": 13.8364,
            "working_capital_per_share3_yr_avg": 13.689,
            "working_capital_per_share5_yr_avg": 11.6856
          },
          "alpha_beta": {
            "period_36m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-04-30",
              "period": "36M",
              "alpha": 0.019051,
              "beta": 1.032369,
              "non_div_alpha": -0.005522,
              "non_div_beta": 1.023017,
              "non_div_r_square": 48.598183,
              "r_square": 49.437756
            },
            "period_48m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-04-30",
              "period": "48M",
              "alpha": 0.015008,
              "beta": 1.170915,
              "non_div_alpha": -0.159606,
              "non_div_beta": 1.172809,
              "non_div_r_square": 49.950576,
              "r_square": 50.531957
            },
            "period_60m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-04-30",
              "period": "60M",
              "alpha": 0.013512,
              "beta": 1.243847,
              "non_div_alpha": -0.221989,
              "non_div_beta": 1.233689,
              "non_div_r_square": 42.687331,
              "r_square": 43.536083
            },
            "period_120m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-04-30",
              "period": "120M",
              "alpha": 0.008512,
              "beta": 1.02019,
              "non_div_alpha": -0.016477,
              "non_div_beta": 1.022949,
              "non_div_r_square": 34.885912,
              "r_square": 35.021821
            }
          }
        }
      }
    ]
  }
]
```
## Get Financial Information
Retrieve corporate financial information and statements.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/beta/markets/fundamentals/financials',
    params={'symbols': 'MSFT'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
[
  {
    "request": "MSFT",
    "type": "Symbol",
    "results": [
      {
        "type": "Company",
        "id": "0C000008EC",
        "tables": {
          "segmentation": {
            "period_3m": {
              "company_id": "0C000008EC",
              "as_of_date": "2018-06-30",
              "period": "3M",
              "operating_income": 1.484E9,
              "operating_revenue": 2.197E9,
              "total_assets": 1.10605424947E11,
              "total_non_current_assets": 2.2819E10
            },
            "period_6m": {
              "company_id": "0C000008EC",
              "as_of_date": "2015-12-31",
              "period": "6M",
              "operating_income": 3.068E9,
              "operating_revenue": 4.609E9
            },
            "period_9m": {
              "company_id": "0C000008EC",
              "as_of_date": "2016-03-31",
              "period": "9M",
              "operating_income": 4.475E9,
              "operating_revenue": 6.947E9
            },
            "period_12m": {
              "company_id": "0C000008EC",
              "as_of_date": "2018-06-30",
              "period": "12M",
              "operating_income": 6.007E9,
              "operating_revenue": 8.59E9,
              "total_assets": 1.10605424947E11,
              "total_non_current_assets": 2.2819E10
            }
          },
          "financial_statements_restate": {
            "company_id": "0C000008EC",
            "as_of_date": "2019-03-31",
            "balance_sheet": [
              {
                "period_3m": {
                  "currency_id": "USD",
                  "fiscal_year_end": "6",
                  "period": "3M",
                  "report_type": "R",
                  "accession_number": "0001564590-19-012709",
                  "accounts_payable": 7.544E9,
                  "accounts_receivable": 1.9269E10,
                  "accumulated_depreciation": -3.5431E10,
                  "allowance_for_doubtful_accounts_receivable": -3.36E8,
                  "b_s_file_date": "1970-01-01",
                  "capital_stock": 7.7791E10,
                  "cash_and_cash_equivalents": 1.1212E10,
                  "cash_cash_equivalents_and_marketable_securities": 1.31618E11,
                  "common_stock": 7.7791E10,
                  "common_stock_equity": 9.4864E10,
                  "current_assets": 1.59887E11,
                  "current_debt": 6.515E9,
                  "current_debt_and_capital_lease_obligation": 6.515E9,
                  "current_deferred_liabilities": 2.4251E10,
                  "current_deferred_revenue": 2.4251E10,
                  "current_liabilities": 5.3861E10,
                  "file_date": "2019-04-24",
                  "finished_goods": 1.43E9,
                  "fiscal_year_end_change": false,
                  "form_type": "10-Q",
                  "gains_losses_not_affecting_retained_earnings": -1.265E9,
                  "goodwill": 4.1861E10,
                  "goodwill_and_other_intangible_assets": 4.9964E10,
                  "gross_accounts_receivable": 1.9605E10,
                  "gross_p_p_e": 6.9079E10,
                  "income_tax_payable": 1.95E9,
                  "inventory": 1.951E9,
                  "invested_capital": 1.67964E11,
                  "investments_and_advances": 2.403E9,
                  "long_term_debt": 6.6585E10,
                  "long_term_debt_and_capital_lease_obligation": 6.6585E10,
                  "long_term_investments": 2.403E9,
                  "net_debt": 6.1888E10,
                  "net_p_p_e": 3.3648E10,
                  "net_tangible_assets": 4.49E10,
                  "non_current_deferred_liabilities": 5.722E9,
                  "non_current_deferred_revenue": 3.884E9,
                  "non_current_deferred_taxes_liabilities": 1.838E9,
                  "number_of_share_holders": 0,
                  "ordinary_shares_number": 7.666E9,
                  "other_current_assets": 7.049E9,
                  "other_current_liabilities": 7.837E9,
                  "other_intangible_assets": 8.103E9,
                  "other_non_current_assets": 1.7379E10,
                  "other_non_current_liabilities": 1.2735E10,
                  "other_short_term_investments": 1.20406E11,
                  "payables": 9.494E9,
                  "payables_and_accrued_expenses": 9.494E9,
                  "pensionand_other_post_retirement_benefit_plans_current": 5.764E9,
                  "period_ending_date": "2019-03-31",
                  "raw_materials": 4.5E8,
                  "receivables": 1.9269E10,
                  "retained_earnings": 1.8338E10,
                  "share_issued": 7.666E9,
                  "stockholders_equity": 9.4864E10,
                  "tangible_book_value": 4.49E10,
                  "total_assets": 2.63281E11,
                  "total_capitalization": 1.61449E11,
                  "total_debt": 7.31E10,
                  "total_equity": 9.4864E10,
                  "total_equity_gross_minority_interest": 9.4864E10,
                  "total_liabilities_net_minority_interest": 1.68417E11,
                  "total_non_current_assets": 1.03394E11,
                  "total_non_current_liabilities_net_minority_interest": 1.14556E11,
                  "total_tax_payable": 1.95E9,
                  "tradeand_other_payables_non_current": 2.9514E10,
                  "working_capital": 1.06026E11,
                  "work_in_process": 7.1E7
                }
              }
            ],
            "cash_flow_statement": [
              {
                "period_12m": {
                  "currency_id": "USD",
                  "fiscal_year_end": "6",
                  "period": "12M",
                  "report_type": "TTM",
                  "beginning_cash_position": 9.221E9,
                  "capital_expenditure": -1.3854E10,
                  "cash_dividends_paid": -1.3516E10,
                  "cash_flow_from_continuing_financing_activities": -3.424E10,
                  "cash_flow_from_continuing_investing_activities": -1.1186E10,
                  "cash_flow_from_continuing_operating_activities": 4.7495E10,
                  "c_f_file_date": "1970-01-01",
                  "change_in_account_payable": -2.2E7,
                  "change_in_inventory": 1.38E8,
                  "change_in_other_current_assets": -1.703E9,
                  "change_in_other_current_liabilities": 7.56E8,
                  "change_in_other_working_capital": -4.35E8,
                  "change_in_payable": -2.2E7,
                  "change_in_payables_and_accrued_expense": -2.2E7,
                  "change_in_receivables": -1.93E9,
                  "change_in_working_capital": -3.196E9,
                  "changes_in_account_receivables": -1.93E9,
                  "changes_in_cash": 2.069E9,
                  "common_stock_dividend_paid": -1.3516E10,
                  "common_stock_issuance": 1.089E9,
                  "common_stock_payments": -1.7272E10,
                  "deferred_income_tax": -3.105E9,
                  "deferred_tax": -3.105E9,
                  "depreciation_amortization_depletion": 1.1274E10,
                  "depreciation_and_amortization": 1.1274E10,
                  "effect_of_exchange_rate_changes": -7.8E7,
                  "end_cash_position": 1.129E10,
                  "file_date": "1970-01-01",
                  "financing_cash_flow": -3.424E10,
                  "fiscal_year_end_change": false,
                  "free_cash_flow": 3.3641E10,
                  "gain_loss_on_investment_securities": -1.037E9,
                  "investing_cash_flow": -1.1186E10,
                  "issuance_of_capital_stock": 1.089E9,
                  "issuance_of_debt": 0.0,
                  "long_term_debt_issuance": 0.0,
                  "long_term_debt_payments": -3.681E9,
                  "net_business_purchase_and_sale": -2.541E9,
                  "net_common_stock_issuance": -1.6183E10,
                  "net_income_from_continuing_operations": 3.4926E10,
                  "net_investment_purchase_and_sale": 5.217E9,
                  "net_issuance_payments_of_debt": -3.681E9,
                  "net_long_term_debt_issuance": -3.681E9,
                  "net_other_financing_charges": -8.6E8,
                  "net_p_p_e_purchase_and_sale": -1.3854E10,
                  "net_short_term_debt_issuance": 0.0,
                  "number_of_share_holders": 0,
                  "operating_cash_flow": 4.7495E10,
                  "operating_gains_losses": 3.122E9,
                  "period_ending_date": "2019-03-31",
                  "purchase_of_business": -2.541E9,
                  "purchase_of_investment": -7.4635E10,
                  "purchase_of_p_p_e": -1.3854E10,
                  "repayment_of_debt": -3.681E9,
                  "repurchase_of_capital_stock": -1.7272E10,
                  "sale_of_investment": 7.9852E10,
                  "stock_based_compensation": 4.474E9
                }
              }
            ],
            "income_statement": [
              {
                "period_12m": {
                  "currency_id": "USD",
                  "fiscal_year_end": "6",
                  "period": "12M",
                  "report_type": "TTM",
                  "cost_of_revenue": 4.224E10,
                  "diluted_n_i_availto_com_stockholders": 3.4926E10,
                  "e_b_i_t": 4.4461E10,
                  "e_b_i_t_d_a": 5.5735E10,
                  "file_date": "1970-01-01",
                  "fiscal_year_end_change": false,
                  "gain_on_sale_of_security": 3.525E9,
                  "general_and_administrative_expense": 4.731E9,
                  "gross_profit": 7.9971E10,
                  "interest_expense": 2.689E9,
                  "interest_expense_non_operating": 2.689E9,
                  "i_s_file_date": "1970-01-01",
                  "net_income": 3.4926E10,
                  "net_income_common_stockholders": 3.4926E10,
                  "net_income_continuous_operations": 3.4926E10,
                  "net_income_from_continuing_and_discontinued_operation": 3.4926E10,
                  "net_income_from_continuing_operation_net_minority_interest": 3.4926E10,
                  "net_income_including_noncontrolling_interests": 3.4926E10,
                  "net_interest_income": -2.689E9,
                  "net_non_operating_interest_income_expense": -2.689E9,
                  "normalized_e_b_i_t_d_a": 5.221E10,
                  "normalized_income": 3.197871114622235E10,
                  "normalized_pre_tax_income": 3.8247E10,
                  "number_of_share_holders": 0,
                  "operating_expense": 3.9038E10,
                  "operating_income": 4.0933E10,
                  "operating_revenue": 1.22211E11,
                  "other_gn_a": 4.731E9,
                  "other_income_expense": 3.528E9,
                  "other_non_operating_income_expenses": 3000000.0,
                  "period_ending_date": "2019-03-31",
                  "pretax_income": 4.1772E10,
                  "reconciled_cost_of_revenue": 4.224E10,
                  "reconciled_depreciation": 1.1274E10,
                  "research_and_development": 1.6296E10,
                  "selling_and_marketing_expense": 1.8011E10,
                  "selling_general_and_administration": 2.2742E10,
                  "tax_effect_of_unusual_items": 5.7771114622235E8,
                  "tax_provision": 6.846E9,
                  "tax_rate_for_calcs": 0.16389,
                  "total_expenses": 8.1278E10,
                  "total_operating_income_as_reported": 4.0933E10,
                  "total_revenue": 1.22211E11,
                  "total_unusual_items": 3.525E9,
                  "total_unusual_items_excluding_goodwill": 3.525E9
                }
              }
            ]
          }
        }
      },
      {
        "type": "Stock",
        "id": "0P000003MH",
        "tables": {
          "historical_returns": {
            "period_1m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-04-30",
              "period": "1M",
              "total_return": 10.734272
            },
            "period_1y": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-04-30",
              "period": "1Y",
              "total_return": 41.531223
            }
          },
          "earning_reports_restate": [
            {
              "period_12m": {
                "share_class_id": "0P000003MH",
                "as_of_date": "2019-03-31",
                "currency_id": "USD",
                "fiscal_year_end": "6",
                "period": "12M",
                "report_type": "TTM",
                "basic_average_shares": 7.67975E9,
                "basic_continuous_operations": 4.54,
                "basic_e_p_s": 4.54,
                "continuing_and_discontinued_basic_e_p_s": 4.54,
                "continuing_and_discontinued_diluted_e_p_s": 4.5,
                "diluted_average_shares": 7.76475E9,
                "diluted_continuous_operations": 4.5,
                "diluted_e_p_s": 4.5,
                "dividend_coverage_ratio": 2.556818,
                "dividend_per_share": 1.76,
                "file_date": "1970-01-01",
                "fiscal_year_end_change": false,
                "normalized_basic_e_p_s": 4.156226,
                "normalized_diluted_e_p_s": 4.120427,
                "period_ending_date": "2019-03-31",
                "reported_normalized_diluted_e_p_s": 4.5,
                "total_dividend_per_share": 1.76
              }
            },
            {
              "period_3m": {
                "share_class_id": "0P000003MH",
                "as_of_date": "2019-03-31",
                "currency_id": "USD",
                "fiscal_year_end": "6",
                "period": "3M",
                "report_type": "R",
                "accession_number": "0001564590-19-012709",
                "basic_average_shares": 7.672E9,
                "basic_continuous_operations": 1.15,
                "basic_e_p_s": 1.15,
                "continuing_and_discontinued_basic_e_p_s": 1.15,
                "continuing_and_discontinued_diluted_e_p_s": 1.14,
                "diluted_average_shares": 7.744E9,
                "diluted_continuous_operations": 1.14,
                "diluted_e_p_s": 1.14,
                "dividend_coverage_ratio": 2.478261,
                "dividend_per_share": 0.46,
                "file_date": "2019-04-24",
                "fiscal_year_end_change": false,
                "form_type": "10-Q",
                "normalized_basic_e_p_s": 1.062409,
                "normalized_diluted_e_p_s": 1.053223,
                "period_ending_date": "2019-03-31",
                "reported_normalized_diluted_e_p_s": 1.14,
                "total_dividend_per_share": 0.46
              },
              "period_9m": {
                "share_class_id": "0P000003MH",
                "as_of_date": "2019-03-31",
                "currency_id": "USD",
                "fiscal_year_end": "6",
                "period": "9M",
                "report_type": "R",
                "accession_number": "0001564590-19-012709",
                "basic_average_shares": 7.679E9,
                "basic_continuous_operations": 3.39,
                "basic_e_p_s": 3.39,
                "continuing_and_discontinued_basic_e_p_s": 3.39,
                "continuing_and_discontinued_diluted_e_p_s": 3.36,
                "diluted_average_shares": 7.759E9,
                "diluted_continuous_operations": 3.36,
                "diluted_e_p_s": 3.36,
                "dividend_coverage_ratio": 2.507463,
                "dividend_per_share": 1.34,
                "file_date": "2019-04-24",
                "fiscal_year_end_change": false,
                "form_type": "10-Q",
                "normalized_basic_e_p_s": 3.117511,
                "normalized_diluted_e_p_s": 3.090321,
                "period_ending_date": "2019-03-31",
                "reported_normalized_diluted_e_p_s": 3.38,
                "total_dividend_per_share": 1.34
              },
              "period_12m": {
                "share_class_id": "0P000003MH",
                "as_of_date": "2019-03-31",
                "currency_id": "USD",
                "fiscal_year_end": "6",
                "period": "12M",
                "report_type": "R",
                "basic_average_shares": 7.67975E9,
                "basic_continuous_operations": 4.54,
                "basic_e_p_s": 4.54,
                "continuing_and_discontinued_basic_e_p_s": 4.54,
                "continuing_and_discontinued_diluted_e_p_s": 4.5,
                "diluted_average_shares": 7.76475E9,
                "diluted_continuous_operations": 4.5,
                "diluted_e_p_s": 4.5,
                "dividend_coverage_ratio": 2.556818,
                "dividend_per_share": 1.76,
                "file_date": "1970-01-01",
                "fiscal_year_end_change": false,
                "normalized_basic_e_p_s": 4.156226,
                "normalized_diluted_e_p_s": 4.120427,
                "period_ending_date": "2019-03-31",
                "reported_normalized_diluted_e_p_s": 4.5,
                "total_dividend_per_share": 1.76
              }
            },
            {
              "period_3m": {
                "share_class_id": "0P000003MH",
                "as_of_date": "2019-03-31",
                "currency_id": "USD",
                "fiscal_year_end": "6",
                "period": "3M",
                "report_type": "P",
                "accession_number": "0001193125-19-117108",
                "basic_average_shares": 7.672E9,
                "basic_continuous_operations": 1.15,
                "basic_e_p_s": 1.15,
                "continuing_and_discontinued_basic_e_p_s": 1.15,
                "continuing_and_discontinued_diluted_e_p_s": 1.14,
                "diluted_average_shares": 7.744E9,
                "diluted_continuous_operations": 1.14,
                "diluted_e_p_s": 1.14,
                "dividend_coverage_ratio": 2.478261,
                "dividend_per_share": 0.46,
                "file_date": "2019-04-24",
                "fiscal_year_end_change": false,
                "form_type": "8-K",
                "normalized_basic_e_p_s": 1.15,
                "normalized_diluted_e_p_s": 1.14,
                "period_ending_date": "2019-03-31",
                "total_dividend_per_share": 0.46
              },
              "period_9m": {
                "share_class_id": "0P000003MH",
                "as_of_date": "2019-03-31",
                "currency_id": "USD",
                "fiscal_year_end": "6",
                "period": "9M",
                "report_type": "P",
                "accession_number": "0001193125-19-117108",
                "basic_average_shares": 7.679E9,
                "basic_continuous_operations": 3.39,
                "basic_e_p_s": 3.39,
                "continuing_and_discontinued_basic_e_p_s": 3.39,
                "continuing_and_discontinued_diluted_e_p_s": 3.36,
                "diluted_average_shares": 7.759E9,
                "diluted_continuous_operations": 3.36,
                "diluted_e_p_s": 3.36,
                "dividend_coverage_ratio": 2.507463,
                "dividend_per_share": 1.34,
                "file_date": "2019-04-24",
                "fiscal_year_end_change": false,
                "form_type": "8-K",
                "normalized_basic_e_p_s": 3.39,
                "normalized_diluted_e_p_s": 3.36,
                "period_ending_date": "2019-03-31",
                "total_dividend_per_share": 1.34
              }
            }
          ],
          "earning_reports_a_o_r": [
            {
              "period_12m": {
                "share_class_id": "0P000003MH",
                "as_of_date": "2019-03-31",
                "currency_id": "USD",
                "fiscal_year_end": "6",
                "period": "12M",
                "report_type": "TTM",
                "basic_average_shares": 7.67975E9,
                "basic_continuous_operations": 4.54,
                "basic_e_p_s": 4.54,
                "continuing_and_discontinued_basic_e_p_s": 4.54,
                "continuing_and_discontinued_diluted_e_p_s": 4.5,
                "diluted_average_shares": 7.76475E9,
                "diluted_continuous_operations": 4.5,
                "diluted_e_p_s": 4.5,
                "dividend_coverage_ratio": 2.556818,
                "dividend_per_share": 1.76,
                "file_date": "1970-01-01",
                "fiscal_year_end_change": false,
                "normalized_basic_e_p_s": 4.156226,
                "normalized_diluted_e_p_s": 4.120427,
                "period_ending_date": "2019-03-31",
                "reported_normalized_diluted_e_p_s": 4.5,
                "total_dividend_per_share": 1.76
              }
            },
            {
              "period_3m": {
                "share_class_id": "0P000003MH",
                "as_of_date": "2019-03-31",
                "currency_id": "USD",
                "fiscal_year_end": "6",
                "period": "3M",
                "report_type": "A",
                "accession_number": "0001564590-19-012709",
                "basic_average_shares": 7.672E9,
                "basic_continuous_operations": 1.15,
                "basic_e_p_s": 1.15,
                "continuing_and_discontinued_basic_e_p_s": 1.15,
                "continuing_and_discontinued_diluted_e_p_s": 1.14,
                "diluted_average_shares": 7.744E9,
                "diluted_continuous_operations": 1.14,
                "diluted_e_p_s": 1.14,
                "dividend_coverage_ratio": 2.478261,
                "dividend_per_share": 0.46,
                "file_date": "2019-04-24",
                "fiscal_year_end_change": false,
                "form_type": "10-Q",
                "normalized_basic_e_p_s": 1.062409,
                "normalized_diluted_e_p_s": 1.053223,
                "period_ending_date": "2019-03-31",
                "reported_normalized_diluted_e_p_s": 1.14,
                "total_dividend_per_share": 0.46
              },
              "period_9m": {
                "share_class_id": "0P000003MH",
                "as_of_date": "2019-03-31",
                "currency_id": "USD",
                "fiscal_year_end": "6",
                "period": "9M",
                "report_type": "A",
                "accession_number": "0001564590-19-012709",
                "basic_average_shares": 7.679E9,
                "basic_continuous_operations": 3.39,
                "basic_e_p_s": 3.39,
                "continuing_and_discontinued_basic_e_p_s": 3.39,
                "continuing_and_discontinued_diluted_e_p_s": 3.36,
                "diluted_average_shares": 7.759E9,
                "diluted_continuous_operations": 3.36,
                "diluted_e_p_s": 3.36,
                "dividend_coverage_ratio": 2.507463,
                "dividend_per_share": 1.34,
                "file_date": "2019-04-24",
                "fiscal_year_end_change": false,
                "form_type": "10-Q",
                "normalized_basic_e_p_s": 3.117511,
                "normalized_diluted_e_p_s": 3.090321,
                "period_ending_date": "2019-03-31",
                "reported_normalized_diluted_e_p_s": 3.38,
                "total_dividend_per_share": 1.34
              }
            },
            {
              "period_3m": {
                "share_class_id": "0P000003MH",
                "as_of_date": "2019-03-31",
                "currency_id": "USD",
                "fiscal_year_end": "6",
                "period": "3M",
                "report_type": "P",
                "accession_number": "0001193125-19-117108",
                "basic_average_shares": 7.672E9,
                "basic_continuous_operations": 1.15,
                "basic_e_p_s": 1.15,
                "continuing_and_discontinued_basic_e_p_s": 1.15,
                "continuing_and_discontinued_diluted_e_p_s": 1.14,
                "diluted_average_shares": 7.744E9,
                "diluted_continuous_operations": 1.14,
                "diluted_e_p_s": 1.14,
                "dividend_coverage_ratio": 2.478261,
                "dividend_per_share": 0.46,
                "file_date": "2019-04-24",
                "fiscal_year_end_change": false,
                "form_type": "8-K",
                "normalized_basic_e_p_s": 1.15,
                "normalized_diluted_e_p_s": 1.14,
                "period_ending_date": "2019-03-31",
                "total_dividend_per_share": 0.46
              },
              "period_9m": {
                "share_class_id": "0P000003MH",
                "as_of_date": "2019-03-31",
                "currency_id": "USD",
                "fiscal_year_end": "6",
                "period": "9M",
                "report_type": "P",
                "accession_number": "0001193125-19-117108",
                "basic_average_shares": 7.679E9,
                "basic_continuous_operations": 3.39,
                "basic_e_p_s": 3.39,
                "continuing_and_discontinued_basic_e_p_s": 3.39,
                "continuing_and_discontinued_diluted_e_p_s": 3.36,
                "diluted_average_shares": 7.759E9,
                "diluted_continuous_operations": 3.36,
                "diluted_e_p_s": 3.36,
                "dividend_coverage_ratio": 2.507463,
                "dividend_per_share": 1.34,
                "file_date": "2019-04-24",
                "fiscal_year_end_change": false,
                "form_type": "8-K",
                "normalized_basic_e_p_s": 3.39,
                "normalized_diluted_e_p_s": 3.36,
                "period_ending_date": "2019-03-31",
                "total_dividend_per_share": 1.34
              }
            }
          ]
        }
      }
    ]
  }
]
```

## Get Price Statistics
Retrieve price statistic Information.

### Code Example
```python
# Version 3.6.1
import requests

response = requests.get('https://api.tradier.com/beta/markets/fundamentals/statistics',
    params={'symbols': 'MSFT'},
    headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'}
)
json_response = response.json()
print(response.status_code)
print(json_response)
```

### JSON Response
```json
[
  {
    "request": "MSFT",
    "type": "Symbol",
    "results": [
      {
        "type": "Stock",
        "id": "0P000003MH",
        "tables": {
          "price_statistics": {
            "period_5d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "5D",
              "close_price_to_moving_average": 0.990404,
              "moving_average_price": 126.716
            },
            "period_1w": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "1W",
              "average_volume": 2.7955174E7,
              "high_price": 129.43,
              "low_price": 123.57,
              "percentage_below_high_price": 3.04,
              "total_volume": 1.67731047E8
            },
            "period_10d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "10D",
              "close_price_to_moving_average": 0.982057,
              "moving_average_price": 127.793
            },
            "period_13d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "13D",
              "close_price_to_moving_average": 0.984296,
              "moving_average_price": 127.502308
            },
            "period_2w": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "2W",
              "average_volume": 2.6975659E7,
              "high_price": 131.37,
              "low_price": 123.57,
              "percentage_below_high_price": 4.47,
              "total_volume": 2.9673225E8
            },
            "period_20d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "20D",
              "close_price_to_moving_average": 0.998977,
              "moving_average_price": 125.6285
            },
            "period_30d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "30D",
              "close_price_to_moving_average": 1.015463,
              "moving_average_price": 123.589
            },
            "period_1m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "1M",
              "average_volume": 2.3311962E7,
              "high_price": 131.37,
              "low_price": 118.58,
              "percentage_below_high_price": 4.47,
              "total_volume": 5.12863184E8
            },
            "period_50d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "50D",
              "close_price_to_moving_average": 1.044521,
              "moving_average_price": 120.1508
            },
            "period_60d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "60D",
              "close_price_to_moving_average": 1.059395,
              "moving_average_price": 118.463833
            },
            "period_90d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "90D",
              "close_price_to_moving_average": 1.100618,
              "moving_average_price": 114.026889
            },
            "period_3m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "3M",
              "average_volume": 2.4513613E7,
              "high_price": 131.37,
              "low_price": 104.965,
              "percentage_below_high_price": 4.47,
              "total_volume": 1.519844032E9
            },
            "period_6m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "6M",
              "average_volume": 3.1526019E7,
              "high_price": 131.37,
              "low_price": 93.96,
              "percentage_below_high_price": 4.47,
              "total_volume": 3.877700387E9
            },
            "period_200d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "200D",
              "close_price_to_moving_average": 1.13331,
              "moving_average_price": 110.7376
            },
            "period_30w": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "30W",
              "close_price_to_moving_average": 1.13363,
              "moving_average_price": 110.706358
            },
            "period_9m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "9M",
              "average_volume": 3.0897771E7,
              "high_price": 131.37,
              "low_price": 93.96,
              "percentage_below_high_price": 4.47,
              "total_volume": 5.808781116E9
            },
            "period_1y": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "1Y",
              "arithmetic_mean": 3.1136,
              "average_volume": 2.9537553E7,
              "best3_month_total_return": 25.5734,
              "close_price_to_moving_average": 1.156486,
              "high_price": 131.37,
              "low_price": 93.96,
              "moving_average_price": 108.518359,
              "percentage_below_high_price": 4.47,
              "standard_deviation": 19.9425,
              "total_volume": 7.443463541E9,
              "worst3_month_total_return": -10.8233
            },
            "period_3y": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "3Y",
              "arithmetic_mean": 2.9874,
              "average_volume": 2.6803689E7,
              "best3_month_total_return": 25.5734,
              "high_price": 131.37,
              "low_price": 48.035,
              "percentage_below_high_price": 4.47,
              "standard_deviation": 15.8931,
              "total_volume": 2.0558429757E10,
              "worst3_month_total_return": -10.8233
            },
            "period_5y": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "5Y",
              "arithmetic_mean": 2.3512,
              "average_volume": 2.940971E7,
              "best3_month_total_return": 26.1805,
              "close_price_to_moving_average": 1.824532,
              "high_price": 131.37,
              "low_price": 39.27,
              "moving_average_price": 68.78478,
              "percentage_below_high_price": 4.47,
              "standard_deviation": 21.1905,
              "total_volume": 3.7879707447E10,
              "worst3_month_total_return": -13.3931
            },
            "period_10y": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "10Y",
              "arithmetic_mean": 1.9584,
              "average_volume": 4.0787319E7,
              "best3_month_total_return": 26.3669,
              "high_price": 131.37,
              "low_price": 19.01,
              "percentage_below_high_price": 4.47,
              "standard_deviation": 21.4302,
              "total_volume": 1.05720731581E11,
              "worst3_month_total_return": -21.0382
            }
          },
          "trailing_returns": {
            "period_1d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "1D",
              "total_return": -0.007967
            },
            "period_5d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "5D",
              "total_return": -0.562554
            },
            "period_1m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "1M",
              "total_return": 5.214621
            },
            "period_3m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "3M",
              "total_return": 19.201287
            },
            "period_6m": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "6M",
              "total_return": 15.378297
            },
            "period_1y": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "1Y",
              "total_return": 31.277079
            },
            "period_3y": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "3Y",
              "total_return": 37.576565
            },
            "period_5y": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "5Y",
              "total_return": 27.437623
            },
            "period_10y": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "10Y",
              "total_return": 21.540256
            },
            "period_15y": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "15Y",
              "total_return": 11.99373
            },
            "m_t_d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "MTD",
              "total_return": -3.905054
            },
            "q_t_d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "QTD",
              "total_return": 6.410039
            },
            "y_t_d": {
              "share_class_id": "0P000003MH",
              "as_of_date": "2019-05-09",
              "period": "YTD",
              "total_return": 24.012996
            }
          }
        }
      }
    ]
  }
]
```
