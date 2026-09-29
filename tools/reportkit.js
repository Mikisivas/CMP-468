// Small helper layer over docx-js used by both project reports.
// Run report scripts with NODE_PATH pointing at a folder that has `docx` installed.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, PageBreak, TableOfContents, Footer, Header,
  PageNumber, LevelFormat, TabStopType,
} = require("docx");

const FONT = "Times New Roman";
const CONTENT_W = 9026; // A4 width 11906 minus 1440 margins each side

function runs(text, base = {}) {
  // Supports **bold** and _italic_ inline markers.
  const out = [];
  const re = /(\*\*[^*]+\*\*|_[^_]+_)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}

const P = (text, opts = {}) => new Paragraph({
  children: runs(text), alignment: opts.align ?? AlignmentType.JUSTIFIED,
  spacing: { after: 160, line: 360 }, ...opts.para,
});
const H1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)], pageBreakBefore: true });
const H2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
const H3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(text)] });
const bullets = (items, ref = "bullets") => items.map((t) => new Paragraph({
  numbering: { reference: ref, level: 0 }, children: runs(t), spacing: { after: 80, line: 320 },
}));
const numbered = (items, ref) => bullets(items, ref);
const Caption = (text) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 60, after: 240 },
  children: [new TextRun({ text, italics: true, size: 20 })],
});
const Break = () => new Paragraph({ children: [new PageBreak()] });

function Figure(path, widthPx, heightPx, caption) {
  const maxW = 600; // points-ish; docx-js uses pixels at 96 dpi
  const scale = Math.min(1, maxW / widthPx);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 120 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(path),
        transformation: { width: Math.round(widthPx * scale), height: Math.round(heightPx * scale) } })],
    }),
    Caption(caption),
  ];
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "8A99A8" };
const borders = { top: border, bottom: border, left: border, right: border };

function Tbl(header, rows, widths, caption) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (text, isHead, w) => new TableCell({
    borders, width: { size: w, type: WidthType.DXA },
    shading: isHead ? { fill: "0B5D3B", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ spacing: { after: 0, line: 260 },
      children: runs(String(text), { size: 20, color: isHead ? "FFFFFF" : undefined, bold: isHead || undefined }) })],
  });
  const out = [];
  if (caption) out.push(new Paragraph({ spacing: { before: 200, after: 80 }, keepNext: true,
    children: [new TextRun({ text: caption, bold: true, size: 20 })] }));
  out.push(new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, true, widths[i])) }),
      ...rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, false, widths[i])) }))],
  }));
  out.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
  return out;
}

function Code(lines) {
  return lines.map((l) => new Paragraph({
    spacing: { after: 0, line: 240 }, shading: { fill: "F1F4F7", type: ShadingType.CLEAR, color: "auto" },
    children: [new TextRun({ text: l || " ", font: "Consolas", size: 18 })],
  })).concat([new Paragraph({ spacing: { after: 120 }, children: [] })]);
}

function coverPage({ title, subtitle, lines }) {
  const c = (text, size, opts = {}) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text, size, font: FONT, ...opts })] });
  return [
    c("[UNIVERSITY NAME]", 32, { bold: true }),
    c("FACULTY OF [FACULTY NAME]", 24, { bold: true }),
    c("DEPARTMENT OF COMPUTER SCIENCE", 24, { bold: true }),
    new Paragraph({ spacing: { after: 1200 }, children: [] }),
    c(title, 36, { bold: true, color: "0B5D3B" }),
    c(subtitle, 26, { italics: true }),
    new Paragraph({ spacing: { after: 1000 }, children: [] }),
    ...lines.map((l) => c(l, 24)),
  ];
}

function buildDoc({ cover, abstract, sections, out, headerText }) {
  const doc = new Document({
    creator: "CMP 468 student",
    features: { updateFields: true }, // Word fills in the table of contents on open
    styles: {
      default: { document: { run: { font: FONT, size: 24 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 32, bold: true, font: FONT, color: "0B5D3B" },
          paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 26, bold: true, font: FONT, color: "1C2733" },
          paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1, keepNext: true } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 24, bold: true, italics: true, font: FONT },
          paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 2, keepNext: true } },
      ],
    },
    numbering: {
      config: [
        { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        ...["n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8"].map((r) => ({ reference: r, levels: [{ level: 0,
          format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] })),
      ],
    },
    sections: [
      { properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
        children: cover },
      {
        properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
        headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: headerText, size: 18, color: "5D6B7A" })] })] }) },
        footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
          children: [new TextRun({ children: [PageNumber.CURRENT], size: 20 })] })] }) },
        children: [
          new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Abstract")] }),
          ...abstract.flat(Infinity),
          new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun("Table of Contents")] }),
          new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }),
          ...sections.flat(Infinity),
        ],
      },
    ],
  });
  return Packer.toBuffer(doc).then((buf) => fs.writeFileSync(out, buf));
}

module.exports = { P, H1, H2, H3, bullets, numbered, Figure, Tbl, Code, Caption, Break, coverPage, buildDoc, CONTENT_W };
