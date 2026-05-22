"""Cliente PNCP paralelo — para coletas mais agressivas mantendo cache."""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterator

from radar_policy.sources.pncp import PNCPClient

log = logging.getLogger(__name__)


def consulta_contratos_parallel(
    client: PNCPClient,
    data_inicial: str,
    data_final: str,
    max_pages: int | None = None,
    n_workers: int = 4,
) -> Iterator[dict]:
    # Pega a primeira página pra descobrir totalPaginas
    params0 = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "pagina": 1,
        "tamanhoPagina": client.page_size,
    }
    first = client._get_page("contratos", params0)
    total = first.get("totalPaginas", 0)
    log.info("paralelo: %d páginas totais, %d workers", total, n_workers)
    for item in first.get("data", []):
        yield item

    limit = total if max_pages is None else min(total, max_pages)
    pages_to_fetch = list(range(2, limit + 1))

    # Fetch paralelo, mas yield em ordem de chegada (não importa a ordem aqui)
    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        futures = {
            ex.submit(
                client._get_page,
                "contratos",
                dict(params0, pagina=p),
            ): p
            for p in pages_to_fetch
        }
        done_count = 0
        for fut in as_completed(futures):
            p = futures[fut]
            try:
                data = fut.result()
            except Exception as exc:
                log.error("Página %d falhou: %s", p, exc)
                continue
            for item in data.get("data", []):
                yield item
            done_count += 1
            if done_count % 50 == 0:
                log.info("  ... %d/%d páginas processadas", done_count, len(pages_to_fetch))
