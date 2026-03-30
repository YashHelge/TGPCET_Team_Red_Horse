"""
TradeOS V2 — Stock Universe
50 Indian stocks (NIFTY 50) + 150 global stocks across NYSE, NASDAQ, LSE, XETRA, TSE, HKEX.
"""

INDIAN_STOCKS = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy", "exchange": "NSE"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "IT", "exchange": "NSE"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Banking", "exchange": "NSE"},
    {"symbol": "INFY.NS", "name": "Infosys", "sector": "IT", "exchange": "NSE"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Banking", "exchange": "NSE"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "sector": "FMCG", "exchange": "NSE"},
    {"symbol": "ITC.NS", "name": "ITC Limited", "sector": "FMCG", "exchange": "NSE"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Banking", "exchange": "NSE"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel", "sector": "Telecom", "exchange": "NSE"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "sector": "Banking", "exchange": "NSE"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro", "sector": "Capital Goods", "exchange": "NSE"},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank", "sector": "Banking", "exchange": "NSE"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints", "sector": "Consumer Durables", "exchange": "NSE"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "TITAN.NS", "name": "Titan Company", "sector": "Consumer Durables", "exchange": "NSE"},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharma", "sector": "Pharma", "exchange": "NSE"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance", "sector": "Financial Services", "exchange": "NSE"},
    {"symbol": "WIPRO.NS", "name": "Wipro", "sector": "IT", "exchange": "NSE"},
    {"symbol": "HCLTECH.NS", "name": "HCL Technologies", "sector": "IT", "exchange": "NSE"},
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement", "sector": "Cement", "exchange": "NSE"},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "NTPC.NS", "name": "NTPC", "sector": "Power", "exchange": "NSE"},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corp", "sector": "Power", "exchange": "NSE"},
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel", "sector": "Metals", "exchange": "NSE"},
    {"symbol": "ONGC.NS", "name": "ONGC", "sector": "Energy", "exchange": "NSE"},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises", "sector": "Conglomerate", "exchange": "NSE"},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports", "sector": "Infrastructure", "exchange": "NSE"},
    {"symbol": "COALINDIA.NS", "name": "Coal India", "sector": "Mining", "exchange": "NSE"},
    {"symbol": "BAJAJFINSV.NS", "name": "Bajaj Finserv", "sector": "Financial Services", "exchange": "NSE"},
    {"symbol": "JSWSTEEL.NS", "name": "JSW Steel", "sector": "Metals", "exchange": "NSE"},
    {"symbol": "TECHM.NS", "name": "Tech Mahindra", "sector": "IT", "exchange": "NSE"},
    {"symbol": "LTIM.NS", "name": "LTIMindtree", "sector": "IT", "exchange": "NSE"},
    {"symbol": "NESTLEIND.NS", "name": "Nestle India", "sector": "FMCG", "exchange": "NSE"},
    {"symbol": "INDUSINDBK.NS", "name": "IndusInd Bank", "sector": "Banking", "exchange": "NSE"},
    {"symbol": "CIPLA.NS", "name": "Cipla", "sector": "Pharma", "exchange": "NSE"},
    {"symbol": "DRREDDY.NS", "name": "Dr Reddy's Labs", "sector": "Pharma", "exchange": "NSE"},
    {"symbol": "DIVISLAB.NS", "name": "Divi's Laboratories", "sector": "Pharma", "exchange": "NSE"},
    {"symbol": "EICHERMOT.NS", "name": "Eicher Motors", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals", "sector": "Healthcare", "exchange": "NSE"},
    {"symbol": "SBILIFE.NS", "name": "SBI Life Insurance", "sector": "Insurance", "exchange": "NSE"},
    {"symbol": "BRITANNIA.NS", "name": "Britannia Industries", "sector": "FMCG", "exchange": "NSE"},
    {"symbol": "GRASIM.NS", "name": "Grasim Industries", "sector": "Cement", "exchange": "NSE"},
    {"symbol": "BAJAJ-AUTO.NS", "name": "Bajaj Auto", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "HEROMOTOCO.NS", "name": "Hero MotoCorp", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "TATACONSUM.NS", "name": "Tata Consumer Products", "sector": "FMCG", "exchange": "NSE"},
    {"symbol": "HINDALCO.NS", "name": "Hindalco Industries", "sector": "Metals", "exchange": "NSE"},
    {"symbol": "BPCL.NS", "name": "BPCL", "sector": "Energy", "exchange": "NSE"},
    {"symbol": "HDFCLIFE.NS", "name": "HDFC Life Insurance", "sector": "Insurance", "exchange": "NSE"},
    {"symbol": "TRENT.NS", "name": "Trent Limited", "sector": "Retail", "exchange": "NSE"},
]

