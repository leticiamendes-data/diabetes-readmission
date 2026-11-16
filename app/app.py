"""Dashboard: escore de risco de readmissao em < 30 dias para pacientes diabeticos.

Como rodar (a partir da raiz do projeto):
    ./venv/bin/streamlit run app/app.py

Idioma: botao PT/EN no topo, ou pelo link (?lang=en).
Usa o modelo salvo por notebooks/02_modelo.ipynb (models/modelo_readmissao.joblib).
"""

import sys
from bisect import bisect_left
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
FIGURAS = RAIZ / "reports" / "figures"
sys.path.insert(0, str(RAIZ))

from etl.rotulos import rotulo  # noqa: E402  (nomes das categorias em PT/EN)

REPO = "https://github.com/leticiamendes-data/diabetes-readmission"
LINKEDIN = "https://www.linkedin.com/in/let%C3%ADcia-mendes-a2127b1b5"

st.set_page_config(page_title="Readmissão · Readmission risk", page_icon=":material/ecg_heart:",
                   layout="wide")

# ---------------------------------------------------------------------
# Textos nos dois idiomas
# ---------------------------------------------------------------------
TXT = {
    "pt": {
        "titulo": "Risco de readmissão em até 30 dias",
        "subtitulo": "Apoio à priorização no planejamento da alta de pacientes diabéticos. "
                     "Modelo treinado com 99 mil internações de 130 hospitais americanos (1999–2008).",
        "autora": "Projeto de Leticia Mendes, enfermeira e analista de dados",
        "aviso": "Projeto de portfólio. Não usar para decisões clínicas reais.",
        "abas": ["Calcular risco", "Principais achados", "Sobre o modelo"],
        "paciente": "Paciente", "historico": "Último ano",
        "internacao": "Internação atual", "diabetes": "Diabetes",
        "idade": "Idade", "idade_ajuda": "O dataset traz a idade em faixas de 10 anos.",
        "genero": "Gênero", "raca": "Raça",
        "n_intern": "Internações", "n_emerg": "Idas à emergência", "n_ambul": "Consultas ambulatoriais",
        "n_hosp": "Internações anteriores neste hospital",
        "n_hosp_ajuda": "Quantas vezes o paciente já aparece na base do hospital antes desta internação.",
        "tipo": "Tipo de admissão", "origem": "Origem", "dias": "Tempo de internação (dias)",
        "diag": "Diagnóstico principal", "destino": "Destino da alta",
        "n_diag": "Nº de diagnósticos registrados", "n_meds": "Nº de medicamentos na internação",
        "hba1c": "HbA1c", "insulina": "Insulina", "metformina": "Metformina",
        "complicado": "Com complicação",
        "complicado_ajuda": "Algum diagnóstico de diabetes com complicação (CID-9 250.1 a 250.9).",
        "mudou": "Medicação alterada",
        "mudou_ajuda": "Houve mudança na medicação do diabetes durante a internação.",
        "botao": "Calcular risco",
        "pulseira": "Risco de readmissão",
        "alto": "alto", "habitual": "habitual",
        "posicao": "Maior que {p}% das internações do conjunto de teste",
        "limite": "limite do alto risco (20% maiores)",
        "escore": "Escore do modelo: {s}",
        "escore_ajuda": "Escore de 0 a 1. Ele ordena o risco, mas não é a probabilidade real de readmissão.",
        "msg_alto": "Paciente entre os 20% de maior risco. Nesse grupo, cerca de 23% voltam em até "
                    "30 dias (taxa geral: {t}).",
        "msg_habitual": "Risco dentro do habitual. Mantém-se o plano de alta padrão, com orientação "
                        "sobre sinais de alerta e acompanhamento ambulatorial.",
        "fatores": "Fatores de risco presentes",
        "sem_fatores": "Nenhum dos principais fatores de risco está presente.",
        "acoes": "Ações de transição de cuidado (ilustrativas)",
        "acoes_lista": ["Revisar o plano de alta e a medicação com o paciente e a família",
                        "Educação em insulinoterapia e sinais de hipo e hiperglicemia",
                        "Retorno ambulatorial em até 7 dias",
                        "Contato telefônico em 48 a 72 horas"],
        "idoso": "Paciente com 80 anos ou mais: o modelo identifica pior o risco nessa faixa. "
                 "Vale uma avaliação complementar de fragilidade, funcionalidade e suporte familiar.",
        "f_destino": "Alta para {d}", "f_intern": "{n} internações no último ano",
        "f_emerg": "{n} ida(s) à emergência", "f_hosp": "Internações anteriores neste hospital",
        "f_compl": "Diabetes com complicação", "f_insulina": "Insulina ajustada",
        "f_hba1c": "HbA1c não medida",
        "achados_intro": "Taxa de readmissão em menos de 30 dias por fator, em 99.340 internações elegíveis.",
        "achados": [
            ("01_internacoes_previas.png", "Histórico: o fator mais forte da análise exploratória."),
            ("03_destino_alta.png", "Para onde o paciente vai depois da alta muda muito o risco."),
            ("04_hba1c.png", "A HbA1c não foi medida em 83% das internações."),
            ("05_insulina.png", "Ajustar a insulina marca o paciente descompensado."),
            ("06_diabetes_complicado.png", "Diabetes com complicação registrada eleva o risco."),
            ("07_tempo_internacao.png", "Internações mais longas, mais readmissão."),
        ],
        "modelo": "Modelo", "auc": "ROC-AUC (teste)", "prauc": "PR-AUC (teste)",
        "auc_ajuda": "0,5 = sorteio; 1,0 = perfeito.",
        "modelo_texto": """
- Treino e teste separados **por paciente**: o modelo é avaliado só em pacientes que nunca viu.
- Os **20% de maior risco** concentram **41% das readmissões** do conjunto de teste.
- No decil de maior risco, **28%** voltam em até 30 dias; no de menor risco, **4%**.
- O desempenho é parecido entre raças e gêneros, mas **menor em pacientes com 80 anos ou mais**.
""",
        "modelo_figs": ["11_decis_de_risco.png", "14_subgrupos.png"],
        "limitacoes": """
**Limitações**
- Dados de 1999–2008, de hospitais dos EUA. Antes de qualquer uso real, o modelo precisaria ser
  revalidado em dados locais e atuais.
- Não há variáveis sociais, funcionais nem de cuidado pós-alta.
- O modelo mostra **associação, não causa**.
""",
        "rodape": "Código, análise e protocolos assistenciais no GitHub",
    },
    "en": {
        "titulo": "30-day readmission risk",
        "subtitulo": "Supporting discharge planning priorities for patients with diabetes. "
                     "Model trained on 99,000 admissions from 130 US hospitals (1999–2008).",
        "autora": "A project by Leticia Mendes, nurse and data analyst",
        "aviso": "Portfolio project. Not for real clinical decisions.",
        "abas": ["Score a patient", "Key findings", "About the model"],
        "paciente": "Patient", "historico": "Past year",
        "internacao": "Current admission", "diabetes": "Diabetes",
        "idade": "Age", "idade_ajuda": "The dataset records age in 10-year bands.",
        "genero": "Gender", "raca": "Race",
        "n_intern": "Inpatient admissions", "n_emerg": "Emergency visits", "n_ambul": "Outpatient visits",
        "n_hosp": "Previous admissions at this hospital",
        "n_hosp_ajuda": "How many times the patient already appears in this hospital's records.",
        "tipo": "Admission type", "origem": "Admission source", "dias": "Length of stay (days)",
        "diag": "Primary diagnosis", "destino": "Discharge destination",
        "n_diag": "Number of recorded diagnoses", "n_meds": "Number of medications during the stay",
        "hba1c": "HbA1c", "insulina": "Insulin", "metformina": "Metformin",
        "complicado": "With complications",
        "complicado_ajuda": "Any diabetes diagnosis with complications (ICD-9 250.1 to 250.9).",
        "mudou": "Medication changed",
        "mudou_ajuda": "Diabetes medication was changed during the stay.",
        "botao": "Score this patient",
        "pulseira": "Readmission risk",
        "alto": "high", "habitual": "usual",
        "posicao": "Higher than {p}% of test-set admissions",
        "limite": "high-risk threshold (top 20%)",
        "escore": "Model score: {s}",
        "escore_ajuda": "A 0–1 score. It ranks risk but is not the actual probability of readmission.",
        "msg_alto": "This patient is in the top 20% by risk. In this group, about 23% are readmitted "
                    "within 30 days (overall rate: {t}).",
        "msg_habitual": "Risk within the usual range. Keep the standard discharge plan, with guidance on "
                        "warning signs and outpatient follow-up.",
        "fatores": "Risk factors present",
        "sem_fatores": "None of the main risk factors is present.",
        "acoes": "Transition-of-care actions (illustrative)",
        "acoes_lista": ["Review the discharge plan and medications with the patient and family",
                        "Insulin education, including signs of hypo- and hyperglycaemia",
                        "Outpatient follow-up within 7 days",
                        "Phone call 48 to 72 hours after discharge"],
        "idoso": "Patient aged 80 or over: the model is less able to identify risk in this group. "
                 "Consider a complementary frailty, function and family-support assessment.",
        "f_destino": "Discharged to {d}", "f_intern": "{n} admissions in the past year",
        "f_emerg": "{n} emergency visit(s)", "f_hosp": "Previous admissions at this hospital",
        "f_compl": "Diabetes with complications", "f_insulina": "Insulin adjusted",
        "f_hba1c": "HbA1c not measured",
        "achados_intro": "30-day readmission rate by factor, across 99,340 eligible admissions.",
        "achados": [
            ("en/01_prior_admissions.png", "History: the strongest factor in the exploratory analysis."),
            ("en/03_discharge_destination.png", "Where patients go after discharge changes their risk."),
            ("en/04_hba1c.png", "HbA1c was not measured in 83% of admissions."),
            ("en/05_insulin.png", "Insulin adjustments flag patients whose diabetes is less controlled."),
            ("en/06_diabetes_complications.png", "Recorded diabetes complications raise the risk."),
            ("en/07_length_of_stay.png", "Longer stays, more readmissions."),
        ],
        "modelo": "Model", "auc": "ROC-AUC (test)", "prauc": "PR-AUC (test)",
        "auc_ajuda": "0.5 = random; 1.0 = perfect.",
        "modelo_texto": """
- Train and test sets split **by patient**: the model is evaluated only on patients it has never seen.
- The **top 20%** by risk account for **41% of readmissions** in the test set.
- In the highest risk decile, **28%** are readmitted within 30 days; in the lowest, **4%**.
- Performance is similar across race and gender, but **lower for patients aged 80+**.
""",
        "modelo_figs": ["en/11_risk_deciles.png", "en/14_subgroups.png"],
        "limitacoes": """
**Limitations**
- Data from 1999–2008, from US hospitals. Before any real use, the model would need revalidation on
  current, local data.
- No social, functional or post-discharge variables are available.
- The model shows **association, not causation**.
""",
        "rodape": "Code, analysis and care protocols on GitHub",
    },
}

