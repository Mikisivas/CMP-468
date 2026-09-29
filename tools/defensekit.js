// Builds a defense-preparation .docx: grouped Q&A, a demo runbook and key numbers.
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, LevelFormat } = require("docx");

const FONT = "Calibri";

function buildDefense({ title, qa, runbook, numbers, out, accent = "0B5D3B" }) {
  const children = [
    new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun(title)] }),
    new Paragraph({ spacing: { after: 240 }, children: [new TextRun({ text: "Likely questions from the panel, with short answers you can say in your own words. Practise out loud.", italics: true })] }),
  ];
  let q = 0;
  for (const [section, items] of qa) {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(section)] }));
    for (const [question, answer] of items) {
      q++;
      children.push(new Paragraph({ spacing: { before: 160, after: 60 }, keepNext: true,
        children: [new TextRun({ text: `Q${q}. ${question}`, bold: true, color: accent })] }));
      children.push(new Paragraph({ spacing: { after: 120, line: 300 }, children: [new TextRun(answer)] }));
    }
  }
  children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun("Live Demo Runbook")] }));
  runbook.forEach((t) => children.push(new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 100 }, children: [new TextRun(t)] })));
  children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Numbers to Remember")] }));
  numbers.forEach((t) => children.push(new Paragraph({ numbering: { reference: "dots", level: 0 }, spacing: { after: 80 }, children: [new TextRun(t)] })));

  const doc = new Document({
    styles: {
      default: { document: { run: { font: FONT, size: 22 } } },
      paragraphStyles: [
        { id: "Title", name: "Title", basedOn: "Normal", run: { size: 40, bold: true, color: "1C2733", font: FONT }, paragraph: { spacing: { after: 120 } } },
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 28, bold: true, color: "1C2733", font: FONT }, paragraph: { spacing: { before: 300, after: 80 }, outlineLevel: 0 } },
      ],
    },
    numbering: { config: [
      { reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "dots", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ] },
    sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1200, bottom: 1200, left: 1300, right: 1300 } } }, children }],
  });
  return Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log(`wrote ${out} with ${q} questions`); });
}

module.exports = { buildDefense };
