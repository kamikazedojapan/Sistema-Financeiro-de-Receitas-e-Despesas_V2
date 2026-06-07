from dash.dependencies import Input, Output, State
from dash import dash_table, dcc, html, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

from app import app
from database import sincronizar_receitas, sincronizar_despesas

COLUNAS = ["id", "Valor", "Efetuado", "Fixo", "Data", "Categoria", "Descrição", "Regra"]
COLUNAS_EDITAVEIS = ["Valor", "Efetuado", "Fixo", "Data", "Categoria", "Descrição", "Regra"]


def _formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _normalizar_df(data):
    df = pd.DataFrame(data)

    for coluna in COLUNAS:
        if coluna not in df.columns:
            df[coluna] = None if coluna == "id" else ""

    if df.empty:
        return pd.DataFrame(columns=COLUNAS)

    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Efetuado"] = pd.to_numeric(df["Efetuado"], errors="coerce").fillna(0).astype(int)
    df["Fixo"] = pd.to_numeric(df["Fixo"], errors="coerce").fillna(0).astype(int)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["Data"] = df["Data"].fillna(pd.Timestamp.today().strftime("%Y-%m-%d"))
    df["Categoria"] = df["Categoria"].fillna("Sem categoria")
    df["Descrição"] = df["Descrição"].fillna("Sem descrição")
    df["Regra"] = (
        df["Regra"]
        .fillna("Necessidades")
        .replace({"Necessidades": "Custos"})
    )

    return df[COLUNAS]


def _criar_tabela(tabela_id, data):
    df = _normalizar_df(data)

    return dash_table.DataTable(
        id=tabela_id,
        data=df.to_dict("records"),
        columns=[
            {
                "name": coluna,
                "id": coluna,
                "editable": coluna in COLUNAS_EDITAVEIS,
            }
            for coluna in COLUNAS
        ],
        editable=True,
        row_deletable=True,
        page_size=10,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "minWidth": "120px",
            "width": "150px",
            "maxWidth": "260px",
            "whiteSpace": "normal",
        },
        style_header={"fontWeight": "bold"},
        style_data_conditional=[
            {
                "if": {"column_id": "id"},
                "backgroundColor": "#f8f9fa",
                "color": "#6c757d",
            }
        ],
    )


layout = dbc.Col([
    html.Legend('Extratos e CRUD financeiro'),
    html.P('Edite diretamente nas tabelas, remova linhas pelo botão de exclusão e clique em salvar. Todas as alterações são persistidas no banco SQLite.'),

    dcc.Tabs([
        dcc.Tab(label="Despesas", children=[
            dbc.Row([
                dbc.Col([
                    html.H4("Despesas"),
                    _criar_tabela('tabela-despesas-crud', []),
                    html.Br(),
                    dbc.Button("Salvar alterações das despesas", id="salvar-crud-despesas", color="danger"),
                    html.Div(id="msg-crud-despesas", className="mt-2"),
                ], xs=12)
            ]),

            html.Hr(),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='bar-graph', style={'margin-right': '20px'})
                ], xs=12, md=9),

                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H4("Despesas"),
                            html.Legend("R$ 0,00", id="valor_despesa_card", style={'font-size': '42px'}),
                            html.H6("Total de despesas"),
                            html.Hr(),
                            html.Div(
                                id="resumo-categorias-despesas",
                                style={"textAlign": "left", "fontSize": "14px"}
                            ),
                        ], style={'text-align': 'center', 'padding-top': '30px'})
                    )
                ], xs=12, md=3)
            ])
        ]),

        dcc.Tab(label="Receitas", children=[
            dbc.Row([
                dbc.Col([
                    html.H4("Receitas"),
                    _criar_tabela('tabela-receitas-crud', []),
                    html.Br(),
                    dbc.Button("Salvar alterações das receitas", id="salvar-crud-receitas", color="success"),
                    html.Div(id="msg-crud-receitas", className="mt-2"),
                ], xs=12)
            ]),

            html.Hr(),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='bar-graph-receitas', style={'margin-right': '20px'})
                ], xs=12, md=9),

                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H4("Receitas"),
                            html.Legend("R$ 0,00", id="valor_receita_card", style={'font-size': '42px'}),
                            html.H6("Total de receitas"),
                        ], style={'text-align': 'center', 'padding-top': '30px'})
                    )
                ], xs=12, md=3)
            ])
        ]),
    ])
], style={'padding': '10px'})


