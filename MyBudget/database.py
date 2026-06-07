from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "financeiro.db"

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

COLUNAS_CATEGORIAS = ["id", "Categoria"]

CATEGORIAS_RECEITAS_PADRAO = ["Salário", "Investimento"]
CATEGORIAS_DESPESAS_PADRAO = [
    "Alimentação",
    "Energia",
    "Internet",
    "Saúde",
    "Transporte",
    "Estudo",
    "Lazer",
    "Quarto",
    "Tatuagens",
    "Perfumes",
    "Acessórios",
    "Desejos",
    "Jogos",
]

CATEGORIAS_REGRA_PADRAO = ["Necessidades", "Desejos", "Investimentos"]


def conectar():
    return sqlite3.connect(DB_PATH)


def inicializar_banco():
    """Cria as tabelas principais e as categorias padrão.

    O banco SQLite é a única fonte de armazenamento do sistema.
    CSVs/planilhas não são mais lidos nem atualizados pela aplicação.
    """
    with conectar() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Valor REAL NOT NULL DEFAULT 0,
                Efetuado INTEGER NOT NULL DEFAULT 0,
                Fixo INTEGER NOT NULL DEFAULT 0,
                Data TEXT NOT NULL,
                Categoria TEXT NOT NULL,
                Descrição TEXT NOT NULL,
                Regra TEXT NOT NULL DEFAULT 'Necessidades'
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS despesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Valor REAL NOT NULL DEFAULT 0,
                Efetuado INTEGER NOT NULL DEFAULT 0,
                Fixo INTEGER NOT NULL DEFAULT 0,
                Data TEXT NOT NULL,
                Categoria TEXT NOT NULL,
                Descrição TEXT NOT NULL,
                Regra TEXT NOT NULL DEFAULT 'Necessidades'
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categorias_receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Categoria TEXT NOT NULL UNIQUE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categorias_despesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Categoria TEXT NOT NULL UNIQUE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS regra_orcamento (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                necessidades INTEGER NOT NULL DEFAULT 50,
                desejos INTEGER NOT NULL DEFAULT 30,
                investimentos INTEGER NOT NULL DEFAULT 20
            )
            """
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO regra_orcamento
            (id, necessidades, desejos, investimentos)
            VALUES (1, 50, 30, 20)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sistema_config (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
            """
        )

        seed_status = dict(
            cursor.execute("SELECT chave, valor FROM sistema_config").fetchall()
        )

        # As categorias padrão devem ser criadas apenas uma vez.
        # Antes, elas eram reinseridas em toda chamada de inicializar_banco(),
        # então uma categoria padrão removida pelo usuário voltava automaticamente.
        if seed_status.get("categorias_receitas_inicializadas") != "1":
            total_receitas = cursor.execute(
                "SELECT COUNT(*) FROM categorias_receitas"
            ).fetchone()[0]

            if total_receitas == 0:
                for categoria in CATEGORIAS_RECEITAS_PADRAO:
                    cursor.execute(
                        "INSERT OR IGNORE INTO categorias_receitas (Categoria) VALUES (?)",
                        (categoria,),
                    )

            cursor.execute(
                "INSERT OR REPLACE INTO sistema_config (chave, valor) VALUES (?, ?)",
                ("categorias_receitas_inicializadas", "1"),
            )

        if seed_status.get("categorias_despesas_inicializadas") != "1":
            total_despesas = cursor.execute(
                "SELECT COUNT(*) FROM categorias_despesas"
            ).fetchone()[0]

            if total_despesas == 0:
                for categoria in CATEGORIAS_DESPESAS_PADRAO:
                    cursor.execute(
                        "INSERT OR IGNORE INTO categorias_despesas (Categoria) VALUES (?)",
                        (categoria,),
                    )

            cursor.execute(
                "INSERT OR REPLACE INTO sistema_config (chave, valor) VALUES (?, ?)",
                ("categorias_despesas_inicializadas", "1"),
            )

        conn.commit()


