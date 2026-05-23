"""Gera index.html institucional do Radar de Políticas Municipais — CLEAR Lab.

Versão 2.0: paleta light institucional CLEAR, áreas temáticas como porta de
entrada principal (tipo Catálogo IPEA), navegação por seções com âncoras,
gráfico de timeline (ativa quando há ≥30 dias de dados), página de
metodologia separada.

Embarca dados como JSON inline. Arquivo único autocontido, sem dependências.
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "processed"
ASSETS = ROOT / "assets"
GEO = ASSETS / "geo"
OUT = ROOT / "index.html"

# ---------------------------------------------------------------------------
# 1) Carregar dados
# ---------------------------------------------------------------------------
contratos = pd.read_parquet(DATA / "contratos_classificados.parquet")
agg = pd.read_parquet(DATA / "municipios_eixos.parquet")
contratos = contratos.where(pd.notna(contratos), None)
agg = agg.where(pd.notna(agg), None)

# ---------------------------------------------------------------------------
# 1b) Carregar fontes geográficas
# ---------------------------------------------------------------------------
# Centroides ficam embarcados no HTML; polígonos por UF são carregados lazy
# (1 fetch por UF clicada), pra não pesar o site inteiro.
CENTROIDES_PATH = GEO / "centroides_muni.json"
BR_UFS_PATH = GEO / "brasil_ufs.geojson"
GEO_DISPONIVEL = CENTROIDES_PATH.exists() and BR_UFS_PATH.exists()

centroides_map = {}
brasil_ufs_geojson = None
if GEO_DISPONIVEL:
    centroides_map = json.loads(CENTROIDES_PATH.read_text(encoding="utf-8"))
    brasil_ufs_geojson = json.loads(BR_UFS_PATH.read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# 2) Metadados estáticos (taxonomia compilada para o front)
# ---------------------------------------------------------------------------
EIXOS_META = {
    "primeira_infancia": {
        "nome": "Primeira Infância",
        "descricao": "Políticas voltadas à criança de 0 a 6 anos: creche/pré-escola, "
                     "visitação domiciliar (Criança Feliz), pré-natal e neonatal, "
                     "busca ativa vacinal infantil.",
        "marco_legal": "Lei 13.257/2016 (Marco Legal da Primeira Infância) · "
                       "Lei 9.394/1996 (LDB) · Lei 8.069/1990 (ECA)",
        "sistemas_setoriais": "SIOPE · Censo Escolar · e-PCF · SISVAN",
        "cor": "#1c79be",
        "icone": "👶",
        "subeixos": ["Creche e Pré-escola", "Visitação Domiciliar / Criança Feliz",
                     "Pré-natal e Neonatal", "Busca Ativa Vacinal Infantil"],
    },
    "busca_ativa_escolar": {
        "nome": "Busca Ativa Escolar e Permanência",
        "descricao": "Políticas de busca ativa de crianças e adolescentes fora da "
                     "escola, prevenção da evasão e programas de permanência "
                     "(transporte escolar, reforço, contraturno).",
        "marco_legal": "Lei 9.394/1996 (LDB) · Lei 14.113/2020 (FUNDEB) · "
                       "Decreto 9.465/2018",
        "sistemas_setoriais": "Censo Escolar · Plataforma Busca Ativa (UNICEF) · "
                              "Frequência Escolar/Bolsa Família",
        "cor": "#008bce",
        "icone": "🎒",
        "subeixos": ["Busca Ativa Escolar", "Transporte Escolar",
                     "Programas de Permanência e Reforço"],
    },
    "seguranca_alimentar": {
        "nome": "Segurança Alimentar e Nutricional",
        "descricao": "Equipamentos públicos de SAN (restaurantes populares, "
                     "cozinhas comunitárias, bancos de alimentos), alimentação "
                     "escolar (PNAE) e aquisição da agricultura familiar (PAA).",
        "marco_legal": "Lei 11.346/2006 (LOSAN) · Lei 11.947/2009 (PNAE) · "
                       "Lei 14.628/2023",
        "sistemas_setoriais": "SISAN / CAISAN municipal · PNAE/FNDE · PAA Conab",
        "cor": "#a1c62e",
        "icone": "🥬",
        "subeixos": ["Equipamentos Públicos de SAN", "Alimentação Escolar (PNAE)",
                     "Aquisição da Agricultura Familiar (PAA)"],
    },
    "saude_mental": {
        "nome": "Saúde Mental",
        "descricao": "Rede de Atenção Psicossocial (RAPS) municipal: CAPS, "
                     "residências terapêuticas, unidades de acolhimento, ações "
                     "em álcool e outras drogas, prevenção ao suicídio.",
        "marco_legal": "Lei 10.216/2001 (Reforma Psiquiátrica) · "
                       "Portaria GM/MS 3.088/2011 (RAPS)",
        "sistemas_setoriais": "CNES · SIA/SUS · RAAS",
        "cor": "#003a78",
        "icone": "🧠",
        "subeixos": ["CAPS", "Rede de Atenção Psicossocial (geral)",
                     "Álcool e Outras Drogas", "Prevenção ao Suicídio"],
    },
}

SUBEIXOS_LABELS = {
    "creche_pre_escola": "Creche e Pré-escola",
    "visitacao_domiciliar": "Visitação Domiciliar / Criança Feliz",
    "pre_natal_neonatal": "Pré-natal e Neonatal",
    "busca_ativa_vacinal": "Busca Ativa Vacinal Infantil",
    "busca_ativa": "Busca Ativa Escolar",
    "transporte_escolar": "Transporte Escolar",
    "programas_permanencia": "Programas de Permanência e Reforço",
    "equipamentos_san": "Equipamentos Públicos de SAN",
    "alimentacao_escolar": "Alimentação Escolar (PNAE)",
    "agricultura_familiar": "Aquisição da Agricultura Familiar",
    "caps": "CAPS",
    "raps_geral": "Rede de Atenção Psicossocial (geral)",
    "alcool_drogas": "Álcool e Outras Drogas",
    "prevencao_suicidio": "Prevenção ao Suicídio",
}

# ---------------------------------------------------------------------------
# 3) Métricas e agregações
# ---------------------------------------------------------------------------
n_contratos = int(contratos["registro_id"].nunique())
n_municipios = int(contratos["codigo_ibge"].nunique())
n_ufs = int(contratos["uf"].nunique())
valor_total = float(contratos["valor_global"].sum())

# Fontes presentes
if "fonte" in contratos.columns:
    fontes_lista = sorted(contratos["fonte"].dropna().unique().tolist())
    n_fontes = len(fontes_lista)
    fontes_distribuicao = contratos.groupby("fonte")["registro_id"].nunique().to_dict()
else:
    fontes_lista = ["PNCP"]
    n_fontes = 1
    fontes_distribuicao = {"PNCP": n_contratos}

dist = (
    contratos.groupby("eixo_id")
    .agg(
        n_contratos=("registro_id", "nunique"),
        n_municipios=("codigo_ibge", "nunique"),
        valor_total=("valor_global", "sum"),
    )
    .to_dict(orient="index")
)

# Cobertura temporal (range de datas observadas)
# As fontes têm formatos diferentes:
#   - PNCP: 'YYYY-MM-DD' (ISO)
#   - Transferegov: 'DD/MM/YYYY'
#   - SICONFI: 'YYYY-12-31' (a gente preenche assim)
# pd.to_datetime com format='mixed' resolve as 3 sem warnings.
def parse_data_mista(s):
    return pd.to_datetime(s, format="mixed", dayfirst=True, errors="coerce")

datas_assinatura = parse_data_mista(contratos["data_referencia"])
data_min = datas_assinatura.min()
data_max = datas_assinatura.max()
n_dias_observados = (datas_assinatura.dropna().dt.normalize().nunique() or 0)

# Timeline mensal por eixo (só faz sentido com >= 30 dias)
timeline_disponivel = n_dias_observados >= 30
timeline_data = []
if timeline_disponivel:
    df_t = contratos.copy()
    df_t["data_referencia"] = parse_data_mista(df_t["data_referencia"])
    df_t = df_t.dropna(subset=["data_referencia"])
    df_t["ym"] = df_t["data_referencia"].dt.to_period("M").astype(str)
    tl = df_t.groupby(["ym", "eixo_id"])["registro_id"].nunique().reset_index()
    timeline_data = tl.to_dict(orient="records")

# ---------------------------------------------------------------------------
# 3b) Agregações geográficas (mapa de pontos + coroplético por UF)
# ---------------------------------------------------------------------------
# Pontos: 1 linha por município presente, com totais por eixo
pontos_mapa = []
if GEO_DISPONIVEL and not agg.empty:
    # agregação por município (somando eixos)
    por_mun = (
        agg.groupby(["codigo_ibge", "municipio", "uf"], dropna=False)
        .agg(
            n_contratos_total=("n_contratos", "sum"),
            valor_total_geral=("valor_total", "sum"),
            eixos=("eixo_id", lambda s: list(s)),
            n_contratos_por_eixo=("n_contratos", lambda s: list(s)),
        )
        .reset_index()
    )
    for _, row in por_mun.iterrows():
        cod = str(row["codigo_ibge"])
        c = centroides_map.get(cod)
        if not c:
            continue
        # centroides_map é {cod: [lat, lng]}
        lat, lng = c[0], c[1]
        # constrói dict {eixo_id: n_contratos}
        eixos_dict = dict(zip(row["eixos"], row["n_contratos_por_eixo"]))
        pontos_mapa.append({
            "codigo_ibge": cod,
            "municipio": row["municipio"],
            "uf": row["uf"],
            "lat": lat,
            "lng": lng,
            "n_total": int(row["n_contratos_total"]),
            "valor_total": float(row["valor_total_geral"] or 0),
            "por_eixo": {k: int(v) for k, v in eixos_dict.items()},
        })

# Coroplético por UF: total por UF x eixo, e também total agregado
choropleth_uf = {}
if not agg.empty:
    # Total geral por UF
    por_uf_total = agg.groupby("uf").agg(
        n_contratos=("n_contratos", "sum"),
        n_municipios=("codigo_ibge", "nunique"),
        valor_total=("valor_total", "sum"),
    ).to_dict(orient="index")
    # Por eixo
    por_uf_eixo = agg.groupby(["uf", "eixo_id"])["n_contratos"].sum().reset_index()
    por_uf_eixo_dict = {}
    for _, row in por_uf_eixo.iterrows():
        por_uf_eixo_dict.setdefault(row["uf"], {})[row["eixo_id"]] = int(row["n_contratos"])
    for uf, totais in por_uf_total.items():
        if uf is None:
            continue
        choropleth_uf[uf] = {
            "n_contratos": int(totais["n_contratos"] or 0),
            "n_municipios": int(totais["n_municipios"] or 0),
            "valor_total": float(totais["valor_total"] or 0),
            "por_eixo": por_uf_eixo_dict.get(uf, {}),
        }

# Estatística de cobertura de geocoding (transparência sobre quem ficou de fora)
n_munis_base = agg["codigo_ibge"].nunique() if not agg.empty else 0
n_munis_no_mapa = len(pontos_mapa)
geocoding_perdidos = max(0, n_munis_base - n_munis_no_mapa)

# Mapa só "ativa" plenamente se temos GEO carregado E pelo menos 1 município geocodificado
mapa_disponivel = GEO_DISPONIVEL and n_munis_no_mapa > 0

# ---------------------------------------------------------------------------
# 4) JSON embarcado
# ---------------------------------------------------------------------------
contratos_json = contratos.to_dict(orient="records")
agg_json = agg.to_dict(orient="records")

DATA_GERACAO = datetime.now().strftime("%d/%m/%Y às %H:%M")
DATA_PRIMEIRO_REGISTRO = data_min.strftime("%d/%m/%Y") if pd.notna(data_min) else "—"
DATA_ULTIMO_REGISTRO = data_max.strftime("%d/%m/%Y") if pd.notna(data_max) else "—"

# Logo CLEAR inline (SVG)
logo_path = ASSETS / "clear-logo-cor.svg"
if logo_path.exists():
    LOGO_SVG = logo_path.read_text(encoding="utf-8")
else:
    LOGO_SVG = '<span style="font-weight:700;color:#003a78">FGV CLEAR</span>'

# Leaflet inline (CSS + JS) — assets/leaflet.css e assets/leaflet.js
leaflet_css = ASSETS / "leaflet.css"
leaflet_js = ASSETS / "leaflet.js"
if leaflet_css.exists():
    LEAFLET_CSS_TAG = "<style>" + leaflet_css.read_text(encoding="utf-8") + "</style>"
else:
    LEAFLET_CSS_TAG = ""
if leaflet_js.exists():
    LEAFLET_JS_TAG = "<script>" + leaflet_js.read_text(encoding="utf-8") + "</script>"
else:
    LEAFLET_JS_TAG = ""

# ---------------------------------------------------------------------------
# 5) HTML
# ---------------------------------------------------------------------------
HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Radar de Políticas Municipais — CLEAR Lab</title>
<meta name="description" content="Camada de classificação de registros administrativos públicos por agenda de política pública municipal. Projeto CLEAR Lab.">
<style>
  :root {
    /* paleta institucional CLEAR */
    --azul-escuro: #003a78;
    --azul-medio:  #1c79be;
    --azul-claro:  #008bce;
    --azul-cyan:   #00adee;
    --verde:       #a1c62e;
    --grafite:     #04354a;

    /* paleta neutra (modo claro institucional) */
    --bg:        #f7f9fc;
    --bg-card:   #ffffff;
    --bg-soft:   #eef3f8;
    --border:    #d8e1ec;
    --border-strong: #b9c8d8;
    --text:      #1a2b3c;
    --text-2:    #4a5d72;
    --text-dim:  #7a8a9c;

    --warn-bg:   #fff8e6;
    --warn-border: #f0c674;
    --warn-text: #7a5a18;

    --shadow-sm: 0 1px 3px rgba(0,58,120,0.06);
    --shadow-md: 0 4px 12px rgba(0,58,120,0.08);
    --radius:    10px;
  }

  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 15px;
    line-height: 1.55;
  }

  /* -------------------------------------------------- Top bar institucional */
  .topbar {
    background: #fff;
    border-bottom: 1px solid var(--border);
    padding: 12px 0;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: var(--shadow-sm);
  }
  .topbar-inner {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    flex-wrap: wrap;
  }
  .topbar-logo {
    display: flex;
    align-items: center;
    gap: 14px;
  }
  .topbar-logo svg { height: 32px; width: auto; }
  .topbar-divider {
    width: 1px; height: 28px; background: var(--border-strong);
  }
  .topbar-project {
    font-size: 13px;
    color: var(--text-2);
    line-height: 1.3;
  }
  .topbar-project strong {
    display: block;
    color: var(--azul-escuro);
    font-size: 14px;
  }
  .topbar-nav {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }
  .topbar-nav a {
    text-decoration: none;
    color: var(--text-2);
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 14px;
    transition: background 0.15s;
  }
  .topbar-nav a:hover { background: var(--bg-soft); color: var(--azul-escuro); }

  /* -------------------------------------------------- Container e seções */
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
  }
  section {
    padding: 56px 0 24px;
    scroll-margin-top: 80px;
  }
  section + section { border-top: 1px solid var(--border); }

  /* -------------------------------------------------- Hero */
  .hero {
    padding-top: 48px;
    padding-bottom: 32px;
  }
  .hero-tag {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--azul-medio);
    background: var(--bg-soft);
    padding: 4px 12px;
    border-radius: 100px;
    margin-bottom: 16px;
  }
  .hero h1 {
    font-size: 38px;
    line-height: 1.15;
    margin: 0 0 12px;
    color: var(--azul-escuro);
    font-weight: 700;
  }
  .hero .lead {
    font-size: 17px;
    color: var(--text-2);
    max-width: 780px;
    margin: 0 0 28px;
  }
  .hero-meta {
    display: flex;
    gap: 24px;
    font-size: 13px;
    color: var(--text-dim);
    flex-wrap: wrap;
  }
  .hero-meta span strong { color: var(--text-2); }

  /* -------------------------------------------------- Disclaimer */
  .disclaimer {
    background: var(--warn-bg);
    border-left: 4px solid var(--warn-border);
    padding: 16px 20px;
    margin: 28px 0;
    border-radius: 0 var(--radius) var(--radius) 0;
    color: var(--warn-text);
    font-size: 14px;
  }
  .disclaimer strong { color: #6b4d10; }

  /* -------------------------------------------------- Metric cards */
  h2 {
    font-size: 26px;
    color: var(--azul-escuro);
    margin: 0 0 4px;
    font-weight: 700;
  }
  h2 + .section-lead {
    font-size: 15px;
    color: var(--text-2);
    margin: 0 0 28px;
    max-width: 760px;
  }
  h3 {
    font-size: 18px;
    color: var(--azul-escuro);
    margin: 28px 0 12px;
    font-weight: 600;
  }
  .metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin: 8px 0 32px;
  }
  .metric {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 22px;
    box-shadow: var(--shadow-sm);
  }
  .metric-label {
    color: var(--text-dim);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
    margin-bottom: 8px;
  }
  .metric-value {
    font-size: 30px;
    font-weight: 700;
    color: var(--azul-escuro);
    line-height: 1;
  }
  .metric-sub {
    font-size: 12px;
    color: var(--text-dim);
    margin-top: 6px;
  }

  /* -------------------------------------------------- Cards de eixos (porta de entrada) */
  .eixos-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 18px;
    margin: 16px 0;
  }
  .eixo-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px 24px;
    box-shadow: var(--shadow-sm);
    border-top: 4px solid var(--azul-medio);
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .eixo-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }
  .eixo-card h3 {
    margin: 0 0 6px;
    font-size: 18px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .eixo-icon { font-size: 22px; }
  .eixo-card .desc {
    color: var(--text-2);
    font-size: 13.5px;
    line-height: 1.5;
    margin: 0 0 14px;
  }
  .eixo-card .stats {
    display: flex;
    gap: 16px;
    margin: 14px 0;
    padding: 12px 0;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
  }
  .eixo-card .stat {
    flex: 1;
  }
  .eixo-card .stat-val {
    font-size: 20px;
    font-weight: 700;
    color: var(--azul-escuro);
  }
  .eixo-card .stat-label {
    font-size: 11px;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  .eixo-card .meta {
    font-size: 12px;
    color: var(--text-dim);
    margin: 6px 0;
  }
  .eixo-card .meta strong { color: var(--text-2); font-weight: 600; }
  .eixo-card .btn {
    display: inline-block;
    margin-top: 12px;
    font-size: 14px;
    color: var(--azul-medio);
    text-decoration: none;
    font-weight: 600;
  }
  .eixo-card .btn:hover { color: var(--azul-escuro); }

  /* -------------------------------------------------- Tabelas */
  table {
    width: 100%;
    border-collapse: collapse;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    font-size: 14px;
    box-shadow: var(--shadow-sm);
    margin: 14px 0 28px;
  }
  th, td {
    text-align: left;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
  }
  th {
    background: var(--bg-soft);
    font-weight: 600;
    color: var(--azul-escuro);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: var(--bg); }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }

  .bar {
    height: 6px;
    background: var(--bg-soft);
    border-radius: 3px;
    overflow: hidden;
    min-width: 60px;
  }
  .bar-fill { height: 100%; background: var(--azul-medio); }

  /* -------------------------------------------------- Filtros */
  .controls {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
    margin: 14px 0 18px;
    padding: 14px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }
  .controls label {
    font-size: 13px;
    color: var(--text-2);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  select, input[type=text] {
    background: #fff;
    border: 1px solid var(--border-strong);
    color: var(--text);
    padding: 7px 10px;
    border-radius: 6px;
    font-size: 14px;
    min-width: 180px;
    font-family: inherit;
  }
  select:focus, input:focus {
    outline: 2px solid var(--azul-claro);
    outline-offset: -1px;
    border-color: var(--azul-claro);
  }

  /* -------------------------------------------------- Badges nível doc */
  .badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 100px;
    font-size: 11px;
    font-weight: 600;
    background: var(--bg-soft);
    color: var(--text-2);
    margin-right: 4px;
  }
  .badge.lvl-1 { background: #e8f3e0; color: #4a7818; }
  .badge.lvl-2 { background: #d9ecf6; color: #1c5d8a; }
  .badge.lvl-3 { background: #fff0d6; color: #875a18; }
  .badge.lvl-4 { background: #ffd9d9; color: #8a2c2c; }

  /* -------------------------------------------------- Details (contratos) */
  details {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin: 8px 0;
    box-shadow: var(--shadow-sm);
  }
  details summary {
    padding: 12px 18px;
    cursor: pointer;
    font-weight: 500;
    user-select: none;
    list-style: none;
  }
  details summary::-webkit-details-marker { display: none; }
  details summary::before {
    content: "›";
    display: inline-block;
    margin-right: 8px;
    transition: transform 0.15s;
    color: var(--azul-medio);
    font-weight: 700;
  }
  details[open] summary::before { transform: rotate(90deg); }
  details summary:hover { background: var(--bg-soft); }
  details[open] summary { border-bottom: 1px solid var(--border); }
  details .detail-body { padding: 14px 22px 18px; font-size: 13.5px; color: var(--text-2); }
  details .obj-text {
    background: var(--bg-soft);
    border-radius: 6px;
    padding: 12px 14px;
    color: var(--text);
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 12.5px;
    margin-top: 10px;
    white-space: pre-wrap;
    border: 1px solid var(--border);
  }

  /* -------------------------------------------------- Metodologia */
  .meto-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin: 14px 0;
  }
  .meto-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px;
    box-shadow: var(--shadow-sm);
  }
  .meto-card h4 {
    margin: 0 0 10px;
    font-size: 14px;
    color: var(--azul-escuro);
    font-weight: 600;
  }
  .meto-card p {
    margin: 0;
    font-size: 13.5px;
    color: var(--text-2);
    line-height: 1.55;
  }
  ol.meto-list, ul.meto-list {
    padding-left: 22px;
    font-size: 14px;
    color: var(--text-2);
    line-height: 1.7;
  }
  code {
    background: var(--bg-soft);
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 13px;
    color: var(--azul-escuro);
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  }

  /* -------------------------------------------------- Timeline (gráfico) */
  .timeline-wrap {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    margin: 14px 0 28px;
    box-shadow: var(--shadow-sm);
  }
  .timeline-disabled {
    background: var(--bg-soft);
    border: 1px dashed var(--border-strong);
    border-radius: var(--radius);
    padding: 20px;
    text-align: center;
    color: var(--text-dim);
    font-size: 14px;
  }

  /* -------------------------------------------------- Footer */
  footer {
    margin-top: 56px;
    padding: 36px 0 48px;
    background: var(--azul-escuro);
    color: #cdd9e6;
    font-size: 13px;
  }
  footer .container { display: flex; justify-content: space-between; gap: 24px; flex-wrap: wrap; }
  footer a { color: #ffffff; text-decoration: none; }
  footer a:hover { text-decoration: underline; }
  footer h5 {
    color: #fff;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin: 0 0 10px;
    font-weight: 600;
  }

  .muted { color: var(--text-dim); }
  .small { font-size: 13px; }

  @media (max-width: 720px) {
    .hero h1 { font-size: 28px; }
    .topbar-inner { flex-direction: column; align-items: flex-start; }
    .topbar-divider { display: none; }
  }
  /* -------------------------------------------------- Mapa (Leaflet) */
  .map-disclaimer {
    background: var(--bg-soft);
    border-left: 3px solid var(--azul-medio);
    padding: 12px 16px;
    margin: 8px 0 16px;
    border-radius: 0 var(--radius) var(--radius) 0;
    font-size: 13.5px;
    color: var(--text-2);
  }
  .map-disclaimer strong { color: var(--azul-escuro); }
  .map-tabs {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 8px;
    margin: 16px 0 14px;
  }
  .map-tab {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px 14px;
    cursor: pointer;
    font-family: inherit;
    text-align: left;
    transition: all 0.15s;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .map-tab:hover {
    border-color: var(--azul-medio);
    background: var(--bg-soft);
  }
  .map-tab.active {
    border-color: var(--azul-medio);
    background: var(--bg-soft);
    box-shadow: 0 0 0 1px var(--azul-medio);
  }
  .map-tab-num {
    display: inline-block;
    width: 22px; height: 22px;
    line-height: 22px; text-align: center;
    background: var(--azul-medio);
    color: white;
    border-radius: 50%;
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 4px;
  }
  .map-tab.active .map-tab-num { background: var(--azul-escuro); }
  .map-tab-label {
    font-weight: 600;
    color: var(--azul-escuro);
    font-size: 14px;
  }
  .map-tab-desc {
    font-size: 11.5px;
    color: var(--text-dim);
  }
  .map-coverage-badge {
    margin: 14px 0 0;
    padding: 10px 14px;
    background: var(--bg-soft);
    border-radius: var(--radius);
    border: 1px solid var(--border);
    font-size: 13px;
    color: var(--text-2);
  }
  .map-coverage-badge strong { color: var(--azul-escuro); }
  /* Override de fonte do Leaflet para casar com a paleta */
  .leaflet-container {
    font-family: inherit;
    background: var(--bg-soft);
  }
  .leaflet-popup-content-wrapper {
    border-radius: 8px;
    box-shadow: var(--shadow-md);
  }
  .leaflet-popup-content {
    margin: 12px 16px;
    font-size: 13px;
    line-height: 1.5;
    color: var(--text);
  }
  .leaflet-popup-content strong {
    color: var(--azul-escuro);
    font-size: 14px;
  }
  .leaflet-popup-content .popup-stat {
    margin: 4px 0;
    color: var(--text-2);
  }
  .leaflet-popup-content .popup-stat b { color: var(--azul-escuro); }
  .map-legend {
    background: rgba(255,255,255,0.95);
    padding: 10px 14px;
    border-radius: 6px;
    box-shadow: var(--shadow-sm);
    font-size: 12px;
    line-height: 1.6;
    color: var(--text-2);
    border: 1px solid var(--border);
  }
  .map-legend strong { color: var(--azul-escuro); display: block; margin-bottom: 6px; font-size: 12px; }
  .map-legend .legend-row {
    display: flex; align-items: center; gap: 8px;
  }
  .map-legend .legend-dot {
    display: inline-block;
    width: 12px; height: 12px;
    border-radius: 50%;
    border: 1.5px solid #fff;
    box-shadow: 0 0 0 1px rgba(0,0,0,0.1);
  }
  .map-legend .legend-square {
    display: inline-block;
    width: 14px; height: 14px;
    border: 1px solid var(--border);
  }

</style>
__LEAFLET_CSS_TAG__
</head>
<body>

<!-- ============================================================ TOP BAR -->
<div class="topbar">
  <div class="topbar-inner">
    <div class="topbar-logo">
      __LOGO_SVG__
      <div class="topbar-divider"></div>
      <div class="topbar-project">
        <strong>Radar de Políticas Municipais</strong>
        CLEAR Lab · FGV EESP
      </div>
    </div>
    <nav class="topbar-nav">
      <a href="#cobertura">Cobertura</a>
      <a href="#areas">Áreas temáticas</a>
      <a href="#mapa">Mapa</a>
      <a href="#municipios">Municípios</a>
      <a href="#timeline">Linha do tempo</a>
      <a href="#contratos">Contratos</a>
      <a href="#metodologia">Metodologia</a>
    </nav>
  </div>
</div>

<div class="container">

<!-- ============================================================ HERO -->
<section class="hero">
  <span class="hero-tag">Protótipo · v0.2</span>
  <h1>Radar de Políticas Municipais</h1>
  <p class="lead">
    Camada de agregação e classificação de registros administrativos públicos
    por agenda de política pública municipal. Reúne contratações do PNCP,
    propostas de convênios federais (Transferegov) e despesas orçamentárias
    consolidadas (SICONFI/Tesouro) sob uma taxonomia versionada de quatro
    agendas — permitindo ver o ciclo completo: <em>anunciado → aprovado →
    contratado → executado</em>.
  </p>
  <div class="hero-meta">
    <span><strong>Cobertura:</strong> __DATA_PRIMEIRO__ a __DATA_ULTIMO__</span>
    <span><strong>Dias com registro:</strong> __N_DIAS__</span>
    <span><strong>Atualização:</strong> __DATA_GERACAO__</span>
  </div>

  <div class="disclaimer">
    <strong>⚠ Leia antes de interpretar.</strong> Esta ferramenta mede
    <em>intensidade de documentação</em>, não intensidade de implementação.
    Municípios com maior capacidade burocrática produzem sistematicamente mais
    registros administrativos. A ausência de registro não significa ausência
    de política — significa ausência de pegada administrativa capturada por
    esta fonte. Leia a <a href="#metodologia">nota metodológica</a> antes de
    qualquer leitura comparativa entre municípios.
  </div>
</section>

<!-- ============================================================ COBERTURA -->
<section id="cobertura">
  <h2>Cobertura</h2>
  <p class="section-lead">
    Volume agregado da amostra atual. A escala dos números reflete o
    período coletado — quanto mais tempo coletado, mais municípios aparecem.
  </p>
  <div class="metrics">
    <div class="metric">
      <div class="metric-label">Contratos classificados</div>
      <div class="metric-value">__N_CONTRATOS__</div>
      <div class="metric-sub">contratos únicos com aderência a algum eixo</div>
    </div>
    <div class="metric">
      <div class="metric-label">Municípios com registro</div>
      <div class="metric-value">__N_MUNICIPIOS__</div>
      <div class="metric-sub">de 5.570 no Brasil</div>
    </div>
    <div class="metric">
      <div class="metric-label">UFs representadas</div>
      <div class="metric-value">__N_UFS__</div>
      <div class="metric-sub">de 27 unidades da federação</div>
    </div>
    <div class="metric">
      <div class="metric-label">Valor total (R$)</div>
      <div class="metric-value">__VALOR_TOTAL__</div>
      <div class="metric-sub">soma dos contratos classificados</div>
    </div>
    <div class="metric">
      <div class="metric-label">Fontes ativas</div>
      <div class="metric-value">__N_FONTES__</div>
      <div class="metric-sub">__FONTES_LISTA__</div>
    </div>
  </div>
  <div class="map-coverage-badge" style="margin-top:8px">
    <strong>Distribuição por fonte:</strong> <span id="dist-fontes">—</span>
  </div>
</section>

<!-- ============================================================ ÁREAS TEMÁTICAS -->
<section id="areas">
  <h2>Áreas temáticas</h2>
  <p class="section-lead">
    Quatro agendas de política pública municipal organizam a taxonomia.
    Um mesmo contrato pode aparecer em mais de uma agenda (intersetorialidade
    é regra, não exceção: merenda em creche conta em Primeira Infância e em
    Segurança Alimentar).
  </p>
  <div class="eixos-grid" id="eixos-grid"></div>
</section>

<!-- ============================================================ MAPA -->
<section id="mapa">
  <h2>Distribuição geográfica</h2>
  <p class="section-lead">
    Quatro maneiras de olhar a mesma informação, cada uma com um trade-off
    epistemológico explícito. Comece pela aba de cobertura — ela mostra
    onde nossa fonte enxerga e onde não enxerga.
  </p>

  <div class="map-disclaimer">
    <strong>Como ler estes mapas.</strong> A presença de um município no
    mapa indica que ele tem registros classificados nesta amostra.
    Municípios ausentes podem estar implementando políticas sem deixar
    rastros nesta fonte. A geografia da pegada documental
    <em>não é</em> a geografia da política.
  </div>

  <div class="map-tabs" id="map-tabs">
    <button class="map-tab active" data-tab="pontos">
      <span class="map-tab-num">1</span>
      <span class="map-tab-label">Por agenda</span>
      <span class="map-tab-desc">Pontos coloridos por eixo</span>
    </button>
    <button class="map-tab" data-tab="binario">
      <span class="map-tab-num">2</span>
      <span class="map-tab-label">Presença/ausência</span>
      <span class="map-tab-desc">Quem aparece × quem não aparece</span>
    </button>
    <button class="map-tab" data-tab="cobertura">
      <span class="map-tab-num">3</span>
      <span class="map-tab-label">Cobertura da fonte</span>
      <span class="map-tab-desc">Onde a base enxerga (autocrítico)</span>
    </button>
    <button class="map-tab" data-tab="uf">
      <span class="map-tab-num">4</span>
      <span class="map-tab-label">Por UF</span>
      <span class="map-tab-desc">Agregado estadual (clique pra zoom)</span>
    </button>
  </div>

  <div class="map-controls">
    <div class="controls" id="map-control-pontos">
      <label>Eixo:
        <select id="mapa-eixo-pontos">
          <option value="">Todos os eixos</option>
        </select>
      </label>
      <span class="muted small" id="info-pontos"></span>
    </div>
    <div class="controls" id="map-control-binario" style="display:none">
      <label>Eixo:
        <select id="mapa-eixo-binario">
          <option value="">Qualquer eixo</option>
        </select>
      </label>
      <span class="muted small" id="info-binario"></span>
    </div>
    <div class="controls" id="map-control-cobertura" style="display:none">
      <span class="muted small">
        Mostra todos os municípios que aparecem na nossa coleta do PNCP,
        independente de classificação. Útil pra ver onde a fonte tem força
        e onde tem buracos.
      </span>
    </div>
    <div class="controls" id="map-control-uf" style="display:none">
      <label>Eixo:
        <select id="mapa-eixo-uf">
          <option value="">Todos os eixos</option>
        </select>
      </label>
      <button id="btn-voltar-brasil" style="display:none; padding:6px 12px; border-radius:6px; border:1px solid var(--azul-medio); background:white; color:var(--azul-medio); cursor:pointer; font-size:13px; font-weight:600;">← Voltar ao Brasil</button>
      <span class="muted small" id="info-uf"></span>
    </div>
  </div>

  <div id="map" style="height:600px;border-radius:10px;border:1px solid var(--border);box-shadow:var(--shadow-sm);background:#eef3f8;"></div>

  <div id="map-fallback" class="timeline-disabled" style="display:none;margin-top:14px;">
    Mapa não disponível: arquivos geográficos (<code>assets/geo/</code>) ausentes
    ou nenhum município geocodificado.
  </div>

  <div class="map-coverage-badge" id="coverage-badge">
    <strong>Cobertura desta amostra:</strong>
    <span id="cov-text">—</span>
  </div>
</section>


<!-- ============================================================ MUNICÍPIOS -->
<section id="municipios">
  <h2>Municípios</h2>
  <p class="section-lead">
    Distribuição município × eixo, com filtros. O nível de documentação é
    discreto (sem_registros → atividade_intensa) e baseado no número de
    contratos no período.
  </p>
  <div class="controls">
    <label>Eixo:
      <select id="filtro-eixo"><option value="">Todos</option></select>
    </label>
    <label>UF:
      <select id="filtro-uf"><option value="">Todas</option></select>
    </label>
    <label>Buscar:
      <input id="filtro-busca" type="text" placeholder="nome do município...">
    </label>
  </div>
  <table>
    <thead><tr>
      <th>Município</th><th>UF</th><th>Eixo</th>
      <th class="num">Contratos</th><th class="num">Valor (R$)</th>
      <th>Nível doc.</th>
    </tr></thead>
    <tbody id="tbl-municipios"></tbody>
  </table>
  <p class="muted small" id="resumo-municipios"></p>
</section>

<!-- ============================================================ TIMELINE -->
<section id="timeline">
  <h2>Linha do tempo</h2>
  <p class="section-lead">
    Evolução mensal das contratações classificadas, por eixo. Disponível
    apenas quando a base cobre 30 dias ou mais — caso contrário a leitura
    seria enganosa.
  </p>
  <div id="timeline-container"></div>
</section>

<!-- ============================================================ CONTRATOS -->
<section id="contratos">
  <h2>Contratos individuais</h2>
  <p class="section-lead">
    Inspeção contrato a contrato. <strong>Sempre verifique o objeto</strong>
    antes de aceitar a classificação — falsos positivos são esperados nesta
    versão da taxonomia e são insumo para refinamentos futuros.
  </p>
  <div class="controls">
    <label>Fonte:
      <select id="contrato-fonte"><option value="">Todas</option></select>
    </label>
    <label>Eixo:
      <select id="contrato-eixo"><option value="">Todos</option></select>
    </label>
    <label>UF:
      <select id="contrato-uf"><option value="">Todas</option></select>
    </label>
  </div>
  <div id="lista-contratos"></div>
</section>

<!-- ============================================================ METODOLOGIA -->
<section id="metodologia">
  <h2>Metodologia</h2>
  <p class="section-lead">
    Como esta ferramenta é construída, o que ela faz e — sobretudo — o que
    ela não faz.
  </p>

  <div class="meto-grid">
    <div class="meto-card">
      <h4>Princípio epistemológico</h4>
      <p>
        Mede pegada documental, não política. Um município sem registros pode
        estar implementando muito; um com muitos pode estar contratando muito
        sem implementar bem. A correlação entre pegada e implementação é
        fraca e enviesada.
      </p>
    </div>
    <div class="meto-card">
      <h4>Taxonomia versionada</h4>
      <p>
        Arquivo <code>YAML</code> auditável (<code>radar_policy/taxonomy/</code>),
        atualmente na v0.2. Cobre 4 eixos e 14 subeixos. Cada mudança fica em
        diff revisável; cada versão tem changelog no cabeçalho.
      </p>
    </div>
    <div class="meto-card">
      <h4>Matching com word boundary</h4>
      <p>
        Palavras-chave são casadas com regex de boundary, corrigindo falsos
        positivos descobertos no MVP (ex: <code>cei</code> casando em
        "Conceição"). Exclusões explícitas eliminam ruído (papelaria genérica
        para "saúde mental").
      </p>
    </div>
    <div class="meto-card">
      <h4>Multi-eixo proposital</h4>
      <p>
        Um contrato pode ser classificado em vários eixos simultaneamente.
        Agendas de política pública são intersetoriais — forçar uma
        classificação única destruiria informação relevante.
      </p>
    </div>
    <div class="meto-card">
      <h4>Fontes ativas</h4>
      <p>
        <strong>PNCP</strong> (Portal Nacional de Contratações Públicas):
        contratos públicos formalizados desde 2021, esfera municipal.<br>
        <strong>Transferegov / SICONV</strong>: propostas e convênios
        federais discricionários, estágios desde "proposta enviada" até
        "convênio aprovado/rejeitado".<br>
        <strong>SICONFI / Tesouro Nacional</strong>: despesas executadas
        por subfunção orçamentária (RREO Anexo 02), via API oficial.
      </p>
    </div>
    <div class="meto-card">
      <h4>Estágios mapeados</h4>
      <p>
        <strong>Anunciado</strong> (Transferegov: proposta enviada/em análise) →
        <strong>Aprovado</strong> (Transferegov: proposta aprovada, antes da contratação) →
        <strong>Contratado</strong> (PNCP: contrato assinado) →
        <strong>Executado</strong> (SICONFI: despesa empenhada). Um mesmo município
        pode aparecer em vários estágios — sinal de política madura.
      </p>
    </div>
    <div class="meto-card">
      <h4>Fontes previstas</h4>
      <p>
        <strong>Censo SUAS / RMA</strong> (CRAS/CREAS, fase 2, download manual);
        <strong>SIOPE direto</strong> (FNDE, fase 2);
        <strong>diários oficiais municipais</strong> (fase 3, com classificação
        assistida por LLM).
      </p>
    </div>
  </div>

  <h3>Limitações conhecidas</h3>
  <ul class="meto-list">
    <li>Viés sistemático contra municípios pequenos com baixa capacidade
        burocrática — eles deixam menos rastros administrativos.</li>
    <li>Falsos positivos sutis (ex: contratos de insumo genérico para escolas
        de educação infantil contabilizados em primeira infância).</li>
    <li>Cobertura temporal limitada à janela coletada — não é tempo real.</li>
    <li><strong>Saúde mental no SICONFI:</strong> a Portaria MOG 42/1999 não tem
        subfunção própria — fica agregada em "Atenção Básica" ou "Assistência
        Hospitalar". Por isso o eixo Saúde Mental hoje depende quase só de
        PNCP/Transferegov.</li>
    <li>Transferegov inclui propostas <em>rejeitadas</em>: o classificador
        pega o objeto, e o estágio é mostrado como rejeitado — mas o
        registro existe na contagem total. Filtre por estágio se relevante.</li>
  </ul>

  <h3>Próximos passos</h3>
  <ol class="meto-list">
    <li>Expandir a janela temporal para 12 meses contínuos.</li>
    <li>Incluir Transferegov para atravessar o gargalo dos municípios pequenos.</li>
    <li>Score de confiança por classificação (n° de keywords + qualidade do match).</li>
    <li>Validação humana estratificada: amostra rotulada para precisão/recall por subeixo.</li>
    <li>Integração com sistemas setoriais (SIOPS, SIOPE, Censo SUAS).</li>
    <li>Fase 3: fontes não estruturadas (diários oficiais, notícias institucionais).</li>
  </ol>
</section>

</div><!-- /container -->

<!-- ============================================================ FOOTER -->
<footer>
  <div class="container">
    <div>
      <h5>Radar de Políticas Municipais</h5>
      <p style="margin:0;max-width:380px;line-height:1.55;">
        Protótipo de bem público desenvolvido no CLEAR Lab. Dados PNCP em
        domínio público. Código aberto.
      </p>
    </div>
    <div>
      <h5>CLEAR Lab</h5>
      <p style="margin:0;">
        FGV EESP CLEAR<br>
        <a href="https://fgvclear.org">fgvclear.org</a>
      </p>
    </div>
    <div>
      <h5>Atualização</h5>
      <p style="margin:0;">
        Última geração: __DATA_GERACAO__<br>
        Taxonomia v0.2
      </p>
    </div>
  </div>
</footer>

__LEAFLET_JS_TAG__

<script>
// ===========================================================================
// Dados embarcados
// ===========================================================================
const CONTRATOS = __CONTRATOS_JSON__;
const AGG = __AGG_JSON__;
const DIST = __DIST_JSON__;
const EIXOS = __EIXOS_META_JSON__;
const SUBEIXOS_LABELS = __SUBEIXOS_LABELS_JSON__;
const TIMELINE_DATA = __TIMELINE_JSON__;
const TIMELINE_DISPONIVEL = __TIMELINE_DISPONIVEL__;
const FONTES_DISTRIBUICAO = __FONTES_DISTRIBUICAO__;
const PONTOS_MAPA = __PONTOS_MAPA_JSON__;
const CHOROPLETH_UF = __CHOROPLETH_UF_JSON__;
const UFS_GEOJSON = __UFS_GEOJSON__;
const MAPA_DISPONIVEL = __MAPA_DISPONIVEL__;
const N_MUNIS_NO_MAPA = __N_MUNIS_NO_MAPA__;
const N_MUNIS_PERDIDOS = __N_MUNIS_PERDIDOS__;

// ===========================================================================
// Helpers
// ===========================================================================
function fmtBR(n) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  return Number(n).toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}
function eixoNome(id) { return (EIXOS[id] && EIXOS[id].nome) || id; }
function subeixoNome(id) { return SUBEIXOS_LABELS[id] || id; }
function lvlBadge(rotulo, nivel) {
  if (!rotulo) return '';
  return `<span class="badge lvl-${nivel}">${rotulo.replace(/_/g, " ")}</span>`;
}

// ===========================================================================
// Cards de eixos
// ===========================================================================
function renderEixos() {
  const box = document.getElementById("eixos-grid");
  const ids = Object.keys(EIXOS);
  box.innerHTML = ids.map(id => {
    const meta = EIXOS[id];
    const d = DIST[id] || { n_contratos: 0, n_municipios: 0, valor_total: 0 };
    return `
      <article class="eixo-card" style="border-top-color:${meta.cor}">
        <h3><span class="eixo-icon">${meta.icone}</span> ${meta.nome}</h3>
        <p class="desc">${meta.descricao}</p>
        <div class="stats">
          <div class="stat">
            <div class="stat-val">${d.n_contratos || 0}</div>
            <div class="stat-label">Contratos</div>
          </div>
          <div class="stat">
            <div class="stat-val">${d.n_municipios || 0}</div>
            <div class="stat-label">Municípios</div>
          </div>
          <div class="stat">
            <div class="stat-val">R$ ${fmtBR(d.valor_total)}</div>
            <div class="stat-label">Valor total</div>
          </div>
        </div>
        <div class="meta"><strong>Marco legal:</strong> ${meta.marco_legal}</div>
        <div class="meta"><strong>Sistemas setoriais:</strong> ${meta.sistemas_setoriais}</div>
        <div class="meta"><strong>Subeixos:</strong> ${meta.subeixos.join(" · ")}</div>
        <a class="btn" href="#municipios" onclick="filtrarPor('${id}');return true;">Ver municípios deste eixo →</a>
      </article>
    `;
  }).join("");
}

function filtrarPor(eixoId) {
  document.getElementById("filtro-eixo").value = eixoId;
  renderMunicipios();
}

// ===========================================================================
// Filtros de municípios
// ===========================================================================
function popularSelects() {
  const fe = document.getElementById("filtro-eixo");
  const ce = document.getElementById("contrato-eixo");
  Object.keys(EIXOS).forEach(id => {
    const opt = `<option value="${id}">${EIXOS[id].nome}</option>`;
    fe.innerHTML += opt;
    ce.innerHTML += opt;
  });
  const ufs_agg = [...new Set(AGG.map(d => d.uf).filter(Boolean))].sort();
  const ufs_c = [...new Set(CONTRATOS.map(d => d.uf).filter(Boolean))].sort();
  ufs_agg.forEach(uf => document.getElementById("filtro-uf").innerHTML += `<option value="${uf}">${uf}</option>`);
  ufs_c.forEach(uf => document.getElementById("contrato-uf").innerHTML += `<option value="${uf}">${uf}</option>`);
  // Popular filtro de fonte (se existir)
  const fontes = [...new Set(CONTRATOS.map(d => d.fonte).filter(Boolean))].sort();
  const seF = document.getElementById("contrato-fonte");
  if (seF) fontes.forEach(f => seF.innerHTML += `<option value="${f}">${f}</option>`);
}

function renderMunicipios() {
  const eixo = document.getElementById("filtro-eixo").value;
  const uf = document.getElementById("filtro-uf").value;
  const busca = (document.getElementById("filtro-busca").value || "")
    .toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
  let rows = AGG.slice();
  if (eixo) rows = rows.filter(r => r.eixo_id === eixo);
  if (uf) rows = rows.filter(r => r.uf === uf);
  if (busca) rows = rows.filter(r => {
    const nome = (r.municipio || "").toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
    return nome.includes(busca);
  });
  rows.sort((a, b) => (b.n_contratos || 0) - (a.n_contratos || 0));
  document.getElementById("tbl-municipios").innerHTML = rows.map(r => `
    <tr>
      <td>${r.municipio || "—"}</td>
      <td>${r.uf || "—"}</td>
      <td>${eixoNome(r.eixo_id)}</td>
      <td class="num">${r.n_contratos}</td>
      <td class="num">${fmtBR(r.valor_total)}</td>
      <td>${lvlBadge(r.rotulo_nivel, r.nivel_documentacao)}</td>
    </tr>`).join("") || `<tr><td colspan="6" class="muted" style="text-align:center;padding:20px">Nenhum município com esses filtros.</td></tr>`;
  document.getElementById("resumo-municipios").textContent =
    `${rows.length} linha${rows.length === 1 ? "" : "s"}.`;
}

// ===========================================================================
// Contratos individuais
// ===========================================================================
function renderContratos() {
  const eixo = document.getElementById("contrato-eixo").value;
  const uf = document.getElementById("contrato-uf").value;
  const seF = document.getElementById("contrato-fonte");
  const fonte = seF ? seF.value : "";
  let rows = CONTRATOS.slice();
  if (eixo) rows = rows.filter(r => r.eixo_id === eixo);
  if (uf) rows = rows.filter(r => r.uf === uf);
  if (fonte) rows = rows.filter(r => (r.fonte || "PNCP") === fonte);
  rows.sort((a, b) => (b.valor_global || 0) - (a.valor_global || 0));
  // limite pra não estourar o DOM
  const LIMIT = 200;
  const trunc = rows.length > LIMIT;
  rows = rows.slice(0, LIMIT);
  const box = document.getElementById("lista-contratos");
  if (!rows.length) { box.innerHTML = '<p class="muted">Nenhum contrato com esses filtros.</p>'; return; }
  let html = rows.map(r => {
    const fonte = r.fonte || 'PNCP';
    const fonteBadgeColor = fonte === 'PNCP' ? '#1c79be' : fonte === 'Transferegov' ? '#a1c62e' : '#7a8a9c';
    const estagioBadge = r.estagio ? `<span class="badge" style="background:#e8eef4;color:#1a3a5c;">${r.estagio}</span>` : '';
    return `
    <details>
      <summary>
        <strong>${r.municipio || "—"}/${r.uf || "—"}</strong> ·
        <span class="badge" style="background:${fonteBadgeColor};color:#fff;">${fonte}</span>
        ${estagioBadge}
        ${eixoNome(r.eixo_id)} · <span class="muted">${subeixoNome(r.subeixo_id)}</span> ·
        <span class="muted">R$ ${fmtBR(r.valor_global)}</span>
      </summary>
      <div class="detail-body">
        <div><strong>Órgão:</strong> ${r.orgao_razao_social || "—"}</div>
        <div><strong>Data:</strong> ${r.data_referencia || "—"} ·
             <strong>ID:</strong> <code>${r.registro_id || "—"}</code></div>
        <div style="margin-top:8px"><strong>Palavras-chave acertadas:</strong> ${
          (r.keywords_hit || "").split(";").filter(Boolean).map(k => `<span class="badge">${k}</span>`).join(" ") || '<span class="muted">—</span>'
        }</div>
        <div class="obj-text">${(r.objeto || "(sem texto de objeto)").trim()}</div>
      </div>
    </details>`;
  }).join("");
  if (trunc) html += `<p class="muted small" style="text-align:center;margin-top:14px">Mostrando primeiros ${LIMIT} contratos por valor. Use os filtros para refinar.</p>`;
  box.innerHTML = html;
}

// ===========================================================================
// Timeline (gráfico SVG simples, sem libs externas)
// ===========================================================================
function renderTimeline() {
  const box = document.getElementById("timeline-container");
  if (!TIMELINE_DISPONIVEL) {
    box.innerHTML = `<div class="timeline-disabled">
      A linha do tempo é ativada automaticamente quando a base cobrir 30 dias
      ou mais. A amostra atual ainda é menor — expandir a coleta temporal é
      o próximo passo natural do projeto.
    </div>`;
    return;
  }

  // Agrupa: { ym: {eixo_id: count} }
  const months = [...new Set(TIMELINE_DATA.map(d => d.ym))].sort();
  const eixoIds = Object.keys(EIXOS);
  const byMonthEixo = {};
  months.forEach(m => byMonthEixo[m] = {});
  TIMELINE_DATA.forEach(d => {
    byMonthEixo[d.ym][d.eixo_id] = d.registro_id;
  });

  // Dimensões SVG
  const W = 920, H = 320, padL = 50, padR = 20, padT = 20, padB = 50;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const groupW = innerW / months.length;
  const barW = Math.max(4, groupW / (eixoIds.length + 1));
  let maxVal = 1;
  months.forEach(m => eixoIds.forEach(e => {
    maxVal = Math.max(maxVal, byMonthEixo[m][e] || 0);
  }));

  // Eixos e barras
  let svg = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;">`;
  // grid horizontal
  for (let i = 0; i <= 4; i++) {
    const y = padT + innerH - (innerH * i / 4);
    const val = Math.round(maxVal * i / 4);
    svg += `<line x1="${padL}" x2="${W - padR}" y1="${y}" y2="${y}" stroke="#d8e1ec" stroke-width="1"/>`;
    svg += `<text x="${padL - 8}" y="${y + 4}" font-size="11" fill="#7a8a9c" text-anchor="end">${val}</text>`;
  }
  // barras agrupadas
  months.forEach((m, mi) => {
    const groupX = padL + mi * groupW;
    eixoIds.forEach((e, ei) => {
      const val = byMonthEixo[m][e] || 0;
      const h = (val / maxVal) * innerH;
      const x = groupX + ei * barW + (groupW - barW * eixoIds.length) / 2;
      const y = padT + innerH - h;
      svg += `<rect x="${x}" y="${y}" width="${barW - 1}" height="${h}" fill="${EIXOS[e].cor}"><title>${EIXOS[e].nome}: ${val} contratos em ${m}</title></rect>`;
    });
    svg += `<text x="${groupX + groupW/2}" y="${H - padB + 18}" font-size="11" fill="#4a5d72" text-anchor="middle">${m}</text>`;
  });
  svg += `</svg>`;

  // Legenda
  let leg = `<div style="margin-top:14px;display:flex;gap:18px;flex-wrap:wrap;font-size:13px;">`;
  eixoIds.forEach(e => {
    leg += `<span style="display:flex;align-items:center;gap:6px;">
      <span style="width:12px;height:12px;background:${EIXOS[e].cor};border-radius:2px;"></span>
      ${EIXOS[e].nome}
    </span>`;
  });
  leg += `</div>`;

  box.innerHTML = `<div class="timeline-wrap">${svg}${leg}</div>`;
}

// ===========================================================================
// MAPA (Leaflet)
// ===========================================================================
let mapInstance = null;
let mapLayers = [];           // array de layers atuais (limpos a cada re-render)
let legendControl = null;
let currentTab = 'pontos';
let currentUFZoom = null;     // se estiver em zoom de uma UF, código IBGE2 (string)
const ufCodes = {
  "AC":"12","AL":"27","AM":"13","AP":"16","BA":"29","CE":"23","DF":"53",
  "ES":"32","GO":"52","MA":"21","MG":"31","MS":"50","MT":"51","PA":"15",
  "PB":"25","PE":"26","PI":"22","PR":"41","RJ":"33","RN":"24","RO":"11",
  "RR":"14","RS":"43","SC":"42","SE":"28","SP":"35","TO":"17"
};
const ufFromCode = Object.fromEntries(Object.entries(ufCodes).map(([s,c])=>[c,s]));

function initMap() {
  if (!MAPA_DISPONIVEL || typeof L === 'undefined') {
    document.getElementById('map').style.display = 'none';
    document.getElementById('map-fallback').style.display = 'block';
    document.getElementById('coverage-badge').style.display = 'none';
    return;
  }
  mapInstance = L.map('map', {
    center: [-14.5, -52.0],
    zoom: 4,
    minZoom: 3,
    maxZoom: 12,
    scrollWheelZoom: false,
    preferCanvas: true,
  });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OSM &copy; CARTO',
    maxZoom: 19,
  }).addTo(mapInstance);

  // Popula selects de eixo em cada controle
  ['mapa-eixo-pontos', 'mapa-eixo-binario', 'mapa-eixo-uf'].forEach(id => {
    const sel = document.getElementById(id);
    Object.keys(EIXOS).forEach(eid => {
      sel.innerHTML += `<option value="${eid}">${EIXOS[eid].nome}</option>`;
    });
    sel.addEventListener('change', renderMapa);
  });

  // Tabs
  document.querySelectorAll('.map-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.map-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tab = btn.dataset.tab;
      currentTab = tab;
      ['pontos','binario','cobertura','uf'].forEach(t => {
        document.getElementById('map-control-' + t).style.display = (t === tab ? 'flex' : 'none');
      });
      // Sair do zoom UF ao trocar de tab
      if (tab !== 'uf') currentUFZoom = null;
      renderMapa();
    });
  });

  // Botão voltar ao Brasil (zoom UF)
  document.getElementById('btn-voltar-brasil').addEventListener('click', () => {
    currentUFZoom = null;
    mapInstance.setView([-14.5, -52.0], 4);
    document.getElementById('btn-voltar-brasil').style.display = 'none';
    renderMapa();
  });

  atualizarCobertura();
  renderMapa();
}

function limparMapa() {
  mapLayers.forEach(l => mapInstance.removeLayer(l));
  mapLayers = [];
  if (legendControl) { mapInstance.removeControl(legendControl); legendControl = null; }
}

function raioPorContratos(n) {
  if (!n) return 4;
  return Math.min(22, 4 + Math.sqrt(n) * 2);
}

function atualizarCobertura() {
  const total = 5570;
  const pct = (N_MUNIS_NO_MAPA / total * 100).toFixed(1);
  let txt = `${N_MUNIS_NO_MAPA} de ${total} municípios brasileiros (${pct}%).`;
  if (N_MUNIS_NO_MAPA < 100) {
    txt += ' Cobertura ainda muito pequena — qualquer leitura comparativa entre regiões é prematura.';
  } else if (N_MUNIS_NO_MAPA < 1000) {
    txt += ' Cobertura parcial — interpretar com cuidado.';
  } else {
    txt += ' Cobertura razoável para análises regionais, com as ressalvas metodológicas.';
  }
  document.getElementById('cov-text').textContent = txt;
}

function renderMapa() {
  limparMapa();
  switch (currentTab) {
    case 'pontos':    return renderTabPontos();
    case 'binario':   return renderTabBinario();
    case 'cobertura': return renderTabCobertura();
    case 'uf':        return currentUFZoom ? renderUFZoom(currentUFZoom) : renderTabUF();
  }
}

// -------- TAB 1: Pontos por agenda --------
function renderTabPontos() {
  const eixo = document.getElementById('mapa-eixo-pontos').value;
  const pontos = PONTOS_MAPA.filter(p => !eixo || (p.por_eixo[eixo] || 0) > 0);
  const markers = pontos.map(p => criarMarcadorPonto(p, eixo));
  const group = L.layerGroup(markers).addTo(mapInstance);
  mapLayers.push(group);

  addLegendaEixos();
  document.getElementById('info-pontos').textContent =
    `${pontos.length} município${pontos.length===1?'':'s'} no mapa${eixo ? ' (filtrado)' : ''}`;
}

function criarMarcadorPonto(p, eixoFiltro) {
  let cor, n;
  if (eixoFiltro) {
    cor = EIXOS[eixoFiltro].cor;
    n = p.por_eixo[eixoFiltro] || 0;
  } else {
    const top = Object.entries(p.por_eixo).sort((a,b)=>b[1]-a[1])[0];
    cor = top ? EIXOS[top[0]].cor : '#7a8a9c';
    n = p.n_total;
  }
  const m = L.circleMarker([p.lat, p.lng], {
    radius: raioPorContratos(n),
    fillColor: cor,
    color: '#fff',
    weight: 1.5,
    opacity: 1,
    fillOpacity: 0.75,
  });
  const linhas = Object.entries(p.por_eixo)
    .sort((a,b)=>b[1]-a[1])
    .map(([eid, nn]) => `<div class="popup-stat"><span style="display:inline-block;width:8px;height:8px;background:${EIXOS[eid].cor};border-radius:50%;margin-right:6px;vertical-align:middle"></span>${EIXOS[eid].nome}: <b>${nn}</b></div>`)
    .join('');
  m.bindPopup(`
    <strong>${p.municipio}/${p.uf}</strong>
    <div class="popup-stat">Total: <b>${p.n_total} contrato${p.n_total===1?'':'s'}</b></div>
    <div class="popup-stat">Valor: <b>R$ ${fmtBR(p.valor_total)}</b></div>
    <hr style="margin:8px 0;border:none;border-top:1px solid #e0e6ed;">
    ${linhas}
  `);
  return m;
}

// -------- TAB 2: Presença binária --------
function renderTabBinario() {
  const eixo = document.getElementById('mapa-eixo-binario').value;
  const pontos = PONTOS_MAPA.filter(p => !eixo || (p.por_eixo[eixo] || 0) > 0);
  const markers = pontos.map(p => {
    const m = L.circleMarker([p.lat, p.lng], {
      radius: 5,
      fillColor: '#1c79be',
      color: '#fff',
      weight: 1,
      opacity: 1,
      fillOpacity: 0.85,
    });
    m.bindPopup(`<strong>${p.municipio}/${p.uf}</strong><div class="popup-stat">Tem registros na nossa amostra${eixo ? ' (em ' + EIXOS[eixo].nome + ')' : ''}.</div>`);
    return m;
  });
  const group = L.layerGroup(markers).addTo(mapInstance);
  mapLayers.push(group);

  addLegendaSimples([
    {cor:'#1c79be', label:'Com registros na amostra'},
    {cor:'#dfe6ee', label:'Sem registros (ou não coletado)'},
  ]);
  document.getElementById('info-binario').textContent =
    `${pontos.length} município${pontos.length===1?'':'s'} com presença${eixo ? ' em ' + EIXOS[eixo].nome : ''}`;
}

// -------- TAB 3: Cobertura da fonte (autocrítico) --------
function renderTabCobertura() {
  // Aqui usamos os mesmos pontos da amostra, mas comunicamos como
  // "onde a fonte enxerga". A mensagem visual é: o mapa não cobre o Brasil
  // inteiro — isso é uma limitação NOSSA, não dos municípios.
  const markers = PONTOS_MAPA.map(p => {
    const m = L.circleMarker([p.lat, p.lng], {
      radius: raioPorContratos(p.n_total),
      fillColor: '#04354a',
      color: '#fff',
      weight: 1,
      opacity: 1,
      fillOpacity: 0.7,
    });
    m.bindPopup(`<strong>${p.municipio}/${p.uf}</strong><div class="popup-stat">Total de contratos capturados: <b>${p.n_total}</b></div><div class="popup-stat muted small">A fonte enxerga este município nesta janela.</div>`);
    return m;
  });
  const group = L.layerGroup(markers).addTo(mapInstance);
  mapLayers.push(group);

  addLegendaSimples([
    {cor:'#04354a', label:`Municípios visíveis à fonte (${PONTOS_MAPA.length} de 5.570)`},
  ]);
}

// -------- TAB 4: Coroplético por UF + drill-down --------
function renderTabUF() {
  if (!UFS_GEOJSON) return;
  const eixo = document.getElementById('mapa-eixo-uf').value;
  const valorPorUF = {};
  let maxVal = 0;
  Object.keys(CHOROPLETH_UF).forEach(uf => {
    const v = eixo
      ? (CHOROPLETH_UF[uf].por_eixo[eixo] || 0)
      : CHOROPLETH_UF[uf].n_contratos;
    valorPorUF[uf] = v;
    if (v > maxVal) maxVal = v;
  });
  const corBase = eixo ? EIXOS[eixo].cor : '#1c79be';

  const layer = L.geoJSON(UFS_GEOJSON, {
    style: f => ({
      fillColor: corPorValor(valorPorUF[f.properties.sigla] || 0, maxVal, corBase),
      weight: 1,
      opacity: 1,
      color: '#7a8a9c',
      fillOpacity: 0.85,
    }),
    onEachFeature: (f, ly) => {
      const uf = f.properties.sigla;
      const nome = f.properties.nome;
      const v = valorPorUF[uf] || 0;
      const d = CHOROPLETH_UF[uf] || {};
      const linhasEixos = Object.entries(d.por_eixo || {})
        .sort((a,b)=>b[1]-a[1])
        .map(([eid, n]) => `<div class="popup-stat"><span style="display:inline-block;width:8px;height:8px;background:${EIXOS[eid].cor};border-radius:50%;margin-right:6px;vertical-align:middle"></span>${EIXOS[eid].nome}: <b>${n}</b></div>`)
        .join('');
      ly.bindPopup(`
        <strong>${nome} (${uf})</strong>
        <div class="popup-stat">${eixo ? EIXOS[eixo].nome+': ' : 'Total: '}<b>${v} contrato${v===1?'':'s'}</b></div>
        <div class="popup-stat">Municípios com registro: <b>${d.n_municipios || 0}</b></div>
        <div class="popup-stat">Valor total: <b>R$ ${fmtBR(d.valor_total || 0)}</b></div>
        ${linhasEixos ? '<hr style="margin:8px 0;border:none;border-top:1px solid #e0e6ed;">' + linhasEixos : ''}
        <div style="margin-top:8px; font-size:12px; color:#1c79be"><em>Clique para zoom municipal →</em></div>
      `);
      ly.on('mouseover', () => ly.setStyle({weight: 2, color: '#003a78'}));
      ly.on('mouseout', () => layer.resetStyle(ly));
      ly.on('click', () => {
        const ufCode = ufCodes[uf];
        if (ufCode) {
          currentUFZoom = ufCode;
          carregarZoomUF(ufCode);
        }
      });
    },
  }).addTo(mapInstance);
  mapLayers.push(layer);

  addLegendaEscala(maxVal, corBase, eixo);
  document.getElementById('info-uf').textContent =
    `Agregação por UF · ${Object.keys(CHOROPLETH_UF).length} UF${Object.keys(CHOROPLETH_UF).length===1?'':'s'} com registros · clique numa UF para zoom`;
  document.getElementById('btn-voltar-brasil').style.display = 'none';
}

async function carregarZoomUF(ufCode) {
  document.getElementById('info-uf').textContent = `Carregando municípios de ${ufFromCode[ufCode]}...`;
  try {
    const resp = await fetch(`assets/geo/uf_${ufCode}.json`);
    if (!resp.ok) throw new Error('Arquivo geográfico não disponível');
    const geo = await resp.json();
    renderUFZoom(ufCode, geo);
  } catch (e) {
    document.getElementById('info-uf').textContent =
      `Não foi possível carregar a UF ${ufFromCode[ufCode]}: ${e.message}`;
    currentUFZoom = null;
  }
}

function renderUFZoom(ufCode, geo) {
  limparMapa();
  if (!geo) {
    carregarZoomUF(ufCode);
    return;
  }
  const eixo = document.getElementById('mapa-eixo-uf').value;
  const ufSigla = ufFromCode[ufCode];

  // Mapa de pontos do município → totais
  const pontosUF = PONTOS_MAPA.filter(p => p.uf === ufSigla);
  const ibgeMap = {};
  pontosUF.forEach(p => ibgeMap[p.codigo_ibge] = p);

  // Calcula max para escala de cor
  let maxVal = 0;
  pontosUF.forEach(p => {
    const v = eixo ? (p.por_eixo[eixo] || 0) : p.n_total;
    if (v > maxVal) maxVal = v;
  });
  const corBase = eixo ? EIXOS[eixo].cor : '#1c79be';

  const layer = L.geoJSON(geo, {
    style: f => {
      const ibge = f.properties.ibge;
      const p = ibgeMap[ibge];
      const v = p ? (eixo ? (p.por_eixo[eixo] || 0) : p.n_total) : 0;
      return {
        fillColor: corPorValor(v, maxVal, corBase),
        weight: 0.5,
        opacity: 1,
        color: '#7a8a9c',
        fillOpacity: v > 0 ? 0.85 : 0.4,
      };
    },
    onEachFeature: (f, ly) => {
      const ibge = f.properties.ibge;
      const nome = f.properties.nome;
      const p = ibgeMap[ibge];
      if (p) {
        const linhas = Object.entries(p.por_eixo)
          .sort((a,b)=>b[1]-a[1])
          .map(([eid, n]) => `<div class="popup-stat"><span style="display:inline-block;width:8px;height:8px;background:${EIXOS[eid].cor};border-radius:50%;margin-right:6px;vertical-align:middle"></span>${EIXOS[eid].nome}: <b>${n}</b></div>`)
          .join('');
        ly.bindPopup(`
          <strong>${nome}/${ufSigla}</strong>
          <div class="popup-stat">Total: <b>${p.n_total} contrato${p.n_total===1?'':'s'}</b></div>
          <div class="popup-stat">Valor: <b>R$ ${fmtBR(p.valor_total)}</b></div>
          <hr style="margin:8px 0;border:none;border-top:1px solid #e0e6ed;">
          ${linhas}
        `);
      } else {
        ly.bindPopup(`<strong>${nome}/${ufSigla}</strong><div class="popup-stat muted">Sem registros classificados nesta amostra.</div>`);
      }
      ly.on('mouseover', () => ly.setStyle({weight: 1.5, color: '#003a78'}));
      ly.on('mouseout', () => layer.resetStyle(ly));
    },
  }).addTo(mapInstance);
  mapLayers.push(layer);

  // Zoom na bbox da UF
  mapInstance.fitBounds(layer.getBounds(), {padding: [20, 20]});
  addLegendaEscala(maxVal, corBase, eixo);
  document.getElementById('btn-voltar-brasil').style.display = 'inline-block';
  document.getElementById('info-uf').textContent =
    `${ufFromCode[ufCode]} · ${pontosUF.length} município${pontosUF.length===1?'':'s'} com registros`;
}

// -------- Helpers de cor e legenda --------
function corPorValor(v, maxVal, corBase) {
  if (!v || maxVal === 0) return '#eef3f8';
  const t = v / maxVal;
  if (t < 0.2) return mix(corBase, '#ffffff', 0.85);
  if (t < 0.4) return mix(corBase, '#ffffff', 0.65);
  if (t < 0.6) return mix(corBase, '#ffffff', 0.45);
  if (t < 0.8) return mix(corBase, '#ffffff', 0.25);
  return corBase;
}
function mix(c1, c2, t) {
  const h = c => [parseInt(c.slice(1,3),16), parseInt(c.slice(3,5),16), parseInt(c.slice(5,7),16)];
  const a = h(c1), b = h(c2);
  return `rgb(${Math.round(a[0]*(1-t)+b[0]*t)},${Math.round(a[1]*(1-t)+b[1]*t)},${Math.round(a[2]*(1-t)+b[2]*t)})`;
}
function addLegendaEixos() {
  legendControl = L.control({position:'bottomright'});
  legendControl.onAdd = () => {
    const div = L.DomUtil.create('div', 'map-legend');
    let html = '<strong>Eixo</strong>';
    Object.keys(EIXOS).forEach(eid => {
      html += `<div class="legend-row"><span class="legend-dot" style="background:${EIXOS[eid].cor}"></span>${EIXOS[eid].nome}</div>`;
    });
    html += '<strong style="margin-top:8px">Tamanho</strong><div class="muted small">∝ √(nº contratos)</div>';
    div.innerHTML = html;
    return div;
  };
  legendControl.addTo(mapInstance);
}
function addLegendaSimples(itens) {
  legendControl = L.control({position:'bottomright'});
  legendControl.onAdd = () => {
    const div = L.DomUtil.create('div', 'map-legend');
    let html = '';
    itens.forEach(it => {
      html += `<div class="legend-row"><span class="legend-dot" style="background:${it.cor}"></span>${it.label}</div>`;
    });
    div.innerHTML = html;
    return div;
  };
  legendControl.addTo(mapInstance);
}
function addLegendaEscala(maxVal, corBase, eixo) {
  legendControl = L.control({position:'bottomright'});
  legendControl.onAdd = () => {
    const div = L.DomUtil.create('div', 'map-legend');
    let html = `<strong>${eixo ? EIXOS[eixo].nome : 'Total de contratos'}</strong>`;
    const passos = [0.2, 0.4, 0.6, 0.8].map(t => Math.round(maxVal * t)).filter(v => v > 0);
    const stops = [0, ...passos, maxVal];
    stops.forEach((val, i) => {
      const next = stops[i+1];
      const cor = corPorValor(val === 0 ? 0 : val, maxVal, corBase);
      let label;
      if (val === 0) label = '0';
      else if (next === undefined || next === val) label = `≥ ${val}`;
      else label = `${val}–${next-1}`;
      html += `<div class="legend-row"><span class="legend-square" style="background:${cor}"></span>${label}</div>`;
    });
    div.innerHTML = html;
    return div;
  };
  legendControl.addTo(mapInstance);
}

// ===========================================================================
// Init
// ===========================================================================
// Distribuição por fonte (badge sob métricas)
function renderDistribuicaoFontes() {
  const box = document.getElementById("dist-fontes");
  if (!box) return;
  const fontesCores = { PNCP: '#1c79be', Transferegov: '#a1c62e', SICONFI: '#04354a' };
  const items = Object.entries(FONTES_DISTRIBUICAO)
    .sort((a,b) => b[1] - a[1])
    .map(([f, n]) => {
      const cor = fontesCores[f] || '#7a8a9c';
      return `<span class="badge" style="background:${cor};color:#fff;margin-right:6px;">${f}: ${fmtBR(n)}</span>`;
    });
  box.innerHTML = items.join(' ');
}

renderDistribuicaoFontes();
renderEixos();
popularSelects();
renderMunicipios();
renderContratos();
renderTimeline();
initMap();
["filtro-eixo", "filtro-uf", "filtro-busca"].forEach(id =>
  document.getElementById(id).addEventListener("input", renderMunicipios));
["contrato-eixo", "contrato-uf", "contrato-fonte"].forEach(id =>
  document.getElementById(id) && document.getElementById(id).addEventListener("input", renderContratos));
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# 6) Substituições
# ---------------------------------------------------------------------------
html = HTML
html = html.replace("__LOGO_SVG__", LOGO_SVG)
html = html.replace("__N_CONTRATOS__", f"{n_contratos:,}".replace(",", "."))
html = html.replace("__N_FONTES__", str(n_fontes))
html = html.replace("__FONTES_LISTA__", " · ".join(fontes_lista))
html = html.replace("__FONTES_DISTRIBUICAO__", json.dumps(fontes_distribuicao, ensure_ascii=False))
html = html.replace("__N_MUNICIPIOS__", f"{n_municipios:,}".replace(",", "."))
html = html.replace("__N_UFS__", str(n_ufs))
html = html.replace("__VALOR_TOTAL__", f"{valor_total:,.0f}".replace(",", "."))
html = html.replace("__DATA_GERACAO__", DATA_GERACAO)
html = html.replace("__DATA_PRIMEIRO__", DATA_PRIMEIRO_REGISTRO)
html = html.replace("__DATA_ULTIMO__", DATA_ULTIMO_REGISTRO)
html = html.replace("__N_DIAS__", str(n_dias_observados))
html = html.replace("__CONTRATOS_JSON__", json.dumps(contratos_json, ensure_ascii=False))
html = html.replace("__AGG_JSON__", json.dumps(agg_json, ensure_ascii=False))
html = html.replace("__DIST_JSON__", json.dumps(dist, ensure_ascii=False))
html = html.replace("__EIXOS_META_JSON__", json.dumps(EIXOS_META, ensure_ascii=False))
html = html.replace("__SUBEIXOS_LABELS_JSON__", json.dumps(SUBEIXOS_LABELS, ensure_ascii=False))
html = html.replace("__TIMELINE_JSON__", json.dumps(timeline_data, ensure_ascii=False))
html = html.replace("__TIMELINE_DISPONIVEL__", "true" if timeline_disponivel else "false")
html = html.replace("__PONTOS_MAPA_JSON__", json.dumps(pontos_mapa, ensure_ascii=False))
html = html.replace("__CHOROPLETH_UF_JSON__", json.dumps(choropleth_uf, ensure_ascii=False))
html = html.replace("__UFS_GEOJSON__", json.dumps(brasil_ufs_geojson, ensure_ascii=False) if brasil_ufs_geojson else "null")
html = html.replace("__MAPA_DISPONIVEL__", "true" if mapa_disponivel else "false")
html = html.replace("__N_MUNIS_NO_MAPA__", str(n_munis_no_mapa))
html = html.replace("__N_MUNIS_PERDIDOS__", str(geocoding_perdidos))
html = html.replace("__LEAFLET_CSS_TAG__", LEAFLET_CSS_TAG)
html = html.replace("__LEAFLET_JS_TAG__", LEAFLET_JS_TAG)

OUT.write_text(html, encoding="utf-8")
print(f"Gerado: {OUT}")
print(f"Tamanho: {OUT.stat().st_size:,} bytes")
print(f"  contratos: {n_contratos}, municípios: {n_municipios}, UFs: {n_ufs}")
print(f"  cobertura: {DATA_PRIMEIRO_REGISTRO} → {DATA_ULTIMO_REGISTRO} ({n_dias_observados} dias)")
print(f"  timeline ativada: {timeline_disponivel}")
print(f"  mapa ativado: {mapa_disponivel} (municípios geocodificados: {n_munis_no_mapa}, perdidos: {geocoding_perdidos})")
