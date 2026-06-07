from dash import html, dcc
from dash.dependencies import Input, Output, State
from datetime import date, datetime, timedelta
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calendar
from globals import *
from app import app
import pdb

card_icon = {
    "color": "white",
    "textAlign": "center",
    "fontSize": 30,
    "margin": "auto"
}
graph_margin = dict(l=25, r=25, t=25, b=0)

# =========  Layout  =========== #
layout = dbc.Col([
       dbc.Row([
           # Saldo Total
           dbc.Col([
               dbc.CardGroup([
                   dbc.Card([
                       html.Legend('Saldo'),
                       html.H5('R$ 5400', id='p-saldo-dashboards', style={})
                   ], style={'padding-left': '20px', 'padding-top': '10px'}),
                   dbc.Card(
                       html.Div(className='fa fa-university', style=card_icon),
                       color='warning',
                       style={'maxWidth': 75, 'height': 100, 'margin-left': '-10px'}
                   )
               ])
           ], width=4),

           # Receita
           dbc.Col([
               dbc.CardGroup([
                   dbc.Card([
                       html.Legend('Receita'),
                       html.H5('R$ 10000', id='p-receita-dashboards', style={})
                   ], style={'padding-left': '20px', 'padding-top': '10px'}),
                   dbc.Card(
                       html.Div(className='fa fa-smile-o', style=card_icon),
                       color='success',
                       style={'maxWidth': 75, 'height': 100, 'margin-left': '-10px'}
                   )
               ])
           ], width=4),

           # Despesa
           dbc.Col([
               dbc.CardGroup([
                   dbc.Card([
                       html.Legend('Despesa'),
                       html.H5('R$ 4600', id='p-despesa-dashboards', style={})
                   ], style={'padding-left': '20px', 'padding-top': '10px'}),
                   dbc.Card(
                       html.Div(className='fa fa-meh-o', style=card_icon),
                       color='danger',
                       style={'maxWidth': 75, 'height': 100, 'margin-left': '-10px'}
                   )
               ])
           ], width=4)
       ], style={'margin': '10px'}),

       dbc.Row([
           dbc.Col([
               dbc.Card([
                   html.Legend("Filtrar lançamentos", className="card-title"),
                   html.Label("Categorias das receitas"),
                   html.Div(
                       dcc.Dropdown(
                           id="dropdown-receita",
                           clearable=False,
                           style={"width": "100%"},
                           persistence=True,
                           persistence_type="session",
                           multi=True)
                   ),
                   html.Label("Categorias das despesas"),
                   html.Div(
                       dcc.Dropdown(
                           id="dropdown-despesa",
                           clearable=False,
                           style={"width": "100%"},
                           persistence=True,
                           persistence_type="session",
                           multi=True)
                    ),

                    html.Legend("Periodo de Análise", style={"margin-top": "10px"}),
                    dcc.DatePickerRange(
                        month_format='Do MMM, YY',
                        end_date_placeholder_text='Data',
                        start_date=datetime(2022, 4, 1).date(),
                        end_date=datetime.today() + timedelta(days=31),
                        updatemode='singledate',
                        id='date-picker-config',
                        style={'z-index': 100}),

                    html.Legend("Analise Mensal", style={"margin-top": "15px"}),
                    html.Label("Mês"),
                    dcc.Dropdown(
                        id="dropdown-mes",
                        options=[
                            {"label": "Janeiro", "value": 1},
                            {"label": "Fevereiro", "value": 2},
                            {"label": "Março", "value": 3},
                            {"label": "Abril", "value": 4},
                            {"label": "Maio", "value": 5},
                            {"label": "Junho", "value": 6},
                            {"label": "Julho", "value": 7},
                            {"label": "Agosto", "value": 8},
                            {"label": "Setembro", "value": 9},
                            {"label": "Outubro", "value": 10},
                            {"label": "Novembro", "value": 11},
                            {"label": "Dezembro", "value": 12},
                        ],
                        value=datetime.now().month,
                        clearable=False
                    ),
                    html.Label("Ano", style={"margin-top": "10px"}),
                    dcc.Dropdown(
                        id="dropdown-ano",
                        options=[
                            {"label": str(ano), "value": ano}
                            for ano in range(2020, datetime.now().year + 1)
                        ],
                        value=datetime.now().year,
                        clearable=False
                    ),
               ], style={'height': '100%', 'padding': '20px'})
           ], width=4),

           dbc.Col(
               dbc.Card(dcc.Graph(id='graph1'), style={'height': '100%', 'padding': '10px'}), width=8
           )
       ], style={'margin': '10px'}),

       dbc.Row([
           dbc.Col(dbc.Card(dcc.Graph(id='graph2'), style={'padding': '10px'}), width=6),
           dbc.Col(dbc.Card(dcc.Graph(id='graph3'), style={'padding': '10px'}), width=3),
           dbc.Col(dbc.Card(dcc.Graph(id='graph4'), style={'padding': '10px'}), width=3),
           dbc.Col(dbc.Card(dcc.Graph(id='graph5'), style={'padding': '10px'}), width=12)
       ], style={"margin": "10px"})
    ])

