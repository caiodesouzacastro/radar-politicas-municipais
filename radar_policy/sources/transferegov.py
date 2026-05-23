"""Cliente Transferegov / SICONV — propostas e convênios federais discricionários.

Fonte: http://repositorio.dados.gov.br/seges/detru/

Dados são publicados diariamente como CSVs zipados. Não há API REST estável
pra consultas pontuais — o fluxo é baixar o snapshot do dia e processar
localmente.

Tabelas relevantes pra nós:
- siconv_proposta.csv — texto livre do objeto, município proponente, ano,
  ministério, valor, situação. ÊSTA é a fonte primária pra classificação.
- siconv_convenio.csv — subset das propostas que viraram convênio formalizado.
  Útil pra confirmar "estágio" (proposta → convênio assinado).

Princípios deste cliente:
- Download único do CSV completo, cache em disco como zip (não descompacta no
  cache pra economizar espaço — descompacta on-the-fly).
- Filtragem na ingestão: apenas natureza municipal + janela temporal
  configurável. O CSV bruto tem 1.1 milhões de linhas, mas o subset relevante
  é muito menor.
- Reutiliza a mesma taxonomia e classificador do PNCP. O texto livre
  (OBJETO_PROPOSTA) é entrada do `classify_text`.
"""
from __future__ import annotations

import csv
import io
import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import requests

log = logging.getLogger(__name__)

REPO_BASE = "http://repositorio.dados.gov.br/seges/detru"
ARQUIVO_PROPOSTAS = "siconv_proposta.csv.zip"
ARQUIVO_CONVENIOS = "siconv_convenio.csv.zip"


@dataclass
class TransferegovClient:
    cache_dir: Path
    timeout: int = 600   # download grande, timeout generoso
    chunk_size: int = 1024 * 1024

    def __post_init__(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def baixar_se_necessario(self, nome_arquivo: str, forcar: bool = False) -> Path:
        """Baixa um zip do repositório se ainda não estiver em cache."""
        destino = self.cache_dir / nome_arquivo
        if destino.exists() and not forcar:
            log.info("Cache: %s (%.1f MB) — pulando download",
                     nome_arquivo, destino.stat().st_size / 1e6)
            return destino
        url = f"{REPO_BASE}/{nome_arquivo}"
        log.info("Baixando %s ...", url)
        with requests.get(url, stream=True, timeout=self.timeout) as resp:
            resp.raise_for_status()
            tmp = destino.with_suffix(destino.suffix + ".part")
            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
            tmp.rename(destino)
        log.info("Baixado: %.1f MB", destino.stat().st_size / 1e6)
        return destino

    def iter_propostas(
        self,
        ano_min: int | None = None,
        ano_max: int | None = None,
        somente_municipal: bool = True,
    ) -> Iterator[dict]:
        """Itera sobre propostas filtradas."""
        zip_path = self.baixar_se_necessario(ARQUIVO_PROPOSTAS)
        log.info("Lendo propostas (filtro: ano %s-%s, municipal=%s)...",
                 ano_min, ano_max, somente_municipal)
        with zipfile.ZipFile(zip_path) as zf:
            csv_name = [n for n in zf.namelist() if n.endswith(".csv")][0]
            with zf.open(csv_name) as raw:
                # Trata BOM e usa utf-8
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"),
                                        delimiter=";")
                for row in reader:
                    if somente_municipal and "Municipal" not in row.get("NATUREZA_JURIDICA", ""):
                        continue
                    try:
                        ano = int(row.get("ANO_PROP") or 0)
                    except ValueError:
                        ano = 0
                    if ano_min and ano < ano_min:
                        continue
                    if ano_max and ano > ano_max:
                        continue
                    yield row


def municipio_info(row: dict) -> dict:
    return {
        "codigo_ibge": (row.get("COD_MUNIC_IBGE") or "").strip(),
        "municipio": (row.get("MUNIC_PROPONENTE") or "").strip(),
        "uf": (row.get("UF_PROPONENTE") or "").strip(),
    }


def texto_objeto(row: dict) -> str:
    return (row.get("OBJETO_PROPOSTA") or "").strip()


def valor_global(row: dict) -> float:
    raw = (row.get("VL_GLOBAL_PROP") or "0").replace(",", ".")
    try:
        return float(raw)
    except (ValueError, TypeError):
        return 0.0


def normalizar_codigo_ibge(cod: str) -> str:
    """Transferegov usa código IBGE de 7 dígitos; alguns vêm sem padding."""
    cod = (cod or "").strip()
    if cod and cod.isdigit() and len(cod) < 7:
        return cod.zfill(7)
    return cod
