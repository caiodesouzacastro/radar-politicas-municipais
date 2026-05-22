"""Classificação de registros administrativos por aderência a eixos temáticos.

NOTA METODOLÓGICA IMPORTANTE
============================
Este classificador NÃO determina se um município "implementa" uma política.
Ele determina se há REGISTROS ADMINISTRATIVOS cujo objeto declarado é
compatível com uma agenda de política pública.

A escala produzida é uma escala de INTENSIDADE DE DOCUMENTAÇÃO, não de
intensidade de implementação. Municípios com maior capacidade burocrática
sistematicamente produzem mais registros, o que enviesa qualquer leitura
da escala como proxy de implementação.

Esta limitação é intencional e deve ser comunicada em todos os outputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from radar_policy.taxonomy.loader import Subeixo, Taxonomia, normalize


@dataclass(frozen=True)
class Classificacao:
    """Resultado da classificação de um único registro administrativo."""

    eixo_id: str
    subeixo_id: str
    keywords_hit: tuple[str, ...]


def classify_text(text: str, taxonomia: Taxonomia) -> list[Classificacao]:
    """Retorna todas as classificações aplicáveis a um texto.

    Um registro pode ser classificado em múltiplos subeixos (ex: contrato para
    "merenda escolar para creches" cai em primeira_infancia/creche_pre_escola
    E em seguranca_alimentar/alimentacao_escolar). Isso é proposital — agendas
    de política pública são intersetoriais por natureza.
    """
    normalized = normalize(text)
    results = []
    for eixo, sub in taxonomia.todos_subeixos():
        if sub.matches(normalized):
            results.append(
                Classificacao(
                    eixo_id=eixo.id,
                    subeixo_id=sub.id,
                    keywords_hit=tuple(sub.matched_keywords(normalized)),
                )
            )
    return results


# Escala de documentação por município x eixo
# Inspirada em escalas de "policy footprint" usadas em estudos comparativos.
NIVEIS_DOCUMENTACAO = {
    0: "sem_registros",          # nenhum contrato/transferência identificado
    1: "registro_isolado",        # 1 a 2 registros no período
    2: "registros_recorrentes",   # 3 a 9 registros
    3: "atividade_substancial",   # 10 a 49 registros
    4: "atividade_intensa",       # 50+ registros
}


def nivel_documentacao(n_registros: int) -> int:
    if n_registros == 0:
        return 0
    if n_registros <= 2:
        return 1
    if n_registros <= 9:
        return 2
    if n_registros <= 49:
        return 3
    return 4


def rotulo_nivel(n: int) -> str:
    return NIVEIS_DOCUMENTACAO[n]
