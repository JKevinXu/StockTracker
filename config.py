# Amazon Stock Tracker Configuration

# RSU Details
TOTAL_RSU_VALUE_RMB = 2000000  # Total value in RMB
CURRENCY_EXCHANGE_RATE = 7.1  # RMB to USD exchange rate
TOTAL_RSU_VALUE_USD = TOTAL_RSU_VALUE_RMB / CURRENCY_EXCHANGE_RATE  # Calculated USD value

# Stock Details
STOCK_SYMBOL = "AMZN"
STOCK_NAME = "Amazon"

# Selling Timeline
SELLING_TIMEFRAME_MONTHS = 24  # 2 years in months
START_DATE = "2023-07-01"  # Change to your actual start date
END_DATE = "2025-07-01"    # Change to your actual end date

# Vesting Schedule - adjust as per your actual vesting schedule
# Format: List of (percentage, date) tuples
VESTING_SCHEDULE = [
    (25, "2023-07-01"),  # 25% vested initially
    (25, "2023-10-01"),  # 25% vested in 3 months
    (25, "2024-01-01"),  # 25% vested in 6 months
    (25, "2024-04-01"),  # Final 25% vested in 9 months
]

# Selling Strategy Parameters
SELLING_STRATEGIES = {
    "equal_distribution": "Sell equal amounts each month",
    "equal_value": "Sell for equal dollar value each month", 
    "dollar_cost_averaging": "Sell more when price is higher",
    "reserve_strategy": "Hold some percentage as reserve for last months",
}
DEFAULT_STRATEGY = "equal_distribution"
RESERVE_PERCENTAGE = 20  # For reserve strategy

# Price Alert Thresholds
PRICE_INCREASE_ALERT = 5  # Alert when price increases by 5%
PRICE_DECREASE_ALERT = 5  # Alert when price decreases by 5%

# Application Settings
DEBUG_MODE = True
DEFAULT_PORT = 8050
HOST = '0.0.0.0'  # Allow access from local network
REFRESH_INTERVAL = 60  # Refresh data every 60 seconds 