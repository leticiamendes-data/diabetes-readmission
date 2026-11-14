"""Pipeline ETL: transforma as internacoes do DuckDB no dataset de modelagem.

Como rodar (a partir da raiz do projeto, depois do sql/01_limpeza.sql):
    ./venv/bin/python etl/pipeline.py

Entrada:  data-processed/diabetes.duckdb (tabela `internacoes`)
Saida:    data-processed/dataset_modelo.csv

Cada decisao de limpeza esta documentada na funcao correspondente.
As justificativas vem da exploracao em sql/02_exploracao.sql.
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BANCO = RAIZ / "data-processed" / "diabetes.duckdb"
SAIDA = RAIZ / "data-processed" / "dataset_modelo.csv"

# Destinos de alta em que o paciente nao pode ser readmitido:
# 11, 19, 20, 21 = obito; 13, 14 = hospice (cuidados de fim de vida).
DESTINOS_SEM_READMISSAO = [11, 13, 14, 19, 20, 21]

# Medicamentos usados em menos de 0,1% das internacoes: quase constantes,
# nao ajudam o modelo.
MEDICAMENTOS_RAROS = [
    "chlorpropamide", "tolazamide", "miglitol", "tolbutamide",
    "glipizide-metformin", "acetohexamide", "troglitazone",
    "metformin-rosiglitazone", "citoglipton", "examide",
    "glimepiride-pioglitazone", "metformin-pioglitazone",
]

MEDICAMENTOS = [
    "metformin", "repaglinide", "nateglinide", "glimepiride", "glipizide",
    "glyburide", "pioglitazone", "rosiglitazone", "acarbose", "insulin",
    "glyburide-metformin",
]


# ---------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------
def extrair(banco: Path = BANCO) -> pd.DataFrame:
    with duckdb.connect(str(banco), read_only=True) as con:
        return con.sql("SELECT * FROM internacoes ORDER BY encounter_id").df()


# ---------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------
def filtrar_elegiveis(df: pd.DataFrame) -> pd.DataFrame:
    """Remove internacoes que nao fazem sentido para a pergunta."""
    df = df[~df["discharge_disposition_id"].isin(DESTINOS_SEM_READMISSAO)]
    # 3 registros com genero 'Unknown/Invalid'.
    df = df[df["gender"] != "Unknown/Invalid"]
    return df.copy()


def criar_alvo(df: pd.DataFrame) -> pd.DataFrame:
    """Alvo binario: 1 = readmitido em menos de 30 dias."""
    df["readmit_30"] = (df["readmitted"] == "<30").astype(int)
    return df.drop(columns=["readmitted"])


def grupo_cid(codigo) -> str:
    """Agrupa o CID-9 por sistema (mesmos grupos de Strack et al., 2014)."""
    if codigo is None or pd.isna(codigo):
        return "Ausente"
    codigo = str(codigo)
    if codigo.startswith(("V", "E")):
        return "Outros"
    if codigo.startswith("250"):
        return "Diabetes"
    valor = float(codigo)
    if 390 <= valor < 460 or int(valor) == 785:
        return "Circulatorio"
    if 460 <= valor < 520 or int(valor) == 786:
        return "Respiratorio"
    if 520 <= valor < 580 or int(valor) == 787:
        return "Digestivo"
    if 800 <= valor < 1000:
        return "Lesao_Trauma"
    if 710 <= valor < 740:
        return "Musculoesqueletico"
    if 580 <= valor < 630 or int(valor) == 788:
        return "Geniturinario"
    if 140 <= valor < 240:
        return "Neoplasias"
    return "Outros"


def tratar_diagnosticos(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["diag_1", "diag_2", "diag_3"]:
        df[f"{col}_grupo"] = df[col].map(grupo_cid)
    # Indicador direto: alguma das 3 posicoes e diabetes com complicacao
    # (250.x com 4o digito diferente de 0 -> 250.1 a 250.9).
    complicado = df[["diag_1", "diag_2", "diag_3"]].apply(
        lambda s: s.fillna("").str.match(r"^250\.[1-9]")
    )
    df["diabetes_complicado"] = complicado.any(axis=1).astype(int)
    return df.drop(columns=["diag_1", "diag_2", "diag_3"])


def tratar_categoricas(df: pd.DataFrame) -> pd.DataFrame:
    # weight: 97% nulo -> descartado.
    df = df.drop(columns=["weight"])

    # Nulos viram uma categoria propria (a ausencia tambem e informacao).
    df["race"] = df["race"].fillna("Desconhecida")
    df["payer_code"] = df["payer_code"].fillna("Nao_informado")

    # Especialidade: 70+ categorias. Mantem 'Nao_informada' + as 10 mais
    # frequentes; o resto vira 'Outras'.
    df["medical_specialty"] = df["medical_specialty"].fillna("Nao_informada")
    top = df["medical_specialty"].value_counts().nlargest(11).index
    df["medical_specialty"] = df["medical_specialty"].where(
        df["medical_specialty"].isin(top), "Outras"
    )

    # Exames: o texto 'None' significa "nao realizado".
    for col in ["A1Cresult", "max_glu_serum"]:
        df[col] = df[col].replace("None", "Nao_medido")

    # Idade '[70-80)' -> ponto medio numerico (75).
    df["idade"] = df["age"].str.extract(r"\[(\d+)-").astype(int)[0] + 5
    df = df.drop(columns=["age"])

    # IDs de admissao/alta/origem: agrupados em categorias clinicas.
    df["tipo_admissao"] = df["admission_type_id"].map(
        {1: "Emergencia", 2: "Urgencia", 3: "Eletiva", 7: "Emergencia"}
    ).fillna("Outro_ou_desconhecido")
    df["destino_alta"] = df["discharge_disposition_id"].map(
        {1: "Casa", 6: "Casa_com_home_care", 8: "Casa_com_home_care",
         3: "SNF", 4: "ICF", 22: "Reabilitacao", 2: "Outro_hospital",
         5: "Outro_hospital", 23: "Longa_permanencia", 7: "Alta_a_pedido",
         28: "Psiquiatria"}
    ).fillna("Outro_ou_desconhecido")
    df["origem_admissao"] = df["admission_source_id"].map(
        {7: "Pronto_socorro", 1: "Encaminhamento", 2: "Encaminhamento",
         3: "Encaminhamento", 4: "Transferencia", 5: "Transferencia",
         6: "Transferencia", 10: "Transferencia", 22: "Transferencia",
         25: "Transferencia"}
    ).fillna("Outro_ou_desconhecido")
    df = df.drop(columns=["admission_type_id", "discharge_disposition_id",
                          "admission_source_id"])
    return df


def tratar_medicamentos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=MEDICAMENTOS_RAROS)
    meds = df[MEDICAMENTOS]
    df["n_medicamentos_diabetes"] = (meds != "No").sum(axis=1)
    df["n_doses_alteradas"] = meds.isin(["Up", "Down"]).sum(axis=1)
    df["mudou_medicacao"] = (df["change"] == "Ch").astype(int)
    df["usa_medicacao_diabetes"] = df["diabetesMed"].astype(int)
    return df.drop(columns=["change", "diabetesMed"])


def criar_variaveis(df: pd.DataFrame) -> pd.DataFrame:
    """Variaveis derivadas do historico de uso do servico de saude."""
    df["total_visitas_previas"] = (
        df["number_outpatient"] + df["number_emergency"] + df["number_inpatient"]
    )
    # Ordem da internacao do paciente dentro do dataset (1a, 2a, ...).
    # encounter_id e crescente no tempo, entao serve como ordem.
    df["ordem_internacao"] = df.groupby("patient_nbr").cumcount() + 1
    return df


def transformar(df: pd.DataFrame) -> pd.DataFrame:
    df = filtrar_elegiveis(df)
    df = criar_alvo(df)
    df = tratar_diagnosticos(df)
    df = tratar_categoricas(df)
    df = tratar_medicamentos(df)
    df = criar_variaveis(df)
    # patient_nbr fica no arquivo: o modelo usa para separar treino/teste
    # por paciente (evita vazamento), mas nao como variavel preditora.
    return df.drop(columns=["encounter_id"]).reset_index(drop=True)


# ---------------------------------------------------------------------
# Validacao
# ---------------------------------------------------------------------
def validar(df: pd.DataFrame) -> None:
    assert df.isna().sum().sum() == 0, "Ainda ha valores nulos"
    assert set(df["readmit_30"].unique()) <= {0, 1}, "Alvo nao e binario"
    assert df["idade"].between(5, 95).all(), "Idade fora do esperado"
    assert len(df) > 95_000, "Perda de linhas maior que a esperada"


# ---------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------
def carregar(df: pd.DataFrame, saida: Path = SAIDA) -> None:
    df.to_csv(saida, index=False)


def main() -> None:
    bruto = extrair()
    tratado = transformar(bruto)
    validar(tratado)
    carregar(tratado)

    print(f"Linhas: {len(bruto):,} -> {len(tratado):,}")
    print(f"Pacientes: {tratado['patient_nbr'].nunique():,}")
    print(f"Colunas: {tratado.shape[1]}")
    print(f"Taxa de readmissao < 30 dias: {tratado['readmit_30'].mean():.1%}")
    print(f"Salvo em: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
