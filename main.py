import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

# Initialize the FastAPI app
app = FastAPI()

# Configure CORS to allow communication from your frontend
origins = [
    "http://localhost:5173",  # Your React app's URL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the mock stock data
try:
    mock_data = pd.read_csv('mock_stock_data.csv')
    mock_data.set_index('symbol', inplace=True)
except FileNotFoundError:
    print("Error: mock_stock_data.csv not found. Please create it.")
    exit()

# Pydantic model for request body
class Portfolio(BaseModel):
    portfolio_str: str

# Helper function to parse the portfolio string
def parse_portfolio(portfolio_str):
    parsed_portfolio = {}
    items = [item.strip() for item in portfolio_str.split(',')]
    for item in items:
        match = re.match(r'([a-zA-Z]+):\s*(\d+)', item)
        if match:
            stock, quantity = match.groups()
            parsed_portfolio[stock.upper()] = int(quantity)
    return parsed_portfolio

# Analysis logic
def analyze_portfolio(portfolio_data):
    advice = "Your portfolio is well-diversified. Keep holding your stocks."
    risk_level = "low"
    suggested_stocks = []
    
    # Check for over-concentration
    total_holdings = sum(portfolio_data.values())
    if total_holdings > 0:
        over_concentrated = False
        for stock, quantity in portfolio_data.items():
            if (quantity / total_holdings) > 0.5:
                over_concentrated = True
                break
        
        if over_concentrated:
            advice = "Your portfolio is highly concentrated in one stock. Consider reducing your position or diversifying."
            risk_level = "high"

    # Check for missing sectors (simple logic for now)
    if not any(stock in ['TCS', 'INFY'] for stock in portfolio_data.keys()):
        advice = "Your portfolio lacks representation in the IT sector. Consider adding INFOSYS."
        suggested_stocks.append('INFOSYS')
        risk_level = "medium"
    
    # Simple P/E ratio check
    high_pe_stocks = mock_data[mock_data['pe_ratio'] > 40].index.tolist()
    for stock in portfolio_data.keys():
        if stock in high_pe_stocks:
            advice += f" The P/E ratio for {stock} is high. Consider reducing your position."
            risk_level = "high"

    return {
        "message": advice,
        "riskLevel": risk_level,
        "suggestedStocks": suggested_stocks
    }

# API endpoint
@app.post("/api/analyze_portfolio")
async def analyze_portfolio_endpoint(portfolio: Portfolio):
    parsed_data = parse_portfolio(portfolio.portfolio_str)
    analysis_result = analyze_portfolio(parsed_data)
    return analysis_result