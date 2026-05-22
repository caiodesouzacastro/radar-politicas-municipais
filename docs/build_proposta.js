// Documento de Proposta — Radar de Políticas Municipais (CLEAR)
// Geração via docx-js seguindo o skill /mnt/skills/public/docx

const {
  Document, Packer, Paragraph, TextRun, Header, Footer,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
  Table, TableRow, TableCell, WidthType, ShadingType, PageNumber,
  TabStopType, TabStopPosition, PageBreak
} = require('docx');
const fs = require('fs');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const P = (text, opts = {}) => new Paragraph({
  spacing: { after: 160, line: 320 },
  ...opts,
  children: [new TextRun({ text, ...(opts.run || {}) })],
});

const H1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 320, after: 200 },
  children: [new TextRun({ text })],
});

const H2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 240, after: 160 },
  children: [new TextRun({ text })],
});

const bullet = (text) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  spacing: { after: 100, line: 300 },
  children: [new TextRun({ text })],
});

const numbered = (text) => new Paragraph({
  numbering: { reference: "numbers", level: 0 },
  spacing: { after: 100, line: 300 },
  children: [new TextRun({ text })],
});

const border = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const cellBorders = { top: border, bottom: border, left: border, right: border };

const headerCell = (text, w) => new TableCell({
  borders: cellBorders,
  width: { size: w, type: WidthType.DXA },
  shading: { fill: "E8EEF4", type: ShadingType.CLEAR },
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  children: [new Paragraph({ children: [new TextRun({ text, bold: true })] })],
});

const dataCell = (text, w) => new TableCell({
  borders: cellBorders,
  width: { size: w, type: WidthType.DXA },
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  children: [new Paragraph({ children: [new TextRun({ text })] })],
});

// ---------------------------------------------------------------------------
// Conteúdo
// ---------------------------------------------------------------------------
const children = [];

// Título e subtítulo
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 120 },
  children: [new TextRun({
    text: "Radar de Políticas Municipais",
    bold: true, size: 40,
  })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 80 },
  children: [new TextRun({
    text: "Proposta de bem público para o CLEAR",
    size: 26, italics: true,
  })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 480 },
  children: [new TextRun({
    text: "Versão de trabalho — acompanha protótipo executável",
    size: 20, color: "666666",
  })],
}));

// 1. Sumário executivo
children.push(H1("1. Sumário executivo"));
children.push(P(
  "O Brasil produz, todos os dias, milhares de registros administrativos sobre " +
  "políticas públicas municipais — contratações, transferências, despesas " +
  "orçamentárias, atos normativos, prestações de contas setoriais. Essas " +
  "informações existem em fontes oficiais (PNCP, Transferegov, SIOPS, SIOPE, " +
  "Censo SUAS, diários oficiais), mas estão fragmentadas em sistemas que não " +
  "se conversam e em formatos que não permitem leitura temática."
));
children.push(P(
  "Esta proposta apresenta o Radar de Políticas Municipais: uma camada de " +
  "agregação e classificação que organiza esses registros dispersos por " +
  "agenda de política pública, com taxonomia transparente e metodologia " +
  "auditável. O entregável final é um bem público — base aberta, código " +
  "aberto, metodologia documentada — útil para gestores municipais que " +
  "querem ver o que pares estão fazendo, pesquisadores que precisam " +
  "identificar casos de implementação, e o próprio CLEAR para mapear " +
  "oportunidades de avaliação."
));
children.push(P(
  "Acompanha esta proposta um protótipo funcional que demonstra o pipeline " +
  "end-to-end (PNCP → classificação por taxonomia → base agregada → " +
  "dashboard exploratório) sobre uma amostra real de 2.700 contratos " +
  "públicos de um dia útil, com taxonomia versionada cobrindo quatro " +
  "agendas: primeira infância, busca ativa escolar, segurança alimentar " +
  "e saúde mental."
));

// 2. Diagnóstico
children.push(H1("2. Diagnóstico"));

children.push(H2("2.1 O problema da fragmentação"));
children.push(P(
  "Hoje, para responder à pergunta \"quais municípios brasileiros estão " +
  "implementando políticas de primeira infância?\", um pesquisador precisa " +
  "consultar separadamente: o PNCP para contratações, o Transferegov para " +
  "convênios federais, o SIOPE para gasto educacional, o Censo SUAS para " +
  "serviços assistenciais, a base do e-PCF para o Programa Criança Feliz, " +
  "o Censo Escolar para matrículas em creche, eventualmente diários " +
  "oficiais municipais para atos normativos, e notícias institucionais " +
  "para anúncios. Cada fonte tem padrão próprio, recortes próprios, " +
  "vocabulário próprio."
));
children.push(P(
  "O resultado prático é que estudos comparativos sobre política municipal " +
  "no Brasil normalmente cobrem ou pouquíssimos casos (estudo qualitativo " +
  "de cinco municípios) ou poucas dimensões (apenas gasto, ou apenas uma " +
  "fonte). A informação existe; o que falta é a camada que a torna " +
  "tematicamente legível."
));

