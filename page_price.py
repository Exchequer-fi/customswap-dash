# Page: Simulation of price changes after trades
#
# DONE: "Target price" change to "Token Price Support Floor"
# DONE: "Price of $Boot in $USDC" change to "Price of Token in $USDC"
# DONE: "Token amount of $USDC/Token amount of $BOOT" change to "Ratio of $USDC vs Token"
# DONE: "$Boot Sales" change to "Token sales"
# DONE: "$Boot Purchases" change to "Token purchases"
#
# As an aside, can you double check the x axis numerical amounts, it seems a bit funky, the numbers do not seem to follow a continuous sequence.


import dash
from dash import html, callback
import plotly.graph_objects as go
from dash import dcc
from dash.dependencies import Input, Output

import sys
import numpy as np

sys.path.append('..')
from simulation import perform_simulation

# app = dash.Dash(__name__)
# app.title = 'Customswap Simulation'

layout = html.Div([

    html.Div(children=[
        html.H1(id='H1', children='Simulation of price changes after trades', style={'textAlign': 'center', \
                                                                                     'marginTop': 40,
                                                                                     'marginBottom': 40}),
        html.Label('Token Price Support Floor: '),
        dcc.Input(
            id="target_price", type="number", placeholder='',
            min=0.25, max=1000, step=0.25, value=8
        ),
        html.Br(),
        html.Br(),
        html.Label('A1:'),
        dcc.Slider(min=0.0001, max=200, step=0.0001, value=85, id='A1', marks={
            0: '0', 50: '50', 100: '100', 150: '150', 200: '200'},
                   tooltip={"placement": "bottom", "always_visible": True}),

        html.Br(),
        html.Br(),
        html.Label('A2:'),
        dcc.Slider(min=0.0001, max=200, step=0.0001, value=0.0001, id='A2', marks={
            0: '0', 50: '50', 100: '100', 150: '150', 200: '200'},
                   tooltip={"placement": "bottom", "always_visible": True}),
        dcc.Graph(id='pr_customswap_plot'),
        html.Br(),
        html.Br(),
        html.A("Click here to see how much market cap could be saved by placing a portion of the liquidity pool in Customswap.",
               href='.'),
        html.Br(),
        html.Br(),
        dcc.Loading(
            id="pr_loading-1",
            type="default",
            fullscreen=False,
            children=html.Div(id="pr_loading-output-1")
        ),
    ], style={'padding': 10, 'flex': 1}),
    html.Div(children=[
        dcc.Graph(id='pr_uniswap_plot'),
        dcc.Graph(id='pr_stableswap_plot'),

    ], style={'padding': 10, 'flex': 1})], style={'display': 'flex', 'flex-direction': 'row'})


@callback(Output('pr_uniswap_plot', 'figure'),
              Output('pr_stableswap_plot', 'figure'),
              Output('pr_customswap_plot', 'figure'),
              Output("pr_loading-output-1", "children"),
              [Input('A1', 'value'),
               Input('A2', 'value'),
               Input('target_price', 'value')])
def graph_update(a1, a2, target_price):
    prices1, prices2, price_slippages1, price_slippages2, token_ratio1, token_ratio2, \
    amplifications1, amplifications2 = perform_simulation(a1=a1, a2=a2)

    figs = []
    fig_labels = ['Uniswap', 'Stableswap', 'Customswap']
    for i in range(3):
        fig = go.Figure([go.Scatter(x=token_ratio1[i, :], y=prices1[i, :] * target_price, mode='lines+markers', \
                                    line=dict(color='firebrick', width=4), name='Token sales'),
                         go.Scatter(x=token_ratio2[i, :], y=prices2[i, :] * target_price, mode='lines+markers', \
                                    line=dict(color='blue', width=4), name='Token Purchases')
                         ])

        fig.update_xaxes(type="log", tickmode='array',
        tickvals = [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 3, 5, 10, 25, 50, 100],
        # ticktext = ['0.05', '0.1', '1', '100']
                         )
        fig.update_yaxes(type="log", tickmode='array',
                         tickvals=target_price * np.array([0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 3, 5, 10, 25, 50, 100]),)
        fig.update_layout(title=fig_labels[i],
                          xaxis_title='Ratio of $USDC vs Token',
                          yaxis_title='Price of Token in $USDC'
                          )

        figs.append(fig)

    return figs[0], figs[1], figs[2], None

# server = app.server  # for heroku

# for command line
# app.run_server(debug=True)