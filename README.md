# 💰 Sistema Financeiro de Receitas e Despesas

Sistema web para gerenciamento financeiro pessoal desenvolvido com Python, Dash, Plotly e SQLite, permitindo o controle de receitas, despesas, orçamento mensal e acompanhamento financeiro através da regra 50-30-20.

# 📋 Sobre o Projeto

O Sistema Financeiro foi desenvolvido com o objetivo de auxiliar usuários no controle das finanças pessoais, oferecendo uma interface intuitiva para cadastro, edição e acompanhamento de receitas e despesas. Além do controle financeiro tradicional, o sistema implementa a metodologia de orçamento 50-30-20, permitindo acompanhar quanto pode ser gasto em cada categoria financeira ao longo dos meses.

## Interface visual do sistema
<img width="1898" height="928" alt="image" src="https://github.com/user-attachments/assets/78efed78-ecc9-4421-8d96-dd7fe5b6c01b" />
<img width="1901" height="926" alt="image" src="https://github.com/user-attachments/assets/5d08a6df-48ff-4e73-ab24-de9220b80c51" />
<img width="1898" height="927" alt="image" src="https://github.com/user-attachments/assets/53c3f794-3aa5-40e5-a770-e649417c11ec" />
<img width="1900" height="928" alt="image" src="https://github.com/user-attachments/assets/3ae7b566-5029-4f63-b13d-e4cd013cd4d8" />

# 🚀 Funcionalidades
## Dashboard  
- Visualização do saldo total.
- Total de receitas.
- Total de despesas.
- Gráficos de receitas e despesas.
- Atualização automática após alterações nos dados.

## Gestão de Receitas
Permite:
- Criar receitas.
- Editar receitas.
- Excluir receitas.
- Visualizar receitas cadastradas.

Campos:
- Valor
- Data
- Categoria
- Regra Financeira
- Descrição
- Receita recorrente
- Receita recebida

## Gestão de Despesas
Permite:
- Criar despesas.
- Editar despesas.
- Excluir despesas.
- Visualizar despesas cadastradas.

Campos:
- Valor
- Data
- Categoria
- Regra Financeira
- Descrição
- Despesa recorrente
- Despesa efetuada

## Categorias Personalizadas
Permite:
- Criar categorias.
- Remover categorias.
- Utilizar categorias personalizadas para receitas e despesas.

## Regra 50-30-20
### O sistema implementa a metodologia:  
Custos = 50% do salário liquido  
Desejos =	30% do salário líquido  
Investimentos =	20% do salário liquido    

### Os percentuais podem ser alterados pelo usuário.  
Exemplo:  
- 50-30-20
- 60-20-20
- 50-40-10    

## Acúmulo Mensal (Rollover)  

O valor não utilizado em um mês é acumulado para o mês seguinte.  
Exemplo:  

### Maio
#### Receita: R$ 1441,00  
- Limite: R$ 720,50  
- Gasto: R$ 260,31
- Sobra: R$ 460,19
### Junho
- Limite Base: R$ 720,50  
- Acumulado: R$ 460,19  
- Limite total R$ 1.180,68    

## Controle de Limites
Para cada categoria o sistema exibe:
- Gasto atual
- Limite Base
- Limite Acumulado
- Limite Total
- Valor Disponível
- Valor Excedido

## Relatórios  
O sistema gera:
- Total de despesas por categoria.
- Total de receitas por categoria.
- Distribuição do orçamento mensal.
- Evolução financeira mensal.

# 🗄️ Banco de Dados

O sistema utiliza SQLite como fonte principal de armazenamento.  
### Tabelas  
Receitas:  
- id  
- valor  
- efetuado
- fixo
- data
- categoria
- regra
- descrição    

Despesas:
- id  
- valor
- efetuado
- fixo
- data
- categoria
- regra
- descricao    

### Categorias de receita  
- id  
- nome

### Categoria de despesas
- id  
- nome

### Regras Financeiras  
- percentual_custos
- percentual_desejos
- percentual_investimentos    

# 🛠️ Tecnologias Utilizadas
## Backend  
- Python
- SQLite  
## Interface  
- Dash
- Plotly
- Dash Bootstrap Components
## Manipulação de Dados  
- Pandas
- NumPy
