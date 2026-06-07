from datetime import datetime, date

from dash import html, dcc, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd

from app import app
from globals import cat_receita, cat_despesa, cat_regra
from database import (
    criar_receita,
    criar_despesa,
    listar_receitas,
    listar_despesas,
    substituir_categorias_receitas,
    substituir_categorias_despesas,
)

COLUNAS_MOVIMENTACOES = [
    "id",
    "Valor",
    "Efetuado",
    "Fixo",
    "Data",
    "Categoria",
    "Descrição",
    "Regra",
]


def _opcoes(lista):
    return [{"label": item, "value": item} for item in lista]


def _opcoes_regra(lista):
    return [{"label": ("Custos" if item == "Necessidades" else item), "value": item} for item in lista]


# ========= Layout ========= #
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("MyDesktop", className="text-primary"),
            html.Hr(),

            html.Img(
                src='/assets/img_hom.png',
                id="avatar_change",
                alt='Avatar',
                className='perfil_avatar',
                style={
                    'width': '200px',
                    'height': 'auto',
                    'border-radius': '50%',
                    'object-fit': 'cover',
                    'display': 'block',
                    'margin': '0 auto'
                }
            ),

            html.Br(),

            dbc.Row([
                dbc.Col(
                    dbc.Button(
                        "+ Receita",
                        color='success',
                        id='open-novo-receita',
                        className='w-100'
                    ),
                    width=6,
                    class_name='pe-3'
                ),
                dbc.Col(
                    dbc.Button(
                        "- Despesa",
                        color='danger',
                        id='open-novo-despesa',
                        className='w-100'
                    ),
                    width=6,
                    class_name='ps-3'
                )
            ], justify='center'),

            html.Br(),

            # Modal Receita
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle('Adicionar receita')),
                dbc.ModalBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label('Descrição:'),
                            dbc.Input(placeholder="Ex.: Salário, Fonte de Renda...", id="txt-receita"),
                        ], xs=12, md=6),
                        dbc.Col([
                            dbc.Label("Valor:"),
                            dbc.Input(placeholder="R$ 100.00", id="valor_receita", value="", type="number", step="0.01")
                        ], xs=12, md=6)
                    ]),

                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Data:"),
                            dcc.DatePickerSingle(
                                id="date-receitas",
                                min_date_allowed=date(2025, 1, 1),
                                max_date_allowed=date(2035, 12, 31),
                                date=datetime.today(),
                                style={"width": "100%"}
                            ),
                        ], xs=12, md=3),

                        dbc.Col([
                            dbc.Label("Extras"),
                            dbc.Checklist(
                                options=[
                                    {"label": "Foi recebida", "value": 1},
                                    {"label": "Receita Recorrente", "value": 2}
                                ],
                                value=[1],
                                id='switches-input-receita',
                                switch=True
                            )
                        ], xs=12, md=3),

                        dbc.Col([
                            html.Label('Categoria da receita'),
                            dbc.Select(
                                id='select_receita',
                                options=_opcoes(cat_receita),
                                value=cat_receita[0] if cat_receita else None
                            )
                        ], xs=12, md=3),

                        dbc.Col([
                            html.Label('Regra 50-30-20'),
                            dbc.Select(
                                id='select-regra-receita',
                                options=_opcoes_regra(cat_regra),
                                value='Investimentos'
                            )
                        ], xs=12, md=3)
                    ], style={'margin-top': '25px'}),

                    dbc.Row([
                        dbc.Accordion([
                            dbc.AccordionItem(children=[
                                dbc.Row([
                                    dbc.Col([
                                        html.Legend('Adicionar categoria', style={'color': 'green'}),
                                        dbc.Input(type="Text", placeholder="Nova categoria", id="input-add-receita", value=""),
                                        html.Br(),
                                        dbc.Button("Adicionar", class_name="btn btn-success", id="add-category-receita", style={"margin-top": "20px"}),
                                        html.Br(),
                                        html.Div(id="category-div-add-receita", style={}),
                                    ], xs=12, md=6),

                                    dbc.Col([
                                        html.Legend('Excluir categorias', style={'color': 'red'}),
                                        dbc.Checklist(
                                            id='checklist-selected-style-receita',
                                            options=_opcoes(cat_receita),
                                            value=[],
                                            label_checked_style={'color': 'red'},
                                            input_checked_style={'backgroundColor': 'blue', 'borderColor': 'orange'},
                                        ),
                                        dbc.Button('Remover', color='warning', id='remove-category-receita', style={'margin-top': '20px'}),
                                    ], xs=12, md=6)
                                ])
                            ], title='Adicionar/Remover Categorias')
                        ], flush=True, start_collapsed=True, id='accordion-receita')
                    ], style={'margin-top': '25px'}),

                    html.Div(id='id_teste_receita', style={'padding-top': '20px'}),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Adicionar Receita", id='salvar_receita', color='success'),
                    dbc.Popover(dbc.PopoverBody("Receita Salva"), target="salvar_receita", placement="left", trigger="click"),
                ])
            ], style={"background-color": "rgba(17, 140, 79, 0.05)"},
            id="modal-novo-receita",
            size='lg',
            is_open=False,
            centered=True,
            backdrop=True),

            # Modal Despesa
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle('Adicionar despesa')),
                dbc.ModalBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label('Descrição:'),
                            dbc.Input(placeholder="Ex.: Supermercado, Combustível...", id="txt-despesa"),
                        ], xs=12, md=6),
                        dbc.Col([
                            dbc.Label("Valor:"),
                            dbc.Input(placeholder="R$ 100.00", id="valor_despesa", value="", type="number", step="0.01")
                        ], xs=12, md=6)
                    ]),

                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Data:"),
                            dcc.DatePickerSingle(
                                id="date-despesas",
                                min_date_allowed=date(2025, 1, 1),
                                max_date_allowed=date(2035, 12, 31),
                                date=datetime.today(),
                                style={"width": "100%"}
                            ),
                        ], xs=12, md=3),

                        dbc.Col([
                            dbc.Label("Extras"),
                            dbc.Checklist(
                                options=[
                                    {"label": "Foi paga", "value": 1},
                                    {"label": "Despesa Recorrente", "value": 2}
                                ],
                                value=[1],
                                id='switches-input-despesa',
                                switch=True
                            )
                        ], xs=12, md=3),

                        dbc.Col([
                            html.Label('Categoria da despesa'),
                            dbc.Select(
                                id='select_despesa',
                                options=_opcoes(cat_despesa),
                                value=cat_despesa[0] if cat_despesa else None
                            )
                        ], xs=12, md=3),

                        dbc.Col([
                            html.Label('Regra 50-30-20'),
                            dbc.Select(
                                id='select-regra-despesa',
                                options=_opcoes_regra(cat_regra),
                                value='Necessidades'
                            )
                        ], xs=12, md=3)
                    ], style={'margin-top': '25px'}),

                    dbc.Row([
                        dbc.Accordion([
                            dbc.AccordionItem(children=[
                                dbc.Row([
                                    dbc.Col([
                                        html.Legend('Adicionar categoria', style={'color': 'green'}),
                                        dbc.Input(type="Text", placeholder="Nova categoria", id="input-add-despesa", value=""),
                                        html.Br(),
                                        dbc.Button("Adicionar", class_name="btn btn-success", id="add-category-despesa", style={"margin-top": "20px"}),
                                        html.Br(),
                                        html.Div(id="category-div-add-despesa", style={}),
                                    ], xs=12, md=6),

                                    dbc.Col([
                                        html.Legend('Excluir categorias', style={'color': 'red'}),
                                        dbc.Checklist(
                                            id='checklist-selected-style-despesa',
                                            options=_opcoes(cat_despesa),
                                            value=[],
                                            label_checked_style={'color': 'red'},
                                            input_checked_style={'backgroundColor': 'blue', 'borderColor': 'orange'},
                                        ),
                                        dbc.Button('Remover', color='warning', id='remove-category-despesa', style={'margin-top': '20px'}),
                                    ], xs=12, md=6)
                                ])
                            ], title='Adicionar/Remover Categorias')
                        ], flush=True, start_collapsed=True, id='accordion-despesa')
                    ], style={'margin-top': '25px'}),

                    html.Div(id='id_teste_despesa', style={'padding-top': '20px'}),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Adicionar Despesa", id='salvar_despesa', color='danger'),
                    dbc.Popover(dbc.PopoverBody("Despesa Salva"), target="salvar_despesa", placement="left", trigger="click"),
                ])
            ],
            id="modal-novo-despesa",
            size='lg',
            is_open=False,
            centered=True,
            backdrop=True),

            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink("Dashboard", href="/dashboards", active="exact"),
                    dbc.NavLink("Extratos", href="/extratos", active="exact"),
                    dbc.NavLink("Regra 50-30-20", href="/regra-orcamento", active="exact")
                ],
                vertical=True,
                pills=True,
                id='nav_buttons',
                style={'margin-bottom': "50px"})

        ], width=12)
    ])
], fluid=True, id='sidebar_completa')


