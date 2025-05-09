import dash
from dash import dcc, html, dash_table, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import stock_data
import config
import socket
import os
import sys

# Initialize the Dash app
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

server = app.server
app.title = f"{config.STOCK_NAME} RSU Tracker"

# Cache for storing the last price to check alerts
last_price = None

# Get hostname and IP for sharing info
def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Could not determine IP"

hostname = socket.gethostname()
ip_address = get_ip_address()

# Layout components
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="https://d1.awsstatic.com/logos/aws-logo-lockups/powerredby/PB_AWS_logo_RGB_stacked_REV_SQ.91cd4af40773cbfbd15577a3c2b8a346fe3e8fa2.png", height="30px")),
                        dbc.Col(dbc.NavbarBrand(f"{config.STOCK_NAME} RSU Tracker", className="ms-2")),
                    ],
                    align="center",
                ),
                href="/",
                style={"textDecoration": "none"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(id="network-info", className="text-light", style={"fontSize": "0.8rem"}),
                            dbc.Button(
                                "Network Access", id="modal-button", size="sm", color="light", className="ml-2"
                            ),
                        ]
                    )
                ]
            )
        ],
    ),
    color="dark",
    dark=True,
)

network_modal = dbc.Modal(
    [
        dbc.ModalHeader("Network Access Information"),
        dbc.ModalBody([
            html.P("Access this dashboard from any device on your network using:"),
            html.Ul([
                html.Li([html.Strong("URL: "), html.A(f"http://{ip_address}:{config.DEFAULT_PORT}", 
                                                     href=f"http://{ip_address}:{config.DEFAULT_PORT}", 
                                                     target="_blank")]),
                html.Li([html.Strong("Hostname: "), f"{hostname}:{config.DEFAULT_PORT}"]),
            ]),
            html.P("Note: Devices must be on the same network to access this URL.")
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-modal", className="ml-auto")
        ),
    ],
    id="network-modal",
    size="lg",
)

# App Layout
app.layout = html.Div([
    navbar,
    network_modal,
    dbc.Container([
        html.Div(id="data-loading-status", className="alert alert-info mt-3", 
                 children="Loading stock data... Please wait.", style={"display": "block"}),
        html.Div(id="data-error-message", className="alert alert-danger mt-3", 
                 children="Failed to load stock data. Check your internet connection.", style={"display": "none"}),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Amazon Stock Overview"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H3(id="current-price", children="--"),
                                html.P("Current Price (USD)"),
                            ], width=4),
                            dbc.Col([
                                html.H3(id="price-change", children="--"),
                                html.P("Today's Change"),
                            ], width=4),
                            dbc.Col([
                                html.H3(id="total-rsu-value", children="--"),
                                html.P("RSU Value (USD)"),
                            ], width=4),
                        ]),
                    ]),
                ], className="mt-3"),
            ], width=12),
        ]),
        
        # Stock Price Information Section
        dbc.Row([
            dbc.Col([
                html.H4("Current Stock Information"),
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H2(id="current-price"),
                                html.P("Current Price ($)", className="text-muted"),
                            ], width=4),
                            dbc.Col([
                                html.H2(id="price-change"),
                                html.P("Change Today", className="text-muted"),
                            ], width=4),
                            dbc.Col([
                                html.H2(id="total-value"),
                                html.P("Total RSU Value ($)", className="text-muted"),
                            ], width=4),
                        ]),
                    ])
                ], className="mb-4"),
                
                # Alerts Section
                html.Div(id="alerts-section", className="mt-3"),
                
                # Price Chart
                dbc.Card([
                    dbc.CardHeader("Stock Price History"),
                    dbc.CardBody([
                        dcc.Graph(id="price-chart"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Time Period"),
                                dcc.Dropdown(
                                    id="time-period",
                                    options=[
                                        {"label": "1 Month", "value": "1mo"},
                                        {"label": "3 Months", "value": "3mo"},
                                        {"label": "6 Months", "value": "6mo"},
                                        {"label": "1 Year", "value": "1y"},
                                        {"label": "2 Years", "value": "2y"},
                                        {"label": "5 Years", "value": "5y"},
                                        {"label": "Max", "value": "max"},
                                    ],
                                    value="1y",
                                    className="mb-3",
                                )
                            ], width=6),
                        ]),
                    ]),
                ], className="mb-4"),
            ], width=12, lg=6),
            
            # RSU Information Section
            dbc.Col([
                html.H4("RSU Information"),
                dbc.Card([
                    dbc.CardHeader("Vesting Schedule"),
                    dbc.CardBody([
                        dcc.Graph(id="vesting-chart"),
                    ]),
                ], className="mb-4"),
                
                dbc.Card([
                    dbc.CardHeader("Selling Strategy"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Strategy"),
                                dcc.Dropdown(
                                    id="selling-strategy",
                                    options=[
                                        {"label": desc, "value": key} 
                                        for key, desc in config.SELLING_STRATEGIES.items()
                                    ],
                                    value=config.DEFAULT_STRATEGY,
                                    className="mb-3",
                                ),
                            ], width=12),
                        ]),
                        dcc.Graph(id="selling-chart"),
                    ]),
                ]),
            ], width=12, lg=6),
        ]),
        
        # Data Tables Section
        dbc.Row([
            dbc.Col([
                html.H4("Selling Plan Details"),
                dash_table.DataTable(
                    id="selling-table",
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "textAlign": "left",
                        "padding": "10px",
                        "minWidth": "80px",
                    },
                    style_header={
                        "backgroundColor": "rgb(230, 230, 230)",
                        "fontWeight": "bold",
                    },
                    style_data_conditional=[
                        {
                            "if": {"row_index": "odd"},
                            "backgroundColor": "rgb(248, 248, 248)",
                        }
                    ],
                    page_size=10,
                ),
            ], width=12),
        ], className="mt-4"),
    ]),
    
    # Network Information Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.Div([
                html.H5("Network Access Information:"),
                html.P([
                    "This dashboard is accessible on your local network at: ",
                    html.Br(),
                    html.Code(f"http://{ip_address}:{config.DEFAULT_PORT}"),
                    html.Br(),
                    "Hostname: ",
                    html.Code(hostname)
                ]),
                html.P([
                    "To access from other devices, make sure they are on the same network ",
                    "and enter the above URL in a web browser."
                ]),
            ], className="mt-3 mb-5 p-3 border rounded bg-light"),
        ], width=12),
    ]),
    
    # Store components for data
    dcc.Store(id="stock-data-store"),
    dcc.Store(id="vesting-data-store"),
    dcc.Store(id="selling-data-store"),
    dcc.Store(id="last-price-store"),
    
    # Interval for automatic updates
    dcc.Interval(
        id="interval-component",
        interval=config.REFRESH_INTERVAL * 1000,  # in milliseconds
        n_intervals=0
    ),
], className="dashboard-container")

