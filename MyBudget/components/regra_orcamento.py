from datetime import datetime

from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app import app
from database import (
    carregar_regra_orcamento,
    salvar_regra_orcamento,
    listar_receitas,
    listar_despesas,
)

regra_atual = carregar_regra_orcamento()

MESES = [
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
]

# A lógica interna continua usando "Necessidades".
# Somente a tela exibe "Custos", conforme solicitado.
NOME_TELA = {
    "Necessidades": "Custos",
    "Desejos": "Desejos",
    "Investimentos": "Investimentos",
}

CORES_TELA = {
    "Necessidades": "#2f80ed",
    "Desejos": "#ff7a00",
    "Investimentos": "#2eaf41",
}


def _formatar_moeda(valor):
    valor = float(valor or 0)
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _filtrar_mes(df, mes, ano):
    """Filtra receitas/despesas pelo mês e ano selecionados."""
    df = pd.DataFrame(df).copy()

    if df.empty or "Data" not in df.columns:
        return df

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Valor"] = pd.to_numeric(df.get("Valor", 0), errors="coerce").fillna(0)

    return df[
        (df["Data"].dt.month == mes) &
        (df["Data"].dt.year == ano)
    ]


def _normalizar_regra(df):
    """Garante compatibilidade caso algum registro antigo use Custos na coluna Regra."""
    df = pd.DataFrame(df).copy()

    if df.empty:
        return df

    if "Regra" not in df.columns:
        df["Regra"] = "Necessidades"

    df["Regra"] = (
        df["Regra"]
        .fillna("Necessidades")
        .replace({"Custos": "Necessidades", "Custo": "Necessidades"})
    )

    return df



def _periodo_mes(data):
    """Converte uma data para período mensal do pandas."""
    data = pd.to_datetime(data, errors="coerce")
    if pd.isna(data):
        return None
    return data.to_period("M")


def _calcular_orcamento_com_acumulado(df_receitas, df_despesas, mes, ano, percentuais):
    """Calcula limite base, acumulado anterior, limite total e gasto por divisão.

    Regra de negócio:
    - O limite base é calculado pela última receita bruta válida.
    - Se o mês selecionado não tiver receita, usa a última receita positiva anterior.
    - O valor não gasto em cada divisão no mês anterior é transferido para a mesma divisão do mês seguinte.
    - O acumulado é individual por divisão: Custos não vira Desejos, Desejos não vira Investimentos.
    - Se uma divisão estourar o limite, o excedente é exibido, mas não gera acumulado negativo no mês seguinte.
    """
    df_receitas = pd.DataFrame(df_receitas).copy()
    df_despesas = _normalizar_regra(df_despesas)

    periodo_alvo = pd.Period(year=int(ano), month=int(mes), freq="M")

    for df in [df_receitas, df_despesas]:
        if not df.empty and "Data" in df.columns:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
            df["Valor"] = pd.to_numeric(df.get("Valor", 0), errors="coerce").fillna(0)
            df["Periodo"] = df["Data"].dt.to_period("M")

    periodos = [periodo_alvo]

    if not df_receitas.empty and "Periodo" in df_receitas.columns:
        periodos.extend(df_receitas.loc[df_receitas["Periodo"].notna(), "Periodo"].tolist())

    if not df_despesas.empty and "Periodo" in df_despesas.columns:
        periodos.extend(df_despesas.loc[df_despesas["Periodo"].notna(), "Periodo"].tolist())

    periodos = [p for p in periodos if p is not None and p <= periodo_alvo]
    periodo_inicial = min(periodos) if periodos else periodo_alvo

    acumulado_anterior = {categoria: 0.0 for categoria in percentuais.keys()}
    ultima_receita_valida = 0.0
    resultado_alvo = None

    for periodo in pd.period_range(periodo_inicial, periodo_alvo, freq="M"):
        if not df_receitas.empty and "Periodo" in df_receitas.columns:
            receita_mes = float(df_receitas.loc[df_receitas["Periodo"] == periodo, "Valor"].sum())
        else:
            receita_mes = 0.0

        if receita_mes > 0:
            ultima_receita_valida = receita_mes

        receita_referencia = receita_mes if receita_mes > 0 else ultima_receita_valida

        if not df_despesas.empty and "Periodo" in df_despesas.columns:
            despesas_mes = df_despesas[df_despesas["Periodo"] == periodo]
        else:
            despesas_mes = pd.DataFrame(columns=["Regra", "Valor"])

        if despesas_mes.empty or "Valor" not in despesas_mes.columns:
            gastos_series = pd.Series(dtype="float64")
        else:
            gastos_series = despesas_mes.groupby("Regra")["Valor"].sum()

        dados_mes = {}
        proximo_acumulado = {}

        for categoria, percentual in percentuais.items():
            limite_base = receita_referencia * (float(percentual) / 100)
            acumulado_cat = acumulado_anterior.get(categoria, 0.0)
            limite_total = limite_base + acumulado_cat
            gasto = float(gastos_series.get(categoria, 0.0))
            diferenca = limite_total - gasto

            dados_mes[categoria] = {
                "percentual": float(percentual),
                "receita_mes": receita_mes,
                "receita_referencia": receita_referencia,
                "limite_base": limite_base,
                "acumulado_anterior": acumulado_cat,
                "limite_total": limite_total,
                "gasto": gasto,
                "diferenca": diferenca,
                "pode_gastar": max(diferenca, 0.0),
                "excedeu": abs(diferenca) if diferenca < 0 else 0.0,
            }

            proximo_acumulado[categoria] = max(diferenca, 0.0)

        if periodo == periodo_alvo:
            resultado_alvo = {
                "periodo": periodo,
                "receita_mes": receita_mes,
                "receita_referencia": receita_referencia,
                "acumulado_total_anterior": sum(acumulado_anterior.values()),
                "categorias": dados_mes,
            }

        acumulado_anterior = proximo_acumulado

    return resultado_alvo or {
        "periodo": periodo_alvo,
        "receita_mes": 0.0,
        "receita_referencia": 0.0,
        "acumulado_total_anterior": 0.0,
        "categorias": {},
    }

