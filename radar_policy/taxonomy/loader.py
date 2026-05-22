"""Loader da taxonomia de políticas municipais.

Princípio: a taxonomia é um artefato versionado em YAML, separado do código.
Mudanças na taxonomia devem ser visíveis em diff, revisáveis e auditáveis.

Matching: palavras-chave são casadas com word boundary, evitando que `cei`
case dentro de `Conceição`. Use espaço em torno dos termos curtos ou prefira
termos compostos quando possível.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


def normalize(text: str | None) -> str:
    """Normaliza texto para matching: sem acento, lowercase, espaços colapsados."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(without_accents.lower().split())


def _compile_keyword(kw: str) -> re.Pattern:
    """Compila palavra-chave com word boundary.

    Para termos com 1-2 palavras o boundary evita matches dentro de outras
    palavras (`cei` em `Conceição`). Para frases longas a precisão já é alta.
    """
    # Boundary genérico: começo/espaço antes, fim/espaço/pontuação depois
    escaped = re.escape(kw.strip())
    return re.compile(rf"(?:^|\s|\b){escaped}(?:\b|\s|$)", re.IGNORECASE)


@dataclass(frozen=True)
class Subeixo:
    id: str
    nome: str
    keywords_include: tuple[str, ...]
    keywords_exclude: tuple[str, ...]
    _include_patterns: tuple[re.Pattern, ...] = ()
    _exclude_patterns: tuple[re.Pattern, ...] = ()

    def matches(self, normalized_text: str) -> bool:
        if not any(p.search(normalized_text) for p in self._include_patterns):
            return False
        if any(p.search(normalized_text) for p in self._exclude_patterns):
            return False
        return True

    def matched_keywords(self, normalized_text: str) -> list[str]:
        return [
            kw for kw, p in zip(self.keywords_include, self._include_patterns)
            if p.search(normalized_text)
        ]


@dataclass(frozen=True)
class Eixo:
    id: str
    nome: str
    descricao: str
    marco_legal: tuple[str, ...]
    sistemas_setoriais: tuple[str, ...]
    subeixos: tuple[Subeixo, ...]


@dataclass(frozen=True)
class Taxonomia:
    version: str
    data_referencia: str
    eixos: tuple[Eixo, ...]

    @property
    def eixos_por_id(self) -> dict[str, Eixo]:
        return {e.id: e for e in self.eixos}

    def todos_subeixos(self) -> Iterable[tuple[Eixo, Subeixo]]:
        for eixo in self.eixos:
            for sub in eixo.subeixos:
                yield eixo, sub


def load_taxonomy(path: str | Path) -> Taxonomia:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    eixos = []
    for eixo_id, eixo_data in raw["eixos"].items():
        subeixos = []
        for sub_id, sub_data in eixo_data.get("subeixos", {}).items():
            inc = tuple(normalize(kw) for kw in sub_data.get("keywords_include", []))
            exc = tuple(normalize(kw) for kw in sub_data.get("keywords_exclude", []))
            sub = Subeixo(
                id=sub_id,
                nome=sub_data["nome"],
                keywords_include=inc,
                keywords_exclude=exc,
                _include_patterns=tuple(_compile_keyword(k) for k in inc),
                _exclude_patterns=tuple(_compile_keyword(k) for k in exc),
            )
            subeixos.append(sub)
        eixos.append(
            Eixo(
                id=eixo_id,
                nome=eixo_data["nome"],
                descricao=eixo_data.get("descricao", "").strip(),
                marco_legal=tuple(eixo_data.get("marco_legal", [])),
                sistemas_setoriais=tuple(eixo_data.get("sistemas_setoriais", [])),
                subeixos=tuple(subeixos),
            )
        )
    return Taxonomia(
        version=raw["version"],
        data_referencia=str(raw["data_referencia"]),
        eixos=tuple(eixos),
    )


def default_taxonomy() -> Taxonomia:
    here = Path(__file__).parent
    return load_taxonomy(here / "taxonomy_v0.yaml")
