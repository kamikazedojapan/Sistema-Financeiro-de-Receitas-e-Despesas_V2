from dash import html, dcc
import dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from app import *
from components import sidebar, dashboards, extratos, regra_orcamento
from globals import  df_receitas, df_despesas, df_cat_receita, df_cat_despesa


# =========  Layout  =========== #
content = html.Div(id="page-content")

app.layout = dbc.Container(children=[
    dcc.Store(id='store-receitas', data=df_receitas.to_dict("records")),
    dcc.Store(id='store-despesas', data=df_despesas.to_dict("records")),
    dcc.Store(id='stored-cat-receitas', data=df_cat_receita.to_dict('records')),
    dcc.Store(id='stored-cat-despesas', data=df_cat_despesa.to_dict('records')),

    dbc.Row([
        dbc.Col([
            dcc.Location(id='url'),
            sidebar.layout
        ], xs=12, sm=12, md=3, lg=2, style={
            'background-color': 'white',
            'minHeight': '100vh'
        }),

        dbc.Col([
            content
        ], xs=12, sm=12, md=9, lg=10, style={
            'background-color': 'white',
            'minHeight': '100vh'
        })
    ])

], fluid=True,)



@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def render_page(pathname):
    if pathname == '/':
        return dashboards.layout
    elif pathname == '/dashboards':
        return dashboards.layout
    elif pathname == '/extratos':
        return extratos.layout
    elif pathname == '/regra-orcamento':
        return regra_orcamento.layout
    return dashboards.layout



if __name__ == '__main__':
    app.run(port=8051, debug=True)