"""Gera index.html estático do Radar de Políticas Municipais.

Embarca os dados processados como JSON inline. Sem dependência de servidor.
Pode ser publicado em GitHub Pages diretamente.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "processed"
OUT = ROOT / "index.html"

contratos = pd.read_parquet(DATA / "contratos_classificados.parquet")
agg = pd.read_parquet(DATA / "municipios_eixos.parquet")

# Trata NaN/None pra JSON
contratos = contratos.where(pd.notna(contratos), None)
agg = agg.where(pd.notna(agg), None)

contratos_json = contratos.to_dict(orient="records")
agg_json = agg.to_dict(orient="records")

# Rótulos dos eixos
EIXOS = {
    "primeira_infancia": "Primeira Infância",
    "busca_ativa_escolar": "Busca Ativa Escolar e Permanência",
    "seguranca_alimentar": "Segurança Alimentar e Nutricional",
    "saude_mental": "Saúde Mental",
}

SUBEIXOS = {
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

# Métricas globais
n_contratos = contratos["numero_controle_pncp"].nunique()
n_municipios = contratos["codigo_ibge"].nunique()
n_ufs = contratos["uf"].nunique()
valor_total = float(contratos["valor_global"].sum())

# Distribuição por eixo
dist = (
    contratos.groupby("eixo_id")
    .agg(
        n_contratos=("numero_controle_pncp", "nunique"),
        n_municipios=("codigo_ibge", "nunique"),
        valor_total=("valor_global", "sum"),
    )
    .reset_index()
    .sort_values("n_contratos", ascending=False)
)
dist_json = dist.to_dict(orient="records")

HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Radar de Políticas Municipais — CLEAR</title>
<style>
  :root {
    --bg: #0d1117;
    --bg-2: #161b22;
    --bg-3: #1c2128;
    --border: #30363d;
    --text: #e6edf3;
    --text-dim: #8b949e;
    --accent: #58a6ff;
    --accent-2: #79c0ff;
    --warn-bg: #3a2d18;
    --warn-border: #6e5926;
    --warn-text: #f0c674;
    --green: #3fb950;
    --orange: #d29922;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 15px;
    line-height: 1.55;
  }
  .container {
    max-width: 1180px;
    margin: 0 auto;
    padding: 32px 24px 80px;
  }
  header.brand {
    border-bottom: 1px solid var(--border);
    padding-bottom: 20px;
    margin-bottom: 28px;
  }
  .brand-tag {
    display: inline-block;
    font-size: 12px;
    color: var(--text-dim);
    border: 1px solid var(--border);
    padding: 2px 8px;
    border-radius: 12px;
    margin-bottom: 12px;
  }
  h1 {
    font-size: 32px;
    margin: 0 0 8px;
    line-height: 1.2;
    font-weight: 600;
  }
  .subtitle {
    color: var(--text-dim);
    font-size: 16px;
    margin: 0;
  }
  h2 {
    font-size: 22px;
    margin: 40px 0 12px;
    font-weight: 600;
    border-bottom: 1px solid var(--border);
    padding-bottom: 6px;
  }
  h3 {
    font-size: 17px;
    margin: 20px 0 8px;
    font-weight: 600;
    color: var(--accent-2);
  }
  p { margin: 0 0 14px; }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }

  .disclaimer {
    background: var(--warn-bg);
    border: 1px solid var(--warn-border);
    border-radius: 8px;
    padding: 14px 18px;
    margin: 0 0 28px;
    color: var(--warn-text);
    font-size: 14px;
  }
  .disclaimer strong { color: #ffd47a; }

  .metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
    margin: 18px 0 28px;
  }
  .metric {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 18px;
  }
  .metric-label {
    color: var(--text-dim);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }
  .metric-value {
    font-size: 26px;
    font-weight: 600;
    color: var(--text);
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 24px;
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    font-size: 14px;
  }
  th, td {
    text-align: left;
    padding: 9px 12px;
    border-bottom: 1px solid var(--border);
  }
  th {
    background: var(--bg-3);
    font-weight: 600;
    color: var(--text);
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: var(--bg-3); }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }

  .bar {
    height: 8px;
    background: var(--border);
    border-radius: 4px;
    overflow: hidden;
    min-width: 80px;
  }
  .bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
  }

  .controls {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
    margin: 16px 0;
  }
  select, input[type=text] {
    background: var(--bg-2);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 7px 10px;
    border-radius: 6px;
    font-size: 14px;
    min-width: 180px;
  }
  select:focus, input:focus { outline: 1px solid var(--accent); }

  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    background: var(--bg-3);
    border: 1px solid var(--border);
    color: var(--text-dim);
    margin-right: 4px;
  }
  .badge.lvl-1 { background: #1a2e1a; border-color: #2d5a2d; color: #6cc66c; }
  .badge.lvl-2 { background: #1c3a4a; border-color: #2d6a8a; color: #6cb6dd; }
  .badge.lvl-3 { background: #3a2d18; border-color: #6e5926; color: #f0c674; }
  .badge.lvl-4 { background: #4a1d1d; border-color: #8a3a3a; color: #ff8a8a; }

  details {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0;
    margin: 8px 0;
  }
  details summary {
    padding: 12px 16px;
    cursor: pointer;
    font-weight: 500;
    user-select: none;
  }
  details summary:hover { background: var(--bg-3); }
  details[open] summary { border-bottom: 1px solid var(--border); }
  details .detail-body { padding: 14px 18px 18px; font-size: 14px; }
  details .obj-text {
    background: var(--bg-3);
    border-radius: 6px;
    padding: 10px 12px;
    color: var(--text-dim);
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 13px;
    margin-top: 8px;
    white-space: pre-wrap;
  }

  footer {
    margin-top: 60px;
    padding-top: 20px;
    border-top: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 13px;
  }

  .nav-tabs {
    display: flex;
    gap: 2px;
    border-bottom: 1px solid var(--border);
    margin: 16px 0 0;
  }
  .nav-tabs button {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--text-dim);
    padding: 10px 16px;
    cursor: pointer;
    font-size: 14px;
    font-family: inherit;
  }
  .nav-tabs button:hover { color: var(--text); }
  .nav-tabs button.active {
    color: var(--accent);
    border-bottom-color: var(--accent);
  }
  .tab-content { display: none; padding-top: 18px; }
  .tab-content.active { display: block; }

  .muted { color: var(--text-dim); }
  .small { font-size: 13px; }
  code {
    background: var(--bg-3);
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 13px;
  }
</style>
</head>
<body>
<div class="container">

  <header class="brand">
    <div class="brand-tag">PROTÓTIPO · CLEAR · v0.2</div>
    <h1>Radar de Políticas Municipais</h1>
    <p class="subtitle">
      Camada de agregação e classificação de registros administrativos públicos
      por agenda de política pública municipal.
    </p>
  </header>

  <div class="disclaimer">
    <strong>⚠ Leia antes de interpretar.</strong> Esta ferramenta mede
    <em>intensidade de documentação</em>, não intensidade de implementação.
    Municípios com maior capacidade burocrática produzem sistematicamente mais
    registros administrativos. Esta amostra cobre <strong>1 dia útil</strong>
    (15/09/2025) e <strong>apenas a fonte PNCP</strong>; qualquer leitura
    comparativa entre municípios é prematura.
  </div>

  <h2>Cobertura desta amostra</h2>
  <div class="metrics">
    <div class="metric">
      <div class="metric-label">Contratos classificados</div>
      <div class="metric-value">__N_CONTRATOS__</div>
    </div>
    <div class="metric">
      <div class="metric-label">Municípios com registro</div>
      <div class="metric-value">__N_MUNICIPIOS__</div>
    </div>
    <div class="metric">
      <div class="metric-label">UFs representadas</div>
      <div class="metric-value">__N_UFS__</div>
    </div>
    <div class="metric">
      <div class="metric-label">Valor total (R$)</div>
      <div class="metric-value">__VALOR_TOTAL__</div>
    </div>
  </div>

  <nav class="nav-tabs">
    <button class="active" data-tab="eixos">Por eixo</button>
    <button data-tab="municipios">Por município</button>
    <button data-tab="contratos">Contratos individuais</button>
    <button data-tab="metodologia">Metodologia</button>
  </nav>

  <!-- TAB EIXOS -->
  <section id="tab-eixos" class="tab-content active">
    <h3>Distribuição por agenda</h3>
    <p class="muted small">
      Um mesmo contrato pode aparecer em mais de um eixo (por exemplo, merenda
      escolar em creche conta em Primeira Infância e em Segurança Alimentar).
      Isso é proposital: agendas de política pública são intersetoriais.
    </p>
    <table>
      <thead><tr>
        <th>Eixo</th>
        <th class="num">Contratos</th>
        <th class="num">Municípios</th>
        <th class="num">Valor (R$)</th>
        <th style="width:240px">Participação</th>
      </tr></thead>
      <tbody id="tbl-eixos"></tbody>
    </table>
  </section>

  <!-- TAB MUNICÍPIOS -->
  <section id="tab-municipios" class="tab-content">
    <h3>Município × eixo</h3>
    <div class="controls">
      <label>Eixo:
        <select id="filtro-eixo">
          <option value="">Todos</option>
        </select>
      </label>
      <label>UF:
        <select id="filtro-uf">
          <option value="">Todas</option>
        </select>
      </label>
      <label>Busca:
        <input id="filtro-busca" type="text" placeholder="nome do município..." />
      </label>
    </div>
    <table>
      <thead><tr>
        <th>Município</th>
        <th>UF</th>
        <th>Eixo</th>
        <th class="num">Contratos</th>
        <th class="num">Valor (R$)</th>
        <th>Nível doc.</th>
      </tr></thead>
      <tbody id="tbl-municipios"></tbody>
    </table>
    <p class="muted small" id="resumo-municipios"></p>
  </section>

  <!-- TAB CONTRATOS -->
  <section id="tab-contratos" class="tab-content">
    <h3>Contratos individuais</h3>
    <p class="muted small">
      Sempre verifique o objeto antes de concluir qualquer coisa sobre a
      classificação. Falsos positivos são esperados nesta versão da taxonomia
      — eles são insumo para a próxima rodada.
    </p>
    <div class="controls">
      <label>Eixo:
        <select id="contrato-eixo">
          <option value="">Todos</option>
        </select>
      </label>
      <label>UF:
        <select id="contrato-uf">
          <option value="">Todas</option>
        </select>
      </label>
    </div>
    <div id="lista-contratos"></div>
  </section>

  <!-- TAB METODOLOGIA -->
  <section id="tab-metodologia" class="tab-content">
    <h3>O que esta ferramenta faz</h3>
    <p>
      Coleta contratos públicos do <strong>PNCP</strong> (Portal Nacional de
      Contratações Públicas), filtra os de esfera municipal, e classifica
      cada um conforme uma taxonomia versionada de agendas de política pública
      municipal. O resultado é uma base que liga registros administrativos
      dispersos a agendas substantivas.
    </p>

    <h3>O que esta ferramenta não faz</h3>
    <p>
      Não mede qualidade de implementação, cobertura populacional efetiva, nem
      adequação técnica ou orçamentária. Mede apenas se um município produziu
      registros administrativos cujo objeto declarado é compatível com uma
      agenda. Um município sem registros pode estar implementando muito (mas
      sem deixar rastro fácil de capturar). Um município com muitos registros
      pode estar implementando pouco (mas contratando muito).
    </p>

    <h3>Taxonomia versionada</h3>
    <p>
      A taxonomia é um arquivo <code>YAML</code> auditável, com cabeçalho que
      lista as mudanças entre versões. A v0.2 atual cobre quatro agendas e
      catorze subeixos. As palavras-chave casam com word boundary
      (corrigindo o falso positivo da v0.1 em que <code>cei</code> casava
      em "Conceição"). Cada agenda tem marco legal documentado e sistemas
      setoriais associados para integração futura.
    </p>

    <h3>Próximos passos</h3>
    <ol>
      <li>Expandir a janela de PNCP para 12 meses contínuos.</li>
      <li>Incluir Transferegov, que cobre melhor municípios pequenos.</li>
      <li>Adicionar score de confiança por classificação (número e qualidade
          das keywords casadas).</li>
      <li>Validação assistida: amostra estratificada rotulada manualmente
          para calcular precisão/recall por subeixo.</li>
      <li>Integração com SIOPS, SIOPE e Censo SUAS para cruzamento setorial.</li>
      <li>Fase 2: fontes não estruturadas (diários oficiais, notícias
          institucionais) com classificação assistida por LLM.</li>
    </ol>

    <h3>Repositório e código</h3>
    <p>
      Toda a pipeline é código aberto, escrita em Python. Cliente PNCP com
      cache em disco, classificador independente da fonte, taxonomia em YAML
      separada do código. Stubs documentados para Transferegov, SIOPS, SIOPE
      e Censo SUAS marcando os pontos de integração da fase 2.
    </p>
  </section>

  <footer>
    Radar de Políticas Municipais · Protótipo CLEAR · Dados públicos do
    PNCP coletados em 15/09/2025 · Taxonomia v0.2 ·
    <a href="#" onclick="event.preventDefault();document.querySelector('[data-tab=metodologia]').click();">
      Ver nota metodológica
    </a>
  </footer>
</div>

<script>
// ===========================================================================
// Dados embarcados
// ===========================================================================
const CONTRATOS = __CONTRATOS_JSON__;
const AGG = __AGG_JSON__;
const DIST_EIXOS = __DIST_EIXOS__;
const EIXOS = __EIXOS_LABELS__;
const SUBEIXOS = __SUBEIXOS_LABELS__;

// ===========================================================================
// Helpers
// ===========================================================================
function fmtBR(n) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  return n.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}
function eixoLabel(id) { return EIXOS[id] || id; }
function subeixoLabel(id) { return SUBEIXOS[id] || id; }
function lvlBadge(rotulo, nivel) {
  return `<span class="badge lvl-${nivel}">${rotulo.replace(/_/g, " ")}</span>`;
}

// ===========================================================================
// Tabs
// ===========================================================================
document.querySelectorAll(".nav-tabs button").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-tabs button").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(s => s.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
  });
});

// ===========================================================================
// Tabela: distribuição por eixo
// ===========================================================================
function renderEixos() {
  const tb = document.getElementById("tbl-eixos");
  const max = Math.max(...DIST_EIXOS.map(d => d.n_contratos));
  tb.innerHTML = DIST_EIXOS.map(d => {
    const pct = (d.n_contratos / max) * 100;
    return `<tr>
      <td><strong>${eixoLabel(d.eixo_id)}</strong></td>
      <td class="num">${d.n_contratos}</td>
      <td class="num">${d.n_municipios}</td>
      <td class="num">${fmtBR(d.valor_total)}</td>
      <td><div class="bar"><div class="bar-fill" style="width:${pct}%"></div></div></td>
    </tr>`;
  }).join("");
}

// ===========================================================================
// Tabela: município × eixo, com filtros
// ===========================================================================
function popularSelectsMunicipios() {
  const fe = document.getElementById("filtro-eixo");
  Object.keys(EIXOS).forEach(id => {
    fe.innerHTML += `<option value="${id}">${EIXOS[id]}</option>`;
  });
  const ufs = [...new Set(AGG.map(d => d.uf).filter(Boolean))].sort();
  const fu = document.getElementById("filtro-uf");
  ufs.forEach(uf => fu.innerHTML += `<option value="${uf}">${uf}</option>`);
}

function renderMunicipios() {
  const eixo = document.getElementById("filtro-eixo").value;
  const uf = document.getElementById("filtro-uf").value;
  const busca = document.getElementById("filtro-busca").value
    .toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
  let rows = AGG.slice();
  if (eixo) rows = rows.filter(r => r.eixo_id === eixo);
  if (uf) rows = rows.filter(r => r.uf === uf);
  if (busca) rows = rows.filter(r => {
    const nome = (r.municipio || "").toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
    return nome.includes(busca);
  });
  rows.sort((a, b) => b.n_contratos - a.n_contratos);

  document.getElementById("tbl-municipios").innerHTML = rows.map(r => `
    <tr>
      <td>${r.municipio || "—"}</td>
      <td>${r.uf || "—"}</td>
      <td>${eixoLabel(r.eixo_id)}</td>
      <td class="num">${r.n_contratos}</td>
      <td class="num">${fmtBR(r.valor_total)}</td>
      <td>${lvlBadge(r.rotulo_nivel, r.nivel_documentacao)}</td>
    </tr>
  `).join("");
  document.getElementById("resumo-municipios").textContent =
    `${rows.length} linha${rows.length === 1 ? "" : "s"} exibida${rows.length === 1 ? "" : "s"}.`;
}

// ===========================================================================
// Lista de contratos individuais
// ===========================================================================
function popularSelectsContratos() {
  const fe = document.getElementById("contrato-eixo");
  Object.keys(EIXOS).forEach(id => {
    fe.innerHTML += `<option value="${id}">${EIXOS[id]}</option>`;
  });
  const ufs = [...new Set(CONTRATOS.map(d => d.uf).filter(Boolean))].sort();
  const fu = document.getElementById("contrato-uf");
  ufs.forEach(uf => fu.innerHTML += `<option value="${uf}">${uf}</option>`);
}

function renderContratos() {
  const eixo = document.getElementById("contrato-eixo").value;
  const uf = document.getElementById("contrato-uf").value;
  let rows = CONTRATOS.slice();
  if (eixo) rows = rows.filter(r => r.eixo_id === eixo);
  if (uf) rows = rows.filter(r => r.uf === uf);
  rows.sort((a, b) => (b.valor_global || 0) - (a.valor_global || 0));

  const box = document.getElementById("lista-contratos");
  if (!rows.length) { box.innerHTML = '<p class="muted">Nenhum contrato com esses filtros.</p>'; return; }
  box.innerHTML = rows.map(r => `
    <details>
      <summary>
        <strong>${r.municipio || "—"}/${r.uf || "—"}</strong> ·
        ${eixoLabel(r.eixo_id)} · ${subeixoLabel(r.subeixo_id)} ·
        <span class="muted">R$ ${fmtBR(r.valor_global)}</span>
      </summary>
      <div class="detail-body">
        <div><span class="muted">Órgão:</span> ${r.orgao_razao_social || "—"}</div>
        <div><span class="muted">Data:</span> ${r.data_assinatura || "—"} ·
             <span class="muted">PNCP:</span> <code>${r.numero_controle_pncp || "—"}</code></div>
        <div><span class="muted">Palavras-chave acertadas:</span> ${
          (r.keywords_hit || "").split(";").map(k => `<span class="badge">${k}</span>`).join(" ")
        }</div>
        <div class="obj-text">${(r.objeto || "(sem texto de objeto)").trim()}</div>
      </div>
    </details>
  `).join("");
}

// ===========================================================================
// Init
// ===========================================================================
renderEixos();
popularSelectsMunicipios();
renderMunicipios();
["filtro-eixo", "filtro-uf", "filtro-busca"].forEach(id =>
  document.getElementById(id).addEventListener("input", renderMunicipios));
popularSelectsContratos();
renderContratos();
["contrato-eixo", "contrato-uf"].forEach(id =>
  document.getElementById(id).addEventListener("input", renderContratos));
</script>
</body>
</html>
"""

# Substituições
html = HTML
html = html.replace("__N_CONTRATOS__", str(n_contratos))
html = html.replace("__N_MUNICIPIOS__", str(n_municipios))
html = html.replace("__N_UFS__", str(n_ufs))
html = html.replace("__VALOR_TOTAL__",
                    f"{valor_total:,.0f}".replace(",", "."))
html = html.replace("__CONTRATOS_JSON__", json.dumps(contratos_json, ensure_ascii=False))
html = html.replace("__AGG_JSON__", json.dumps(agg_json, ensure_ascii=False))
html = html.replace("__DIST_EIXOS__", json.dumps(dist_json, ensure_ascii=False))
html = html.replace("__EIXOS_LABELS__", json.dumps(EIXOS, ensure_ascii=False))
html = html.replace("__SUBEIXOS_LABELS__", json.dumps(SUBEIXOS, ensure_ascii=False))

OUT.write_text(html, encoding="utf-8")
print(f"Gerado: {OUT}")
print(f"Tamanho: {OUT.stat().st_size:,} bytes")