def _grafico_vazio(titulo):
    fig = go.Figure()
    fig.add_annotation(
        text="Sem dados para exibir",
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=16),
    )
    fig.update_layout(
        title=titulo,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=360,
    )
    return fig


def _grafico_donut(percentual, cor):
    """Cria um mini gráfico em rosca para o percentual já utilizado da divisão."""
    usado = max(min(float(percentual or 0), 100), 0)
    restante = max(100 - usado, 0)

    fig = go.Figure(
        data=[
            go.Pie(
                values=[usado, restante],
                labels=["Usado", "Livre"],
                hole=0.70,
                sort=False,
                direction="clockwise",
                marker=dict(colors=[cor, "#e9ecef"]),
                textinfo="none",
                hoverinfo="skip",
                showlegend=False,
            )
        ]
    )

    fig.add_annotation(
        text=f"{percentual:.2f}%<br><span style='font-size:11px'>usado</span>",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=15),
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=120,
        width=120,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def _card_regra(categoria_logica, dados):
    """Monta o card de cada divisão da regra com acumulado por categoria."""
    nome_tela = NOME_TELA[categoria_logica]
    cor = CORES_TELA[categoria_logica]

    percentual = dados["percentual"]
    limite_base = dados["limite_base"]
    acumulado_anterior = dados["acumulado_anterior"]
    limite_total = dados["limite_total"]
    gasto = dados["gasto"]
    diferenca = dados["diferenca"]
    percentual_usado = (gasto / limite_total * 100) if limite_total > 0 else 0

    if diferenca >= 0:
        mensagem_final = html.P(
            f"Pode gastar: {_formatar_moeda(diferenca)}",
            style={"color": "green", "fontWeight": "600", "margin": "0"},
        )
    else:
        mensagem_final = html.P(
            f"Excedeu: {_formatar_moeda(abs(diferenca))}",
            style={"color": "red", "fontWeight": "600", "margin": "0"},
        )

    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H4(nome_tela, style={"color": cor}),
                    html.P(f"Gasto: {_formatar_moeda(gasto)}", style={"margin": "0"}),
                    html.P(
                        f"Limite base ({percentual:g}%): {_formatar_moeda(limite_base)}",
                        style={"margin": "0"},
                    ),
                    html.P(
                        f"Acumulado anterior: {_formatar_moeda(acumulado_anterior)}",
                        style={"margin": "0"},
                    ),
                    html.P(
                        f"Limite total: {_formatar_moeda(limite_total)}",
                        style={"margin": "0", "fontWeight": "600"},
                    ),
                    mensagem_final,
                ], xs=8),
                dbc.Col([
                    dcc.Graph(
                        figure=_grafico_donut(percentual_usado, cor),
                        config={"displayModeBar": False},
                        style={"height": "120px"},
                    )
                ], xs=4, className="d-flex justify-content-end align-items-center"),
            ])
        ]),
        style={
            "borderLeft": f"5px solid {cor}",
            "minHeight": "190px",
        },
        className="mb-3",
    )