# =========  Callbacks  =========== #
@app.callback(
    Output("dropdown-receita", "options"),
    Output("dropdown-receita", "value"),
    Output("p-receita-dashboards", "children"),
    Input("store-receitas", "data"))

def populate_dropdownvalues(data):
    df = pd.DataFrame(data)
    valor = df['Valor'].sum()
    val = df.Categoria.unique().tolist()

    [{"label": x, "value": x} for x in val]

    return ([{"label": x, "value": x} for x in val], val, f"R$ {valor:.2f}")

@app.callback(
    Output("dropdown-despesa", "options"),
    Output("dropdown-despesa", "value"),
    Output("p-despesa-dashboards", "children"),
    Input("store-despesas", "data"))

def populate_dropdownvalues(data):
    df = pd.DataFrame(data)
    valor = df['Valor'].sum()
    valor = round(valor, 2)  # Arredonda para duas casas
    val = df.Categoria.unique().tolist()

    return ([{"label": x, "value": x} for x in val], val, f"R$ {valor:.2f}")


@app.callback(
    Output("p-saldo-dashboards", "children"),
    [Input("store-despesas", "data"),
     Input("store-receitas", "data")])

def saldo_total(despesas, receitas):
    df_despesas = pd.DataFrame(despesas)
    df_receitas = pd.DataFrame(receitas)

    total_despesas = df_despesas["Valor"].sum() if "Valor" in df_despesas.columns else 0
    total_receitas = df_receitas["Valor"].sum() if "Valor" in df_receitas.columns else 0

    saldo = total_receitas - total_despesas

    return f"R$ {saldo:.2f}"

@app.callback(
    Output('graph1', 'figure'),
    [Input('store-receitas', 'data'),
     Input('store-despesas', 'data'),
     Input('dropdown-receita', 'value'),
     Input('dropdown-despesa', 'value')]
)

def update_output(data_receita, data_despesa, receita, despesa):
    df_despesas = pd.DataFrame(data_despesa)
    df_despesas["Data"] = pd.to_datetime(df_despesas["Data"])
    df_despesas = df_despesas.set_index("Data")[["Valor"]]
    df_ds = df_despesas.groupby("Data").sum().rename(columns={"Valor": "Despesa"})

    df_receitas = pd.DataFrame(data_receita)
    df_receitas["Data"] = pd.to_datetime(df_receitas["Data"])
    df_receitas = df_receitas.set_index("Data")[["Valor"]]
    df_rc = df_receitas.groupby("Data").sum().rename(columns={"Valor": "Receita"})

    df_acum = df_ds.join(df_rc, how="outer").fillna(0)
    df_acum["Acum"] = df_acum["Receita"] - df_acum["Despesa"]
    df_acum["Acum"] = df_acum["Acum"].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(name="Fluxo de caixa", x=df_acum.index, y=df_acum["Acum"], mode="lines"))

    fig.update_layout(margin=graph_margin,height=400)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

@app.callback(
    Output('graph2', 'figure'),
    [Input('store-receitas', 'data'),
     Input('store-despesas', 'data'),
     Input('dropdown-receita', 'value'),
     Input('dropdown-despesa', 'value'),
     Input('date-picker-config', 'start_date'),
     Input('date-picker-config', 'end_date'), ]
)

def graph2_show(data_receita, data_despesa, receita, despesa, start_date, end_date):
    df_ds = pd.DataFrame(data_despesa)
    df_rc = pd.DataFrame(data_receita)

    df_ds["Output"] = "Despesas"
    df_rc["Output"] = "Receitas"
    df_final = pd.concat([df_ds, df_rc])
    df_final["Data"] = pd.to_datetime(df_final["Data"])

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df_final = df_final[(df_final["Data"] >= start_date) & (df_final["Data"] <= end_date)]
    df_final = df_final[(df_final["Categoria"].isin(receita)) | (df_final["Categoria"].isin(despesa))]

    fig = px.bar(df_final, x="Data", y="Valor", color="Output", barmode="group")

    fig.update_layout(margin=graph_margin,height=400)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

