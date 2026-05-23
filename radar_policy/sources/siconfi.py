"""Cliente SICONFI/Tesouro Nacional — despesas municipais por função/subfunção.

API REST oficial: https://apidatalake.tesouro.gov.br/ords/siconfi/

Princípios:
- Filtra RREO Anexo 02 (despesas por função/subfunção).
- Período: bimestre (1-6). Coleta o bimestre 6 do ano para ter consolidado.
- Mapeamento direto subfunção → eixo (não usa classificador textual, pois
  os dados já vêm pré-categorizados pela LOA).

Limitações honestas:
- Subfunções padrão BR (Portaria MOG 42/1999) não separam saúde mental — fica
  agregada em "Assistência Hospitalar" ou "Atenção Básica". Comunicar isso.
- 1 chamada por município por ano. Com 5.570 municípios, fica pesado. A
  estratégia recomendada é usar a tabela consolidada via paginação por UF.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import requests

log = logging.getLogger(__name__)

API_BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"

# Mapeamento subfunção SIOPE/SICONFI → (eixo_id, subeixo_id)
# Baseado na Portaria MOG 42/1999 + classificação funcional padrão BR
SUBFUNCAO_EIXO_MAP = {
    "Educação Infantil":          ("primeira_infancia", "creche_pre_escola"),
    "Ensino Fundamental":         ("busca_ativa_escolar", "programas_permanencia"),
    "Transporte":                 (None, None),  # ambíguo; pular
    "Educação Especial":          ("busca_ativa_escolar", "programas_permanencia"),
    "Alimentação e Nutrição":     ("seguranca_alimentar", "alimentacao_escolar"),
    "Assistência à Criança e ao Adolescente": ("primeira_infancia", "visitacao_domiciliar"),
}


@dataclass
class SiconfiClient:
    cache_dir: Path
    timeout: int = 60
    sleep_between: float = 0.3
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session.headers.update({"Accept": "application/json"})

    def _cache_path(self, params: dict) -> Path:
        key = "_".join(f"{k}{v}" for k, v in sorted(params.items()))
        return self.cache_dir / f"rreo_{key}.json"

    def consulta_rreo_anexo2(
        self, ano: int, bimestre: int, codigo_ibge: int
    ) -> list[dict]:
        """RREO Anexo 02 (despesas por subfunção) de um município/ano/bimestre."""
        params = {
            "an_exercicio": ano,
            "nr_periodo": bimestre,
            "co_tipo_demonstrativo": "RREO",
            "id_ente": codigo_ibge,
            "co_esfera": "M",
        }
        cache = self._cache_path(params)
        if cache.exists():
            return json.loads(cache.read_text(encoding="utf-8"))
        url = f"{API_BASE}/rreo"
        try:
            r = self.session.get(url, params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json().get("items", [])
        except (requests.RequestException, ValueError) as e:
            log.error("SICONFI falhou (%s/%s/%s): %s", ano, bimestre, codigo_ibge, e)
            return []
        # filtra anexo 02
        anexo2 = [x for x in data if "Anexo 02" in x.get("anexo", "")]
        cache.write_text(json.dumps(anexo2, ensure_ascii=False), encoding="utf-8")
        time.sleep(self.sleep_between)
        return anexo2

    def coletar_municipios(
        self,
        codigos_ibge: list[int],
        ano: int,
        bimestre: int = 6,  # bimestre 6 = consolidado anual
    ) -> Iterator[dict]:
        """Itera sobre despesas Anexo 02 dos municípios solicitados."""
        for i, cod in enumerate(codigos_ibge):
            itens = self.consulta_rreo_anexo2(ano, bimestre, cod)
            if (i + 1) % 50 == 0:
                log.info("SICONFI: %d/%d municípios", i + 1, len(codigos_ibge))
            for x in itens:
                yield x


def classifica_subfuncao(conta: str) -> tuple[str, str] | None:
    """Mapeia o texto da conta/subfunção pra (eixo_id, subeixo_id)."""
    for chave, mapping in SUBFUNCAO_EIXO_MAP.items():
        if chave.lower() in (conta or "").lower():
            if mapping[0] is None:
                return None
            return mapping
    return None
