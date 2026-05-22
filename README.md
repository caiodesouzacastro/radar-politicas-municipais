# Radar de Políticas Municipais — MVP

Protótipo para o CLEAR. Camada que organiza registros administrativos públicos
(contratações via PNCP e, em fases futuras, Transferegov, SIOPS, SIOPE,
Censo SUAS, diários oficiais) em informação navegável sobre o que os
municípios brasileiros estão documentadamente fazendo em quatro agendas:

- Primeira Infância
- Busca Ativa Escolar e Permanência
- Segurança Alimentar e Nutricional
- Saúde Mental

## Nota metodológica antes de qualquer uso

Esta ferramenta mede **intensidade de documentação**, não intensidade de
implementação. Municípios com mais capacidade burocrática deixam mais
rastros administrativos, o que enviesa qualquer leitura comparativa entre
municípios de portes diferentes. A escala de níveis de documentação
(`sem_registros` → `atividade_intensa`) é uma medida do volume de pegadas
contratuais classificadas, não da existência ou qualidade de uma política.

## O que tem aqui

```
radar_clear/
├── radar_policy/
│   ├── taxonomy/
│   │   ├── taxonomy_v0.yaml      # taxonomia versionada das 4 agendas
│   │   └── loader.py             # carrega + compila regex com word boundary
│   ├── classify/
│   │   └── classifier.py         # aplica taxonomia + escala de documentação
│   ├── sources/
│   │   ├── pncp.py               # cliente PNCP com cache em disco
│   │   ├── pncp_parallel.py      # fetch paralelo de páginas
│   │   ├── transferegov.py       # stub documentado (fase 2)
│   │   └── setoriais.py          # stubs SIOPS/SIOPE/Censo SUAS (fase 2)
│   └── pipeline.py               # PNCP → classifica → parquet
├── data/
│   ├── raw/pncp_cache/           # cache JSON bruto da API (54 páginas)
│   └── processed/                # parquets resultantes
├── notebooks/
│   └── 01_exploracao.ipynb       # análise exploratória da amostra
├── dashboard/
│   └── app.py                    # dashboard Streamlit
├── docs/                         # proposta + notas metodológicas
├── fetch_chunk.py                # baixa N páginas do PNCP por execução
├── process_cache.py              # processa cache local sem chamar API
└── run_mvp.py                    # pipeline end-to-end
```

## Como rodar

### Pré-requisitos

```
pip install pyyaml requests pandas pyarrow
```

(O `streamlit` e o `plotly` só são necessários se você quiser usar o
dashboard interativo em `dashboard/app.py`. Pro site `index.html` estático,
basta abrir no navegador.)

### Ver o site rapidamente

Abra `index.html` no navegador. Não precisa de servidor.

### Expandir a coleta

```
python expandir_coleta.py --inicio 2025-01-01 --fim 2025-12-31
```

Script idempotente — pode interromper e retomar. Detalhes em `GUIDE.md`.

### Reprocessar a base + regerar o site

```
python process_cache.py     # lê cache, aplica taxonomia, gera parquets
python build_html.py        # regera index.html com dados atualizados
```

### Publicar no GitHub Pages

Veja **GUIDE.md** — instruções passo a passo desde o `git init` até o
push e a configuração do Pages.

## Status da amostra atual

- **Cobertura**: 1 dia útil (15/09/2025), 54 das 142 páginas do dia coletadas
- **Volume bruto**: 2.700 contratos PNCP processados
- **Municipais únicos**: 1.479 contratos
- **Classificados**: 72 contratos em 27 municípios distribuídos em 13 UFs

Esta amostra é suficiente para validar o pipeline end-to-end e a metodologia.
Não é suficiente para qualquer leitura comparativa entre municípios.

## Próximos passos do projeto

Em ordem de prioridade:

1. **Expansão temporal** — 12 meses contínuos de PNCP para todos os municípios.
   Trabalho de infra (provavelmente fora deste sandbox), não conceitual.
2. **Score de confiança por classificação** — número de keywords casadas +
   presença de termos reforçadores no objeto. Permite filtrar a base por
   nível de certeza.
3. **Validação assistida** — amostra estratificada de 300 contratos rotulados
   manualmente para calcular precisão/recall por subeixo.
4. **Transferegov** — convênios federais discricionários, captura o que o
   PNCP perde para municípios pequenos.
5. **Sistemas setoriais** (SIOPS, SIOPE, Censo SUAS) — para cada eixo, o
   sistema setorial correspondente confirma ou contradiz o sinal do PNCP.
6. **Fase 2 — fontes não estruturadas**: diários oficiais municipais e
   notícias de prefeituras, com classificação assistida por LLM.

## Decisões metodológicas registradas

- Taxonomia é YAML versionado, fora do código. Mudanças são revisáveis em
  diff e auditáveis. Cada bump de versão (`v0.1 → v0.2`) traz changelog
  no cabeçalho do YAML.
- Word boundary nas keywords: a v0.1 sofria com `cei` casando em "Conceição";
  a v0.2 usa `(?:^|\\s|\\b)kw(?:\\b|\\s|$)`.
- Múltiplas classificações por contrato são propositais: agendas de política
  pública são intersetoriais (merenda em creche cai em primeira infância
  E em segurança alimentar).
- Escala de documentação tem 5 níveis, definidos por faixas de número de
  registros, intencionalmente grosseiros para evitar leitura espúria de
  variação fina.