# ---------------------------------------------------------------------
# Estilo
# ---------------------------------------------------------------------
ESTILO = """
<style>
:root {
  --tinta: #16324f; --tinta-2: #4a6178; --azul: #2a78d6; --azul-claro: #eaf2fc;
  --linha: #d5e3f3; --verde: #0f6e56; --verde-claro: #e1f5ee; --verde-borda: #1d9e75;
  --ambar: #633806; --ambar-claro: #faeeda; --ambar-borda: #ba7517;
}
.block-container { padding-top: 1.5rem; max-width: 1180px; }
h1, h2, h3 { color: var(--tinta); letter-spacing: -0.01em; }

.topo { position: relative; padding: 0.25rem 0 0; }
.topo h1 { font-size: 2.4rem; line-height: 1.15; margin: 0 0 0.5rem; padding: 0; }
.topo p.sub { color: var(--tinta-2); font-size: 1.05rem; max-width: 62ch; margin: 0 0 0.75rem; }
.topo .autora { font-size: 0.95rem; color: var(--tinta); }
.topo .autora a { color: var(--azul); text-decoration: none; margin-left: 0.75rem; }
.topo .autora a:hover { text-decoration: underline; }
.topo .aviso { font-size: 0.85rem; color: var(--tinta-2); margin-top: 0.15rem; }
.ecg { display: block; width: 100%; height: 56px; margin: 0.75rem 0 0.25rem; }
.ecg path { fill: none; stroke: var(--azul); stroke-width: 2.2; stroke-linejoin: round;
  stroke-dasharray: 1600; stroke-dashoffset: 1600; animation: tracar 2.4s ease-out 0.2s forwards; }
@keyframes tracar { to { stroke-dashoffset: 0; } }
@media (prefers-reduced-motion: reduce) { .ecg path { animation: none; stroke-dashoffset: 0; } }

.secao { display: flex; align-items: center; gap: 0.5rem; color: var(--tinta);
  font-weight: 700; font-size: 1.1rem; margin: 0.25rem 0 0.75rem; }
.secao svg { width: 22px; height: 22px; stroke: var(--azul); flex: none; }

.pulseira { display: flex; align-items: center; gap: 1rem; border-radius: 999px;
  padding: 0.9rem 1.5rem; margin: 0.5rem 0 1rem; border: 1.5px solid; }
.pulseira .furo { width: 16px; height: 16px; border-radius: 50%; border: 3px solid; flex: none; background: #fff; }
.pulseira .rotulo { font-size: 0.9rem; }
.pulseira .faixa { font-size: 1.6rem; font-weight: 700; line-height: 1.1; }
.pulseira .codigo { margin-left: auto; display: flex; gap: 3px; align-items: stretch; height: 34px; opacity: 0.7; }
.pulseira .codigo i { display: block; background: currentColor; }
.pulseira.alto { background: var(--ambar-claro); border-color: var(--ambar-borda); color: var(--ambar); }
.pulseira.alto .furo { border-color: var(--ambar-borda); }
.pulseira.habitual { background: var(--verde-claro); border-color: var(--verde-borda); color: var(--verde); }
.pulseira.habitual .furo { border-color: var(--verde-borda); }

.escala { position: relative; margin: 0.25rem 0 0.4rem; }
.escala .trilho { height: 10px; border-radius: 5px; background: linear-gradient(90deg, #eaf2fc, #86b6ef 55%, #1c5cab); }
.escala .marca { position: absolute; top: -6px; width: 4px; height: 22px; border-radius: 2px;
  background: var(--tinta); transform: translateX(-2px); }
.escala .corte { position: absolute; top: 14px; border-left: 1.5px dashed var(--tinta-2); height: 10px; }
.legenda-escala { display: flex; justify-content: space-between; gap: 1rem; font-size: 0.85rem;
  color: var(--tinta-2); margin-top: 0.75rem; }

.leg-corte { text-align: right; }
.leg-corte::before { content: ""; display: inline-block; height: 0.9em; margin-right: 0.4rem;
  border-left: 1.5px dashed var(--tinta-2); vertical-align: -0.1em; }
.chips { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.4rem 0 0.25rem; }
.chip { background: var(--azul-claro); color: var(--tinta); border: 1px solid var(--linha);
  border-radius: 999px; padding: 0.3rem 0.8rem; font-size: 0.9rem; }
.rodape { margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid var(--linha);
  font-size: 0.9rem; color: var(--tinta-2); }
.rodape a { color: var(--azul); }
</style>
"""