# Callback to update the stock data store
@app.callback(
    Output("stock-data-store", "data"),
    Input("interval-component", "n_intervals"),
    Input("time-period", "value")
)
def update_stock_data(n_intervals, time_period):
    if time_period is None:
        time_period = "1y"
    
    hist_data = stock_data.get_historical_data(period=time_period)
    hist_data_dict = {
        'date': hist_data.index.strftime('%Y-%m-%d').tolist(),
        'open': hist_data['Open'].tolist(),
        'high': hist_data['High'].tolist(),
        'low': hist_data['Low'].tolist(),
        'close': hist_data['Close'].tolist(),
        'volume': hist_data['Volume'].tolist()
    }
    
    # Store current price for alerts
    global last_price
    if len(hist_data) > 0:
        last_price = hist_data['Close'].iloc[-2] if len(hist_data) > 1 else None
    
    return hist_data_dict

# Callback to update the vesting data store
@app.callback(
    Output("vesting-data-store", "data"),
    Input("interval-component", "n_intervals")
)
def update_vesting_data(n_intervals):
    vesting_df = stock_data.calculate_shares_from_vesting()
    
    vesting_data_dict = {
        'date': vesting_df['date'].dt.strftime('%Y-%m-%d').tolist(),
        'percentage': vesting_df['percentage'].tolist(),
        'value_usd': vesting_df['value_usd'].tolist(),
        'shares': vesting_df['shares'].tolist(),
        'price_at_vesting': vesting_df['price_at_vesting'].tolist() if 'price_at_vesting' in vesting_df.columns else []
    }
    
    return vesting_data_dict

