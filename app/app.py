"""Dashboard: escore de risco de readmissao em < 30 dias para pacientes diabeticos.

Como rodar (a partir da raiz do projeto):
    ./venv/bin/streamlit run app/app.py

Usa o modelo salvo por notebooks/02_modelo.ipynb (models/modelo_readmissao.joblib).
"""

from bisect import bisect_left
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
FIGURAS = RAIZ / "reports" / "figures"

st.set_page_config(page_title="Risco de readmissão — diabetes", page_icon="🩺", layout="wide")


@st.cache_resource
def carregar_modelo():
    return joblib.load(RAIZ / "models" / "modelo_readmissao.joblib")


art = carregar_modelo()
CAT = art["categorias"]

# Rotulos em portugues para os codigos do dataset.
ROTULOS = {
    "Female": "Feminino", "Male": "Masculino",
    "Caucasian": "Branca", "AfricanAmerican": "Negra", "Hispanic": "Hispânica",
    "Asian": "Asiática", "Other": "Outra", "Desconhecida": "Não informada",
    "Nao_medido": "Não medido", "Norm": "Normal",
    "No": "Não usa", "Steady": "Dose mantida", "Up": "Dose aumentada", "Down": "Dose reduzida",
    "Casa": "Casa", "Casa_com_home_care": "Casa com home care", "SNF": "SNF (cuidados de enfermagem)",
    "ICF": "ICF (cuidados intermediários)", "Reabilitacao": "Reabilitação",
    "Outro_hospital": "Outro hospital", "Longa_permanencia": "Hospital de longa permanência",
    "Alta_a_pedido": "Alta a pedido", "Psiquiatria": "Hospital psiquiátrico",
    "Outro_ou_desconhecido": "Outro / desconhecido",
    "Emergencia": "Emergência", "Urgencia": "Urgência", "Eletiva": "Eletiva",
    "Pronto_socorro": "Pronto-socorro", "Encaminhamento": "Encaminhamento",
    "Transferencia": "Transferência",
    "Circulatorio": "Circulatório", "Respiratorio": "Respiratório", "Digestivo": "Digestivo",
    "Diabetes": "Diabetes", "Lesao_Trauma": "Lesão / trauma",
    "Musculoesqueletico": "Musculoesquelético", "Geniturinario": "Geniturinário",
    "Neoplasias": "Neoplasias", "Outros": "Outros", "Ausente": "Não informado",
    "Nao_informada": "Não informada", "Outras": "Outras",
}


def rotulo(valor):
    return ROTULOS.get(valor, str(valor).replace("_", " "))


def escolha(label, coluna, ordem=None, **kw):
    opcoes = ordem or CAT[coluna]
    padrao = art["padroes"][coluna]
    return st.selectbox(label, opcoes, index=opcoes.index(padrao) if padrao in opcoes else 0,
                        format_func=rotulo, **kw)


# ---------------------------------------------------------------------
st.title("🩺 Risco de readmissão em até 30 dias")
st.caption(
    "Pacientes diabéticos internados · modelo treinado com 99 mil internações de 130 hospitais "
    "americanos (1999–2008). Projeto de portfólio — **não usar para decisão clínica real**."
)

aba_risco, aba_achados, aba_modelo = st.tabs(["Calcular risco", "Principais achados", "Sobre o modelo"])