# Icones de contorno (estilo Tabler)
ICONES = {
    "paciente": '<circle cx="12" cy="7" r="4"/><path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/>',
    "historico": '<path d="M12 8v4l2 2"/><path d="M3.05 11a9 9 0 1 1 .5 4m-.5 5v-5h5"/>',
    "internacao": '<path d="M3 7v11m0-4h18m0 4v-8a2 2 0 0 0-2-2h-8v6"/><circle cx="7" cy="10" r="1"/>',
    "diabetes": '<path d="M12 3l5 7a6 6 0 1 1-10 0z"/>',
}


def icone(nome):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{ICONES[nome]}</svg>')


def secao(nome, titulo):
    st.markdown(f'<div class="secao">{icone(nome)}<span>{titulo}</span></div>', unsafe_allow_html=True)


# Linha de ECG: tres batimentos ao longo da largura.
def _batimento(x):
    return (f"L{x} 30 L{x+8} 30 Q{x+14} 22 {x+20} 30 L{x+30} 30 L{x+34} 36 L{x+40} 6 L{x+46} 48 "
            f"L{x+51} 30 L{x+62} 30 Q{x+72} 18 {x+82} 30")


ECG = ('<svg class="ecg" viewBox="0 0 1000 56" preserveAspectRatio="none" aria-hidden="true">'
       f'<path d="M0 30 {_batimento(140)} {_batimento(480)} {_batimento(800)} L1000 30"/></svg>')


