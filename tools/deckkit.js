// Shared helpers for both project decks (pptxgenjs, 13.33 x 7.5 in).
// Run deck scripts with NODE_PATH pointing at a folder that has pptxgenjs, react, react-dom,
// react-icons and sharp installed.
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

const W = 13.333, H = 7.5, M = 0.6;

async function icon(IconComponent, color = "FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(IconComponent, { color: "#" + color, size }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

function makeTheme(pal) {
  const T = { ...pal, W, H, M, fHead: "Cambria", fBody: "Calibri" };

  T.title = (slide, text, opts = {}) => slide.addText(text, {
    x: M, y: 0.4, w: W - 2 * M, h: 0.9, fontFace: T.fHead, fontSize: 34, bold: true,
    color: opts.color || T.ink, margin: 0, isTextBox: true, valign: "middle",
  });

  T.kicker = (slide, text, color) => slide.addText(text.toUpperCase(), {
    x: M, y: 0.18, w: 8, h: 0.3, fontFace: T.fBody, fontSize: 12, bold: true, charSpacing: 3,
    color: color || T.primary, margin: 0, isTextBox: true,
  });

  T.body = (slide, text, x, y, w, h, o = {}) => slide.addText(text, {
    x, y, w, h, fontFace: T.fBody, fontSize: 16, color: T.ink, margin: 0, isTextBox: true,
    valign: "top", paraSpaceAfter: 6, ...o,
  });

  T.bullets = (slide, items, x, y, w, h, o = {}) => slide.addText(
    items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
    { x, y, w, h, fontFace: T.fBody, fontSize: 16, color: T.ink, margin: 0, isTextBox: true,
      valign: "top", paraSpaceAfter: 8, ...o });

  // Icon inside a filled circle: the visual motif used across both decks.
  T.badge = (slide, data, x, y, d = 0.7, fill) => {
    slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: fill || T.primary }, line: { type: "none" } });
    slide.addImage({ data, x: x + d * 0.22, y: y + d * 0.22, w: d * 0.56, h: d * 0.56 });
  };

  T.card = (slide, x, y, w, h, fill) => slide.addShape("roundRect", {
    x, y, w, h, rectRadius: 0.12, fill: { color: fill || T.tint }, line: { type: "none" },
  });

  T.stat = (slide, value, label, x, y, w, color) => {
    slide.addText(value, { x, y, w, h: 0.95, fontFace: T.fHead, fontSize: 44, bold: true,
      color: color || T.primary, margin: 0, isTextBox: true, valign: "bottom" });
    slide.addText(label, { x, y: y + 1.0, w, h: 1.1, fontFace: T.fBody, fontSize: 14,
      color: T.muted, margin: 0, isTextBox: true, valign: "top" });
  };

  T.footer = (slide, text, n) => slide.addText(`${text}   |   ${n}`, {
    x: M, y: H - 0.42, w: W - 2 * M, h: 0.3, fontFace: T.fBody, fontSize: 10, color: T.muted,
    align: "right", margin: 0, isTextBox: true,
  });
  return T;
}

module.exports = { icon, makeTheme, W, H, M };