children.push(H2("2.2 O que a ferramenta NÃO se propõe a medir"));
children.push(P(
  "Ser explícito sobre o que está fora do escopo é tão importante quanto " +
  "definir o escopo. Esta ferramenta não mede:"
));
children.push(bullet(
  "Qualidade de implementação. Um contrato existe ou não; o contrato ter " +
  "produzido resultado é outra pergunta, normalmente respondida por avaliação."
));
children.push(bullet(
  "Cobertura populacional efetiva. Cinco creches contratadas em um município " +
  "não dizem se a fila de vagas zerou."
));
children.push(bullet(
  "Adequação técnica ou orçamentária. O valor pago pode ser alto, baixo ou " +
  "adequado; a ferramenta não opina."
));
children.push(P(
  "O que a ferramenta mede é intensidade de documentação: quantos registros " +
  "administrativos públicos um município produziu cujo objeto declarado é " +
  "compatível com uma agenda de política pública. É uma medida bem mais " +
  "modesta, mas é a medida honesta dado o material disponível."
));

children.push(H2("2.3 Viés conhecido a tratar"));
children.push(P(
  "A correlação entre pegada documental e implementação real é fraca e " +
  "enviesada: municípios com maior capacidade burocrática deixam mais " +
  "rastros sistematicamente. Isso significa que qualquer ranking ingênuo " +
  "vai sub-representar municípios pequenos e pobres — justamente aqueles " +
  "que mais interessam para política pública."
));
children.push(P(
  "Esta limitação é estrutural e não pode ser eliminada — mas pode ser " +
  "comunicada, controlada estatisticamente quando útil (cruzamento com " +
  "capacidade institucional do município) e mitigada pela inclusão de " +
  "fontes que dependem menos de capacidade burocrática (notícias " +
  "institucionais, atos normativos)."
));

// 3. Solução
children.push(H1("3. Solução proposta"));

children.push(H2("3.1 Arquitetura conceitual"));
children.push(P(
  "Quatro camadas, cada uma versionada e auditável:"
));
children.push(numbered(
  "Camada de ingestão: clientes específicos para cada fonte oficial, com " +
  "cache em disco e tratamento explícito de falhas. Hoje cobrindo PNCP; " +
  "previsto Transferegov, SIOPS, SIOPE, Censo SUAS."
));
children.push(numbered(
  "Camada de taxonomia: artefato YAML versionado que define, para cada " +
  "agenda, os subeixos, marco legal, sistemas setoriais relacionados, " +
  "palavras-chave de inclusão e exclusão. Mudanças visíveis em diff."
));
children.push(numbered(
  "Camada de classificação: aplica a taxonomia sobre os registros " +
  "ingeridos, produzindo classificações multi-eixo (um contrato pode " +
  "ser simultaneamente primeira infância e segurança alimentar, e isso " +
  "é proposital). Produz também a escala de intensidade de documentação."
));
children.push(numbered(
  "Camada de apresentação: dashboards, notebooks e base aberta. " +
  "Cada output traz disclaimer metodológico explícito."
));

children.push(H2("3.2 Por que o CLEAR é o lugar certo"));
children.push(P(
  "O valor agregado do projeto não está nos dados — eles são públicos. " +
  "Está na metodologia transparente, no rigor da taxonomia, e na " +
  "explicitação das limitações epistemológicas. É exatamente o tipo de " +
  "bem público que centros de avaliação produzem bem e que entidades " +
  "puramente técnicas produzem mal. A ferramenta também alimenta " +
  "diretamente a missão do CLEAR de mapear oportunidades de avaliação: " +
  "saber onde uma política existe é o primeiro passo para avaliar se " +
  "ela funciona."
));

// 4. MVP entregue
children.push(H1("4. MVP entregue (este documento acompanha código executável)"));