@st.cache_resource
def carregar_modelo():
    return joblib.load(RAIZ / "models" / "modelo_readmissao.joblib")


art = carregar_modelo()
CAT = art["categorias"]

# ---------------------------------------------------------------------
# Idioma
# ---------------------------------------------------------------------
if "idioma" not in st.session_state:
    st.session_state.idioma = "en" if st.query_params.get("lang", "pt").lower() == "en" else "pt"


CAMPOS = ["k_idade", "k_genero", "k_raca", "k_intern", "k_emerg", "k_ambul", "k_hosp", "k_tipo",
          "k_origem", "k_dias", "k_diag", "k_destino", "k_ndiag", "k_nmeds", "k_hba1c", "k_insulina",
          "k_metformina", "k_compl", "k_mudou"]


def trocar_idioma():
    antigo = st.session_state.idioma
    novo = (st.session_state.botao_idioma or "PT").lower()
    # Cada idioma tem seus proprios campos (para os menus mostrarem os rotulos certos);
    # na troca, os valores preenchidos passam para os campos do novo idioma.
    for campo in CAMPOS:
        if f"{campo}_{antigo}" in st.session_state:
            st.session_state[f"{campo}_{novo}"] = st.session_state[f"{campo}_{antigo}"]
    st.session_state.idioma = novo
    st.query_params["lang"] = novo


