import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_current_price(symbol=config.STOCK_SYMBOL, max_retries=3, retry_delay=5):
    """Get the current stock price for the given symbol with retry logic."""
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            todays_data = ticker.history(period='1d')
            if not todays_data.empty:
                return todays_data['Close'].iloc[-1]
            raise ValueError("Empty data returned from Yahoo Finance")
        except Exception as e:
            logging.warning(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logging.error(f"Failed to retrieve current price after {max_retries} attempts")
                return None

def get_historical_data(symbol=config.STOCK_SYMBOL, period="2y", max_retries=3, retry_delay=5):
    """Get historical stock data with retry logic.
    
    Args:
        symbol: Stock symbol
        period: Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        Pandas DataFrame with historical data or empty DataFrame on failure
    """
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            hist_data = ticker.history(period=period)
            if not hist_data.empty:
                return hist_data
            raise ValueError("Empty data returned from Yahoo Finance")
        except Exception as e:
            logging.warning(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logging.error(f"Failed to retrieve historical data after {max_retries} attempts")
                return pd.DataFrame()  # Return empty DataFrame on failure

def get_vesting_dataframe():
    """Convert vesting schedule to DataFrame with dollar values."""
    vesting_data = []
    total_value_usd = config.TOTAL_RSU_VALUE_USD
    
    for percentage, date in config.VESTING_SCHEDULE:
        vesting_value = (percentage / 100) * total_value_usd
        vesting_data.append({
            'date': pd.to_datetime(date),
            'percentage': percentage,
            'value_usd': vesting_value,
            'shares': 0  # Will be calculated later based on stock price
        })
    
    df = pd.DataFrame(vesting_data)
    return df

def calculate_shares_from_vesting():
    """Calculate number of shares from vesting schedule based on stock prices."""
    vesting_df = get_vesting_dataframe()
    price_data = get_historical_data(period="5y")  # Get enough historical data
    
    for idx, row in vesting_df.iterrows():
        vesting_date = row['date']
        # Find closest date in price data
        if vesting_date in price_data.index:
            price = price_data.loc[vesting_date, 'Close']
        else:
            # Get the closest date before vesting date
            closest_date = price_data.index[price_data.index <= vesting_date][-1]
            price = price_data.loc[closest_date, 'Close']
        
        # Calculate shares based on price (assuming vesting date price)
        vesting_df.at[idx, 'shares'] = row['value_usd'] / price
        vesting_df.at[idx, 'price_at_vesting'] = price
    
    return vesting_df

def calculate_selling_strategy(strategy=config.DEFAULT_STRATEGY):
    """Calculate selling strategy based on selected approach."""
    vesting_df = calculate_shares_from_vesting()
    total_shares = vesting_df['shares'].sum()
    
    # Create date range for the selling period
    start_date = pd.to_datetime(config.START_DATE)
    end_date = pd.to_datetime(config.END_DATE)
    date_range = pd.date_range(start=start_date, end=end_date, freq='MS')  # Monthly start frequency
    
    selling_df = pd.DataFrame(index=date_range)
    selling_df.index.name = 'date'
    selling_df['month'] = selling_df.index.strftime('%Y-%m')
    
    if strategy == "equal_distribution":
        # Sell equal number of shares each month
        shares_per_month = total_shares / len(selling_df)
        selling_df['shares_to_sell'] = shares_per_month
        
    elif strategy == "equal_value":
        # Attempt to sell equal dollar value each month (estimate)
        current_price = get_current_price()
        value_per_month = (total_shares * current_price) / len(selling_df)
        
        # Initial estimate - will be updated with real prices as they come
        selling_df['target_value'] = value_per_month
        selling_df['estimated_shares'] = value_per_month / current_price
        selling_df['shares_to_sell'] = selling_df['estimated_shares']
        
    elif strategy == "dollar_cost_averaging":
        # Sell more when price is higher (varies with price)
        current_price = get_current_price()
        
        # Get historical price volatility to estimate price variations
        hist_data = get_historical_data(period="1y")
        price_std = hist_data['Close'].std()
        price_mean = hist_data['Close'].mean()
        
        # Create a model price curve (just for planning)
        # This will be replaced with actual prices when they become available
        x = np.linspace(0, len(selling_df)-1, len(selling_df))
        
        # Model price variations with a sine wave + trend
        trend = 0.05  # Assuming 5% annual trend
        amplitude = price_std / price_mean  # Normalized amplitude
        
        # Generate modeled prices with some randomness
        np.random.seed(42)  # For reproducibility
        noise = np.random.normal(0, amplitude/3, len(x))
        price_factors = 1 + amplitude * np.sin(x * np.pi / 6) + trend * x / len(x) + noise
        
        selling_df['price_factor'] = price_factors
        # Adjust shares based on price - sell more when price is higher
        selling_df['shares_to_sell'] = total_shares * (selling_df['price_factor'] / selling_df['price_factor'].sum())
        
    elif strategy == "reserve_strategy":
        # Hold some percentage as reserve for last months
        reserve_pct = config.RESERVE_PERCENTAGE
        regular_shares = total_shares * (100 - reserve_pct) / 100
        reserve_shares = total_shares * reserve_pct / 100
        
        # Regular period
        regular_months = int(len(selling_df) * 0.75)  # First 75% of months
        shares_per_regular_month = regular_shares / regular_months
        
        # Reserve period
        reserve_months = len(selling_df) - regular_months
        shares_per_reserve_month = reserve_shares / reserve_months
        
        selling_df['period'] = 'regular'
        selling_df.iloc[regular_months:, selling_df.columns.get_loc('period')] = 'reserve'
        
        selling_df['shares_to_sell'] = shares_per_regular_month
        selling_df.loc[selling_df['period'] == 'reserve', 'shares_to_sell'] = shares_per_reserve_month
    
    # Calculate cumulative shares sold
    selling_df['cumulative_shares'] = selling_df['shares_to_sell'].cumsum()
    selling_df['remaining_shares'] = total_shares - selling_df['cumulative_shares']
    
    # Calculate percentages
    selling_df['percent_sold_this_month'] = (selling_df['shares_to_sell'] / total_shares) * 100
    selling_df['percent_sold_cumulative'] = (selling_df['cumulative_shares'] / total_shares) * 100
    selling_df['percent_remaining'] = 100 - selling_df['percent_sold_cumulative']
    
    return selling_df

def get_stock_stats():
    """Get key statistics for the stock."""
    ticker = yf.Ticker(config.STOCK_SYMBOL)
    
    try:
        info = ticker.info
        stats = {
            'marketCap': info.get('marketCap', 'N/A'),
            'forwardPE': info.get('forwardPE', 'N/A'),
            'dividendYield': info.get('dividendYield', 'N/A'),
            'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', 'N/A'),
            'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', 'N/A'),
            'fiftyDayAverage': info.get('fiftyDayAverage', 'N/A'),
            'twoHundredDayAverage': info.get('twoHundredDayAverage', 'N/A'),
            'averageVolume': info.get('averageVolume', 'N/A'),
        }
        return stats
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return {}

def check_price_alerts(previous_price=None):
    """Check if current price triggers any alerts based on thresholds."""
    if previous_price is None:
        return None
    
    current_price = get_current_price()
    percent_change = ((current_price - previous_price) / previous_price) * 100
    
    alerts = []
    if percent_change >= config.PRICE_INCREASE_ALERT:
        alerts.append({
            'type': 'increase',
            'message': f'Price increased by {percent_change:.2f}% to ${current_price:.2f}',
            'change': percent_change
        })
    elif percent_change <= -config.PRICE_DECREASE_ALERT:
        alerts.append({
            'type': 'decrease',
            'message': f'Price decreased by {abs(percent_change):.2f}% to ${current_price:.2f}',
            'change': percent_change
        })
    
    return alerts if alerts else None 