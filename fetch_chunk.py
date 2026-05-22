"""Baixa um chunk de páginas do PNCP. Idempotente — pula o que já está em cache.

Uso:
    python fetch_chunk.py --data 20250915 --start 1 --end 50

Roda em < 2min normalmente. Para coletar tudo, executar várias vezes
ajustando start/end. O cache em data/raw/pncp_cache evita refazer trabalho.
"""
import argparse
import logging
import time
from pathlib import Path

from radar_policy.sources.pncp import PNCPClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-inicial", required=True)
    ap.add_argument("--data-final", required=True)
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=None)
    ap.add_argument("--page-size", type=int, default=50)
    args = ap.parse_args()

    client = PNCPClient(
        cache_dir=ROOT / "data" / "raw" / "pncp_cache",
        page_size=args.page_size,
        timeout=45,
        sleep_between_pages=0.2,
        max_retries=3,
    )

    base_params = {
        "dataInicial": args.data_inicial,
        "dataFinal": args.data_final,
        "tamanhoPagina": args.page_size,
    }
    # pega primeira pra ter totalPaginas
    p1 = client._get_page("contratos", dict(base_params, pagina=1))
    total = p1.get("totalPaginas", 0)
    end = min(args.end or total, total)
    log.info("Total páginas: %d. Vou baixar %d até %d", total, args.start, end)

    t0 = time.time()
    for page in range(args.start, end + 1):
        params = dict(base_params, pagina=page)
        cache_path = client._cache_key("contratos", params)
        if cache_path.exists():
            continue
        try:
            client._get_page("contratos", params)
        except Exception as exc:
            log.error("página %d falhou: %s", page, exc)
            continue
        if (page - args.start) % 10 == 0:
            elapsed = time.time() - t0
            log.info("  página %d/%d (%.1fs)", page, end, elapsed)

    log.info("Chunk finalizado em %.1fs", time.time() - t0)


if __name__ == "__main__":
    main()
