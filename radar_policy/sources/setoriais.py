"""Stubs para os sistemas setoriais.

SIOPS  — https://siops.datasus.gov.br/  (despesas em saúde por município)
SIOPE  — https://www.fnde.gov.br/siope/ (despesas em educação por município)
Censo SUAS — http://aplicacoes.mds.gov.br/sagirmps/portal-censo/ (assistência)

Cada um desses sistemas tem regras próprias:

SIOPS:
- Bimestral, por município.
- Acesso via CSV/Excel exportável; não há REST API estável.
- Para a primeira infância: rubricas de atenção básica, vacinação, saúde da
  criança e da mulher.

SIOPE:
- Anual, por município.
- Permite recortar "Educação Infantil" como subfunção orçamentária.
- Cruzamento natural com Censo Escolar (matrículas) para dimensionar
  esforço por matrícula.

Censo SUAS:
- Anual, survey respondido pelos municípios sobre serviços socioassistenciais.
- Cobre CRAS, CREAS, Centro POP, Serviços de Acolhimento.
- Microdados públicos no portal do MDS.

Plano para fase 2:
- Implementar adapter para cada base.
- Padronizar saída no formato {codigo_ibge, ano, indicador, valor}.
- Cruzamento por codigo_ibge produz painel multi-fonte por município x eixo.
"""

SISTEMAS_PREVISTOS = ["siops", "siope", "censo_suas"]