# ---------------------------------------------------------------------
with aba_risco:
    with st.form("paciente"):
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.subheader("Paciente")
            idade = st.slider("Idade", 5, 95, int(art["padroes"]["idade"]), step=10,
                              help="O dataset traz a idade em faixas de 10 anos.")
            genero = escolha("Gênero", "gender")
            raca = escolha("Raça", "race")

        with c2:
            st.subheader("Histórico (último ano)")
            n_intern = st.number_input("Internações", 0, 25, 0)
            n_emerg = st.number_input("Idas à emergência", 0, 80, 0)
            n_ambul = st.number_input("Consultas ambulatoriais", 0, 50, 0)
            n_previas_hosp = st.number_input(
                "Internações anteriores registradas neste hospital", 0, 30, 0,
                help="Quantas vezes o paciente já aparece na base do hospital antes desta internação.")

        with c3:
            st.subheader("Internação atual")
            tipo = escolha("Tipo de admissão", "tipo_admissao")
            origem = escolha("Origem", "origem_admissao")
            dias = st.slider("Tempo de internação (dias)", 1, 14, int(art["padroes"]["time_in_hospital"]))
            diag = escolha("Diagnóstico principal", "diag_1_grupo")
            destino = escolha("Destino da alta", "destino_alta")
            n_diag = st.slider("Nº de diagnósticos registrados", 1, 16, int(art["padroes"]["number_diagnoses"]))
            n_meds = st.slider("Nº de medicamentos na internação", 1, 80, int(art["padroes"]["num_medications"]))

        with c4:
            st.subheader("Diabetes")
            hba1c = escolha("HbA1c", "A1Cresult", ordem=["Nao_medido", "Norm", ">7", ">8"])
            insulina = escolha("Insulina", "insulin", ordem=["No", "Steady", "Up", "Down"])
            metformina = escolha("Metformina", "metformin", ordem=["No", "Steady", "Up", "Down"])
            complicado = st.checkbox("Diabetes com complicação (CID 250.1–250.9)")
            mudou = st.checkbox("Houve mudança na medicação do diabetes")

        enviado = st.form_submit_button("Calcular risco", type="primary", width="stretch")

    if enviado:
        # Comeca com o paciente "tipico" e sobrescreve com o que foi informado.
        p = dict(art["padroes"])
        p.update({
            "idade": idade, "gender": genero, "race": raca,
            "number_inpatient": n_intern, "number_emergency": n_emerg, "number_outpatient": n_ambul,
            "ordem_internacao": n_previas_hosp + 1,
            "tipo_admissao": tipo, "origem_admissao": origem, "time_in_hospital": dias,
            "diag_1_grupo": diag, "destino_alta": destino,
            "number_diagnoses": n_diag, "num_medications": n_meds,
            "A1Cresult": hba1c, "insulin": insulina, "metformin": metformina,
            "diabetes_complicado": int(complicado), "mudou_medicacao": int(mudou),
        })
        # Variaveis derivadas (mesma regra do etl/pipeline.py).
        meds = [p[m] for m in ("metformin", "repaglinide", "nateglinide", "glimepiride", "glipizide",
                               "glyburide", "pioglitazone", "rosiglitazone", "acarbose", "insulin",
                               "glyburide-metformin")]
        p["n_medicamentos_diabetes"] = sum(m != "No" for m in meds)
        p["n_doses_alteradas"] = sum(m in ("Up", "Down") for m in meds)
        p["usa_medicacao_diabetes"] = int(p["n_medicamentos_diabetes"] > 0)
        p["total_visitas_previas"] = n_intern + n_emerg + n_ambul

        entrada = pd.DataFrame([p])[art["colunas"]]
        score = float(art["modelo"].predict_proba(entrada)[0, 1])
        # percentis_risco[k] = percentil k do escore no conjunto de teste.
        percentil = max(0, bisect_left(art["percentis_risco"], score) - 1)
        alto = score >= art["corte_alto_risco"]

        st.divider()
        r1, r2, r3 = st.columns(3)
        r1.metric("Faixa de risco", "🔴 ALTO" if alto else "🟢 Habitual")
        r2.metric("Posição entre as internações do teste", f"maior que {min(percentil, 100)}%")
        r3.metric("Escore do modelo", f"{score:.2f}",
                  help="Escore de 0 a 1. O modelo foi treinado com pesos balanceados, então o escore "
                       "ordena o risco mas não é a probabilidade real de readmissão.")

        if alto:
            st.warning(
                "**Paciente entre os 20% de maior risco.** Nesse grupo, cerca de **23%** voltam em "
                f"até 30 dias (taxa geral: {art['taxa_base']:.0%}).\n\n"
                "Exemplos de ações de transição de cuidado *(ilustrativas)*: revisar o plano de alta e "
                "a medicação com o paciente/família, educação em insulinoterapia, retorno ambulatorial "
                "em até 7 dias, contato telefônico em 48–72 h."
            )
        else:
            st.success(
                "Risco dentro do habitual. Mantém-se o plano de alta padrão, com orientação sobre "
                "sinais de alerta e acompanhamento ambulatorial."
            )

        # O que mais pesa para este paciente.
        fatores = []
        if destino in ("Reabilitacao", "Psiquiatria", "Outro_hospital"):
            fatores.append(f"Destino da alta: **{rotulo(destino)}**")
        if n_intern >= 2:
            fatores.append(f"**{n_intern} internações** no último ano")
        if n_emerg >= 1:
            fatores.append(f"**{n_emerg} ida(s) à emergência** no último ano")
        if n_previas_hosp >= 1:
            fatores.append("Internações anteriores neste hospital")
        if complicado:
            fatores.append("Diabetes com complicação")
        if insulina in ("Up", "Down"):
            fatores.append("Ajuste de insulina durante a internação")
        if hba1c == "Nao_medido":
            fatores.append("HbA1c não medida")
        if fatores:
            st.markdown("**Fatores de risco presentes:** " + " · ".join(fatores))

