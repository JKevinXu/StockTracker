# Amazon RSU Stock Tracker

A web-based dashboard tool to track Amazon stock prices and plan the selling of RSUs worth 2 million RMB over a 2-year period.

## Features

- **Real-time Stock Data**: Track Amazon stock price in real-time using Yahoo Finance data
- **RSU Vesting Schedule**: Visualize your RSU vesting schedule
- **Selling Strategy Analysis**: Compare different strategies for selling your RSUs
- **Price Alerts**: Get notified of significant price movements
- **Accessible Interface**: Responsive design works on desktop and mobile
- **Network Sharing**: Access the dashboard from any device on your local network

## Prerequisites

- Python 3.7 or higher
- Internet connection for stock data retrieval

## Installation

1. Clone this repository or download the files to your computer.

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Configure your RSU details in `config.py`:
   - Set your total RSU value (already set to 2 million RMB)
   - Update the current exchange rate if needed
   - Adjust the vesting schedule to match your actual RSU vesting dates
   - Choose your preferred selling strategy

## Usage

1. Run the application:

```bash
python run.py
```

or

```bash
python app.py
```

2. Your default web browser will open automatically with the dashboard.

3. The dashboard will also be accessible from other devices on your network at the URL shown in the terminal and in the dashboard footer.

## Customizing the Dashboard

You can customize various aspects of the stock tracker:

- **config.py**: Adjust RSU details, vesting schedule, selling strategies, and alert thresholds
- **assets/style.css**: Customize the visual appearance of the dashboard

## Selling Strategies

The application provides several selling strategies:

1. **Equal Distribution**: Sell an equal number of shares each month
2. **Equal Value**: Aim to sell an equal dollar value each month
3. **Dollar Cost Averaging**: Sell more when price is higher, less when lower
4. **Reserve Strategy**: Hold a percentage as reserve for the final months

## Network Sharing

The dashboard can be accessed from:
- Your computer: http://localhost:8050
- Other devices on your network: http://[Your IP Address]:8050

The exact URLs will be displayed when you start the application.

## Security Note

This application is designed for personal use on your local network. No RSU or financial data is sent to external servers - all processing happens locally on your computer.

## License

This project is for personal use only. 