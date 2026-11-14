-- =====================================================================
-- 02_exploracao.sql — exploracao e validacao dos dados com SQL
--
-- Como rodar (depois do 01_limpeza.sql):
--   duckdb data-processed/diabetes.duckdb < sql/02_exploracao.sql
--
-- Pergunta central: quais fatores se associam a readmissao em < 30 dias?
-- Metrica usada em quase todas as consultas:
--   pct_readmit_30 = % de internacoes com readmitted = '<30'
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. VISAO GERAL
-- ---------------------------------------------------------------------

-- 1.1 Internacoes x pacientes. O mesmo paciente aparece varias vezes:
--     isso importa para o modelo (risco de vazamento entre treino e teste).
SELECT
    COUNT(*)                                       AS internacoes,
    COUNT(DISTINCT patient_nbr)                    AS pacientes,
    COUNT(DISTINCT encounter_id)                   AS encounters_unicos,
    ROUND(COUNT(*) / COUNT(DISTINCT patient_nbr), 2) AS internacoes_por_paciente
FROM internacoes;

-- 1.2 Quantos pacientes tem 1, 2, 3... internacoes no dataset.
SELECT n_internacoes, COUNT(*) AS pacientes
FROM (SELECT patient_nbr, COUNT(*) AS n_internacoes FROM internacoes GROUP BY 1)
GROUP BY 1
ORDER BY 1
LIMIT 10;

-- 1.3 Distribuicao da variavel alvo.
SELECT
    readmitted,
    COUNT(*) AS internacoes,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM internacoes
GROUP BY 1
ORDER BY 2 DESC;


-- ---------------------------------------------------------------------
-- 2. QUALIDADE DOS DADOS
-- ---------------------------------------------------------------------

-- 2.1 Percentual de nulos por coluna (somente colunas com algum nulo).
WITH nulos AS (
    UNPIVOT (
        SELECT COUNT(*) - COUNT(COLUMNS(*)) FROM internacoes
    ) ON COLUMNS(*) INTO NAME coluna VALUE qtd_nulos
)
SELECT
    coluna,
    qtd_nulos,
    ROUND(100.0 * qtd_nulos / (SELECT COUNT(*) FROM internacoes), 1) AS pct_nulos
FROM nulos
WHERE qtd_nulos > 0
ORDER BY qtd_nulos DESC;

-- 2.2 Valores "invalidos" que nao vieram como '?'.
SELECT 'gender = Unknown/Invalid' AS problema, COUNT(*) AS qtd
FROM internacoes WHERE gender = 'Unknown/Invalid'
UNION ALL
SELECT 'admission_type sem informacao (5, 6, 8)', COUNT(*)
FROM internacoes WHERE admission_type_id IN (5, 6, 8)
UNION ALL
SELECT 'discharge_disposition sem informacao (18, 25, 26)', COUNT(*)
FROM internacoes WHERE discharge_disposition_id IN (18, 25, 26);

-- 2.3 Medicamentos praticamente constantes (pouca utilidade para o modelo).
WITH meds AS (
    UNPIVOT (
        SELECT metformin, repaglinide, nateglinide, chlorpropamide, glimepiride,
               acetohexamide, glipizide, glyburide, tolbutamide, pioglitazone,
               rosiglitazone, acarbose, miglitol, troglitazone, tolazamide,
               examide, citoglipton, insulin, "glyburide-metformin",
               "glipizide-metformin", "glimepiride-pioglitazone",
               "metformin-rosiglitazone", "metformin-pioglitazone"
        FROM internacoes
    ) ON COLUMNS(*) INTO NAME medicamento VALUE uso
)
SELECT
    medicamento,
    ROUND(100.0 * COUNT(*) FILTER (WHERE uso <> 'No') / COUNT(*), 2) AS pct_em_uso
FROM meds
GROUP BY 1
ORDER BY 2 DESC;


-- ---------------------------------------------------------------------
-- 3. DESTINO DA ALTA — quem nao pode ser readmitido
-- ---------------------------------------------------------------------

-- 3.1 Readmissao por destino de alta. Obito (11, 19, 20, 21) e
--     hospice (13, 14) devem sair da base do modelo: esses pacientes
--     nao tem como voltar, e manter distorce a taxa.
SELECT
    i.discharge_disposition_id,
    d.descricao,
    COUNT(*) AS internacoes,
    ROUND(100.0 * AVG(CASE WHEN readmitted = '<30' THEN 1 ELSE 0 END), 1) AS pct_readmit_30
FROM internacoes i
LEFT JOIN dim_discharge_disposition d USING (discharge_disposition_id)
GROUP BY 1, 2
ORDER BY internacoes DESC;

-- 3.2 Tamanho da base apos remover obitos e hospice.
SELECT
    COUNT(*)                    AS internacoes_elegiveis,
    COUNT(DISTINCT patient_nbr) AS pacientes_elegiveis
FROM internacoes
WHERE discharge_disposition_id NOT IN (11, 13, 14, 19, 20, 21);


-- ---------------------------------------------------------------------
-- 4. FATORES ASSOCIADOS A READMISSAO < 30 DIAS
--    (a partir daqui, so internacoes elegiveis)
-- ---------------------------------------------------------------------