# Callback to update the selling data store
@app.callback(
    Output("selling-data-store", "data"),
    Input("interval-component", "n_intervals"),
    Input("selling-strategy", "value")
)
def update_selling_data(n_intervals, strategy):
    if strategy is None:
        strategy = config.DEFAULT_STRATEGY
    
    selling_df = stock_data.calculate_selling_strategy(strategy)
    
    selling_data_dict = {
        'date': selling_df.index.strftime('%Y-%m-%d').tolist(),
        'month': selling_df['month'].tolist(),
        'shares_to_sell': selling_df['shares_to_sell'].tolist(),
        'cumulative_shares': selling_df['cumulative_shares'].tolist(),
        'remaining_shares': selling_df['remaining_shares'].tolist(),
        'percent_sold_this_month': selling_df['percent_sold_this_month'].tolist(),
        'percent_sold_cumulative': selling_df['percent_sold_cumulative'].tolist(),
        'percent_remaining': selling_df['percent_remaining'].tolist()
    }
    
    # Add strategy-specific columns
    if strategy == "equal_value" and 'target_value' in selling_df.columns:
        selling_data_dict['target_value'] = selling_df['target_value'].tolist()
        selling_data_dict['estimated_shares'] = selling_df['estimated_shares'].tolist()
    
    if strategy == "dollar_cost_averaging" and 'price_factor' in selling_df.columns:
        selling_data_dict['price_factor'] = selling_df['price_factor'].tolist()
    
    if strategy == "reserve_strategy" and 'period' in selling_df.columns:
        selling_data_dict['period'] = selling_df['period'].tolist()
    
    return selling_data_dict

# Callbacks to update UI elements
@app.callback(
    [
        Output("current-price", "children"),
        Output("price-change", "children"),
        Output("price-change", "className"),
        Output("total-value", "children"),
        Output("last-price-store", "data")
    ],
    Input("interval-component", "n_intervals"),
    State("vesting-data-store", "data")
)
def update_price_info(n_intervals, vesting_data):
    try:
        current_price = stock_data.get_current_price()
        
        # Calculate daily change
        ticker = stock_data.yf.Ticker(config.STOCK_SYMBOL)
        today_data = ticker.history(period='1d')
        
        if not today_data.empty:
            prev_close = today_data['Open'].iloc[0]
            change = current_price - prev_close
            pct_change = (change / prev_close) * 100
            change_text = f"${change:.2f} ({pct_change:.2f}%)"
            
            # Determine text color
            className = "text-success" if change >= 0 else "text-danger"
        else:
            change_text = "N/A"
            className = ""
        
        # Calculate total value
        total_value = "N/A"
        if vesting_data and 'shares' in vesting_data:
            total_shares = sum(vesting_data['shares'])
            total_value = f"${total_shares * current_price:,.2f}"
        
        return f"${current_price:.2f}", change_text, className, total_value, current_price
    
    except Exception as e:
        print(f"Error updating price info: {e}")
        return "N/A", "N/A", "", "N/A", None