US_STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "MSFT", "name": "Microsoft", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "GOOGL", "name": "Alphabet Inc", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "AMZN", "name": "Amazon", "sector": "Consumer Cyclical", "exchange": "NASDAQ"},
    {"symbol": "NVDA", "name": "NVIDIA", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "META", "name": "Meta Platforms", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "TSLA", "name": "Tesla", "sector": "Automobile", "exchange": "NASDAQ"},
    {"symbol": "BRK-B", "name": "Berkshire Hathaway", "sector": "Financial Services", "exchange": "NYSE"},
    {"symbol": "JPM", "name": "JPMorgan Chase", "sector": "Banking", "exchange": "NYSE"},
    {"symbol": "V", "name": "Visa Inc", "sector": "Financial Services", "exchange": "NYSE"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "exchange": "NYSE"},
    {"symbol": "WMT", "name": "Walmart", "sector": "Retail", "exchange": "NYSE"},
    {"symbol": "PG", "name": "Procter & Gamble", "sector": "FMCG", "exchange": "NYSE"},
    {"symbol": "MA", "name": "Mastercard", "sector": "Financial Services", "exchange": "NYSE"},
    {"symbol": "UNH", "name": "UnitedHealth Group", "sector": "Healthcare", "exchange": "NYSE"},
    {"symbol": "HD", "name": "Home Depot", "sector": "Retail", "exchange": "NYSE"},
    {"symbol": "DIS", "name": "Walt Disney", "sector": "Entertainment", "exchange": "NYSE"},
    {"symbol": "BAC", "name": "Bank of America", "sector": "Banking", "exchange": "NYSE"},
    {"symbol": "XOM", "name": "Exxon Mobil", "sector": "Energy", "exchange": "NYSE"},
    {"symbol": "PFE", "name": "Pfizer", "sector": "Pharma", "exchange": "NYSE"},
    {"symbol": "NFLX", "name": "Netflix", "sector": "Entertainment", "exchange": "NASDAQ"},
    {"symbol": "ADBE", "name": "Adobe Inc", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "CRM", "name": "Salesforce", "sector": "Technology", "exchange": "NYSE"},
    {"symbol": "COST", "name": "Costco", "sector": "Retail", "exchange": "NASDAQ"},
    {"symbol": "AVGO", "name": "Broadcom", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "KO", "name": "Coca-Cola", "sector": "FMCG", "exchange": "NYSE"},
    {"symbol": "PEP", "name": "PepsiCo", "sector": "FMCG", "exchange": "NASDAQ"},
    {"symbol": "TMO", "name": "Thermo Fisher", "sector": "Healthcare", "exchange": "NYSE"},
    {"symbol": "ABT", "name": "Abbott Labs", "sector": "Healthcare", "exchange": "NYSE"},
    {"symbol": "CSCO", "name": "Cisco Systems", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "ACN", "name": "Accenture", "sector": "IT", "exchange": "NYSE"},
    {"symbol": "MRK", "name": "Merck & Co", "sector": "Pharma", "exchange": "NYSE"},
    {"symbol": "LLY", "name": "Eli Lilly", "sector": "Pharma", "exchange": "NYSE"},
    {"symbol": "AMD", "name": "AMD", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "INTC", "name": "Intel", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "ORCL", "name": "Oracle", "sector": "Technology", "exchange": "NYSE"},
    {"symbol": "NKE", "name": "Nike", "sector": "Consumer Cyclical", "exchange": "NYSE"},
    {"symbol": "T", "name": "AT&T", "sector": "Telecom", "exchange": "NYSE"},
    {"symbol": "VZ", "name": "Verizon", "sector": "Telecom", "exchange": "NYSE"},
    {"symbol": "GS", "name": "Goldman Sachs", "sector": "Banking", "exchange": "NYSE"},
    {"symbol": "MS", "name": "Morgan Stanley", "sector": "Banking", "exchange": "NYSE"},
    {"symbol": "CVX", "name": "Chevron", "sector": "Energy", "exchange": "NYSE"},
    {"symbol": "QCOM", "name": "Qualcomm", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "TXN", "name": "Texas Instruments", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "PM", "name": "Philip Morris", "sector": "FMCG", "exchange": "NYSE"},
    {"symbol": "UPS", "name": "UPS", "sector": "Logistics", "exchange": "NYSE"},
    {"symbol": "CAT", "name": "Caterpillar", "sector": "Capital Goods", "exchange": "NYSE"},
    {"symbol": "RTX", "name": "RTX Corp", "sector": "Defence", "exchange": "NYSE"},
    {"symbol": "GE", "name": "GE Aerospace", "sector": "Capital Goods", "exchange": "NYSE"},
    {"symbol": "IBM", "name": "IBM", "sector": "Technology", "exchange": "NYSE"},
    {"symbol": "AMAT", "name": "Applied Materials", "sector": "Technology", "exchange": "NASDAQ"},
    {"symbol": "NOW", "name": "ServiceNow", "sector": "Technology", "exchange": "NYSE"},
    {"symbol": "ISRG", "name": "Intuitive Surgical", "sector": "Healthcare", "exchange": "NASDAQ"},
    {"symbol": "SPGI", "name": "S&P Global", "sector": "Financial Services", "exchange": "NYSE"},
    {"symbol": "BLK", "name": "BlackRock", "sector": "Financial Services", "exchange": "NYSE"},
    {"symbol": "AXP", "name": "American Express", "sector": "Financial Services", "exchange": "NYSE"},
    {"symbol": "DE", "name": "Deere & Co", "sector": "Capital Goods", "exchange": "NYSE"},
    {"symbol": "BKNG", "name": "Booking Holdings", "sector": "Travel", "exchange": "NASDAQ"},
    {"symbol": "SYK", "name": "Stryker Corp", "sector": "Healthcare", "exchange": "NYSE"},
    {"symbol": "MDLZ", "name": "Mondelez", "sector": "FMCG", "exchange": "NASDAQ"},
]