def _normalizar_movimentacoes(df):
    df = pd.DataFrame(df).copy()

    for coluna in COLUNAS_MOVIMENTACOES:
        if coluna not in df.columns:
            if coluna == "id":
                df[coluna] = None
            elif coluna == "Valor":
                df[coluna] = 0.0
            elif coluna in ["Efetuado", "Fixo"]:
                df[coluna] = 0
            elif coluna == "Regra":
                df[coluna] = "Necessidades"
            else:
                df[coluna] = ""

    if df.empty:
        return pd.DataFrame(columns=COLUNAS_MOVIMENTACOES)

    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
    df["Efetuado"] = pd.to_numeric(df["Efetuado"], errors="coerce").fillna(0).astype(int)
    df["Fixo"] = pd.to_numeric(df["Fixo"], errors="coerce").fillna(0).astype(int)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").fillna(pd.Timestamp.today()).dt.strftime("%Y-%m-%d")
    df["Categoria"] = df["Categoria"].fillna("Sem categoria").astype(str)
    df["Descrição"] = df["Descrição"].fillna("Sem descrição").astype(str)
    df["Regra"] = (
        df["Regra"]
        .fillna("Necessidades")
        .astype(str)
        .replace({"Custos": "Necessidades", "Custo": "Necessidades"})
    )

    return df[COLUNAS_MOVIMENTACOES]


def _id_valido(valor):
    try:
        if pd.isna(valor):
            return None
        return int(valor)
    except (TypeError, ValueError):
        return None


def listar_receitas():
    inicializar_banco()
    with conectar() as conn:
        df = pd.read_sql_query("SELECT * FROM receitas ORDER BY Data DESC, id DESC", conn)
    return _normalizar_movimentacoes(df)


def listar_despesas():
    inicializar_banco()
    with conectar() as conn:
        df = pd.read_sql_query("SELECT * FROM despesas ORDER BY Data DESC, id DESC", conn)
    return _normalizar_movimentacoes(df)


def criar_receita(valor, efetuado, fixo, data, categoria, descricao, regra):
    inicializar_banco()
    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO receitas
            (Valor, Efetuado, Fixo, Data, Categoria, Descrição, Regra)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (float(valor), int(efetuado), int(fixo), str(data), categoria, descricao, regra),
        )
        conn.commit()


def criar_despesa(valor, efetuado, fixo, data, categoria, descricao, regra):
    inicializar_banco()
    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO despesas
            (Valor, Efetuado, Fixo, Data, Categoria, Descrição, Regra)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (float(valor), int(efetuado), int(fixo), str(data), categoria, descricao, regra),
        )
        conn.commit()


def atualizar_receita(id, valor, efetuado, fixo, data, categoria, descricao, regra):
    inicializar_banco()
    with conectar() as conn:
        conn.execute(
            """
            UPDATE receitas
            SET Valor = ?, Efetuado = ?, Fixo = ?, Data = ?, Categoria = ?, Descrição = ?, Regra = ?
            WHERE id = ?
            """,
            (float(valor), int(efetuado), int(fixo), str(data), categoria, descricao, regra, int(id)),
        )
        conn.commit()


def atualizar_despesa(id, valor, efetuado, fixo, data, categoria, descricao, regra):
    inicializar_banco()
    with conectar() as conn:
        conn.execute(
            """
            UPDATE despesas
            SET Valor = ?, Efetuado = ?, Fixo = ?, Data = ?, Categoria = ?, Descrição = ?, Regra = ?
            WHERE id = ?
            """,
            (float(valor), int(efetuado), int(fixo), str(data), categoria, descricao, regra, int(id)),
        )
        conn.commit()


def remover_receita(id):
    inicializar_banco()
    with conectar() as conn:
        conn.execute("DELETE FROM receitas WHERE id = ?", (int(id),))
        conn.commit()


def remover_despesa(id):
    inicializar_banco()
    with conectar() as conn:
        conn.execute("DELETE FROM despesas WHERE id = ?", (int(id),))
        conn.commit()


