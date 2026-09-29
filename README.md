# CMP-468: Computer Security

Two projects for CMP 468 (Computer Security, 2 units). Each one has working
code, tests, a demo, a report, a slide deck and defense preparation. Both are
designed around Nigerian conditions.

| | Project 1: UniGuard | Project 2: AgroPeace |
|---|---|---|
| Question | Automated monitoring, backup and recovery system for university digital infrastructure | GIS-based early warning and real-time framework for farmer/herder conflict resolution |
| Folder | [project1-uniguard](project1-uniguard) | [project2-agropeace](project2-agropeace) |
| Report | `docs/UniGuard_Report.docx` | `docs/AgroPeace_Report.docx` |
| Slides | `docs/UniGuard_Presentation.pptx` (16 slides, speaker notes) | `docs/AgroPeace_Presentation.pptx` (17 slides, speaker notes) |
| Defense | `docs/UniGuard_Defense_QA.docx` (33 questions + demo runbook) | `docs/AgroPeace_Defense_QA.docx` (30 questions + demo runbook) |
| Tests | 23 | 30 |
| Quick demo | `python demo/run_demo.py` | `python demo/run_demo.py` |

Before submitting, replace the placeholders on each report cover and title
slide: `[UNIVERSITY NAME]`, `[FACULTY NAME]`, `[YOUR FULL NAME]`,
`[MATRIC NUMBER]`, `[LECTURER'S NAME]`, `[MONTH, YEAR]`. When Word opens a
report it asks to update fields; say yes so the table of contents fills in.

## Running

Each project folder has its own README. In short:

```
cd project1-uniguard && pip install -r requirements.txt && python -m pytest -q && python demo/run_demo.py
cd project2-agropeace && pip install -r requirements.txt && python -m pytest -q && python demo/run_demo.py
```

## Rebuilding the documents

The Word and PowerPoint files are generated from scripts, so a change to the
text is a change to `docs/build_*.js`. The scripts need Node.js and these npm
packages in one folder: `docx pptxgenjs react react-dom react-icons sharp`.

```
npm install --prefix ~/cmp468-node docx pptxgenjs react react-dom react-icons sharp
export NODE_PATH=~/cmp468-node/node_modules
node project1-uniguard/docs/build_report.js
node project1-uniguard/docs/build_slides.js
node project1-uniguard/docs/build_defense.js
node project2-agropeace/docs/build_report.js
node project2-agropeace/docs/build_slides.js
node project2-agropeace/docs/build_defense.js
```

`tools/` holds the shared helpers: `reportkit.js`, `deckkit.js`,
`defensekit.js`, and two checks used when no office suite is available:
`fitcheck.py` (text overflow in slides) and `preview_pptx.py` (HTML preview).
