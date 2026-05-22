"""Processa contratos que já estão no cache local — sem chamar a API.

Use após `fetch_chunk.py` ter baixado material suficiente. Isso permite
iterar na taxonomia e na classificação sem depender de rede.
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
CACHE_DIR = ROOT / "data" / "raw" / "pncp_cache"
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    taxonomia = default_taxonomy()
    rows = []
    seen = set()
    n_files = 0
    n_records = 0
    n_municipais = 0

    for path in sorted(CACHE_DIR.glob("contratos_*.json")):
        n_files += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for record in data.get("data", []):
            n_records += 1
            ncpncp = record.get("numeroControlePNCP")
            if ncpncp in seen:
                continue
            seen.add(ncpncp)
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
                    "numero_controle_pncp": ncpncp,
                    "codigo_ibge": mun["codigo_ibge"],
                    "municipio": mun["municipio"],
                    "uf": mun["uf"],
                    "orgao_cnpj": record.get("orgaoEntidade", {}).get("cnpj"),
                    "orgao_razao_social": record.get("orgaoEntidade", {}).get("razaoSocial"),
                    "data_assinatura": record.get("dataAssinatura"),
                    "valor_global": record.get("valorGlobal"),
                    "objeto": record.get("objetoContrato"),
                    "eixo_id": c.eixo_id,
                    "subeixo_id": c.subeixo_id,
                    "keywords_hit": ";".join(c.keywords_hit),
                })

    log.info(
        "Arquivos cache: %d | registros totais: %d | municipais únicos: %d | classificações: %d",
        n_files, n_records, n_municipais, len(rows),
    )

    df = pd.DataFrame(rows)
    contratos_path = OUT_DIR / "contratos_classificados.parquet"
    df.to_parquet(contratos_path, index=False)

    if df.empty:
        log.warning("Nenhuma classificação gerada — verifique a taxonomia.")
        return

    agg = (
        df.groupby(["codigo_ibge", "municipio", "uf", "eixo_id"])
        .agg(
            n_contratos=("numero_controle_pncp", "nunique"),
            valor_total=("valor_global", "sum"),
            subeixos_atingidos=("subeixo_id", lambda s: ";".join(sorted(set(s)))),
        )
        .reset_index()
    )
    agg["nivel_documentacao"] = agg["n_contratos"].apply(nivel_documentacao)
    agg["rotulo_nivel"] = agg["nivel_documentacao"].apply(rotulo_nivel)
    agg_path = OUT_DIR / "municipios_eixos.parquet"
    agg.to_parquet(agg_path, index=False)

    # Resumos pro console
    log.info("\n=== Distribuição por eixo ===")
    print(df.groupby("eixo_id").size().to_string())
    log.info("\n=== Top 10 municípios em primeira_infancia ===")
    pi = agg[agg.eixo_id == "primeira_infancia"].sort_values("n_contratos", ascending=False).head(10)
    print(pi[["municipio", "uf", "n_contratos", "valor_total", "subeixos_atingidos"]].to_string(index=False))


if __name__ == "__main__":
    main()
