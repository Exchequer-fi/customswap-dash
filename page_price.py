import dash
from dash import html, callback
import plotly.graph_objects as go
from dash import dcc
from dash.dependencies import Input, Output

import sys

sys.path.append('..')
from simulation import perform_simulation

# app = dash.Dash(__name__)
# app.title = 'Customswap Simulation'

layout = html.Div([

    html.Div(children=[
        html.H1(id='H1', children='Simulation of price changes after trades', style={'textAlign': 'center', \
                                                                                     'marginTop': 40,
                                                                                     'marginBottom': 40}),
        html.Label('Target Price: '),
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
                                    line=dict(color='firebrick', width=4), name='$Boot Sales'),
                         go.Scatter(x=token_ratio2[i, :], y=prices2[i, :] * target_price, mode='lines+markers', \
                                    line=dict(color='blue', width=4), name='$Boot Purchases')
                         ])

        fig.update_xaxes(type="log")
        fig.update_yaxes(type="log")
        fig.update_layout(title=fig_labels[i],
                          xaxis_title='Token amount of $USDC / Token amount of $Boot',
                          yaxis_title='Price of $Boot in $USDC'
                          )

        figs.append(fig)

    return figs[0], figs[1], figs[2], None

# server = app.server  # for heroku

# for command line
# app.run_server(debug=True)