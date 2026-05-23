"""Processa caches de TODAS as fontes (PNCP, Transferegov, SICONFI) e produz
a base classificada unificada.

Fontes:
- PNCP (data/raw/pncp_cache/): contratos públicos, classificados por texto livre.
- Transferegov (data/raw/transferegov_cache/): propostas de convênios federais,
  classificadas por texto livre da proposta. SE O ZIP EXISTIR.
- SICONFI (data/raw/siconfi_cache/): despesas RREO Anexo 02, classificação por
  subfunção orçamentária. SE O CACHE EXISTIR.

Saída unificada com coluna `fonte` discriminando origem.
"""
import json
import logging
from pathlib import Path

import pandas as pd

from radar_policy.classify.classifier import (
    classify_text,
    nivel_documentacao,
    rotulo_nivel,
)
from radar_policy.sources.pncp import is_municipal, municipio_info, texto_objeto
from radar_policy.taxonomy.loader import default_taxonomy

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent
PNCP_CACHE = ROOT / "data" / "raw" / "pncp_cache"
TRANSFEREGOV_CACHE = ROOT / "data" / "raw" / "transferegov_cache"
SICONFI_CACHE = ROOT / "data" / "raw" / "siconfi_cache"
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def processar_pncp(taxonomia) -> list[dict]:
    """Lê cache PNCP, classifica por texto, devolve linhas."""
    rows = []
    seen = set()
    n_files = 0
    n_records = 0
    n_municipais = 0

    for path in sorted(PNCP_CACHE.glob("contratos_*.json")):
        n_files += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for record in data.get("data", []):
            n_records += 1
            nc = record.get("numeroControlePNCP")
            if nc in seen:
                continue
            seen.add(nc)
            if not is_municipal(record):
                continue
            n_municipais += 1
            texto = texto_objeto(record)
            if not texto.strip():
                continue
            cls = classify_text(texto, taxonomia)
            if not cls:
                continue
            mun = municipio_info(record)
            for c in cls:
                rows.append({
                    "fonte": "PNCP",
                    "registro_id": nc,
                    "codigo_ibge": mun["codigo_ibge"],
                    "municipio": mun["municipio"],
                    "uf": mun["uf"],
                    "orgao_razao_social": record.get("orgaoEntidade", {}).get("razaoSocial"),
                    "data_referencia": record.get("dataAssinatura"),
                    "valor_global": record.get("valorGlobal"),
                    "objeto": record.get("objetoContrato"),
                    "eixo_id": c.eixo_id,
                    "subeixo_id": c.subeixo_id,
                    "keywords_hit": ";".join(c.keywords_hit),
                    "estagio": "contratado",
                })
    log.info("PNCP: %d arquivos | %d registros | %d municipais | %d classificações",
             n_files, n_records, n_municipais, len(rows))
    return rows


def processar_transferegov(taxonomia, ano_min=2024, ano_max=2025) -> list[dict]:
    """Lê cache Transferegov, classifica por texto da proposta."""
    if not TRANSFEREGOV_CACHE.exists():
        log.info("Transferegov: cache ausente, pulando.")
        return []
    from radar_policy.sources.transferegov import (
        TransferegovClient, texto_objeto as tg_texto,
        municipio_info as tg_mun, valor_global as tg_valor,
        normalizar_codigo_ibge,
    )
    cli = TransferegovClient(cache_dir=TRANSFEREGOV_CACHE)
    if not (TRANSFEREGOV_CACHE / "siconv_proposta.csv.zip").exists():
        log.info("Transferegov: zip ausente em %s, pulando.", TRANSFEREGOV_CACHE)
        return []
    rows = []
    n_proc = 0
    n_class = 0
    # Mapeia situação Transferegov → estágio simplificado
    mapa_estagio = {
        "Cadastrados": "anunciado",
        "Enviado para Análise": "anunciado",
        "em Análise": "anunciado",
        "em Complementação": "anunciado",
        "Aprovados": "aprovado",
        "Rejeitados": "rejeitado",
        "Rejeitados por Impedimento técnico": "rejeitado",
    }
    for row in cli.iter_propostas(ano_min=ano_min, ano_max=ano_max,
                                  somente_municipal=True):
        n_proc += 1
        texto = tg_texto(row)
        if not texto:
            continue
        cls = classify_text(texto, taxonomia)
        if not cls:
            continue
        n_class += 1
        mun = tg_mun(row)
        # situação → estágio
        sit = row.get("SIT_PROPOSTA", "")
        estagio = "anunciado"
        for chave, est in mapa_estagio.items():
            if chave in sit:
                estagio = est
                break
        for c in cls:
            rows.append({
                "fonte": "Transferegov",
                "registro_id": row.get("ID_PROPOSTA"),
                "codigo_ibge": normalizar_codigo_ibge(mun["codigo_ibge"]),
                "municipio": mun["municipio"],
                "uf": mun["uf"],
                "orgao_razao_social": row.get("DESC_ORGAO_SUP", ""),
                "data_referencia": row.get("DIA_PROPOSTA"),
                "valor_global": tg_valor(row),
                "objeto": texto,
                "eixo_id": c.eixo_id,
                "subeixo_id": c.subeixo_id,
                "keywords_hit": ";".join(c.keywords_hit),
                "estagio": estagio,
            })
    log.info("Transferegov: %d propostas | %d classificadas (%d linhas)",
             n_proc, n_class, len(rows))
    return rows


