"""English versions of the key charts, used in the English README and the English dashboard.

Run from the project root (after etl/pipeline.py and notebooks/02_modelo.ipynb):
    ./venv/bin/python reports/figuras_readme_en.py

Output: reports/figures/en/*.png
"""

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "reports" / "figures" / "en"
SAIDA.mkdir(parents=True, exist_ok=True)
SEMENTE = 42  # same split as notebooks/02_modelo.ipynb

AZUL, CINZA, TINTA, TINTA_2, SUPERFICIE = "#2a78d6", "#8a8984", "#0b0b0b", "#52514e", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE,
    "axes.edgecolor": "#d6d5d0", "axes.labelcolor": TINTA_2,
    "xtick.color": TINTA_2, "ytick.color": TINTA_2, "text.color": TINTA,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#ebeae6", "grid.linewidth": 0.8,
    "axes.axisbelow": True, "font.size": 11, "figure.dpi": 110,
})
pct = plt.FuncFormatter(lambda v, _: f"{v:.0%}")

DESTINOS = {
    "Casa": "Home", "Casa_com_home_care": "Home with home health care",
    "SNF": "Skilled nursing facility", "ICF": "Intermediate care facility",
    "Reabilitacao": "Rehabilitation", "Outro_hospital": "Another hospital",
    "Longa_permanencia": "Long-term care hospital", "Alta_a_pedido": "Left against medical advice",
    "Psiquiatria": "Psychiatric hospital", "Outro_ou_desconhecido": "Other / unknown",
}
RACAS = {"Caucasian": "White", "AfricanAmerican": "Black (African American)", "Hispanic": "Hispanic",
         "Asian": "Asian", "Other": "Other", "Desconhecida": "Not recorded"}
GENEROS = {"Female": "Female", "Male": "Male"}


def wilson(eventos, n, z=1.96):
    p = eventos / n
    centro = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    meia = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return centro - meia, centro + meia


def titulo(fig, ax, texto, subtitulo):
    fig.suptitle(texto, x=0.01, ha="left", fontsize=13, fontweight="bold")
    ax.set_title(subtitulo, loc="left", fontsize=9, color=TINTA_2)