UK_STOCKS = [
    {"symbol": "SHEL.L", "name": "Shell PLC", "sector": "Energy", "exchange": "LSE"},
    {"symbol": "AZN.L", "name": "AstraZeneca", "sector": "Pharma", "exchange": "LSE"},
    {"symbol": "HSBA.L", "name": "HSBC Holdings", "sector": "Banking", "exchange": "LSE"},
    {"symbol": "ULVR.L", "name": "Unilever PLC", "sector": "FMCG", "exchange": "LSE"},
    {"symbol": "BP.L", "name": "BP PLC", "sector": "Energy", "exchange": "LSE"},
    {"symbol": "GSK.L", "name": "GSK PLC", "sector": "Pharma", "exchange": "LSE"},
    {"symbol": "RIO.L", "name": "Rio Tinto", "sector": "Mining", "exchange": "LSE"},
    {"symbol": "BARC.L", "name": "Barclays", "sector": "Banking", "exchange": "LSE"},
    {"symbol": "LLOY.L", "name": "Lloyds Banking", "sector": "Banking", "exchange": "LSE"},
    {"symbol": "VOD.L", "name": "Vodafone", "sector": "Telecom", "exchange": "LSE"},
    {"symbol": "DGE.L", "name": "Diageo", "sector": "FMCG", "exchange": "LSE"},
    {"symbol": "BATS.L", "name": "British American Tobacco", "sector": "FMCG", "exchange": "LSE"},
    {"symbol": "REL.L", "name": "RELX PLC", "sector": "Media", "exchange": "LSE"},
    {"symbol": "NG.L", "name": "National Grid", "sector": "Utilities", "exchange": "LSE"},
    {"symbol": "RKT.L", "name": "Reckitt Benckiser", "sector": "FMCG", "exchange": "LSE"},
]

