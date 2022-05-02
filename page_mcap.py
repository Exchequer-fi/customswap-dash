import dash
from dash import html
import plotly.graph_objects as go
from dash import dcc
from dash.dependencies import Input, Output
import numpy as np

import sys

sys.path.append('..')
from pool_pair_price import compute_market_cap_saved

app = dash.Dash(__name__)
app.title = 'Customswap Market Cap Saved Simulation'

# for heroku
server = app.server

app.layout = html.Div([

    html.Div(children=[
        html.H1(id='H1', children='Simulation of market cap saved by Customswap', style={'textAlign': 'center', \
                                                                                     'marginTop': 40,
                                                                                     'marginBottom': 40}),
        html.Label('Target Price: '),
        dcc.Input(
            id="target_price", type="number", placeholder='',
            min=0.25, max=1000, step=0.25, value=8
        ),
        html.Br(),
        html.Br(),
        html.Label('Total Number of Tokens:'),
        dcc.Input(
            id="num_tokens", type="number", placeholder='',
            min=1000, max=10000000000, step=1, value=1000000
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

        html.Br(),
        html.Br(),
        html.Label('Large $Boot sale pool ratio:'),
        dcc.Slider(min=0.0001, max=0.5, step=0.05, value=0.1, id='large_sell_ratio', marks={
            0: '0', 50: '50', 100: '100', 150: '150', 200: '200'},
                   tooltip={"placement": "bottom", "always_visible": True}),

        dcc.Loading(
            id="loading-1",
            type="default",
            fullscreen=False,
            children=html.Div(id="loading-output-1")
        ),
        #dcc.Graph(id='customswap_plot'),
    ], style={'padding': 10, 'flex': 1}),
    html.Div(children=[
        dcc.Graph(id='uniswap_plot'),
        dcc.Graph(id='customswap_plot'),

    ], style={'padding': 10, 'flex': 1})], style={'display': 'flex', 'flex-direction': 'row'})


@app.callback(Output('uniswap_plot', 'figure'),
              Output('customswap_plot', 'figure'),
              Output("loading-output-1", "children"),
              [Input('A1', 'value'),
               Input('A2', 'value'),
               Input('target_price', 'value'),
               Input('large_sell_ratio', 'value'),
               Input('num_tokens', 'value')])
def graph_update(a1, a2, target_price, large_sell_ratio, num_tokens):
    arb_trade_boot_num = 1 + int(num_tokens * 75/1000000)  # 50

    # print('num_tokens:', num_tokens)
    # print('arb_trade_boot_num:', arb_trade_boot_num)

    market_cap_saved_uni, final_prices_for_liquidity_ratio_uni, uniswap_liquity_ratios_uni, price_if_all_uniswap_uni = \
        compute_market_cap_saved(large_uniswap_trade=True, arb_trade_boot_num=arb_trade_boot_num, large_sell_ratio=large_sell_ratio,
                                 arb_price_tolerance=0.03, amplification=[a1, a2], boot_token_num=num_tokens)

    market_cap_saved_cus, final_prices_for_liquidity_ratio_cus, uniswap_liquity_ratios_cus, price_if_all_uniswap_cus= \
        compute_market_cap_saved(large_uniswap_trade=False, arb_trade_boot_num=arb_trade_boot_num, large_sell_ratio=large_sell_ratio,
                                 arb_price_tolerance=0.03, amplification=[a1, a2], boot_token_num=num_tokens)

    fig_cap = go.Figure([go.Scatter(x=uniswap_liquity_ratios_uni, y=market_cap_saved_uni * target_price, mode='lines+markers', \
                                line=dict(color='firebrick', width=4), name='Large Trade in Uniswap'),

                            # go.Scatter(x=uniswap_liquity_ratios_cus, y=market_cap_saved_cus * target_price,
                            #            mode='lines+markers', \
                            #            line=dict(color='blue', width=4), name='Large Trade in Customswap')
                     ])


    fig_prices = go.Figure([go.Scatter(x=uniswap_liquity_ratios_uni, y=final_prices_for_liquidity_ratio_uni * target_price, mode='lines+markers', \
                                line=dict(color='firebrick', width=4), name='Large Trade in Uniswap'),
                         # go.Scatter(x=uniswap_liquity_ratios_cus, y=final_prices_for_liquidity_ratio_cus * target_price,
                         #            mode='lines+markers', \
                         #            line=dict(color='blue', width=4), name='Large Trade in Customswap')
                     ])

    fig_prices.add_hline(
        y=price_if_all_uniswap_uni * target_price, line_width=3, line_dash="dash",
        annotation_text='Price if all in Uniswap', annotation_position="bottom",
        line_color="green")

    fig_cap.update_layout(title='',
                      xaxis_title='Pool ratio in Uniswap',
                      yaxis_title='Markep cap saved ($)',
                      yaxis_range=[0, 1.1 * max(np.max(market_cap_saved_uni),
                                          np.max(market_cap_saved_cus)) * target_price]
                      )

    fig_prices.update_layout(title='',
                      xaxis_title='Pool ratio in Uniswap',
                      yaxis_title='Final $Boot Price',
                      yaxis_range=[0, 1.1 * max(np.max(final_prices_for_liquidity_ratio_uni),
                                          np.max(final_prices_for_liquidity_ratio_cus)) * target_price]
                      )


    return fig_cap, fig_prices, None


# for heroku
# server = app.server

# for command line
# app.run_server(debug=True)
