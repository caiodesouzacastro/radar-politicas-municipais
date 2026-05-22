"""Cliente para a API de Consulta do PNCP (Portal Nacional de Contratações Públicas).

Endpoint público, sem autenticação. Documentação:
https://pncp.gov.br/api/consulta/swagger-ui/index.html

Princípios:
- Cache em disco por janela temporal (datas + página + filtros) — chamadas
  repetidas não batem na API.
- Paginação automática até `tamanhoPagina` * `totalPaginas`.
- Filtro por esfera (M=municipal, E=estadual, F=federal) feito no cliente
  porque a API não aceita esse parâmetro na consulta de contratos.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import requests

log = logging.getLogger(__name__)

PNCP_BASE = "https://pncp.gov.br/api/consulta/v1"
DEFAULT_PAGE_SIZE = 50


@dataclass
class PNCPClient:
    cache_dir: Path
    page_size: int = DEFAULT_PAGE_SIZE
    timeout: int = 60
    sleep_between_pages: float = 0.4
    max_retries: int = 4
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session.headers.update({"Accept": "application/json"})

    def _cache_key(self, endpoint: str, params: dict) -> Path:
        payload = json.dumps({"endpoint": endpoint, "params": params}, sort_keys=True)
        h = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return self.cache_dir / f"{endpoint}_{h}.json"

    def _get_page(self, endpoint: str, params: dict) -> dict:
        cache_file = self._cache_key(endpoint, params)
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))
        url = f"{PNCP_BASE}/{endpoint}"
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 204:
                    data = {"data": [], "totalPaginas": 0, "totalRegistros": 0}
                else:
                    resp.raise_for_status()
                    data = resp.json()
                cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                return data
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
                last_exc = exc
                backoff = (2 ** attempt) + 1
                log.warning(
                    "PNCP falha (tentativa %d/%d) em %s pag=%s: %s — retry em %ds",
                    attempt + 1, self.max_retries, endpoint,
                    params.get("pagina"), exc, backoff,
                )
                time.sleep(backoff)
        raise RuntimeError(f"PNCP falhou após {self.max_retries} tentativas: {last_exc}")

    def consulta_contratos(
        self,
        data_inicial: str,
        data_final: str,
        max_pages: int | None = None,
    ) -> Iterator[dict]:
        """Itera sobre contratos publicados num intervalo.

        Datas no formato YYYYMMDD. A janela máxima recomendada é de 1 ano por
        chamada, mas a API aceita até cerca de 1 ano sem problemas.
        """
        params = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "pagina": 1,
            "tamanhoPagina": self.page_size,
        }
        first = self._get_page("contratos", params)
        total_paginas = first.get("totalPaginas", 0)
        total_reg = first.get("totalRegistros", 0)
        log.info(
            "PNCP %s-%s: %d registros em %d páginas",
            data_inicial, data_final, total_reg, total_paginas,
        )
        for item in first.get("data", []):
            yield item

        limit = total_paginas if max_pages is None else min(total_paginas, max_pages)
        for page in range(2, limit + 1):
            params_p = dict(params, pagina=page)
            data = self._get_page("contratos", params_p)
            for item in data.get("data", []):
                yield item
            if page % 20 == 0:
                log.info("  ... página %d/%d", page, limit)
            time.sleep(self.sleep_between_pages)


# Helpers de extração de campos relevantes

def is_municipal(record: dict) -> bool:
    return record.get("orgaoEntidade", {}).get("esferaId") == "M"


def municipio_info(record: dict) -> dict:
    u = record.get("unidadeOrgao", {}) or {}
    return {
        "codigo_ibge": u.get("codigoIbge"),
        "municipio": u.get("municipioNome"),
        "uf": u.get("ufSigla"),
    }


def texto_objeto(record: dict) -> str:
    """Texto livre para classificação por keywords."""
    parts = [
        record.get("objetoContrato") or "",
        record.get("informacaoComplementar") or "",
    ]
    return " ".join(p for p in parts if p)