EU_STOCKS = [
    {"symbol": "SAP.DE", "name": "SAP SE", "sector": "Technology", "exchange": "XETRA"},
    {"symbol": "SIE.DE", "name": "Siemens AG", "sector": "Capital Goods", "exchange": "XETRA"},
    {"symbol": "ALV.DE", "name": "Allianz SE", "sector": "Insurance", "exchange": "XETRA"},
    {"symbol": "BAS.DE", "name": "BASF SE", "sector": "Chemicals", "exchange": "XETRA"},
    {"symbol": "BMW.DE", "name": "BMW AG", "sector": "Automobile", "exchange": "XETRA"},
    {"symbol": "MBG.DE", "name": "Mercedes-Benz", "sector": "Automobile", "exchange": "XETRA"},
    {"symbol": "DTE.DE", "name": "Deutsche Telekom", "sector": "Telecom", "exchange": "XETRA"},
    {"symbol": "VOW3.DE", "name": "Volkswagen", "sector": "Automobile", "exchange": "XETRA"},
    {"symbol": "ADS.DE", "name": "Adidas AG", "sector": "Consumer Cyclical", "exchange": "XETRA"},
    {"symbol": "MUV2.DE", "name": "Munich Re", "sector": "Insurance", "exchange": "XETRA"},
    {"symbol": "DBK.DE", "name": "Deutsche Bank", "sector": "Banking", "exchange": "XETRA"},
    {"symbol": "IFX.DE", "name": "Infineon", "sector": "Technology", "exchange": "XETRA"},
    {"symbol": "BEI.DE", "name": "Beiersdorf", "sector": "FMCG", "exchange": "XETRA"},
    {"symbol": "HEN3.DE", "name": "Henkel AG", "sector": "FMCG", "exchange": "XETRA"},
    {"symbol": "RWE.DE", "name": "RWE AG", "sector": "Utilities", "exchange": "XETRA"},
]

