"""Execução do MVP — coleta de 1 semana de contratos do PNCP.

Justificativa do recorte: 1 semana arbitrária de 2025 produz ~13k contratos
totais (~10k municipais), suficiente pra demonstrar o pipeline end-to-end
sem martelar a API. O mesmo código rodaria em janelas maiores ajustando
data_inicial/data_final.
"""
import logging
from pathlib import Path

from radar_policy.pipeline import PipelineConfig, run_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

ROOT = Path(__file__).parent
cfg = PipelineConfig(
    data_inicial="20250915",   # 1 dia - set/2025 (segunda-feira típica)
    data_final="20250915",
    cache_dir=ROOT / "data" / "raw" / "pncp_cache",
    output_dir=ROOT / "data" / "processed",
    max_pages_per_window=None,
    page_size=50,
    n_workers=6,
)

result = run_pipeline(cfg)
print()
print("=== Resultado ===")
for k, v in result.items():
    print(f"  {k}: {v}")