st.markdown(ESTILO, unsafe_allow_html=True)
_, col_idioma = st.columns([6, 1])
with col_idioma:
    st.segmented_control("Idioma / Language", ["PT", "EN"], key="botao_idioma",
                         default=st.session_state.idioma.upper(), on_change=trocar_idioma,
                         label_visibility="collapsed")
L = st.session_state.idioma
T = TXT[L]


def num(valor, casas=2):
    texto = f"{valor:.{casas}f}"
    return texto.replace(".", ",") if L == "pt" else texto


def campo(nome, **padrao):
    """Chave do campo no idioma atual; o valor padrao so entra se o campo ainda nao existe."""
    chave = f"{nome}_{L}"
    return {"key": chave} if chave in st.session_state else {"key": chave, **padrao}


def escolha(label, coluna, nome, ordem=None):
    opcoes = ordem or CAT[coluna]
    padrao = art["padroes"][coluna]
    return st.selectbox(label, opcoes, format_func=lambda v: rotulo(v, L),
                        **campo(nome, index=opcoes.index(padrao) if padrao in opcoes else 0))


# ---------------------------------------------------------------------
# Topo
# ---------------------------------------------------------------------
links = f'<a href="{REPO}" target="_blank">GitHub</a>'
if LINKEDIN:
    links += f'<a href="{LINKEDIN}" target="_blank">LinkedIn</a>'
st.markdown(
    f'<div class="topo"><h1>{T["titulo"]}</h1><p class="sub">{T["subtitulo"]}</p>'
    f'<div class="autora">{T["autora"]}{links}</div>'
    f'<div class="aviso">{T["aviso"]}</div>{ECG}</div>',
    unsafe_allow_html=True,
)

aba_risco, aba_achados, aba_modelo = st.tabs(T["abas"])

