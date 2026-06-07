import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Home Page", className="text-primary"),
    html.Hr(),
    dbc.Row([
        dbc.Col(
            dbc.Button("Receita", color="success", id="btn-receita"),
            width=6
        ),
        dbc.Col(
            dbc.Button("Despesa", color="danger", id="btn-despesa"),
            width=6
        ),
    ])
], fluid=True)

if __name__ == '__main__':
    app.run(debug=True)
