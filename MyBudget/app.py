import dash
import dash_bootstrap_components as dbc

# ✅ IMPORTAÇÃO ADICIONAL
from globals import carregar_dados  # importa a função que carrega os DataFrames

# ✅ CHAMADA PARA CARREGAR OS DADOS
carregar_dados()  # executa o carregamento das variáveis globais (df_receitas, etc.)

estilos = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css",
    "https://fonts.googleapis.com/icon?family=Material+Icons",
    dbc.themes.COSMO
]

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css"

app = dash.Dash(__name__, external_stylesheets=estilos + [dbc_css])

app.config['suppress_callback_exceptions'] = True
app.scripts.config.serve_locally = True

server = app.server
