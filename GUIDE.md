# GUIDE — Operando o Radar de Políticas Municipais

Três fluxos: publicar no GitHub, expandir a coleta de municípios, e
atualizar o site após mudanças.

---

## 1. Publicar no GitHub

### 1.1 Pré-requisitos

- Conta no GitHub (já tem)
- `git` instalado localmente
- Autenticação com GitHub configurada (SSH ou token HTTPS). Se ainda não
  estiver, o GitHub Desktop ou `gh auth login` resolvem em 2 minutos.

### 1.2 Criar o repositório

No GitHub, crie um repositório novo (sugestão: `radar-politicas-municipais`).
**Não** marque "Initialize with README" — o repositório local já tem um.

### 1.3 Inicializar localmente

Descompacte o `radar_clear.zip` e, dentro da pasta `radar_clear/`:

```bash
git init
git add .
git commit -m "Versão inicial: MVP com PNCP (1 dia, 4 eixos)"
git branch -M main
git remote add origin git@github.com:SEU_USUARIO/radar-politicas-municipais.git
git push -u origin main
```

(Se autenticar por HTTPS, troque `git@github.com:` por `https://github.com/`.)

### 1.4 Habilitar GitHub Pages

No repositório, **Settings → Pages → Source**: escolha `main` branch, pasta
`/ (root)`. Salva. Em ~1 minuto o site fica disponível em
`https://SEU_USUARIO.github.io/radar-politicas-municipais/`.

O GitHub Pages serve qualquer `index.html` na raiz — e o seu já está lá.

### 1.5 Cuidados com o que vai pro repositório

O `.gitignore` já está configurado para excluir:

- `data/raw/pncp_cache/` — cache bruto da API, pode chegar a centenas de MB
  com 12 meses de dados. Não faz sentido versionar; é regenerável.
- `__pycache__/`, `.ipynb_checkpoints/` — lixo de execução.

O que **vai** pro repositório (e deve ir):

- Código (`radar_policy/`, scripts soltos)
- Taxonomia (`radar_policy/taxonomy/taxonomy_v0.yaml`)
- `index.html` (o site)
- Dados processados (`data/processed/*.parquet` e `.csv`) — leves, úteis
  para quem clonar o repositório consumir direto

---

## 2. Expandir para mais municípios

### 2.1 Por que não dá pra "escolher municípios"

A API do PNCP não filtra por município. Você pede um intervalo de datas
e recebe contratos de todos os municípios que publicaram naquele intervalo.

Então a expansão da cobertura **municipal** se dá através da expansão
**temporal**: quanto mais dias você coleta, mais municípios aparecem na
sua base (porque mais municípios contratam ao longo do tempo).

Para referência: 1 dia útil produz ~27 municípios classificados na nossa
amostra. 12 meses contínuos provavelmente cobrem 4.000+ dos 5.570
municípios brasileiros.

### 2.2 Como rodar uma janela maior

Use o `expandir_coleta.py`:

```bash
# Trimestre inteiro
python expandir_coleta.py --inicio 2025-07-01 --fim 2025-09-30

# Ano inteiro (vai demorar várias horas — use tela/tmux ou rode à noite)
python expandir_coleta.py --inicio 2025-01-01 --fim 2025-12-31

# Demo rápida (5 dias, limitando páginas por dia)
python expandir_coleta.py --inicio 2025-09-01 --fim 2025-09-05 --max-paginas-por-dia 20
```

### 2.3 Estimativas de tempo (aproximadas, dependem da carga do PNCP)

| Janela            | Páginas estimadas | Tempo (~0.4s/pág)    |
|-------------------|-------------------|----------------------|
| 1 dia             | ~150              | 1 a 2 min            |
| 1 semana          | ~1.000            | 8 a 15 min           |
| 1 mês             | ~4.500            | 35 min a 1h          |
| 1 trimestre       | ~13.500           | 1h45 a 3h            |
| 1 ano             | ~55.000           | 7h a 12h             |

A API ocasionalmente fica lenta — o script tem retry com backoff
exponencial e cacheia tudo, então pode interromper com Ctrl+C e retomar
sem perder nada.

### 2.4 Retomada de coleta interrompida