CREATE OR REPLACE TEMP VIEW elegiveis AS
SELECT *, CASE WHEN readmitted = '<30' THEN 1 ELSE 0 END AS readmit_30
FROM internacoes
WHERE discharge_disposition_id NOT IN (11, 13, 14, 19, 20, 21);

-- 4.1 Faixa etaria.
SELECT age, COUNT(*) AS internacoes, ROUND(100.0 * AVG(readmit_30), 1) AS pct_readmit_30
FROM elegiveis GROUP BY 1 ORDER BY 1;

-- 4.2 Internacoes no ano anterior (number_inpatient) — historico do paciente.
SELECT
    CASE WHEN number_inpatient >= 5 THEN '5+' ELSE CAST(number_inpatient AS VARCHAR) END AS internacoes_previas,
    COUNT(*) AS internacoes,
    ROUND(100.0 * AVG(readmit_30), 1) AS pct_readmit_30
FROM elegiveis GROUP BY 1 ORDER BY 1;

-- 4.3 Visitas a emergencia no ano anterior.
SELECT
    CASE WHEN number_emergency >= 3 THEN '3+' ELSE CAST(number_emergency AS VARCHAR) END AS emergencias_previas,
    COUNT(*) AS internacoes,
    ROUND(100.0 * AVG(readmit_30), 1) AS pct_readmit_30
FROM elegiveis GROUP BY 1 ORDER BY 1;

-- 4.4 Tempo de internacao (dias).
SELECT time_in_hospital AS dias, COUNT(*) AS internacoes, ROUND(100.0 * AVG(readmit_30), 1) AS pct_readmit_30
FROM elegiveis GROUP BY 1 ORDER BY 1;

-- 4.5 HbA1c: foi medida? estava alterada? houve mudanca na medicacao?
--     (Strack et al., 2014 — artigo original do dataset — estudou exatamente isso.)
SELECT
    -- no dataset, 'None' (texto) significa que o exame nao foi feito
    CASE WHEN A1Cresult = 'None' THEN 'Nao medida' ELSE A1Cresult END AS hba1c,
    change AS mudou_medicacao,
    COUNT(*) AS internacoes,
    ROUND(100.0 * AVG(readmit_30), 1) AS pct_readmit_30
FROM elegiveis GROUP BY 1, 2 ORDER BY 1, 2;

-- 4.6 Insulina.
SELECT insulin, COUNT(*) AS internacoes, ROUND(100.0 * AVG(readmit_30), 1) AS pct_readmit_30
FROM elegiveis GROUP BY 1 ORDER BY 2 DESC;

-- 4.7 Diagnostico principal agrupado por sistema (CID-9),
--     seguindo os grupos usados por Strack et al. (2014).
CREATE OR REPLACE TEMP MACRO grupo_cid(cod) AS
    CASE
        WHEN cod IS NULL                          THEN 'Ausente'
        WHEN cod LIKE 'V%' OR cod LIKE 'E%'       THEN 'Outros'
        WHEN cod LIKE '250%'                      THEN 'Diabetes'
        WHEN CAST(cod AS DOUBLE) BETWEEN 390 AND 459 OR CAST(cod AS DOUBLE) BETWEEN 785 AND 785.99 THEN 'Circulatorio'
        WHEN CAST(cod AS DOUBLE) BETWEEN 460 AND 519 OR CAST(cod AS DOUBLE) BETWEEN 786 AND 786.99 THEN 'Respiratorio'
        WHEN CAST(cod AS DOUBLE) BETWEEN 520 AND 579 OR CAST(cod AS DOUBLE) BETWEEN 787 AND 787.99 THEN 'Digestivo'
        WHEN CAST(cod AS DOUBLE) BETWEEN 800 AND 999 THEN 'Lesao/Trauma'
        WHEN CAST(cod AS DOUBLE) BETWEEN 710 AND 739 THEN 'Musculoesqueletico'
        WHEN CAST(cod AS DOUBLE) BETWEEN 580 AND 629 OR CAST(cod AS DOUBLE) BETWEEN 788 AND 788.99 THEN 'Geniturinario'
        WHEN CAST(cod AS DOUBLE) BETWEEN 140 AND 239 THEN 'Neoplasias'
        ELSE 'Outros'
    END;

SELECT
    grupo_cid(diag_1) AS diagnostico_principal,
    COUNT(*) AS internacoes,
    ROUND(100.0 * AVG(readmit_30), 1) AS pct_readmit_30
FROM elegiveis GROUP BY 1 ORDER BY 2 DESC;

-- 4.8 Tipo de admissao.
SELECT
    e.admission_type_id, a.descricao,
    COUNT(*) AS internacoes,
    ROUND(100.0 * AVG(readmit_30), 1) AS pct_readmit_30
FROM elegiveis e
LEFT JOIN dim_admission_type a USING (admission_type_id)
GROUP BY 1, 2 ORDER BY 3 DESC;

-- 4.9 Especialidade medica (top 10 por volume).
SELECT
    COALESCE(medical_specialty, 'Nao informada') AS especialidade,
    COUNT(*) AS internacoes,
    ROUND(100.0 * AVG(readmit_30), 1) AS pct_readmit_30
FROM elegiveis GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