# ========= CALLBACKS ========= #
@app.callback(
    Output('modal-novo-receita', 'is_open'),
    Input('open-novo-receita', 'n_clicks'),
    State('modal-novo-receita', 'is_open')
)
def toggle_modal_receita(n1, is_open):
    if n1:
        return not is_open
    return is_open


@app.callback(
    Output('modal-novo-despesa', 'is_open'),
    Input('open-novo-despesa', 'n_clicks'),
    State('modal-novo-despesa', 'is_open')
)
def toggle_modal_despesa(n1, is_open):
    if n1:
        return not is_open
    return is_open


@app.callback(
     Output('store-receitas', 'data'),
     Input('salvar_receita', 'n_clicks'),
    [
        State('txt-receita', 'value'),
        State('valor_receita', 'value'),
        State('date-receitas','date'),
        State('switches-input-receita', 'value'),
        State('select_receita', 'value'),
        State('select-regra-receita', 'value'),
        State('store-receitas', 'data')
    ]
)
def salve_form_receita(n, descricao, valor, data, switches, categoria, regra, dict_receitas):
    if n and valor not in ["", None]:
        valor = round(float(valor), 2)
        data = pd.to_datetime(data).date() if data else datetime.today().date()
        efetuado = 1 if switches and 1 in switches else 0
        fixo = 1 if switches and 2 in switches else 0

        criar_receita(
            valor=valor,
            efetuado=efetuado,
            fixo=fixo,
            data=data,
            categoria=categoria or "Sem categoria",
            descricao=descricao or "Sem descrição",
            regra=regra or "Necessidades",
        )

    return listar_receitas().to_dict("records")


