"""Dashboard Streamlit — Radar de Políticas Municipais.

Para rodar:
    cd radar_clear
    streamlit run dashboard/app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"

st.set_page_config(
    page_title="Radar de Políticas Municipais — MVP",
    page_icon="📡",
    layout="wide",
)


@st.cache_data
def load_data():
    contratos = pd.read_parquet(DATA / "contratos_classificados.parquet")
    agg = pd.read_parquet(DATA / "municipios_eixos.parquet")
    return contratos, agg


contratos, agg = load_data()

# ---------------------------------------------------------------------------
# Cabeçalho e disclaimer metodológico
# ---------------------------------------------------------------------------
st.title("📡 Radar de Políticas Municipais — MVP")
st.caption(
    "Protótipo CLEAR · Taxonomia v0.2 · "
    "Dados: PNCP, 15/09/2025 (amostra de demonstração)"
)

with st.expander("⚠️ Leia antes de interpretar qualquer número", expanded=False):
    st.markdown(
        """
        Esta ferramenta mostra **intensidade de documentação** — a quantidade
        de registros administrativos públicos cujo objeto declarado é
        compatível com uma agenda de política pública. **Não é** uma medida
        de implementação real. Municípios com maior capacidade burocrática
        produzem sistematicamente mais registros, o que enviesa qualquer
        leitura comparativa.

        **Limitações específicas desta amostra:**
        - Janela de **1 dia útil** apenas (15/09/2025) — qualquer ranking
          reflete picos contratuais, não política sustentada.
        - Apenas a fonte PNCP foi processada nesta rodada.
        - A taxonomia v0.2 ainda admite falsos positivos (ex: contratos de
          insumos genéricos para escolas de educação infantil).

        Para uso responsável, esta ferramenta deve ser combinada com:
        leitura qualitativa do objeto do contrato, ampliação temporal,
        cruzamento com sistemas setoriais (SIOPS/SIOPE/Censo SUAS) e,
        idealmente, validação direta com o município.
        """
    )

# ---------------------------------------------------------------------------
# Métricas de cabeçalho
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Contratos classificados", f"{len(contratos):,}")
col2.metric("Municípios com registro", f"{contratos.codigo_ibge.nunique()}")
col3.metric("UFs representadas", f"{contratos.uf.nunique()}")
col4.metric(
    "Valor total (R$)",
    f"{contratos.valor_global.sum():,.0f}".replace(",", "."),
)

# ---------------------------------------------------------------------------
# Visão por eixo
# ---------------------------------------------------------------------------
st.header("Distribuição por eixo temático")

dist = (
    contratos.groupby("eixo_id")
    .agg(
        n_classificacoes=("numero_controle_pncp", "count"),
        n_contratos=("numero_controle_pncp", "nunique"),
        n_municipios=("codigo_ibge", "nunique"),
        valor_total=("valor_global", "sum"),
    )
    .reset_index()
    .sort_values("n_contratos", ascending=False)
)

col_a, col_b = st.columns([2, 3])
with col_a:
    st.dataframe(
        dist.rename(
            columns={
                "eixo_id": "Eixo",
                "n_classificacoes": "Classificações",
                "n_contratos": "Contratos únicos",
                "n_municipios": "Municípios",
                "valor_total": "Valor R$",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )
with col_b:
    fig = px.bar(
        dist,
        x="eixo_id",
        y="n_contratos",
        title="Contratos únicos por eixo",
        labels={"eixo_id": "Eixo", "n_contratos": "Contratos"},
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Filtro por eixo + lista de municípios
# ---------------------------------------------------------------------------
st.header("Municípios por eixo")

eixo_sel = st.selectbox(
    "Selecione um eixo",
    options=sorted(agg.eixo_id.unique()),
    format_func=lambda x: x.replace("_", " ").title(),
)

sub = agg[agg.eixo_id == eixo_sel].sort_values("n_contratos", ascending=False)
st.dataframe(
    sub.rename(
        columns={
            "municipio": "Município",
            "uf": "UF",
            "n_contratos": "Contratos",
            "valor_total": "Valor R$",
            "subeixos_atingidos": "Subeixos",
            "rotulo_nivel": "Nível documentação",
        }
    )[["Município", "UF", "Contratos", "Valor R$", "Subeixos", "Nível documentação"]],
    hide_index=True,
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# Inspeção de contratos individuais
# ---------------------------------------------------------------------------
st.header("Inspeção de contratos individuais")
st.caption(
    "Sempre verifique o objeto antes de interpretar a classificação. "
    "Falsos positivos são esperados nesta versão da taxonomia."
)

municipios_no_eixo = sorted(sub.municipio.dropna().unique())
if municipios_no_eixo:
    mun_sel = st.selectbox("Município", options=municipios_no_eixo)
    detalhe = contratos[
        (contratos.eixo_id == eixo_sel) & (contratos.municipio == mun_sel)
    ][
        [
            "data_assinatura",
            "subeixo_id",
            "keywords_hit",
            "valor_global",
            "objeto",
            "orgao_razao_social",
        ]
    ].reset_index(drop=True)
    st.dataframe(detalhe, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------------------
# Rodapé
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Radar de Políticas Municipais · Protótipo metodológico · "
    "Dados públicos do PNCP · Taxonomia versionada em "
    "`radar_policy/taxonomy/taxonomy_v0.yaml`"
)