layout = dbc.Container([

    html.H3("Regra de Orçamento Mensal"),
    html.Hr(),

    html.P(
        "A regra pode ser ajustada livremente, desde que a soma das três divisões seja 100%."
    ),

    dbc.Row([
        dbc.Col([
            dbc.Label("Mês"),
            dcc.Dropdown(
                id="dropdown-mes-regra",
                options=MESES,
                value=datetime.now().month,
                clearable=False,
            )
        ], xs=12, md=6),

        dbc.Col([
            dbc.Label("Ano"),
            dcc.Dropdown(
                id="dropdown-ano-regra",
                options=[
                    {"label": str(ano), "value": ano}
                    for ano in range(2020, datetime.now().year + 2)
                ],
                value=datetime.now().year,
                clearable=False,
            )
        ], xs=12, md=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Label("Custos (%)"),
            dbc.Input(
                id="input-necessidades",
                type="number",
                value=regra_atual["necessidades"],
                min=0,
                max=100,
                step=1,
                class_name="form-control",
            )
        ], xs=12, md=4),

        dbc.Col([
            dbc.Label("Desejos (%)"),
            dbc.Input(
                id="input-desejos",
                type="number",
                value=regra_atual["desejos"],
                min=0,
                max=100,
                step=1,
                className="form-control",
            ),
        ], xs=12, md=4),

        dbc.Col([
            dbc.Label("Investimentos (%)"),
            dbc.Input(
                id="input-investimentos",
                type="number",
                value=regra_atual["investimentos"],
                min=0,
                max=100,
                step=1,
                className="form-control",
            )
        ], xs=12, md=4),
    ], className="mb-4"),

    html.Div(id="alerta-regra-orcamento"),

    dbc.Row([
        dbc.Col(html.Div(id="card-necessidades"), xs=12, lg=4),
        dbc.Col(html.Div(id="card-desejos"), xs=12, lg=4),
        dbc.Col(html.Div(id="card-investimentos"), xs=12, lg=4),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id="grafico-regra-orcamento")
        ], xs=12, lg=6),

        dbc.Col([
            dcc.Graph(id="grafico-consumo-regra-orcamento")
        ], xs=12, lg=6),
    ]),

    dbc.Alert(
        "Os valores são calculados com base na receita bruta mensal e nos gastos categorizados pela regra no período selecionado.",
        color="info",
        className="mt-3",
    )
], fluid=True)


