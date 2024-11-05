import os
import requests
import pandas as pd
from dotenv import load_dotenv
from dash import Dash, dcc, html, Output, Input
import plotly.graph_objs as go

load_dotenv()
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

def fetch_cryptocurrency_data(limit=10):
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": CMC_API_KEY
    }
    params = {
        "start": "1",
        "limit": str(limit),
        "convert": "USD"
    }
    response = requests.get(CMC_BASE_URL, headers=headers, params=params)
    data = response.json()
    print(data)  
    response.raise_for_status()
    return data.get("data")



def format_cryptocurrency_data(data):
    rows = []
    for item in data:
        try:
            rows.append({
                "Name": item["name"],
                "Symbol": item["symbol"],
                "Price (USD)": item["quote"]["USD"]["price"],
                "Market Cap": item["quote"]["USD"]["market_cap"],
                "24h Change (%)": item["quote"]["USD"]["percent_change_24h"],
                "24h High (USD)": item["quote"]["USD"].get("high_24h", 0),  
                "24h Low (USD)": item["quote"]["USD"].get("low_24h", 0)                                                                  
            })
        except KeyError as e:
            print(f"Key error: {e}") 
    return pd.DataFrame(rows)


# Create Dash app
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Cryptocurrency Tracker"),
    dcc.Dropdown(
        id='crypto-dropdown',
        options=[
            {'label': 'Top 10 Cryptocurrencies', 'value': 10},
            {'label': 'Top 25 Cryptocurrencies', 'value': 25},
            {'label': 'Top 50 Cryptocurrencies', 'value': 50}
        ],
        value=10,
        clearable=False
    ),
    dcc.Graph(id='price-chart'),
    dcc.Graph(id='trend-chart'),
    dcc.Interval(
        id='interval-component',
        interval=60*1000, 
        n_intervals=0
    ),
    html.Div(id='crypto-table')
])

@app.callback(
    Output('crypto-table', 'children'),
    Output('price-chart', 'figure'),
    Output('trend-chart', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('crypto-dropdown', 'value')
)
def update_data(n, limit):
    try:
        data = fetch_cryptocurrency_data(limit)
        df = format_cryptocurrency_data(data)
        
        if df.empty:
            return "No data available", go.Figure(), go.Figure()

        table_header = [html.Tr([html.Th(col) for col in df.columns])]
        table_rows = [html.Tr([html.Td(df.iloc[i][col]) for col in df.columns]) for i in range(len(df))]
        table = table_header + table_rows

        # Create price chart
        price_fig = go.Figure(data=[go.Bar(x=df['Symbol'], y=df['Price (USD)'])])
        price_fig.update_layout(title='Cryptocurrency Prices',
                                xaxis_title='Cryptocurrency',
                                yaxis_title='Price (USD)')

        # Create trend chart
        trend_fig = go.Figure()
        for i in range(len(df)):
            trend_fig.add_trace(go.Scatter(x=[0, 1, 2], 
                                            y=[df.iloc[i]['24h High (USD)'], 
                                               df.iloc[i]['Price (USD)'], 
                                               df.iloc[i]['24h Low (USD)']],
                                            mode='lines+markers', 
                                            name=df.iloc[i]['Name']))

        trend_fig.update_layout(title='24h Price Trend',
                                xaxis_title='Time (arbitrary units)',
                                yaxis_title='Price (USD)')

        return table, price_fig, trend_fig
    except Exception as e:
        return f"Error fetching data: {str(e)}", go.Figure(), go.Figure()

if __name__ == '__main__':
    app.run_server(debug=True)
