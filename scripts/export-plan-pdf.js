#!/usr/bin/env bun
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { marked } from 'marked';

/**
 * Uso:
 *   bun export-plan-pdf.js <plano.md> [saida.pdf] [--skip A,B,...]
 *
 * --skip A,B    Remove as seções listadas (ex.: 4 ou 4,8,9). Pular "8" também
 *               remove "8.1". Padrão: não pula nada (exporta 100%).
 *               Use --skip none para explicitar que nada deve ser pulado.
 */

const USAGE =
  'Uso: bun export-plan-pdf.js <plano.md> [saida.pdf] [--skip A,B|none]';

function parseSectionId(raw) {
  const value = String(raw).trim();
  if (!/^\d+(?:\.\d+)*$/.test(value)) {
    console.error(`Erro: id de seção inválido "${raw}". Use números como 4 ou 8.1.`);
    process.exit(1);
  }
  return value;
}

function parseSkipList(raw) {
  if (raw === undefined) return null;
  const trimmed = String(raw).trim();
  if (trimmed === '' || trimmed === 'none') return [];
  return trimmed.split(',').map(parseSectionId);
}

function parseArgs(argv) {
  const positional = [];
  let skipSections = null; // null = aplicar default depois

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--until' || arg.startsWith('--until=')) {
      console.error('Erro: --until foi removido. O padrão agora exporta 100%; use --skip A,B para pular seções.');
      console.error(USAGE);
      process.exit(1);
    } else if (arg === '--skip') {
      skipSections = parseSkipList(argv[++i]);
    } else if (arg.startsWith('--skip=')) {
      skipSections = parseSkipList(arg.slice('--skip='.length));
    } else if (arg.startsWith('-')) {
      console.error(`Erro: flag desconhecida "${arg}".`);
      console.error(USAGE);
      process.exit(1);
    } else {
      positional.push(arg);
    }
  }

  // Default: exporta 100% — só pula se pedido via --skip explícito.
  if (skipSections === null) {
    skipSections = [];
  }

  return { positional, skipSections };
}

/**
 * True se `sectionId` deve ser pulado: match exato ou filho de um id na lista
 * (ex.: skip "8" também remove "8.1").
 */
function shouldSkipSection(sectionId, skipSections) {
  return skipSections.some(
    (skipId) => sectionId === skipId || sectionId.startsWith(`${skipId}.`)
  );
}

/**
 * Remove blocos inteiros de seções numeradas (`## N.` / `## N.M.`) listadas em skipSections.
 * Headings ### internos (5.1 etc. sob ## 5) não são tratados como seções de topo —
 * só headings #/## com número no padrão do template QA.
 */
function skipMarkdownSections(markdown, skipSections) {
  if (!skipSections.length) return markdown;

  const headingRegex = /^#{1,2}\s+(\d+(?:\.\d+)*)\.\s[^\n]*/gm;
  const matches = [...markdown.matchAll(headingRegex)];
  if (!matches.length) return markdown;

  let result = markdown.slice(0, matches[0].index);
  const removed = [];

  for (let i = 0; i < matches.length; i++) {
    const match = matches[i];
    const sectionId = match[1];
    const start = match.index;
    const end = i + 1 < matches.length ? matches[i + 1].index : markdown.length;
    if (shouldSkipSection(sectionId, skipSections)) {
      removed.push(sectionId);
      continue;
    }
    result += markdown.slice(start, end);
  }

  if (removed.length) {
    console.log(`Pulando seções: ${removed.map((id) => `## ${id}.`).join(', ')}.`);
  } else {
    console.warn(
      `Aviso: nenhuma seção correspondente a --skip ${skipSections.join(',')} foi encontrada.`
    );
  }

  return result.replace(/\n{3,}/g, '\n\n').replace(/^\s+|\s+$/g, '') + '\n';
}

const { positional, skipSections } = parseArgs(process.argv.slice(2));
const inputFile = positional[0];
if (!inputFile) {
  console.error(USAGE);
  process.exit(1);
}

const inputAbsPath = path.resolve(inputFile);
if (!fs.existsSync(inputAbsPath)) {
  console.error(`Erro: Arquivo "${inputAbsPath}" não encontrado.`);
  process.exit(1);
}

const inputDir = path.dirname(inputAbsPath);
const baseName = path.basename(inputAbsPath, path.extname(inputAbsPath));

// Diretório de exportação dedicado: .ai_qa_acervo/exports/
const scriptDir = path.dirname(new URL(import.meta.url).pathname);
const acervoRoot = path.resolve(scriptDir, '..');
const defaultOutputDir = path.join(acervoRoot, 'exports');

if (!fs.existsSync(defaultOutputDir)) {
  fs.mkdirSync(defaultOutputDir, { recursive: true });
}

const outputFile = positional[1]
  ? path.resolve(positional[1])
  : path.join(defaultOutputDir, `${baseName}.pdf`);

const outputDir = path.dirname(outputFile);
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

let markdownContent = fs.readFileSync(inputAbsPath, 'utf8');
markdownContent = skipMarkdownSections(markdownContent, skipSections);

// Converter caminhos locais de imagens para data:image/png;base64 para garantir inclusão 100% autocontida
markdownContent = markdownContent.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, imagePath) => {
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://') || imagePath.startsWith('data:')) {
    return match;
  }
  const cleanPath = imagePath.split('?')[0].split('#')[0];
  const absImagePath = path.isAbsolute(cleanPath) ? cleanPath : path.resolve(inputDir, cleanPath);
  if (fs.existsSync(absImagePath)) {
    const ext = path.extname(absImagePath).toLowerCase().replace('.', '');
    const mime = ext === 'svg' ? 'image/svg+xml' : ext === 'jpg' ? 'image/jpeg' : `image/${ext}`;
    const base64Data = fs.readFileSync(absImagePath).toString('base64');
    return `![${alt}](data:${mime};base64,${base64Data})`;
  }
  return match;
});

