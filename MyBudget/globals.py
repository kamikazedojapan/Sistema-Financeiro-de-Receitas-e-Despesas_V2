import pandas as pd
from database import (
    listar_receitas,
    listar_despesas,
    listar_categorias_receitas,
    listar_categorias_despesas,
    CATEGORIAS_REGRA_PADRAO,
)

COLUNAS = ["id", "Valor", "Efetuado", "Fixo", "Data", "Categoria", "Descrição", "Regra"]
cat_regra = CATEGORIAS_REGRA_PADRAO.copy()


def carregar_dados():
    global df_receitas, df_despesas, df_cat_receita, df_cat_despesa, cat_receita, cat_despesa

    df_receitas = listar_receitas()
    df_despesas = listar_despesas()
    df_cat_receita = listar_categorias_receitas()
    df_cat_despesa = listar_categorias_despesas()

    cat_receita = df_cat_receita["Categoria"].tolist()
    cat_despesa = df_cat_despesa["Categoria"].tolist()

    return df_receitas, df_despesas


carregar_dados()