ASIA_STOCKS = [
    {"symbol": "7203.T", "name": "Toyota Motor", "sector": "Automobile", "exchange": "TSE"},
    {"symbol": "6758.T", "name": "Sony Group", "sector": "Technology", "exchange": "TSE"},
    {"symbol": "6861.T", "name": "Keyence", "sector": "Technology", "exchange": "TSE"},
    {"symbol": "8306.T", "name": "Mitsubishi UFJ", "sector": "Banking", "exchange": "TSE"},
    {"symbol": "9984.T", "name": "SoftBank Group", "sector": "Technology", "exchange": "TSE"},
    {"symbol": "6501.T", "name": "Hitachi", "sector": "Capital Goods", "exchange": "TSE"},
    {"symbol": "6902.T", "name": "Denso Corp", "sector": "Automobile", "exchange": "TSE"},
    {"symbol": "7741.T", "name": "HOYA Corp", "sector": "Healthcare", "exchange": "TSE"},
    {"symbol": "4063.T", "name": "Shin-Etsu Chemical", "sector": "Chemicals", "exchange": "TSE"},
    {"symbol": "8035.T", "name": "Tokyo Electron", "sector": "Technology", "exchange": "TSE"},
    {"symbol": "0700.HK", "name": "Tencent Holdings", "sector": "Technology", "exchange": "HKEX"},
    {"symbol": "9988.HK", "name": "Alibaba Group", "sector": "Technology", "exchange": "HKEX"},
    {"symbol": "1299.HK", "name": "AIA Group", "sector": "Insurance", "exchange": "HKEX"},
    {"symbol": "0005.HK", "name": "HSBC Holdings", "sector": "Banking", "exchange": "HKEX"},
    {"symbol": "3690.HK", "name": "Meituan", "sector": "Technology", "exchange": "HKEX"},
    {"symbol": "9618.HK", "name": "JD.com", "sector": "Technology", "exchange": "HKEX"},
    {"symbol": "2318.HK", "name": "Ping An Insurance", "sector": "Insurance", "exchange": "HKEX"},
    {"symbol": "0941.HK", "name": "China Mobile", "sector": "Telecom", "exchange": "HKEX"},
    {"symbol": "1398.HK", "name": "ICBC", "sector": "Banking", "exchange": "HKEX"},
    {"symbol": "2388.HK", "name": "BOC Hong Kong", "sector": "Banking", "exchange": "HKEX"},
]

ETF_INDICES = [
    {"symbol": "SPY", "name": "S&P 500 ETF", "sector": "Index", "exchange": "NYSE"},
    {"symbol": "QQQ", "name": "NASDAQ 100 ETF", "sector": "Index", "exchange": "NASDAQ"},
    {"symbol": "DIA", "name": "Dow Jones ETF", "sector": "Index", "exchange": "NYSE"},
    {"symbol": "IWM", "name": "Russell 2000 ETF", "sector": "Index", "exchange": "NYSE"},
    {"symbol": "EEM", "name": "Emerging Markets ETF", "sector": "Index", "exchange": "NYSE"},
    {"symbol": "VTI", "name": "Total Stock Market ETF", "sector": "Index", "exchange": "NYSE"},
    {"symbol": "GLD", "name": "Gold ETF", "sector": "Commodity", "exchange": "NYSE"},
    {"symbol": "USO", "name": "Oil ETF", "sector": "Commodity", "exchange": "NYSE"},
    {"symbol": "TLT", "name": "20+ Year Treasury ETF", "sector": "Bonds", "exchange": "NASDAQ"},
    {"symbol": "VWO", "name": "Vanguard EM ETF", "sector": "Index", "exchange": "NYSE"},
]

# ── Combined Universe ────────────────────────────────────────
STOCK_UNIVERSE = INDIAN_STOCKS + US_STOCKS + UK_STOCKS + EU_STOCKS + ASIA_STOCKS + ETF_INDICES

# ── Helper Functions ─────────────────────────────────────────

def get_stock_info(symbol: str) -> dict | None:
    """Get stock info by symbol."""
    return next((s for s in STOCK_UNIVERSE if s["symbol"] == symbol), None)


def get_sector_stocks(sector: str) -> list[dict]:
    """Get all stocks in a given sector."""
    return [s for s in STOCK_UNIVERSE if s["sector"] == sector]


def get_exchange_stocks(exchange: str) -> list[dict]:
    """Get all stocks on a given exchange."""
    return [s for s in STOCK_UNIVERSE if s["exchange"] == exchange]


def get_indian_symbols() -> list[str]:
    return [s["symbol"] for s in INDIAN_STOCKS]


def get_us_symbols() -> list[str]:
    return [s["symbol"] for s in US_STOCKS]


def get_all_symbols() -> list[str]:
    return [s["symbol"] for s in STOCK_UNIVERSE]


def get_sectors() -> list[str]:
    return sorted(set(s["sector"] for s in STOCK_UNIVERSE))


def get_exchanges() -> list[str]:
    return sorted(set(s["exchange"] for s in STOCK_UNIVERSE))