@app.callback(
    Output("price-chart", "figure"),
    Input("stock-data-store", "data"),
    Input("vesting-data-store", "data")
)
def update_price_chart(stock_data_dict, vesting_data_dict):
    if stock_data_dict is None:
        return go.Figure()
    
    # Create DataFrame from stock data
    dates = pd.to_datetime(stock_data_dict['date'])
    df = pd.DataFrame({
        'Date': dates,
        'Open': stock_data_dict['open'],
        'High': stock_data_dict['high'],
        'Low': stock_data_dict['low'],
        'Close': stock_data_dict['close'],
        'Volume': stock_data_dict['volume']
    })
    
    # Create candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC'
    )])
    
    # Add volume bars
    fig.add_trace(go.Bar(
        x=df['Date'],
        y=df['Volume'],
        name='Volume',
        yaxis='y2',
        marker_color='rgba(200, 200, 200, 0.5)',
        opacity=0.5
    ))
    
    # Add vesting dates if available
    if vesting_data_dict and 'date' in vesting_data_dict:
        vesting_dates = pd.to_datetime(vesting_data_dict['date'])
        vesting_values = vesting_data_dict['value_usd']
        
        for i, date in enumerate(vesting_dates):
            if date in df['Date'].values or (date >= df['Date'].min() and date <= df['Date'].max()):
                fig.add_vline(
                    x=date, 
                    line_width=1, 
                    line_dash="dash", 
                    line_color="green",
                    annotation_text=f"Vest: ${vesting_values[i]:,.0f}",
                    annotation_position="top right"
                )
    
    # Update layout for dual axis
    fig.update_layout(
        title=f"{config.STOCK_NAME} Stock Price",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        yaxis2=dict(
            title="Volume",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        height=500,
        margin=dict(l=50, r=50, t=50, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

@app.callback(
    Output("vesting-chart", "figure"),
    Input("vesting-data-store", "data")
)
def update_vesting_chart(vesting_data_dict):
    if vesting_data_dict is None or 'date' not in vesting_data_dict:
        return go.Figure()
    
    # Create DataFrame from vesting data
    df = pd.DataFrame({
        'Date': pd.to_datetime(vesting_data_dict['date']),
        'Percentage': vesting_data_dict['percentage'],
        'Value_USD': vesting_data_dict['value_usd'],
        'Shares': vesting_data_dict['shares']
    })
    
    # Create figure with dual axis
    fig = go.Figure()
    
    # Bar chart for percentage
    fig.add_trace(go.Bar(
        x=df['Date'],
        y=df['Percentage'],
        name='Vesting %',
        marker_color='rgba(58, 71, 80, 0.6)',
        text=df['Percentage'].apply(lambda x: f"{x}%"),
        textposition='auto',
    ))
    
    # Line chart for cumulative percentage
    cumulative_pct = df['Percentage'].cumsum()
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=cumulative_pct,
        mode='lines+markers',
        name='Cumulative %',
        line=dict(color='rgba(0, 128, 0, 0.7)', width=3),
        yaxis='y'
    ))
    
    # Update layout
    fig.update_layout(
        title="RSU Vesting Schedule",
        xaxis_title="Vesting Date",
        yaxis_title="Percentage (%)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    # Add table below the chart with value information
    vesting_info = pd.DataFrame({
        'Date': df['Date'].dt.strftime('%Y-%m-%d'),
        'Percentage': df['Percentage'].apply(lambda x: f"{x}%"),
        'USD Value': df['Value_USD'].apply(lambda x: f"${x:,.2f}"),
        'RMB Value': (df['Value_USD'] * config.CURRENCY_EXCHANGE_RATE).apply(lambda x: f"¥{x:,.2f}"),
        'Shares': df['Shares'].apply(lambda x: f"{x:.2f}")
    })
    
    fig.add_trace(go.Table(
        header=dict(
            values=list(vesting_info.columns),
            font=dict(size=12, color='white'),
            fill_color='rgba(58, 71, 80, 0.8)',
            align='left'
        ),
        cells=dict(
            values=[vesting_info[col] for col in vesting_info.columns],
            font=dict(size=11),
            fill_color='rgba(242, 242, 242, 0.5)',
            align='left'
        ),
        domain=dict(x=[0, 1], y=[0, 0.3])
    ))
    
    fig.update_layout(height=500)
    
    return fig

@app.callback(
    Output("selling-chart", "figure"),
    Input("selling-data-store", "data")
)
def update_selling_chart(selling_data_dict):
    if selling_data_dict is None:
        return go.Figure()
    
    # Create DataFrame from selling data
    df = pd.DataFrame({
        'Date': pd.to_datetime(selling_data_dict['date']),
        'Month': selling_data_dict['month'],
        'Shares_To_Sell': selling_data_dict['shares_to_sell'],
        'Cumulative_Shares': selling_data_dict['cumulative_shares'],
        'Remaining_Shares': selling_data_dict['remaining_shares'],
        'Percent_Month': selling_data_dict['percent_sold_this_month'],
        'Percent_Cumulative': selling_data_dict['percent_sold_cumulative'],
        'Percent_Remaining': selling_data_dict['percent_remaining']
    })
    
    # Add strategy-specific columns
    if 'price_factor' in selling_data_dict:
        df['Price_Factor'] = selling_data_dict['price_factor']
    
    if 'period' in selling_data_dict:
        df['Period'] = selling_data_dict['period']
    
    # Create figure with dual axis
    fig = go.Figure()
    
    # Bar chart for shares to sell each month
    fig.add_trace(go.Bar(
        x=df['Date'],
        y=df['Shares_To_Sell'],
        name='Shares to Sell',
        marker_color='rgba(58, 71, 80, 0.6)',
        text=df['Shares_To_Sell'].apply(lambda x: f"{x:.1f}"),
        textposition='auto',
    ))
    
    # Line chart for cumulative percentage
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Percent_Cumulative'],
        mode='lines+markers',
        name='Cumulative %',
        line=dict(color='rgba(0, 128, 0, 0.7)', width=3),
        yaxis='y2'
    ))
    
    # Update layout
    fig.update_layout(
        title="RSU Selling Plan",
        xaxis_title="Date",
        yaxis_title="Shares to Sell",
        yaxis2=dict(
            title="%",
            overlaying="y",
            side="right",
            range=[0, 100]
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=350,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    return fig

@app.callback(
    Output("selling-table", "data"),
    Output("selling-table", "columns"),
    Input("selling-data-store", "data"),
    Input("last-price-store", "data")
)
def update_selling_table(selling_data_dict, current_price):
    if selling_data_dict is None:
        return [], []
    
    # Create DataFrame from selling data
    df = pd.DataFrame({
        'Date': pd.to_datetime(selling_data_dict['date']),
        'Month': selling_data_dict['month'],
        'Shares_To_Sell': selling_data_dict['shares_to_sell'],
        'Cumulative_Shares': selling_data_dict['cumulative_shares'],
        'Remaining_Shares': selling_data_dict['remaining_shares'],
        'Percent_Month': selling_data_dict['percent_sold_this_month'],
        'Percent_Cumulative': selling_data_dict['percent_sold_cumulative'],
        'Percent_Remaining': selling_data_dict['percent_remaining']
    })
    
    # Format data for display
    display_df = pd.DataFrame({
        'Month': df['Month'],
        'Date': df['Date'].dt.strftime('%Y-%m-%d'),
        'Shares to Sell': df['Shares_To_Sell'].apply(lambda x: f"{x:.2f}"),
        '% of Total': df['Percent_Month'].apply(lambda x: f"{x:.2f}%"),
        'Cumulative %': df['Percent_Cumulative'].apply(lambda x: f"{x:.2f}%"),
    })
    
    # Add estimated value columns if current price is available
    if current_price:
        df['Est_Value_USD'] = df['Shares_To_Sell'] * current_price
        df['Est_Value_RMB'] = df['Est_Value_USD'] * config.CURRENCY_EXCHANGE_RATE
        
        display_df['Est. Value (USD)'] = df['Est_Value_USD'].apply(lambda x: f"${x:,.2f}")
        display_df['Est. Value (RMB)'] = df['Est_Value_RMB'].apply(lambda x: f"¥{x:,.2f}")
    
    # Create columns configuration
    columns = [{"name": col, "id": col} for col in display_df.columns]
    
    return display_df.to_dict('records'), columns

@app.callback(
    Output("alerts-section", "children"),
    Input("interval-component", "n_intervals"),
    State("last-price-store", "data")
)
def update_alerts(n_intervals, current_price):
    global last_price
    
    if last_price is None or current_price is None:
        return html.Div()
    
    alerts = stock_data.check_price_alerts(last_price)
    
    if not alerts:
        return html.Div()
    
    alert_components = []
    for alert in alerts:
        alert_type = alert['type']
        message = alert['message']
        change = alert['change']
        
        color = "success" if alert_type == "increase" else "danger"
        
        alert_components.append(
            dbc.Alert(
                message,
                color=color,
                dismissable=True,
                className="mt-3",
            )
        )
    
    return html.Div(alert_components)

# Modal callbacks
@app.callback(
    Output("network-modal", "is_open"),
    [Input("modal-button", "n_clicks"), Input("close-modal", "n_clicks")],
    [State("network-modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# Network info update
@app.callback(
    Output("network-info", "children"),
    [Input("interval-component", "n_intervals")]
)
def update_network_info(n):
    return f"Network: {ip_address}:{config.DEFAULT_PORT}"

if __name__ == "__main__":
    port = config.DEFAULT_PORT
    host = config.HOST
    debug = config.DEBUG_MODE
    
    # Display server information
    print(f"\n{'='*50}")
    print(f"Amazon Stock Tracker is running!")
    print(f"{'='*50}")
    print(f"Local URL: http://localhost:{port}")
    print(f"Network URL: http://{ip_address}:{port}")
    print(f"Hostname: {hostname}")
    print(f"{'='*50}\n")
    
    # Run the app
    app.run(debug=debug, host=host, port=port) 