@app.callback(
    Output('tabela-despesas-crud', 'data'),
    Input('store-despesas', 'data')
)
def importar_tabela_despesas(data):
    return _normalizar_df(data).to_dict('records')


@app.callback(
    Output('tabela-receitas-crud', 'data'),
    Input('store-receitas', 'data')
)
def importar_tabela_receitas(data):
    return _normalizar_df(data).to_dict('records')


@app.callback(
    Output('store-despesas', 'data', allow_duplicate=True),
    Output('msg-crud-despesas', 'children'),
    Input('salvar-crud-despesas', 'n_clicks'),
    State('tabela-despesas-crud', 'data'),
    prevent_initial_call=True
)
def salvar_edicoes_despesas(n_clicks, dados_tabela):
    if not n_clicks:
        return no_update, no_update

    df_atualizado = sincronizar_despesas(dados_tabela or [])
    mensagem = dbc.Alert("Despesas salvas no banco de dados. Edições e exclusões foram persistidas.", color="success", duration=3000)
    return df_atualizado.to_dict("records"), mensagem


@app.callback(
    Output('store-receitas', 'data', allow_duplicate=True),
    Output('msg-crud-receitas', 'children'),
    Input('salvar-crud-receitas', 'n_clicks'),
    State('tabela-receitas-crud', 'data'),
    prevent_initial_call=True
)
def salvar_edicoes_receitas(n_clicks, dados_tabela):
    if not n_clicks:
        return no_update, no_update

    df_atualizado = sincronizar_receitas(dados_tabela or [])
    mensagem = dbc.Alert("Receitas salvas no banco de dados. Edições e exclusões foram persistidas.", color="success", duration=3000)
    return df_atualizado.to_dict("records"), mensagem


@app.callback(
    Output('bar-graph', 'figure'),
    Input('store-despesas','data')
)
def bar_chart(data):
    df = _normalizar_df(data)

    if df.empty:
        return px.bar(title="Nenhuma despesa cadastrada")

    df_grouped = df.groupby("Categoria", as_index=False)["Valor"].sum()
    df_grouped = df_grouped.sort_values("Valor", ascending=False)
    df_grouped["Valor_formatado"] = df_grouped["Valor"].apply(_formatar_moeda)

    graph = px.bar(
        df_grouped,
        x='Categoria',
        y='Valor',
        text='Valor_formatado',
        title="Despesas Gerais por Categoria",
        hover_data={"Valor_formatado": True, "Valor": False}
    )
    graph.update_traces(textposition='outside')
    graph.update_layout(
        xaxis_title="Categoria",
        yaxis_title="Valor (R$)",
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return graph


@app.callback(
    Output('bar-graph-receitas', 'figure'),
    Input('store-receitas','data')
)
def bar_chart_receitas(data):
    df = _normalizar_df(data)

    if df.empty:
        return px.bar(title="Nenhuma receita cadastrada")

    df_grouped = df.groupby("Categoria", as_index=False)["Valor"].sum()
    graph = px.bar(df_grouped, x='Categoria', y='Valor', title="Receitas Gerais")
    graph.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return graph


@app.callback(
    Output('valor_despesa_card', 'children'),
    Input('store-despesas', 'data')
)
def display_desp(data):
    df = _normalizar_df(data)
    valor = df["Valor"].sum() if not df.empty else 0
    return _formatar_moeda(valor)



@app.callback(
    Output('resumo-categorias-despesas', 'children'),
    Input('store-despesas', 'data')
)
def display_resumo_categorias_despesas(data):
    df = _normalizar_df(data)

    if df.empty:
        return html.Small("Nenhuma categoria com despesa.", className="text-muted")

    df_grouped = (
        df.groupby("Categoria", as_index=False)["Valor"]
        .sum()
        .sort_values("Valor", ascending=False)
    )

    return html.Div([
        html.H6("Por categoria", className="mb-2"),
        html.Ul([
            html.Li([
                html.Strong(f"{linha['Categoria']}: "),
                html.Span(_formatar_moeda(linha["Valor"]))
            ])
            for _, linha in df_grouped.iterrows()
        ], style={"paddingLeft": "18px", "marginBottom": "0"})
    ])


@app.callback(
    Output('valor_receita_card', 'children'),
    Input('store-receitas', 'data')
)
def display_receita(data):
    df = _normalizar_df(data)
    valor = df["Valor"].sum() if not df.empty else 0
    return _formatar_moeda(valor)