Como o cache é por (data + página + tamanho), rodar o mesmo comando
duas vezes só baixa o que falta. Pode rodar com confiança:

```bash
# Travou no meio? Roda de novo, ele continua de onde parou
python expandir_coleta.py --inicio 2025-01-01 --fim 2025-12-31
```

### 2.5 Processar o que foi baixado

Após a coleta, gera as bases:

```bash
python process_cache.py
```

Esse comando lê todo o cache de uma vez e produz:
- `data/processed/contratos_classificados.parquet`
- `data/processed/municipios_eixos.parquet`
- Versões `.csv` das duas

### 2.6 Regerar o site com os novos dados

```bash
python build_html.py
```

O `index.html` é regerado com os números atualizados.

---

## 3. Atualização contínua (rotina depois do primeiro push)

Você vai querer atualizar duas coisas ao longo do tempo:

1. **Dados** — incorporar mais dias de PNCP conforme o tempo passa.
2. **Taxonomia** — refinar palavras-chave conforme descobre falsos
   positivos/negativos.

Ambas seguem o mesmo fluxo: roda local, gera arquivos, commita, push.

### 3.1 Atualização mensal típica

```bash
# 1) Baixa o mês recém-fechado
python expandir_coleta.py --inicio 2026-04-01 --fim 2026-04-30

# 2) Reprocessa o cache inteiro (rápido, < 1 min)
python process_cache.py

# 3) Regera o site
python build_html.py

# 4) Inspeciona localmente
open index.html   # macOS / xdg-open no Linux

# 5) Se estiver tudo bem, commit + push
git add data/processed/ index.html
git commit -m "Dados de abril/2026"
git push
```

GitHub Pages atualiza em ~1 min após o push.

### 3.2 Refinar a taxonomia

Quando inspecionar contratos individuais no site e identificar falsos
positivos (a aba "Contratos individuais" foi feita para isso), o caminho é:

1. Edite `radar_policy/taxonomy/taxonomy_v0.yaml`
2. **Bump da versão** no cabeçalho (`v0.2.0 → v0.3.0`) e registre o
   changelog em comentário no topo do arquivo
3. Rode `python process_cache.py` — vai reclassificar tudo com a nova
   taxonomia
4. Rode `python build_html.py`
5. Inspecione, commite, push

A taxonomia em YAML separada do código é justamente pra que mudanças
fiquem auditáveis em diff. Não tem nada de mágico — você abre o arquivo,
acrescenta uma `keywords_exclude`, salva.

### 3.3 Fluxo recomendado pra evoluir o projeto

Ordem de prioridade dos próximos passos, em termos de retorno por
esforço:

1. **Expandir pra 12 meses contínuos** (1 dia → 1 ano = 365x mais
   municípios cobertos). Roda uma vez, à noite, deixa terminar.
2. **Score de confiança por classificação** — número de keywords casadas
   + qualidade do match. Permite filtrar a base por nível de certeza.
3. **Validação humana estratificada** — sortear 300 contratos
   classificados, rotular manualmente cada um (correto/incorreto/duvidoso),
   e usar isso pra calcular precisão e recall por subeixo. É o que dá
   credibilidade científica pro projeto.
4. **Transferegov** — atravessa o gargalo do PNCP para municípios pequenos
   que recebem mais convênios do que contratam.
5. **Sistemas setoriais** (SIOPS, SIOPE, Censo SUAS) — confirmam ou
   contradizem o sinal do PNCP.
6. **Fase 2**: diários oficiais municipais com classificação assistida
   por LLM.

---

## Apêndice: comandos de emergência

```bash
# Apagar cache e recomeçar do zero (cuidado!)
rm -rf data/raw/pncp_cache/

# Ver quantas páginas estão em cache
ls data/raw/pncp_cache/ | wc -l

# Ver tamanho do cache em disco
du -sh data/raw/pncp_cache/

# Limpar parquets processados (regerável com process_cache.py)
rm data/processed/*.parquet data/processed/*.csv

# Rodar o site localmente sem servidor (qualquer SO moderno)
open index.html       # macOS
xdg-open index.html   # Linux
start index.html      # Windows
```
