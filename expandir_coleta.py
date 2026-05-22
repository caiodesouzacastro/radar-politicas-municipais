"""Expansão da coleta do PNCP.

Como funciona:
- Quebra um intervalo de datas em janelas diárias (a API aceita janelas
  maiores, mas dias soltos cacheiam melhor e ajudam a retomar coletas).
- Para cada dia, baixa todas as páginas. Como o cliente PNCP cacheia em
  disco, executar de novo o mesmo dia é grátis — ele só baixa o que falta.
- Mostra progresso por dia, permitindo Ctrl+C a qualquer momento sem
  perder o que já foi baixado.

Por que coletar por dia, e não por mês:
- PNCP retorna até X páginas por consulta; janelas muito largas misturam
  meses de publicação numa única paginação e dificultam retomada.
- Dia é a granularidade natural de "dataPublicacaoPncp", que é o filtro da API.

Uso típico:
    # baixa de 01/01/2025 até 31/03/2025
    python expandir_coleta.py --inicio 2025-01-01 --fim 2025-03-31

    # mesmo comando de novo é seguro — pula o que já tem em cache
    python expandir_coleta.py --inicio 2025-01-01 --fim 2025-03-31
"""
from __future__ import annotations

import argparse
import logging
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from radar_policy.sources.pncp import PNCPClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def days_between(d0: date, d1: date):
    cur = d0
    while cur <= d1:
        yield cur
        cur += timedelta(days=1)


def coletar_dia(client: PNCPClient, dia: date, max_pages: int | None) -> dict:
    """Baixa todas as páginas de um único dia. Retorna estatísticas."""
    s = dia.strftime("%Y%m%d")
    params0 = {
        "dataInicial": s,
        "dataFinal": s,
        "pagina": 1,
        "tamanhoPagina": client.page_size,
    }
    # Descobre totalPaginas (já cacheia a primeira página)
    first = client._get_page("contratos", params0)
    total = first.get("totalPaginas", 0)
    total_reg = first.get("totalRegistros", 0)
    if total == 0:
        return {"dia": s, "paginas": 0, "registros": 0, "novas": 0}

    end = min(total, max_pages) if max_pages else total
    novas = 0
    t0 = time.time()
    for page in range(1, end + 1):
        params = dict(params0, pagina=page)
        cache_path = client._cache_key("contratos", params)
        if cache_path.exists():
            continue
        try:
            client._get_page("contratos", params)
            novas += 1
        except Exception as exc:
            log.error("  %s pag %d falhou: %s", s, page, exc)
    elapsed = time.time() - t0
    return {
        "dia": s, "paginas_total": end, "registros": total_reg,
        "novas": novas, "tempo_s": round(elapsed, 1),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inicio", required=True, help="Data inicial YYYY-MM-DD")
    ap.add_argument("--fim", required=True, help="Data final YYYY-MM-DD (inclusiva)")
    ap.add_argument("--max-paginas-por-dia", type=int, default=None,
                    help="Limita páginas por dia (útil pra demo)")
    ap.add_argument("--page-size", type=int, default=50)
    args = ap.parse_args()

    d0 = parse_date(args.inicio)
    d1 = parse_date(args.fim)
    if d1 < d0:
        raise SystemExit("--fim precisa ser >= --inicio")

    client = PNCPClient(
        cache_dir=ROOT / "data" / "raw" / "pncp_cache",
        page_size=args.page_size,
        timeout=60,
        sleep_between_pages=0.3,
        max_retries=4,
    )

    dias = list(days_between(d0, d1))
    log.info("Coleta planejada: %d dia(s) (%s → %s)", len(dias),
             d0.isoformat(), d1.isoformat())

    total_novas = 0
    t_global = time.time()
    for i, dia in enumerate(dias, 1):
        try:
            stats = coletar_dia(client, dia, args.max_paginas_por_dia)
        except KeyboardInterrupt:
            log.warning("Interrompido pelo usuário — cache preservado.")
            break
        total_novas += stats.get("novas", 0)
        log.info(
            "[%d/%d] %s · %s reg · %s pag · %s novas · %ss",
            i, len(dias),
            stats["dia"],
            stats.get("registros", 0),
            stats.get("paginas_total", 0),
            stats.get("novas", 0),
            stats.get("tempo_s", "—"),
        )

    log.info("=" * 60)
    log.info("Coleta concluída: %d páginas novas em %.1fs",
             total_novas, time.time() - t_global)
    log.info("Próximo passo: python process_cache.py && python build_html.py")


if __name__ == "__main__":
    main()
