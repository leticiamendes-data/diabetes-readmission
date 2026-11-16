# Pipeline completo com um comando:  make all
# Passo a passo:                     make help

PY  := ./venv/bin/python
BIN := ./venv/bin
DB  := data-processed/diabetes.duckdb

.PHONY: help setup all banco exploracao etl notebooks figuras app limpar

help:  ## Lista os comandos disponíveis
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-11s %s\n", $$1, $$2}'

setup:  ## Cria o ambiente virtual e instala as dependências
	python3 -m venv venv
	$(BIN)/pip install -q --upgrade pip
	$(BIN)/pip install -q -r requirements.txt

all: banco etl notebooks figuras  ## Roda o pipeline inteiro (banco -> ETL -> notebooks -> figuras)
	@echo "Pronto. Para abrir o dashboard: make app"

banco:  ## Carrega o CSV bruto no banco DuckDB (sql/01_limpeza.sql)
	$(PY) -c "import duckdb; duckdb.connect('$(DB)').execute(open('sql/01_limpeza.sql').read())"
	@echo "Banco criado em $(DB)"

exploracao:  ## Mostra as consultas de exploração (sql/02_exploracao.sql; requer o DuckDB CLI)
	duckdb $(DB) < sql/02_exploracao.sql

etl:  ## Gera o dataset de modelagem (etl/pipeline.py)
	$(PY) etl/pipeline.py

notebooks:  ## Executa a análise exploratória e o modelo (salva o modelo e as figuras)
	$(BIN)/jupyter nbconvert --to notebook --execute --inplace \
		--ExecutePreprocessor.timeout=1200 \
		notebooks/01_analise_exploratoria.ipynb notebooks/02_modelo.ipynb

figuras:  ## Gera as versões em inglês dos gráficos do README
	$(PY) reports/figuras_readme_en.py

app:  ## Abre o dashboard Streamlit
	$(BIN)/streamlit run app/app.py

limpar:  ## Apaga os arquivos gerados em data-processed/
	rm -f data-processed/*.duckdb data-processed/*.csv