def sincronizar_receitas(registros):
    """Sincroniza a tabela visual de receitas com o SQLite.

    - Linhas existentes com id são atualizadas.
    - Linhas removidas da DataTable são removidas do banco.
    - Linhas sem id válido são criadas como novas receitas.
    """
    inicializar_banco()
    registros_df = _normalizar_movimentacoes(pd.DataFrame(registros or []))

    with conectar() as conn:
        ids_banco = {
            linha[0]
            for linha in conn.execute("SELECT id FROM receitas").fetchall()
        }

    ids_tabela = set()

    for _, linha in registros_df.iterrows():
        id_atual = _id_valido(linha["id"])
        if id_atual and id_atual in ids_banco:
            ids_tabela.add(id_atual)
            atualizar_receita(
                id_atual,
                linha["Valor"],
                linha["Efetuado"],
                linha["Fixo"],
                linha["Data"],
                linha["Categoria"],
                linha["Descrição"],
                linha["Regra"],
            )
        else:
            criar_receita(
                linha["Valor"],
                linha["Efetuado"],
                linha["Fixo"],
                linha["Data"],
                linha["Categoria"],
                linha["Descrição"],
                linha["Regra"],
            )

    for id_removido in ids_banco - ids_tabela:
        remover_receita(id_removido)

    return listar_receitas()


def sincronizar_despesas(registros):
    """Sincroniza a tabela visual de despesas com o SQLite.

    - Linhas existentes com id são atualizadas.
    - Linhas removidas da DataTable são removidas do banco.
    - Linhas sem id válido são criadas como novas despesas.
    """
    inicializar_banco()
    registros_df = _normalizar_movimentacoes(pd.DataFrame(registros or []))

    with conectar() as conn:
        ids_banco = {
            linha[0]
            for linha in conn.execute("SELECT id FROM despesas").fetchall()
        }

    ids_tabela = set()

    for _, linha in registros_df.iterrows():
        id_atual = _id_valido(linha["id"])
        if id_atual and id_atual in ids_banco:
            ids_tabela.add(id_atual)
            atualizar_despesa(
                id_atual,
                linha["Valor"],
                linha["Efetuado"],
                linha["Fixo"],
                linha["Data"],
                linha["Categoria"],
                linha["Descrição"],
                linha["Regra"],
            )
        else:
            criar_despesa(
                linha["Valor"],
                linha["Efetuado"],
                linha["Fixo"],
                linha["Data"],
                linha["Categoria"],
                linha["Descrição"],
                linha["Regra"],
            )

    for id_removido in ids_banco - ids_tabela:
        remover_despesa(id_removido)

    return listar_despesas()


def listar_categorias_receitas():
    inicializar_banco()
    with conectar() as conn:
        df = pd.read_sql_query("SELECT * FROM categorias_receitas ORDER BY Categoria", conn)
    return df if not df.empty else pd.DataFrame(columns=COLUNAS_CATEGORIAS)


def listar_categorias_despesas():
    inicializar_banco()
    with conectar() as conn:
        df = pd.read_sql_query("SELECT * FROM categorias_despesas ORDER BY Categoria", conn)
    return df if not df.empty else pd.DataFrame(columns=COLUNAS_CATEGORIAS)


def substituir_categorias_receitas(categorias):
    categorias = [str(c).strip() for c in categorias if str(c).strip()]
    inicializar_banco()
    with conectar() as conn:
        conn.execute("DELETE FROM categorias_receitas")
        conn.executemany(
            "INSERT OR IGNORE INTO categorias_receitas (Categoria) VALUES (?)",
            [(c,) for c in categorias],
        )
        conn.commit()
    return listar_categorias_receitas()


def substituir_categorias_despesas(categorias):
    categorias = [str(c).strip() for c in categorias if str(c).strip()]
    inicializar_banco()
    with conectar() as conn:
        conn.execute("DELETE FROM categorias_despesas")
        conn.executemany(
            "INSERT OR IGNORE INTO categorias_despesas (Categoria) VALUES (?)",
            [(c,) for c in categorias],
        )
        conn.commit()
    return listar_categorias_despesas()


def carregar_regra_orcamento():
    inicializar_banco()
    with conectar() as conn:
        row = conn.execute(
            "SELECT necessidades, desejos, investimentos FROM regra_orcamento WHERE id = 1"
        ).fetchone()
    return {"necessidades": row[0], "desejos": row[1], "investimentos": row[2]}


def salvar_regra_orcamento(necessidades, desejos, investimentos):
    inicializar_banco()
    with conectar() as conn:
        conn.execute(
            """
            UPDATE regra_orcamento
            SET necessidades = ?, desejos = ?, investimentos = ?
            WHERE id = 1
            """,
            (int(necessidades), int(desejos), int(investimentos)),
        )
        conn.commit()
    return carregar_regra_orcamento()


inicializar_banco()
