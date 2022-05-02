import dash
from dash import Dash, dcc, html, Input, Output, callback
import page_mcap, page_price


app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/':
        app.title = 'Customswap Market Cap Saved Simulation'
        return page_mcap.layout
    elif pathname == '/page_price':
        app.title = 'Customswap Price Dynamics Simulation'
        return page_price.layout
    else:
        return '404'

# for heroku
# app = dash.Dash(__name__)
# server = app.server

if __name__ == '__main__':
    app.run_server(debug=False)
    server = app.server