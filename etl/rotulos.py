"""Rotulos em portugues para variaveis e categorias do dataset.

O dataset original vem em ingles e o ETL mantem codigos sem acento
(ex.: 'Reabilitacao'). Este modulo e a fonte unica dos nomes exibidos
em graficos, tabelas e no dashboard.
"""

# Nome legivel de cada variavel usada no modelo.
VARIAVEIS = {
    "race": "Raça",
    "gender": "Gênero",
    "idade": "Idade",
    "time_in_hospital": "Tempo de internação (dias)",
    "payer_code": "Fonte pagadora",
    "medical_specialty": "Especialidade",
    "num_lab_procedures": "Nº de exames laboratoriais",
    "num_procedures": "Nº de procedimentos",
    "num_medications": "Nº de medicamentos na internação",
    "number_outpatient": "Consultas ambulatoriais no ano anterior",
    "number_emergency": "Idas à emergência no ano anterior",
    "number_inpatient": "Internações no ano anterior",
    "number_diagnoses": "Nº de diagnósticos registrados",
    "max_glu_serum": "Glicemia sérica",
    "A1Cresult": "HbA1c",
    "metformin": "Metformina",
    "repaglinide": "Repaglinida",
    "nateglinide": "Nateglinida",
    "glimepiride": "Glimepirida",
    "glipizide": "Glipizida",
    "glyburide": "Glibenclamida",
    "pioglitazone": "Pioglitazona",
    "rosiglitazone": "Rosiglitazona",
    "acarbose": "Acarbose",
    "insulin": "Insulina",
    "glyburide-metformin": "Glibenclamida + metformina",
    "diag_1_grupo": "Diagnóstico principal",
    "diag_2_grupo": "Diagnóstico secundário",
    "diag_3_grupo": "Diagnóstico adicional",
    "diabetes_complicado": "Diabetes com complicação",
    "tipo_admissao": "Tipo de admissão",
    "destino_alta": "Destino da alta",
    "origem_admissao": "Origem da admissão",
    "n_medicamentos_diabetes": "Nº de antidiabéticos em uso",
    "n_doses_alteradas": "Nº de antidiabéticos com dose alterada",
    "mudou_medicacao": "Mudança na medicação do diabetes",
    "usa_medicacao_diabetes": "Usa medicação para diabetes",
    "total_visitas_previas": "Total de atendimentos no ano anterior",
    "ordem_internacao": "Internações anteriores no hospital (ordem)",
}

# Valores das categorias.
CATEGORIAS = {
    # gênero e raça
    "Female": "Feminino", "Male": "Masculino",
    "Caucasian": "Branca", "AfricanAmerican": "Negra (afro-americana)",
    "Hispanic": "Hispânica", "Asian": "Asiática", "Other": "Outra",
    "Desconhecida": "Não informada",
    # exames
    "Nao_medido": "Não medido", "Norm": "Normal",
    # medicamentos
    "No": "Não usa", "Steady": "Dose mantida", "Up": "Dose aumentada", "Down": "Dose reduzida",
    # destino da alta
    "Casa": "Casa", "Casa_com_home_care": "Casa com atenção domiciliar",
    "SNF": "Instituição de cuidados de enfermagem", "ICF": "Instituição de cuidados intermediários",
    "Reabilitacao": "Reabilitação", "Outro_hospital": "Outro hospital",
    "Longa_permanencia": "Hospital de longa permanência", "Alta_a_pedido": "Alta a pedido",
    "Psiquiatria": "Hospital psiquiátrico", "Outro_ou_desconhecido": "Outro / desconhecido",
    # admissão
    "Emergencia": "Emergência", "Urgencia": "Urgência", "Eletiva": "Eletiva",
    "Pronto_socorro": "Pronto-socorro", "Encaminhamento": "Encaminhamento",
    "Transferencia": "Transferência",
    # grupos de diagnóstico
    "Circulatorio": "Circulatório", "Respiratorio": "Respiratório", "Digestivo": "Digestivo",
    "Diabetes": "Diabetes", "Lesao_Trauma": "Lesão / trauma",
    "Musculoesqueletico": "Musculoesquelético", "Geniturinario": "Geniturinário",
    "Neoplasias": "Neoplasias", "Outros": "Outros", "Ausente": "Não informado",
    # especialidades
    "Nao_informada": "Não informada", "Outras": "Outras",
    "InternalMedicine": "Clínica médica", "Emergency/Trauma": "Emergência / trauma",
    "Family/GeneralPractice": "Medicina de família / clínica geral",
    "Cardiology": "Cardiologia", "Surgery-General": "Cirurgia geral",
    "Nephrology": "Nefrologia", "Orthopedics": "Ortopedia",
    "Orthopedics-Reconstructive": "Ortopedia reconstrutiva",
    "Radiologist": "Radiologia", "Pulmonology": "Pneumologia",
    # fonte pagadora
    "Nao_informado": "Não informada",
}