// Forçar <details> a renderizar aberto no PDF para exibir os prints
markdownContent = markdownContent.replace(/<details>/g, '<details open>');

const htmlBody = marked.parse(markdownContent);

const fullHtml = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>${baseName}</title>
  <style>
    @page {
      margin: 14mm 16mm;
      size: A4 portrait;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 11pt;
      line-height: 1.5;
      color: #1f2937;
      background: #ffffff;
      margin: 0;
      padding: 0;
    }
    h1 {
      font-size: 18pt;
      color: #0f172a;
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 6px;
      margin-top: 0;
    }
    h2 {
      font-size: 14pt;
      color: #1e293b;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 4px;
      margin-top: 18px;
    }
    h3 {
      font-size: 12pt;
      color: #334155;
      margin-top: 14px;
    }
    h4 {
      font-size: 11pt;
      color: #475569;
      margin-top: 10px;
    }
    blockquote {
      margin: 10px 0;
      padding: 8px 14px;
      background-color: #f8fafc;
      border-left: 4px solid #3b82f6;
      color: #334155;
      border-radius: 2px 4px 4px 2px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 14px 0;
      font-size: 9.5pt;
    }
    th, td {
      border: 1px solid #cbd5e1;
      padding: 6px 10px;
      text-align: left;
    }
    th {
      background-color: #f1f5f9;
      color: #0f172a;
      font-weight: 600;
    }
    code {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 9pt;
      background-color: #f1f5f9;
      padding: 2px 4px;
      border-radius: 4px;
      color: #0f172a;
    }
    pre {
      background-color: #0f172a;
      color: #f8fafc;
      padding: 10px 14px;
      border-radius: 6px;
      overflow-x: auto;
      font-size: 8.5pt;
    }
    pre code {
      background-color: transparent;
      color: inherit;
      padding: 0;
    }
    ul {
      list-style-type: none;
      padding-left: 18px;
    }
    li {
      margin-bottom: 4px;
      position: relative;
    }
    input[type="checkbox"] {
      margin-right: 6px;
      vertical-align: middle;
      transform: scale(1.1);
    }
    img {
      max-width: 100%;
      height: auto;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      margin: 10px 0;
      display: block;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      page-break-inside: avoid;
    }
    details {
      margin: 8px 0;
      padding: 8px 12px;
      background-color: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      page-break-inside: avoid;
    }
    summary {
      font-weight: 600;
      cursor: pointer;
      color: #2563eb;
    }
    hr {
      border: 0;
      height: 1px;
      background-color: #e2e8f0;
      margin: 20px 0;
    }
  </style>
</head>
<body>
  ${htmlBody}
</body>
</html>`;

const tempHtml = path.join(outputDir, `.${baseName}.temp.html`);
fs.writeFileSync(tempHtml, fullHtml, 'utf8');

try {
  console.log(`Gerando PDF com Chrome Headless...`);
  execSync(`google-chrome --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="${outputFile}" "${tempHtml}"`, {
    stdio: 'inherit'
  });
  console.log(`\n✅ PDF gerado com sucesso em:\n${outputFile}`);
} finally {
  if (fs.existsSync(tempHtml)) {
    fs.unlinkSync(tempHtml);
  }
}