# ---------------------------------------------------------------------
with aba_risco:
    with st.form("paciente", border=True):
        c1, c2, c3, c4 = st.columns(4, gap="large")

        with c1:
            secao("paciente", T["paciente"])
            idade = st.slider(T["idade"], 5, 95, step=10, help=T["idade_ajuda"],
                              **campo("k_idade", value=int(art["padroes"]["idade"])))
            genero = escolha(T["genero"], "gender", "k_genero")
            raca = escolha(T["raca"], "race", "k_raca")

        with c2:
            secao("historico", T["historico"])
            n_intern = st.number_input(T["n_intern"], 0, 25, **campo("k_intern", value=0))
            n_emerg = st.number_input(T["n_emerg"], 0, 80, **campo("k_emerg", value=0))
            n_ambul = st.number_input(T["n_ambul"], 0, 50, **campo("k_ambul", value=0))
            n_previas_hosp = st.number_input(T["n_hosp"], 0, 30, help=T["n_hosp_ajuda"], **campo("k_hosp", value=0))

        with c3:
            secao("internacao", T["internacao"])
            tipo = escolha(T["tipo"], "tipo_admissao", "k_tipo")
            origem = escolha(T["origem"], "origem_admissao", "k_origem")
            dias = st.slider(T["dias"], 1, 14, **campo("k_dias", value=int(art["padroes"]["time_in_hospital"])))
            diag = escolha(T["diag"], "diag_1_grupo", "k_diag")
            destino = escolha(T["destino"], "destino_alta", "k_destino")
            n_diag = st.slider(T["n_diag"], 1, 16, **campo("k_ndiag", value=int(art["padroes"]["number_diagnoses"])))
            n_meds = st.slider(T["n_meds"], 1, 80, **campo("k_nmeds", value=int(art["padroes"]["num_medications"])))

        with c4:
            secao("diabetes", T["diabetes"])
            hba1c = escolha(T["hba1c"], "A1Cresult", "k_hba1c", ordem=["Nao_medido", "Norm", ">7", ">8"])
            insulina = escolha(T["insulina"], "insulin", "k_insulina", ordem=["No", "Steady", "Up", "Down"])
            metformina = escolha(T["metformina"], "metformin", "k_metformina", ordem=["No", "Steady", "Up", "Down"])
            complicado = st.checkbox(T["complicado"], help=T["complicado_ajuda"], **campo("k_compl"))
            mudou = st.checkbox(T["mudou"], help=T["mudou_ajuda"], **campo("k_mudou"))

        if st.form_submit_button(T["botao"], type="primary", width="stretch"):
            # Guarda a entrada: o resultado continua na tela se o idioma for trocado.
            st.session_state.entrada = {
                "idade": idade, "gender": genero, "race": raca,
                "number_inpatient": n_intern, "number_emergency": n_emerg, "number_outpatient": n_ambul,
                "ordem_internacao": n_previas_hosp + 1,
                "tipo_admissao": tipo, "origem_admissao": origem, "time_in_hospital": dias,
                "diag_1_grupo": diag, "destino_alta": destino,
                "number_diagnoses": n_diag, "num_medications": n_meds,
                "A1Cresult": hba1c, "insulin": insulina, "metformin": metformina,
                "diabetes_complicado": int(complicado), "mudou_medicacao": int(mudou),
            }

    if "entrada" in st.session_state:
        e = st.session_state.entrada
        # Comeca com o paciente "tipico" e sobrescreve com o que foi informado.
        p = dict(art["padroes"])
        p.update(e)
        # Variaveis derivadas (mesma regra do etl/pipeline.py).
        meds = [p[m] for m in ("metformin", "repaglinide", "nateglinide", "glimepiride", "glipizide",
                               "glyburide", "pioglitazone", "rosiglitazone", "acarbose", "insulin",
                               "glyburide-metformin")]
        p["n_medicamentos_diabetes"] = sum(m != "No" for m in meds)
        p["n_doses_alteradas"] = sum(m in ("Up", "Down") for m in meds)
        p["usa_medicacao_diabetes"] = int(p["n_medicamentos_diabetes"] > 0)
        p["total_visitas_previas"] = e["number_inpatient"] + e["number_emergency"] + e["number_outpatient"]

        entrada = pd.DataFrame([p])[art["colunas"]]
        score = float(art["modelo"].predict_proba(entrada)[0, 1])
        # percentis_risco[k] = percentil k do escore no conjunto de teste.
        percentil = min(100, max(0, bisect_left(art["percentis_risco"], score) - 1))
        alto = score >= art["corte_alto_risco"]
        faixa = "alto" if alto else "habitual"

        st.write("")
        col_res, col_acoes = st.columns([3, 2], gap="large")
        with col_res:
            codigo = "".join(f'<i style="width:{w}px"></i>' for w in (2, 1, 3, 1, 1, 2, 4, 1, 2, 1, 3, 2, 1))
            st.markdown(
                f'<div class="pulseira {faixa}" role="status">'
                f'<span class="furo"></span>'
                f'<span><div class="rotulo">{T["pulseira"]}</div><div class="faixa">{T[faixa]}</div></span>'
                f'<span class="codigo" aria-hidden="true">{codigo}</span></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="escala"><div class="trilho"></div>'
                f'<div class="marca" style="left:{percentil}%"></div>'
                f'<div class="corte" style="left:80%"></div></div>'
                f'<div class="legenda-escala"><span>{T["posicao"].format(p=percentil)}</span>'
                f'<span class="leg-corte">{T["limite"]}</span></div>',
                unsafe_allow_html=True,
            )
            st.caption(T["escore"].format(s=num(score)), help=T["escore_ajuda"])

            if alto:
                st.markdown(T["msg_alto"].format(t=f"{art['taxa_base']:.0%}"))
            else:
                st.markdown(T["msg_habitual"])

            fatores = []
            if e["destino_alta"] in ("Reabilitacao", "Psiquiatria", "Outro_hospital"):
                fatores.append(T["f_destino"].format(d=rotulo(e["destino_alta"], L).lower()))
            if e["number_inpatient"] >= 2:
                fatores.append(T["f_intern"].format(n=e["number_inpatient"]))
            if e["number_emergency"] >= 1:
                fatores.append(T["f_emerg"].format(n=e["number_emergency"]))
            if e["ordem_internacao"] > 1:
                fatores.append(T["f_hosp"])
            if e["diabetes_complicado"]:
                fatores.append(T["f_compl"])
            if e["insulin"] in ("Up", "Down"):
                fatores.append(T["f_insulina"])
            if e["A1Cresult"] == "Nao_medido":
                fatores.append(T["f_hba1c"])
            st.markdown(f"**{T['fatores']}**")
            if fatores:
                st.markdown('<div class="chips">' + "".join(f'<span class="chip">{f}</span>' for f in fatores)
                            + "</div>", unsafe_allow_html=True)
            else:
                st.markdown(T["sem_fatores"])

        with col_acoes:
            if alto:
                st.markdown(f"**{T['acoes']}**")
                st.markdown("\n".join(f"- {a}" for a in T["acoes_lista"]))
            if e["idade"] >= 80:
                st.info(T["idoso"], icon=":material/elderly:")

# ---------------------------------------------------------------------
with aba_achados:
    st.markdown(T["achados_intro"])
    figuras = T["achados"]
    for i in range(0, len(figuras), 2):
        cols = st.columns(2, gap="large")
        for col, (arquivo, legenda) in zip(cols, figuras[i:i + 2]):
            col.image(str(FIGURAS / arquivo), caption=legenda, width="stretch")

# ---------------------------------------------------------------------
with aba_modelo:
    m = art["metricas_teste"]
    a, b, c = st.columns(3)
    a.metric(T["modelo"], "Gradient boosting")
    b.metric(T["auc"], num(m["ROC-AUC"], 3), help=T["auc_ajuda"])
    c.metric(T["prauc"], num(m["PR-AUC"], 3))
    st.markdown(T["modelo_texto"])
    c1, c2 = st.columns(2, gap="large")
    c1.image(str(FIGURAS / T["modelo_figs"][0]), width="stretch")
    c2.image(str(FIGURAS / T["modelo_figs"][1]), width="stretch")
    st.markdown(T["limitacoes"])

st.markdown(f'<div class="rodape"><a href="{REPO}" target="_blank">{T["rodape"]}</a></div>',
            unsafe_allow_html=True)
