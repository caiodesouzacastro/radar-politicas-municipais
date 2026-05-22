"""Cliente Transferegov (Plataforma de Transferências Discricionárias).

STATUS: stub. Esta classe documenta a estrutura prevista mas a coleta real
ainda não foi executada no MVP. Razão: o Transferegov não tem uma API REST
pública estável para consulta de convênios; a integração robusta requer
download dos arquivos CSV mensais publicados em
https://www.gov.br/transferenciasabertas/pt-br/dados-abertos.

Campos esperados (após download e processamento):
- nr_convenio
- ds_objeto (texto livre — entrada do classificador)
- vl_global_conv
- co_municipio_ibge
- nm_municipio
- sg_uf
- dt_ass_conv
- ds_situacao_conv

Próximos passos (fase 2 do projeto):
1. Baixar dump mensal mais recente.
2. Filtrar por esfera municipal (proponente = Prefeitura).
3. Reusar `classify_text` da taxonomia.
4. Cruzar com PNCP via codigo_ibge.
"""
from __future__ import annotations


class TransferegovStub:
    def __init__(self):
        raise NotImplementedError(
            "Transferegov ainda não implementado no MVP. Ver docstring para plano."
        )