# ---------------------------------------------------------------------
with aba_achados:
    st.markdown(
        "Taxa de readmissão em < 30 dias por fator (99.340 internações elegíveis). "
        "Detalhes em `notebooks/01_analise_exploratoria.ipynb`."
    )
    figuras = [
        ("01_internacoes_previas.png", "Histórico: o fator mais forte da análise exploratória."),
        ("03_destino_alta.png", "Para onde o paciente vai depois da alta muda muito o risco."),
        ("04_hba1c.png", "HbA1c não foi medida em 83% das internações."),
        ("05_insulina.png", "Ajustar a insulina marca o paciente descompensado."),
        ("06_diabetes_complicado.png", "Complicação do diabetes registrada eleva o risco."),
        ("07_tempo_internacao.png", "Internações mais longas, mais readmissão."),
    ]
    for i in range(0, len(figuras), 2):
        cols = st.columns(2)
        for col, (arquivo, legenda) in zip(cols, figuras[i:i + 2]):
            col.image(str(FIGURAS / arquivo), caption=legenda, width="stretch")

# ---------------------------------------------------------------------
with aba_modelo:
    m = art["metricas_teste"]
    a, b, c = st.columns(3)
    a.metric("Modelo", art["nome"])
    b.metric("ROC-AUC (teste)", f"{m['ROC-AUC']:.3f}", help="0,5 = sorteio; 1,0 = perfeito.")
    c.metric("PR-AUC (teste)", f"{m['PR-AUC']:.3f}", help=f"Base aleatória ≈ {art['taxa_base']:.2f}.")

    st.markdown("""
- Treino e teste separados **por paciente**: o modelo é avaliado só em pacientes que nunca viu.
- Os **20% de maior risco** concentram **41% das readmissões** do conjunto de teste.
- No decil de maior risco, **28%** voltam em até 30 dias; no de menor risco, **4%**.
""")
    c1, c2 = st.columns(2)
    c1.image(str(FIGURAS / "11_decis_de_risco.png"), width="stretch")
    c2.image(str(FIGURAS / "13_importancia_variaveis.png"), width="stretch")

    st.markdown("""
**Limitações**
- Dados de 1999–2008, hospitais dos EUA. Antes de qualquer uso real, o modelo precisaria ser
  revalidado em dados locais e atuais.
- Não há variáveis sociais nem de cuidado pós-alta (adesão, suporte familiar, acesso a consulta).
- O modelo mostra **associação, não causa**.
""")