@app.callback(
    Output("card-necessidades", "children"),
    Output("card-desejos", "children"),
    Output("card-investimentos", "children"),
    Output("grafico-regra-orcamento", "figure"),
    Output("grafico-consumo-regra-orcamento", "figure"),
    Output("alerta-regra-orcamento", "children"),
    Input("store-receitas", "data"),
    Input("store-despesas", "data"),
    Input("input-necessidades", "value"),
    Input("input-desejos", "value"),
    Input("input-investimentos", "value"),
    Input("dropdown-mes-regra", "value"),
    Input("dropdown-ano-regra", "value"),
)
def atualizar_regra_orcamento(
    receitas,
    despesas,
    necessidades,
    desejos,
    investimentos,
    mes,
    ano,
):
    """Atualiza a página da regra 50-30-20 com acumulado mensal.

    Fórmula:
    limite_base = última receita bruta válida * percentual da divisão
    limite_total = limite_base + sobra da mesma divisão no mês anterior
    pode_gastar/excedeu = limite_total - gasto atual da divisão
    """

    necessidades = necessidades or 0
    desejos = desejos or 0
    investimentos = investimentos or 0
    soma = necessidades + desejos + investimentos

    if soma != 100:
        fig_distribuicao = _grafico_vazio("Distribuição inválida")
        fig_consumo = _grafico_vazio("Quanto falta para gastar em cada divisão")
        alerta = dbc.Alert(
            "A soma dos percentuais precisa ser exatamente 100%.",
            color="danger",
        )

        return (
            dbc.Alert("Ajuste a regra para calcular custos.", color="warning"),
            dbc.Alert("Ajuste a regra para calcular desejos.", color="warning"),
            dbc.Alert("Ajuste a regra para calcular investimentos.", color="warning"),
            fig_distribuicao,
            fig_consumo,
            alerta,
        )

    salvar_regra_orcamento(necessidades, desejos, investimentos)

    # SQLite é a fonte de verdade. Os Stores apenas disparam atualização.
    df_receitas = listar_receitas()
    df_despesas = listar_despesas()
    df_despesas = _normalizar_regra(df_despesas)

    percentuais = {
        "Necessidades": necessidades,
        "Desejos": desejos,
        "Investimentos": investimentos,
    }

    orcamento = _calcular_orcamento_com_acumulado(
        df_receitas=df_receitas,
        df_despesas=df_despesas,
        mes=mes,
        ano=ano,
        percentuais=percentuais,
    )

    categorias = orcamento["categorias"]
    receita_mes = orcamento["receita_mes"]
    receita_referencia = orcamento["receita_referencia"]
    acumulado_total_anterior = orcamento["acumulado_total_anterior"]

    card_necessidades = _card_regra("Necessidades", categorias["Necessidades"])
    card_desejos = _card_regra("Desejos", categorias["Desejos"])
    card_investimentos = _card_regra("Investimentos", categorias["Investimentos"])

    df_distribuicao = pd.DataFrame({
        "Categoria": [
            f"Custos ({necessidades}%)",
            f"Desejos ({desejos}%)",
            f"Investimentos ({investimentos}%)",
        ],
        "Valor": [
            categorias["Necessidades"]["limite_base"],
            categorias["Desejos"]["limite_base"],
            categorias["Investimentos"]["limite_base"],
        ],
        "Percentual": [necessidades, desejos, investimentos],
    })

    if receita_referencia <= 0:
        fig_distribuicao = _grafico_vazio("Distribuição do Orçamento Mensal")
    else:
        df_distribuicao["Texto"] = df_distribuicao.apply(
            lambda linha: f"{linha['Percentual']}%<br>{_formatar_moeda(linha['Valor'])}",
            axis=1,
        )

        fig_distribuicao = px.pie(
            df_distribuicao,
            names="Categoria",
            values="Valor",
            title="Distribuição do Orçamento Mensal",
            custom_data=["Texto"],
            color="Categoria",
        )

        fig_distribuicao.update_traces(
            textposition="inside",
            textinfo="percent",
            texttemplate="%{customdata[0]}",
            hovertemplate="%{label}<br>%{customdata[0]}<extra></extra>",
        )

        fig_distribuicao.update_layout(
            legend_title_text="Divisão",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
        )

    dados_saldo_regra = []
    for categoria in ["Necessidades", "Desejos", "Investimentos"]:
        dados = categorias[categoria]
        diferenca = dados["diferenca"]
        nome_tela = NOME_TELA[categoria]

        if diferenca >= 0:
            status = "Pode gastar"
            valor = diferenca
            texto = _formatar_moeda(valor)
        else:
            status = "Excedeu"
            valor = diferenca
            texto = f"-{_formatar_moeda(abs(diferenca))}"

        dados_saldo_regra.append({
            "Divisão": nome_tela,
            "Status": status,
            "Valor": valor,
            "Texto": texto,
        })

    df_saldo_regra = pd.DataFrame(dados_saldo_regra)

    fig_consumo = px.bar(
        df_saldo_regra,
        x="Divisão",
        y="Valor",
        color="Status",
        text="Texto",
        title="Quanto falta para gastar em cada divisão",
    )

    fig_consumo.update_traces(textposition="outside")
    fig_consumo.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_consumo.update_layout(
        xaxis_title="",
        yaxis_title="Valor (R$)",
        legend_title_text="Status",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=380,
    )

    alerta = dbc.Alert(
        (
            f"Regra atual salva no banco: {necessidades}-{desejos}-{investimentos}. "
            f"Receita bruta no mês: {_formatar_moeda(receita_mes)}. "
            f"Receita base usada: {_formatar_moeda(receita_referencia)}. "
            f"Acumulado do mês anterior: {_formatar_moeda(acumulado_total_anterior)}."
        ),
        color="success",
    )

    return (
        card_necessidades,
        card_desejos,
        card_investimentos,
        fig_distribuicao,
        fig_consumo,
        alerta,
    )