@app.callback(
    Output('graph3', "figure"),
    [Input('store-receitas', 'data'),
     Input('dropdown-receita', 'value')]
)

def pie_receita(data_receita, receita):
    df = pd.DataFrame(data_receita)

    if df.empty or 'Categoria' not in df.columns:
        fig = px.pie(values=[1], names=["Sem dados"])
        fig.update_layout(title={'text': 'Receitas'})
        return fig

    df = df[df['Categoria'].isin(receita)]

    fig = px.pie(df, values='Valor', names='Categoria', hole=0.4)
    fig.update_layout(title={'text': 'Receitas'})
    fig.update_layout(margin=graph_margin, height=400)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    return fig

@app.callback(
    Output('graph4', 'figure'),
    [Input('store-despesas', 'data'),
     Input('dropdown-despesa', 'value')]
)

def pie_despesa(data_despesa, despesa):
    df = pd.DataFrame(data_despesa)

    if df.empty or 'Categoria' not in df.columns:
        fig = px.pie(values=[1], names=["Sem dados"])
        fig.update_layout(title={'text': 'Despesas'})
        fig.update_layout(margin=graph_margin, height=400)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig

    df = df[df['Categoria'].isin(despesa)]

    fig = px.pie(df, values='Valor', names='Categoria', hole=0.4)
    fig.update_layout(title={'text': 'Despesas'})
    fig.update_layout(margin=graph_margin, height=400)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    return fig

@app.callback(
    Output("graph5", "figure"),
    [
        Input("store-receitas", "data"),
        Input("store-despesas", "data"),
        Input("dropdown-mes", "value"),
        Input("dropdown-ano", "value")
    ]
)
def grafico_saldo_mensal(receitas, despesas, mes, ano):

    df_receitas = pd.DataFrame(receitas)
    df_despesas = pd.DataFrame(despesas)

    if df_receitas.empty:
        return px.pie(
            names=["Sem dados"],
            values=[1],
            title="Nenhuma receita cadastrada"
        )

    df_receitas["Data"] = pd.to_datetime(df_receitas["Data"])
    df_despesas["Data"] = pd.to_datetime(df_despesas["Data"])

    inicio_mes = pd.Timestamp(
        year=ano,
        month=mes,
        day=1
    )

    receitas_anteriores = df_receitas[
        df_receitas["Data"] < inicio_mes
    ]

    despesas_anteriores = df_despesas[
        df_despesas["Data"] < inicio_mes
    ]

    saldo_inicial = (
        receitas_anteriores["Valor"].sum() - despesas_anteriores["Valor"].sum()
    )

    receitas_mes = df_receitas[
        (df_receitas["Data"].dt.month == mes) & (df_receitas["Data"].dt.year == ano)
    ]

    despesas_mes = df_despesas[
        (df_despesas["Data"].dt.month == mes) & (df_despesas["Data"].dt.year == ano)
    ]

    receita_mes = receitas_mes["Valor"].sum()
    despesa_mes = despesas_mes["Valor"].sum()

    saldo_final = saldo_inicial + receita_mes - despesa_mes

    base_calculo = saldo_inicial + receita_mes

    patrimonio_mes = saldo_inicial + receita_mes

    patrimonio_formatado = (
        f"{patrimonio_mes:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    if base_calculo == 0 and despesa_mes == 0:
        return px.pie(
            names=["Sem dados"],
            values=[1],
            title="Nenhuma receita encontrada"
        )

    fig = px.pie(
        names=["Saldo Restante", "Despesas"],
        values=[max(saldo_final, 0), despesa_mes],
        hole=0.5
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    fig.update_layout(
        title={
            "text": (
                f"Distribuição Financeira - {mes:02d}/{ano}"
                f"<br><sup>Patrimônio do mês: R$ {patrimonio_formatado}</sup>"
            ),
            "x": 0.5
        },
        margin=graph_margin,
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    saldo_formatado = (
        f"R$ {saldo_final:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    fig.add_annotation(
        text=f"<b>{saldo_formatado}</b><br>Saldo Final",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=20)
    )

    return fig