children.push(H2("4.1 O que foi construído"));
children.push(bullet(
  "Taxonomia v0.2 em YAML cobrindo quatro agendas e 14 subeixos, com " +
  "marco legal, sistemas setoriais e palavras-chave de inclusão/exclusão " +
  "documentadas."
));
children.push(bullet(
  "Cliente PNCP com cache em disco, paginação, fetch paralelo e retry " +
  "com backoff exponencial."
));
children.push(bullet(
  "Pipeline de classificação multi-eixo com matching por word boundary " +
  "(corrigindo falso positivo da v0.1 em que \"cei\" casava em \"Conceição\")."
));
children.push(bullet(
  "Escala de intensidade de documentação com cinco níveis discretos " +
  "(sem_registros até atividade_intensa)."
));
children.push(bullet(
  "Base agregada município × eixo em parquet, navegável via notebook e " +
  "dashboard Streamlit."
));
children.push(bullet(
  "Stubs documentados para Transferegov, SIOPS, SIOPE e Censo SUAS, " +
  "explicitando os caminhos de integração na fase 2."
));

children.push(H2("4.2 Tabela de resultados da amostra de demonstração"));
children.push(P(
  "Os números abaixo são da execução sobre contratos publicados em " +
  "15/09/2025 no PNCP (primeiras 50 páginas, 2.700 contratos brutos)."
));

const tabelaResultados = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [3120, 1560, 1560, 3120],
  rows: [
    new TableRow({ tableHeader: true, children: [
      headerCell("Eixo", 3120),
      headerCell("Classificações", 1560),
      headerCell("Municípios", 1560),
      headerCell("Comentário", 3120),
    ]}),
    new TableRow({ children: [
      dataCell("Segurança Alimentar", 3120),
      dataCell("37", 1560),
      dataCell("~15", 1560),
      dataCell("Domínio do PNAE/merenda", 3120),
    ]}),
    new TableRow({ children: [
      dataCell("Primeira Infância", 3120),
      dataCell("25", 1560),
      dataCell("~10", 1560),
      dataCell("Quase tudo em creche/pré-escola", 3120),
    ]}),
    new TableRow({ children: [
      dataCell("Busca Ativa Escolar", 3120),
      dataCell("8", 1560),
      dataCell("~5", 1560),
      dataCell("Sobretudo transporte escolar", 3120),
    ]}),
    new TableRow({ children: [
      dataCell("Saúde Mental", 3120),
      dataCell("2", 1560),
      dataCell("2", 1560),
      dataCell("CAPS em Mutuípe/BA + saúde mental São Miguel do Iguaçu/PR", 3120),
    ]}),
  ],
});
children.push(tabelaResultados);
children.push(P(" "));

children.push(H2("4.3 Lições da execução real"));
children.push(P(
  "A primeira rodada já produziu três aprendizados não-óbvios que vão " +
  "guiar o restante do projeto:"
));
children.push(numbered(
  "Word boundary é mandatório. A v0.1 da taxonomia tinha \"cei\" como " +
  "keyword de creche e gerou falsos positivos em \"Conceição\", " +
  "\"Ceirárias-ME\" e \"CEI\" usado como sigla de outros centros. A v0.2 " +
  "exige boundary em todas as keywords."
));
numbered(
  "Termos genéricos puxam ruído. \"Saúde mental\" aparece com frequência " +
  "como uma de várias secretarias atendidas por compras genéricas de " +
  "papelaria. Foram adicionados excludes de \"expediente\", \"papelaria\", " +
  "\"material de escritório\"."
);
children.push(numbered(
  "Termos genéricos puxam ruído. \"Saúde mental\" aparece com frequência " +
  "como uma de várias secretarias atendidas por compras genéricas de " +
  "papelaria. Foram adicionados excludes de \"expediente\", \"papelaria\", " +
  "\"material de escritório\"."
));
children.push(numbered(
  "A intersetorialidade é o caso normal, não a exceção. Quase metade dos " +
  "contratos classificados foi para mais de um eixo (merenda em creches " +
  "= primeira infância + segurança alimentar). Isso valida a decisão de " +
  "permitir classificação multi-eixo."
));

// 5. Roadmap
children.push(H1("5. Roadmap"));

children.push(H2("5.1 Fase 1 — Solidificação do MVP (próximos 2-3 meses)"));
children.push(bullet("Expansão da coleta PNCP para 12 meses contínuos."));
children.push(bullet(
  "Score de confiança por classificação (número de keywords casadas, " +
  "presença de termos reforçadores)."
));
children.push(bullet(
  "Validação assistida: rotulação manual de amostra estratificada (n=300) " +
  "para calcular precisão/recall por subeixo."
));
children.push(bullet("Inclusão do Transferegov."));
children.push(bullet(
  "Publicação da base v1.0 em formato aberto + documento metodológico."
));

children.push(H2("5.2 Fase 2 — Integração setorial (3-6 meses adicionais)"));
children.push(bullet(
  "Adaptadores para SIOPS, SIOPE e Censo SUAS, padronizando saída como " +
  "{codigo_ibge, ano, indicador, valor}."
));
children.push(bullet(
  "Cruzamento PNCP × sistema setorial: quando o sinal do PNCP é " +
  "confirmado ou contradito pela base administrativa correspondente?"
));
children.push(bullet(
  "Versão pública do dashboard hospedada (fora do escopo do sandbox)."
));