# Versao em ingles das categorias (usada pelo dashboard no modo EN).
CATEGORIAS_EN = {
    "Female": "Female", "Male": "Male",
    "Caucasian": "White", "AfricanAmerican": "Black (African American)",
    "Hispanic": "Hispanic", "Asian": "Asian", "Other": "Other", "Desconhecida": "Not recorded",
    "Nao_medido": "Not measured", "Norm": "Normal",
    "No": "Not used", "Steady": "Dose kept", "Up": "Dose increased", "Down": "Dose decreased",
    "Casa": "Home", "Casa_com_home_care": "Home with home health care",
    "SNF": "Skilled nursing facility", "ICF": "Intermediate care facility",
    "Reabilitacao": "Rehabilitation", "Outro_hospital": "Another hospital",
    "Longa_permanencia": "Long-term care hospital", "Alta_a_pedido": "Left against medical advice",
    "Psiquiatria": "Psychiatric hospital", "Outro_ou_desconhecido": "Other / unknown",
    "Emergencia": "Emergency", "Urgencia": "Urgent", "Eletiva": "Elective",
    "Pronto_socorro": "Emergency department", "Encaminhamento": "Referral",
    "Transferencia": "Transfer",
    "Circulatorio": "Circulatory", "Respiratorio": "Respiratory", "Digestivo": "Digestive",
    "Diabetes": "Diabetes", "Lesao_Trauma": "Injury / trauma",
    "Musculoesqueletico": "Musculoskeletal", "Geniturinario": "Genitourinary",
    "Neoplasias": "Neoplasms", "Outros": "Other", "Ausente": "Not recorded",
    "Nao_informada": "Not recorded", "Outras": "Other",
    "Nao_informado": "Not recorded",
}


def rotulo(valor, idioma: str = "pt") -> str:
    """Nome de um valor de categoria em portugues ('pt') ou ingles ('en')."""
    tabela = CATEGORIAS_EN if idioma == "en" else CATEGORIAS
    return tabela.get(valor, str(valor).replace("_", " "))


def nome_variavel(coluna: str) -> str:
    """Nome em portugues de uma variavel."""
    return VARIAVEIS.get(coluna, coluna.replace("_", " "))


def nome_feature(nome: str) -> str:
    """Nome em portugues de uma coluna gerada pelo one-hot (ex.: 'destino_alta_Reabilitacao').

    Fonte pagadora: o dataset traz apenas codigos (ex.: 'OG') sem dicionario oficial.
    """
    for coluna in sorted(VARIAVEIS, key=len, reverse=True):
        if nome == coluna:
            return nome_variavel(coluna)
        if nome.startswith(coluna + "_"):
            valor = nome[len(coluna) + 1:]
            if coluna == "payer_code" and valor not in CATEGORIAS:
                return f"Fonte pagadora: código {valor}"
            if valor == "infrequent_sklearn":
                return f"{nome_variavel(coluna)}: categorias raras"
            return f"{nome_variavel(coluna)}: {rotulo(valor)}"
    return nome.replace("_", " ")