def barras_taxa(tabela, rotulos, texto, xlabel, arquivo, taxa_geral, horizontal=False):
    lo, hi = wilson(tabela["sum"], tabela["size"])
    taxa = tabela["mean"]
    erro = [taxa - lo, hi - taxa]
    pos = np.arange(len(tabela))
    if horizontal:
        fig, ax = plt.subplots(figsize=(8, 0.45 * len(tabela) + 1.8), layout="constrained")
        ax.barh(pos, taxa, height=0.6, color=AZUL)
        ax.errorbar(taxa, pos, xerr=erro, fmt="none", ecolor=TINTA, elinewidth=1)
        ax.axvline(taxa_geral, color=TINTA_2, ls="--", lw=1)
        ax.set_yticks(pos, rotulos)
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(pct)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("30-day readmission rate")
    else:
        fig, ax = plt.subplots(figsize=(8, 4.2), layout="constrained")
        ax.bar(pos, taxa, width=0.6, color=AZUL)
        ax.errorbar(pos, taxa, yerr=erro, fmt="none", ecolor=TINTA, elinewidth=1)
        ax.axhline(taxa_geral, color=TINTA_2, ls="--", lw=1)
        ax.set_xticks(pos, rotulos)
        ax.yaxis.set_major_formatter(pct)
        ax.grid(axis="x", visible=False)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("30-day readmission rate")
    for i in {int(np.argmax(taxa.values)), int(np.argmin(taxa.values))}:
        v = taxa.iloc[i]
        if horizontal:
            ax.annotate(f"{v:.1%}", (hi.iloc[i], i), xytext=(4, 0), textcoords="offset points", va="center")
        else:
            ax.annotate(f"{v:.1%}", (i, hi.iloc[i]), xytext=(0, 4), textcoords="offset points", ha="center")
    titulo(fig, ax, texto, f"Dashed line = overall rate ({taxa_geral:.1%}) · black bars = 95% CI")
    fig.savefig(SAIDA / arquivo, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    df = pd.read_csv(RAIZ / "data-processed" / "dataset_modelo.csv")
    geral = df["readmit_30"].mean()

    # 1. Prior admissions
    previas = df["number_inpatient"].clip(upper=5)
    t = df.groupby(previas)["readmit_30"].agg(["size", "sum", "mean"])
    barras_taxa(t, ["0", "1", "2", "3", "4", "5+"],
                "More admissions in the previous year, more readmissions",
                "Inpatient admissions in the previous year", "01_prior_admissions.png", geral)

    # 2. Discharge destination
    t = df.groupby("destino_alta")["readmit_30"].agg(["size", "sum", "mean"]).sort_values("mean", ascending=False)
    barras_taxa(t, [DESTINOS[i] for i in t.index],
                "Discharge to rehabilitation or another facility: more readmissions",
                "", "03_discharge_destination.png", geral, horizontal=True)

    # 3. Diabetes care and length of stay (used by the dashboard in English)
    ordem = ["Nao_medido", "Norm", ">7", ">8"]
    t = df.groupby("A1Cresult")["readmit_30"].agg(["size", "sum", "mean"]).reindex(ordem)
    barras_taxa(t, ["Not measured", "Normal", "> 7%", "> 8%"],
                "HbA1c was not measured in 83% of admissions",
                "HbA1c result", "04_hba1c.png", geral)

    ordem = ["No", "Steady", "Up", "Down"]
    t = df.groupby("insulin")["readmit_30"].agg(["size", "sum", "mean"]).reindex(ordem)
    barras_taxa(t, ["Not used", "Dose kept", "Dose increased", "Dose decreased"],
                "Insulin adjusted during the stay: more readmissions",
                "Insulin", "05_insulin.png", geral)

    t = df.groupby("diabetes_complicado")["readmit_30"].agg(["size", "sum", "mean"])
    barras_taxa(t, ["No", "Yes"],
                "Diabetes with recorded complications raises readmission",
                "Any diabetes diagnosis with complications (ICD-9 250.1–250.9)",
                "06_diabetes_complications.png", geral)

    t = df.groupby("time_in_hospital")["readmit_30"].agg(["size", "sum", "mean"])
    barras_taxa(t, [str(i) for i in t.index],
                "Longer stays, more readmissions",
                "Length of stay (days)", "07_length_of_stay.png", geral)

    # 4. Model: risk deciles and subgroups (same test split as the notebook)
    art = joblib.load(RAIZ / "models" / "modelo_readmissao.joblib")
    y, grupos = df["readmit_30"], df["patient_nbr"]
    X = df.drop(columns=["readmit_30", "patient_nbr"])
    _, idx = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEMENTE).split(X, y, groups=grupos))
    teste = X.iloc[idx].assign(y=y.iloc[idx].values)
    teste["p"] = art["modelo"].predict_proba(X.iloc[idx])[:, 1]

    teste["decil"] = pd.qcut(teste["p"].rank(method="first"), 10, labels=range(1, 11))
    decis = teste.groupby("decil", observed=True)["y"].mean()
    fig, ax = plt.subplots(figsize=(8, 4.2), layout="constrained")
    ax.bar(range(1, 11), decis.values, width=0.6, color=AZUL)
    ax.axhline(teste["y"].mean(), color=TINTA_2, ls="--", lw=1)
    for d in (1, 10):
        ax.annotate(f"{decis.loc[d]:.1%}", (d, decis.loc[d]), xytext=(0, 4), textcoords="offset points", ha="center")
    ax.set_xticks(range(1, 11))
    ax.yaxis.set_major_formatter(pct)
    ax.grid(axis="x", visible=False)
    ax.set(xlabel="Predicted risk decile (1 = lowest, 10 = highest)", ylabel="Observed 30-day readmission")
    titulo(fig, ax, "The model separates who comes back from who does not",
           f"Test set (patients never seen in training) · dashed line = overall rate ({teste['y'].mean():.1%})")
    fig.savefig(SAIDA / "11_risk_deciles.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    rng = np.random.default_rng(SEMENTE)
    teste["idade_faixa"] = pd.cut(teste["idade"], [0, 50, 70, 80, 100], right=False,
                                  labels=["< 50", "50–69", "70–79", "80+"])
    linhas = []
    for col, nome, mapa in [("race", "Race", RACAS), ("gender", "Gender", GENEROS), ("idade_faixa", "Age", None)]:
        for g, d in teste.groupby(col, observed=True):
            if len(d) < 100:
                continue
            yy, pp = d["y"].to_numpy(), d["p"].to_numpy()
            boot = []
            for _ in range(500):
                i = rng.integers(0, len(yy), len(yy))
                if yy[i].min() != yy[i].max():
                    boot.append(roc_auc_score(yy[i], pp[i]))
            linhas.append({"rotulo": f"{nome} · {mapa[g] if mapa else g}", "auc": roc_auc_score(yy, pp),
                           "lo": np.percentile(boot, 2.5), "hi": np.percentile(boot, 97.5)})
    s = pd.DataFrame(linhas).iloc[::-1].reset_index(drop=True)
    auc_geral = roc_auc_score(teste["y"], teste["p"])
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(s) + 1.6), layout="constrained")
    ax.errorbar(s["auc"], s.index, xerr=[s["auc"] - s["lo"], s["hi"] - s["auc"]],
                fmt="o", color=AZUL, ecolor=AZUL, elinewidth=1.5, markersize=7)
    ax.axvline(auc_geral, color=TINTA_2, ls="--", lw=1)
    ax.axvline(0.5, color=CINZA, ls=":", lw=1)
    ax.set_yticks(s.index, s["rotulo"])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("ROC-AUC on the test set (0.5 = random)")
    titulo(fig, ax, "Performance drops in the oldest patients",
           f"Dot = subgroup AUC, bar = 95% bootstrap CI · dashed = overall AUC ({auc_geral:.3f})")
    fig.savefig(SAIDA / "14_subgroups.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved {len(list(SAIDA.glob('*.png')))} figures to {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