children.push(H2("5.3 Fase 3 — Fontes não estruturadas (6-12 meses)"));
children.push(bullet(
  "Pipeline de raspagem de diários oficiais municipais. Heterogeneidade " +
  "é o grande inimigo aqui — 5.570 padrões diferentes."
));
children.push(bullet(
  "Classificação por LLM com prompts auditáveis e validação humana " +
  "estratificada."
));
children.push(bullet(
  "Notícias institucionais como fonte complementar para anúncios e atos " +
  "não formalizados."
));

// 6. Riscos
children.push(H1("6. Riscos e mitigações"));

const tabelaRiscos = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [3120, 6240],
  rows: [
    new TableRow({ tableHeader: true, children: [
      headerCell("Risco", 3120),
      headerCell("Mitigação", 6240),
    ]}),
    new TableRow({ children: [
      dataCell("Leitura ingênua dos dados como medida de implementação", 3120),
      dataCell(
        "Disclaimer metodológico em todo output. Linguagem deliberada da " +
        "ferramenta usa \"intensidade de documentação\" e nunca \"intensidade " +
        "de política\". Escala discreta de cinco níveis em vez de score " +
        "contínuo evita falsa precisão.", 6240
      ),
    ]}),
    new TableRow({ children: [
      dataCell("Viés sistemático contra municípios pequenos", 3120),
      dataCell(
        "Combinar PNCP (rico para municípios médios/grandes) com Transferegov " +
        "e diários oficiais (que dependem menos de sofisticação burocrática).", 6240
      ),
    ]}),
    new TableRow({ children: [
      dataCell("Taxonomia engessada ou capturada por preferências de quem a desenha", 3120),
      dataCell(
        "Versionamento em YAML, changelog em cabeçalho, processo de revisão " +
        "pública periódica com especialistas setoriais.", 6240
      ),
    ]}),
    new TableRow({ children: [
      dataCell("Falsos positivos minam credibilidade", 3120),
      dataCell(
        "Validação humana estratificada com publicação das métricas de " +
        "precisão/recall por subeixo. Score de confiança permite ao usuário " +
        "filtrar por nível de certeza.", 6240
      ),
    ]}),
    new TableRow({ children: [
      dataCell("API do PNCP pode mudar ou ficar instável", 3120),
      dataCell(
        "Cache em disco de todas as respostas — análises são reprodutíveis " +
        "mesmo se a API mudar. Arquitetura de cliente isolado por fonte " +
        "facilita adaptação.", 6240
      ),
    ]}),
  ],
});
children.push(tabelaRiscos);
children.push(P(" "));

// 7. Anexo técnico
children.push(H1("7. Anexo técnico — estrutura do código"));
children.push(P(
  "O protótipo executável está em /home/claude/radar_clear/, organizado por " +
  "responsabilidade. As principais entradas:"
));
children.push(bullet("`radar_policy/taxonomy/taxonomy_v0.yaml` — taxonomia versionada."));
children.push(bullet("`radar_policy/sources/pncp.py` — cliente PNCP."));
children.push(bullet("`radar_policy/classify/classifier.py` — classificação + escala."));
children.push(bullet("`radar_policy/pipeline.py` — orquestração end-to-end."));
children.push(bullet("`dashboard/app.py` — dashboard Streamlit."));
children.push(bullet("`notebooks/01_exploracao.ipynb` — análise exploratória."));
children.push(bullet("`README.md` — instruções de uso e status atual."));

children.push(P(" "));
children.push(P(
  "Este documento é uma versão de trabalho. Críticas, correções de " +
  "vocabulário, e contribuições à taxonomia são especialmente bem-vindas " +
  "antes da próxima rodada de execução.",
  { run: { italics: true, color: "555555" } }
));

// ---------------------------------------------------------------------------
// Documento final
// ---------------------------------------------------------------------------
const doc = new Document({
  creator: "Radar de Políticas Municipais",
  title: "Radar de Políticas Municipais — Proposta CLEAR",
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "1A3A5C" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E5C8C" },
        paragraph: { spacing: { before: 240, after: 140 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({
            text: "Radar de Políticas Municipais · Proposta CLEAR",
            size: 18, color: "888888",
          })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Página ", size: 18, color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "888888" }),
          ],
        })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  const outPath = "/home/claude/radar_clear/docs/proposta_radar_clear.docx";
  fs.writeFileSync(outPath, buf);
  console.log("Documento gerado:", outPath);
});
