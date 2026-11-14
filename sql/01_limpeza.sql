-- =====================================================================
-- 01_limpeza.sql — carga do dataset bruto no banco DuckDB
--
-- Como rodar (a partir da raiz do projeto):
--   duckdb data-processed/diabetes.duckdb < sql/01_limpeza.sql
--
-- O arquivo original em data-raw/ permanece inalterado.
-- =====================================================================

-- 1. Tabela principal: uma linha por internacao (encounter).
--    No dataset original, valores ausentes aparecem como '?'.
--    Os codigos de diagnostico (CID-9) sao texto, pois existem codigos
--    como 'V57' e 'E909'. examide e citoglipton so tem 'No' e seriam
--    detectados como booleanos; forcamos texto como os demais medicamentos.
CREATE OR REPLACE TABLE internacoes AS
SELECT *
FROM read_csv(
    'data-raw/diabetic_data.csv',
    header = true,
    nullstr = '?',
    sample_size = -1,  -- le o arquivo inteiro para detectar os tipos
    types = {
        'diag_1': 'VARCHAR', 'diag_2': 'VARCHAR', 'diag_3': 'VARCHAR',
        'examide': 'VARCHAR', 'citoglipton': 'VARCHAR'
    }
);

-- 2. Tabelas de dominio. O IDS_mapping.csv tem 3 tabelas empilhadas
--    no mesmo arquivo, separadas por linhas vazias. Cada bloco comeca
--    com uma linha de cabecalho terminada em '_id'.
CREATE OR REPLACE TEMP TABLE mapping_bruto AS
SELECT
    row_number() OVER () AS linha,
    trim(column0) AS codigo,
    trim(column1) AS descricao
FROM read_csv('data-raw/IDS_mapping.csv', header = false, all_varchar = true);

CREATE OR REPLACE TEMP TABLE mapping AS
SELECT
    last_value(CASE WHEN codigo LIKE '%_id' THEN codigo END IGNORE NULLS)
        OVER (ORDER BY linha ROWS UNBOUNDED PRECEDING) AS tabela,
    codigo,
    descricao
FROM mapping_bruto;

CREATE OR REPLACE TABLE dim_admission_type AS
SELECT CAST(codigo AS INTEGER) AS admission_type_id, descricao
FROM mapping
WHERE tabela = 'admission_type_id' AND codigo <> 'admission_type_id' AND codigo IS NOT NULL;

CREATE OR REPLACE TABLE dim_discharge_disposition AS
SELECT CAST(codigo AS INTEGER) AS discharge_disposition_id, descricao
FROM mapping
WHERE tabela = 'discharge_disposition_id' AND codigo <> 'discharge_disposition_id' AND codigo IS NOT NULL;

CREATE OR REPLACE TABLE dim_admission_source AS
SELECT CAST(codigo AS INTEGER) AS admission_source_id, descricao
FROM mapping
WHERE tabela = 'admission_source_id' AND codigo <> 'admission_source_id' AND codigo IS NOT NULL;

-- 3. Conferencias basicas da carga.
SELECT 'internacoes' AS tabela, COUNT(*) AS linhas FROM internacoes
UNION ALL SELECT 'dim_admission_type', COUNT(*) FROM dim_admission_type
UNION ALL SELECT 'dim_discharge_disposition', COUNT(*) FROM dim_discharge_disposition
UNION ALL SELECT 'dim_admission_source', COUNT(*) FROM dim_admission_source;

SELECT readmitted, COUNT(*) AS quantidade
FROM internacoes
GROUP BY readmitted
ORDER BY quantidade DESC;

-- 4. Copia em CSV com os '?' convertidos em nulos (entrada do ETL em Python).
COPY internacoes TO 'data-processed/diabetic_data_clean.csv' (HEADER, DELIMITER ',');
