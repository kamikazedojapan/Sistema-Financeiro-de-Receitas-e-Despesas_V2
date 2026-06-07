# Alterações implementadas

## Banco de dados

O sistema agora usa SQLite em `MyBudget/database/financeiro.db`.
Os arquivos CSV antigos continuam no projeto apenas como base de migração inicial.
Na primeira execução, o banco é criado automaticamente e os dados dos CSVs são migrados caso o banco esteja vazio.

## CRUD

A página `Extratos` agora possui duas abas:

- Despesas
- Receitas

Nas tabelas é possível:

- visualizar registros;
- editar campos diretamente;
- remover linhas;
- salvar alterações no banco de dados.

A criação de novas receitas/despesas continua pelos botões do sidebar.

## Regra 50-30-20

Receitas e despesas agora possuem o campo `Regra`, com as opções:

- Necessidades
- Desejos
- Investimentos

A página da regra 50-30-20 agora salva a regra no banco e mostra no gráfico:

- a categoria;
- a porcentagem;
- o valor em reais.
