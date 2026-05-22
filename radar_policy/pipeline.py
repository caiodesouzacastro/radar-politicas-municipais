"""Pipeline principal do Radar de Políticas Municipais.

Fluxo:
1. Ingere contratos do PNCP num intervalo de datas.
2. Filtra por esfera municipal.
3. Classifica cada contrato pela taxonomia.
4. Persiste duas tabelas:
   - contratos_classificados.parquet  (1 linha por contrato classificado)
   - municipios_eixos.parquet         (1 linha por município x eixo, agregado)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from radar_policy.classify.classifier import (
    Classificacao,
    classify_text,
    nivel_documentacao,
    rotulo_nivel,
)
from radar_policy.sources.pncp import (
    PNCPClient,
    is_municipal,
    municipio_info,
    texto_objeto,
)
from radar_policy.sources.pncp_parallel import consulta_contratos_parallel
from radar_policy.taxonomy.loader import Taxonomia, default_taxonomy

log = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    data_inicial: str           # YYYYMMDD
    data_final: str             # YYYYMMDD
    cache_dir: Path
    output_dir: Path
    max_pages_per_window: int | None = None  # truncar pra demo
    page_size: int = 50
    n_workers: int = 4


def run_pipeline(cfg: PipelineConfig, taxonomia: Taxonomia | None = None) -> dict:
    taxonomia = taxonomia or default_taxonomy()
    client = PNCPClient(cache_dir=cfg.cache_dir, page_size=cfg.page_size)

    contratos_rows: list[dict] = []
    municipal_count = 0
    total_count = 0

    fonte = consulta_contratos_parallel(
        client,
        cfg.data_inicial, cfg.data_final,
        max_pages=cfg.max_pages_per_window,
        n_workers=cfg.n_workers,
    )

    for record in fonte:
        total_count += 1
        if not is_municipal(record):
            continue
        municipal_count += 1
        texto = texto_objeto(record)
        if not texto.strip():
            continue
        classificacoes: list[Classificacao] = classify_text(texto, taxonomia)
        if not classificacoes:
            continue
        mun = municipio_info(record)
        for cl in classificacoes:
            contratos_rows.append(
                {
                    "numero_controle_pncp": record.get("numeroControlePNCP"),
                    "codigo_ibge": mun["codigo_ibge"],
                    "municipio": mun["municipio"],
                    "uf": mun["uf"],
                    "orgao_cnpj": record.get("orgaoEntidade", {}).get("cnpj"),
                    "orgao_razao_social": record.get("orgaoEntidade", {}).get("razaoSocial"),
                    "data_assinatura": record.get("dataAssinatura"),
                    "valor_global": record.get("valorGlobal"),
                    "objeto": record.get("objetoContrato"),
                    "eixo_id": cl.eixo_id,
                    "subeixo_id": cl.subeixo_id,
                    "keywords_hit": ";".join(cl.keywords_hit),
                }
            )

    log.info(
        "Pipeline: %d contratos totais, %d municipais, %d classificações geradas",
        total_count, municipal_count, len(contratos_rows),
    )

    df_contratos = pd.DataFrame(contratos_rows)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    contratos_path = cfg.output_dir / "contratos_classificados.parquet"
    df_contratos.to_parquet(contratos_path, index=False)

    # Agregado por município x eixo
    if not df_contratos.empty:
        agg = (
            df_contratos.groupby(["codigo_ibge", "municipio", "uf", "eixo_id"])
            .agg(
                n_contratos=("numero_controle_pncp", "nunique"),
                valor_total=("valor_global", "sum"),
                subeixos_atingidos=("subeixo_id", lambda s: ";".join(sorted(set(s)))),
            )
            .reset_index()
        )
        agg["nivel_documentacao"] = agg["n_contratos"].apply(nivel_documentacao)
        agg["rotulo_nivel"] = agg["nivel_documentacao"].apply(rotulo_nivel)
        mun_eixos_path = cfg.output_dir / "municipios_eixos.parquet"
        agg.to_parquet(mun_eixos_path, index=False)
    else:
        agg = pd.DataFrame()

    return {
        "n_contratos_total_api": total_count,
        "n_contratos_municipais": municipal_count,
        "n_classificacoes": len(contratos_rows),
        "n_municipios_com_registro": df_contratos["codigo_ibge"].nunique() if not df_contratos.empty else 0,
        "contratos_path": str(contratos_path),
        "agg_path": str(cfg.output_dir / "municipios_eixos.parquet"),
    }
