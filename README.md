# Diabetes Hospital Readmission — Data Pipeline & ML

Pipeline completo de dados em Python: de dataset bruto a modelo de Machine Learning, prevendo se um paciente diabético será readmitido no hospital em até 30 dias.

## Sobre o dataset

"Diabetes 130-US hospitals for years 1999-2008" — 10 anos de registros clínicos de 130 hospitais americanos, ~100 mil internações de pacientes diabéticos.
Fonte: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008)

## Pipeline

```
Dataset bruto
    ↓
Banco SQL
    ↓
Exploração e validação com SQL
    ↓
Pipeline ETL em Python
    ↓
Dados tratados
    ↓
Notebook de análise e insights
    ↓
Machine Learning
    ↓
Dashboard ou relatório final
```

## Stack técnica

- **Python** (pandas, scikit-learn, matplotlib, seaborn)
- **SQL** (SQLite para exploração local)
- **Cloud**: AWS S3 (armazenamento) + AWS Lambda (processamento) — dentro do free tier permanente
- **Ambiente**: venv (ambiente virtual isolado)

## Estrutura do projeto

```
diabetes-readmission/
├── data/
│   ├── raw/            → dataset original, sem alterações
│   └── processed/      → dados já tratados pelo pipeline ETL
├── sql/                → scripts de exploração e criação do banco
├── etl/                → pipeline de limpeza e transformação
├── notebooks/          → análise exploratória e insights
├── models/             → Machine Learning
└── README.md
```

## Status

🚧 Em construção — Fase 1: carregando o dataset bruto num banco SQL.

## Autora

Projeto de portfólio combinando experiência clínica (enfermagem) com engenharia de dados.