def processar_siconfi() -> list[dict]:
    """Lê cache SICONFI já baixado (chamadas RREO Anexo 02 por município)."""
    if not SICONFI_CACHE.exists():
        log.info("SICONFI: cache ausente, pulando.")
        return []
    from radar_policy.sources.siconfi import classifica_subfuncao
    rows = []
    n_files = 0
    n_class = 0
    for path in sorted(SICONFI_CACHE.glob("rreo_*.json")):
        n_files += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for item in data:
            # Só usamos linha de "DESPESAS EMPENHADAS ATÉ O BIMESTRE" (consolidado)
            if "DESPESAS EMPENHADAS ATÉ O BIMESTRE" not in item.get("coluna", ""):
                continue
            conta = item.get("conta", "")
            mapping = classifica_subfuncao(conta)
            if not mapping:
                continue
            eixo, sub = mapping
            valor = float(item.get("valor", 0) or 0)
            if valor <= 0:
                continue
            n_class += 1
            cod = str(item.get("cod_ibge", "")).zfill(7)
            rows.append({
                "fonte": "SICONFI",
                "registro_id": f"siconfi-{item.get('exercicio')}-{cod}-{conta}",
                "codigo_ibge": cod,
                "municipio": (item.get("instituicao") or "").replace("Prefeitura Municipal de ", "").rsplit(" - ", 1)[0],
                "uf": item.get("uf"),
                "orgao_razao_social": "Prefeitura",
                "data_referencia": f"{item.get('exercicio')}-12-31",
                "valor_global": valor,
                "objeto": f"Despesa empenhada em subfunção: {conta}",
                "eixo_id": eixo,
                "subeixo_id": sub,
                "keywords_hit": f"subfuncao:{conta}",
                "estagio": "executado",
            })
    log.info("SICONFI: %d arquivos | %d linhas classificadas", n_files, n_class)
    return rows


def main():
    taxonomia = default_taxonomy()

    log.info("=== PROCESSANDO PNCP ===")
    rows_pncp = processar_pncp(taxonomia)

    log.info("=== PROCESSANDO TRANSFEREGOV ===")
    rows_tg = processar_transferegov(taxonomia)

    log.info("=== PROCESSANDO SICONFI ===")
    rows_sf = processar_siconfi()

    rows = rows_pncp + rows_tg + rows_sf
    log.info("=== TOTAL UNIFICADO ===")
    log.info("Linhas: %d (PNCP=%d, Transferegov=%d, SICONFI=%d)",
             len(rows), len(rows_pncp), len(rows_tg), len(rows_sf))

    df = pd.DataFrame(rows)
    contratos_path = OUT_DIR / "contratos_classificados.parquet"
    df.to_parquet(contratos_path, index=False)
    df.to_csv(OUT_DIR / "contratos_classificados.csv", index=False)

    if df.empty:
        log.warning("Nenhuma classificação gerada.")
        return

    # Agregação por município x eixo (todas as fontes)
    agg = (
        df.groupby(["codigo_ibge", "municipio", "uf", "eixo_id"])
        .agg(
            n_contratos=("registro_id", "nunique"),
            valor_total=("valor_global", "sum"),
            subeixos_atingidos=("subeixo_id", lambda s: ";".join(sorted(set(s)))),
            fontes=("fonte", lambda s: ";".join(sorted(set(s)))),
        )
        .reset_index()
    )
    agg["nivel_documentacao"] = agg["n_contratos"].apply(nivel_documentacao)
    agg["rotulo_nivel"] = agg["nivel_documentacao"].apply(rotulo_nivel)
    agg.to_parquet(OUT_DIR / "municipios_eixos.parquet", index=False)
    agg.to_csv(OUT_DIR / "municipios_eixos.csv", index=False)

    log.info("\n=== Distribuição por eixo e fonte ===")
    print(df.groupby(["eixo_id", "fonte"]).size().unstack(fill_value=0).to_string())

    log.info("\n=== Top municípios em primeira_infancia ===")
    pi = agg[agg.eixo_id == "primeira_infancia"].sort_values("n_contratos", ascending=False).head(10)
    print(pi[["municipio", "uf", "n_contratos", "valor_total", "fontes"]].to_string(index=False))


if __name__ == "__main__":
    main()