@app.callback(
     Output('store-despesas', 'data'),
     Input('salvar_despesa', 'n_clicks'),
    [
        State('txt-despesa', 'value'),
        State('valor_despesa', 'value'),
        State('date-despesas','date'),
        State('switches-input-despesa', 'value'),
        State('select_despesa', 'value'),
        State('select-regra-despesa', 'value'),
        State('store-despesas', 'data')
    ]
)
def salve_form_despesa(n, descricao, valor, data, switches, categoria, regra, dict_despesas):
    if n and valor not in ["", None]:
        valor = round(float(valor), 2)
        data = pd.to_datetime(data).date() if data else datetime.today().date()
        efetuado = 1 if switches and 1 in switches else 0
        fixo = 1 if switches and 2 in switches else 0

        criar_despesa(
            valor=valor,
            efetuado=efetuado,
            fixo=fixo,
            data=data,
            categoria=categoria or "Sem categoria",
            descricao=descricao or "Sem descrição",
            regra=regra or "Necessidades",
        )

    return listar_despesas().to_dict("records")


@app.callback(
    [Output("select_receita", "options"),
     Output('checklist-selected-style-receita', 'options'),
     Output('checklist-selected-style-receita', 'value'),
     Output('stored-cat-receitas', 'data')],
    [Input("add-category-receita", "n_clicks"),
     Input('remove-category-receita', "n_clicks")],
    [State("input-add-receita", "value"),
     State("checklist-selected-style-receita", 'value'),
     State('stored-cat-receitas', 'data')]
)
def update_categoria_receita(n_add, n_remove, nova_categoria, categorias_remover, data_atual):
    categorias = list(pd.DataFrame(data_atual)["Categoria"]) if data_atual else []

    botao_acionado = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else None

    if botao_acionado == "add-category-receita" and nova_categoria:
        nova_categoria = nova_categoria.strip()
        if nova_categoria and nova_categoria not in categorias:
            categorias.append(nova_categoria)

    elif botao_acionado == "remove-category-receita" and categorias_remover:
        categorias = [item for item in categorias if item not in categorias_remover]

    df_cat_receita = substituir_categorias_receitas(categorias)
    opcoes = _opcoes(df_cat_receita["Categoria"].tolist())
    return opcoes, opcoes, [], df_cat_receita.to_dict("records")


@app.callback(
    [Output("select_despesa", "options"),
     Output('checklist-selected-style-despesa', 'options'),
     Output('checklist-selected-style-despesa', 'value'),
     Output('stored-cat-despesas', 'data')],
    [Input("add-category-despesa", "n_clicks"),
     Input('remove-category-despesa', "n_clicks")],
    [State("input-add-despesa", "value"),
     State("checklist-selected-style-despesa", 'value'),
     State('stored-cat-despesas', 'data')]
)
def update_categoria_despesa(n_add, n_remove, nova_categoria, categorias_remover, data_atual):
    categorias = list(pd.DataFrame(data_atual)["Categoria"]) if data_atual else []

    botao_acionado = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else None

    if botao_acionado == "add-category-despesa" and nova_categoria:
        nova_categoria = nova_categoria.strip()
        if nova_categoria and nova_categoria not in categorias:
            categorias.append(nova_categoria)

    elif botao_acionado == "remove-category-despesa" and categorias_remover:
        categorias = [item for item in categorias if item not in categorias_remover]

    df_cat_despesa = substituir_categorias_despesas(categorias)
    opcoes = _opcoes(df_cat_despesa["Categoria"].tolist())
    return opcoes, opcoes, [], df_cat_despesa.to_dict("records")
