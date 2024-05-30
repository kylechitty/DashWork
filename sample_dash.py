from dash import Dash, html, dash_table, dcc, Input, Output
import dash_mantine_components as dmc
import pandas as pd
import numpy as np
import plotly.express as px
import datetime as dt
import yfinance as yf

app = Dash(__name__)

server = app.server
app.config.suppress_callback_exceptions = True

# Cocoa return data
cocoa_df = yf.Ticker("CC=F").history(period="max").loc[:,"Open":"Volume"]
cocoa_df["Date"] = cocoa_df.index

ret_dropdown_options = [{'label':'Daily','value':'D'},{'label':'Weekly','value':'W'},{'label':'Monthly','value':'ME'},
                        {'label':'Quarterly','value':'Q'},{'label':'Annually','value':'A'}]

@app.callback(
    Output('cocoa_graph', 'figure'),
    Input('ret_freq_dropdown', 'value'),
    Input('ret_type_dropdown', 'value'),
    Input('ret_price', 'value'),
    Input('ret_start_date', 'value'),
    Input('ret_end_date', 'value')

)
def update_ret_graph(freq, ret_type, ret_price, start_date, end_date):
    cocoa_loc_df = cocoa_df[(cocoa_df.index >= start_date) & (cocoa_df.index <= end_date)]

    if ret_price == "Price":
        fig = px.line(data_frame=cocoa_loc_df[ret_type].resample(freq).mean(), y=ret_type)
    else:
        cocoa_ret = cocoa_loc_df[ret_type] - cocoa_loc_df[ret_type].shift(1)
        fig = px.line(data_frame=cocoa_ret.resample(freq).mean(), y=ret_type)

    fig.update_layout(margin=dict(l=15, r=15, t=0, b=25), height=300)
    return fig

#Production data
prod_df = pd.read_csv('production_data.csv', index_col=0)
prod_df.insert(0, 'Country', prod_df.index)

@app.callback(
    Output('production_datatable', 'data'),
    Input('country_checklist', 'value')
)

def update_prod_datatable(selected_cols):
    if not selected_cols:
        return [],[]
    data = prod_df.loc[selected_cols].to_dict('records')
    return data

# Open interest data
open_int_df = pd.read_csv('open_interest.csv')
open_int_df['datetime_index'] = pd.to_datetime(open_int_df['datetime_index'])
open_int_df.index = open_int_df['datetime_index']

partition_df = open_int_df[['CSCE-COCOA COM. LONG FUT - OPEN INTEREST', 'CSCE-COCOA COM. SHORT FUT - OPEN INTEREST', 
                            'CSCE-COCOA N-COM. LONG FUT - OPEN INTEREST', 'CSCE-COCOA N-COM. SHORT FUT - OPEN INTEREST']]

partition_df = partition_df.rename(columns={'CSCE-COCOA COM. LONG FUT - OPEN INTEREST' : 'Commercial Long Futures',
                                            'CSCE-COCOA N-COM. LONG FUT - OPEN INTEREST' : 'Non-Commercial Long Futures',
                                            'CSCE-COCOA COM. SHORT FUT - OPEN INTEREST' : 'Commercial Short Futures',
                                            'CSCE-COCOA N-COM. SHORT FUT - OPEN INTEREST' : 'Non-Commercial Short Futures'})

partition_df['Date'] = open_int_df['datetime_index']

@app.callback(
    Output('open_int_graph', 'figure'),
    Input('open_int_dropdown', 'value'),
    Input('open_start_date', 'value'),
    Input('open_end_date', 'value')
)

def update_open_int_graph(col, start_date, end_date):
    fig = px.line(data_frame=partition_df[(partition_df.index >= start_date) & (partition_df.index <= end_date)], 
                  x='Date', y=col)
    fig.update_layout(margin=dict(l=15, r=15, t=0, b=10), height=300)
    return fig

app.layout = html.Div([
    html.H1('Cocoa Data Dashboard', style={'textAlign':'center','marginTop':"50px"}),

    html.H2('Cocoa Historical Time Series', style={'marginLeft':'20px'}),
    dcc.Graph(id='cocoa_graph', figure={}, style={'textAlign':'center', 'margin':'auto'}),
    
    
    dmc.MantineProvider([]),
    html.Div([
        dmc.Select(id='ret_freq_dropdown', data=ret_dropdown_options, value='ME', clearable=False, 
                 style={'width':'250px', 'height':'50px', 'display':'inline-block'}),

        dmc.Select(id='ret_type_dropdown', data=cocoa_df.columns[:-1], value='Close', clearable=False, 
                 style={'width':'250px', 'height':'50px', 'display':'inline-block'}),
        
        dmc.Select(id='ret_price', data=["Price", "Returns"], value='Price', clearable=False, 
                 style={'width':'250px', 'height':'50px', 'display':'inline-block'}),

        dmc.DateInput(id='ret_start_date', minDate=cocoa_df['Date'].min(), maxDate=cocoa_df['Date'].max(), value=cocoa_df['Date'].min(),
                       style={'width':'300px', 'height':'30px', 'margin':'auto', 'display':'inline-block'}),

        dmc.DateInput(id='ret_end_date', minDate=cocoa_df['Date'].min(), maxDate=cocoa_df['Date'].max(), value=cocoa_df['Date'].max(),
                       style={'width':'300px', 'height':'30px', 'margin':'auto', 'display':'inline-block'})

        ], style={'textAlign':'center', 'margin-top':'20px'}),

    html.H2('Cocoa Production Dataset', style={'marginLeft':'20px', 'marginTop':'50px'}),
    dash_table.DataTable(id='production_datatable', columns=[{'name':i, 'id':i} for i in prod_df.columns], 
                         data=prod_df.to_dict('records'), style_table={'width': '90%', 'margin': 'auto'}),
    dcc.Checklist(id='country_checklist', options=list(prod_df.index), value=list(prod_df.index), style = {'textAlign':'center'},
                  labelStyle={'display':'inline-block', 'margin-right':'20px', 'margin-top':'10px'}),
    
    html.H2('Open Interest Volume', style={'marginLeft':'20px', 'marginTop':'50px'}),
    dcc.Graph(id='open_int_graph', figure={}, style={'textAlign':'center', 'margin':'auto'}),
    html.Div([
        dmc.Select(id='open_int_dropdown', data=partition_df.columns[:-1], value='Commercial Long Futures', clearable=False, 
                style={'width':'250px', 'height':'50px', 'display':'inline-block'}),

        dmc.DateInput(id='open_start_date', minDate=partition_df['Date'].min(), maxDate=partition_df['Date'].max(), 
                value=partition_df['Date'].min(), style={'width':'300px', 'height':'30px', 'margin':'auto', 'display':'inline-block'}),

        dmc.DateInput(id='open_end_date', minDate=partition_df['Date'].min(), maxDate=partition_df['Date'].max(), 
                value=partition_df['Date'].max(), style={'width':'300px', 'height':'30px', 'margin':'auto', 'display':'inline-block'})
    ], style={'textAlign':'center', 'margin-top':'20px'}),
])

# Run the app
if __name__ == '__main__':
    app.run(debug=True)