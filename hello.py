import dash
import dash_html_components as html
import plotly.graph_objects as go
import dash_core_components as dcc
import plotly.express as px
from dash.dependencies import Input, Output

import sys

sys.path.append('..')
from src.simulation import perform_simulation

app = dash.Dash()

app.layout = html.Div([

    html.Div(children=[
        html.H1(id='H1', children='Simulation of price changes after trades', style={'textAlign': 'center', \
                                                                                     'marginTop': 40,
                                                                                     'marginBottom': 40}),
        html.Label('A1'),
        dcc.Slider(min=0, max=200, step=1, value=85, id='A1', tooltip={"placement": "bottom", "always_visible": True}),

        html.Br(),
        html.Label('A2'),
        dcc.Slider(min=0, max=200, step=1, value=0.0001, id='A2',
                   tooltip={"placement": "bottom", "always_visible": True}),
        dcc.Graph(id='customswap_plot'),
    ], style={'padding': 10, 'flex': 1}),
    html.Div(children=[
        dcc.Graph(id='uniswap_plot'),
        dcc.Graph(id='stableswap_plot'),



    ], style={'padding': 10, 'flex': 1})], style={'display': 'flex', 'flex-direction': 'row'})


# app.layout = html.Div(id='parent', children=[
#     html.H1(id='H1', children='Simulation of price changes after trades', style={'textAlign': 'center', \
#                                                                       'marginTop': 40, 'marginBottom': 40}),
#     dcc.Slider(min=0, max=200, step=1, value=85, id='A1', tooltip={"placement": "bottom", "always_visible": True}),
#     dcc.Slider(min=0, max=200, step=1, value=0.0001, id='A2', tooltip={"placement": "bottom", "always_visible": True}),
#     dcc.Graph(id='uniswap_plot'),
#     dcc.Graph(id='stableswap_plot'),
#     dcc.Graph(id='customswap_plot')
# ])
#
#
@app.callback(Output('uniswap_plot', 'figure'),
              Output('stableswap_plot', 'figure'),
              Output('customswap_plot', 'figure'),
              [Input('A1', 'value'),
               Input('A2', 'value')])
def graph_update(a1, a2):
    prices1, prices2, price_slippages1, price_slippages2, token_ratio1, token_ratio2, \
    amplifications1, amplifications2 = perform_simulation(a1=a1, a2=a2)

    figs = []
    fig_labels = ['Uniswap', 'Stableswap', 'Customswap']
    for i in range(3):
        fig = go.Figure([go.Scatter(x=token_ratio1[i, :], y=prices1[i, :], mode='lines+markers', \
                                    line=dict(color='firebrick', width=4), name='$Boot Sales'),
                         go.Scatter(x=token_ratio2[i, :], y=prices2[i, :], mode='lines+markers', \
                                    line=dict(color='blue', width=4), name='$Boot Purchases')
                         ])

        fig.update_xaxes(type="log")
        fig.update_yaxes(type="log")
        fig.update_layout(title=fig_labels[i],
                          xaxis_title='Token amount of $USDC / Token amount of $Boot',
                          yaxis_title='Price of $Boot in $USDC'
                          )

        figs.append(fig)

    return figs[0], figs[1], figs[2]


if __name__ == '__main__':
    app.run_server()


# from flask import Flask
# app = Flask(__name__)
#
# @app.route('/')
# def hello_world():
#     return 'Hello World!'
#
# if __name__ == '__main__':
#     app.run()
