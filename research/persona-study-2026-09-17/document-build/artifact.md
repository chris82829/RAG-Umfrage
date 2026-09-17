# Persona dossiers derived from Experiment Analysis

Reference: /Users/christophscharnagl/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-experiment-analysis/assets/reference.docx
SHA256 d823cd0115186b34c01c6e4b4da3be28b64ee73cac849dbd62d6f4bb6385b0fb
The retained reference has 8 rendered pages and one section. Every page was inspected. Render evidence is reference-render/page-1.png through page-8.png. Inventory is template-parts.json; styles evidence is template-style-evidence.json.

## Page system
One portrait Letter section, 12240 by 15840 twips. Margins 1440 twips on all sides; header/footer 720 twips. Usable width 9360 twips. Single column; no special first/odd/even page treatment. Page numbering starts at 1. Keep sectPr byte-equivalent, including rId8/rId9 references. Footer is a locked SDT containing two borderless cells, report name left and PAGE field right; patch only the report-name text node. Header is empty and preserved. Set updateFields in settings to true without changing other settings; PAGE deferred refresh in Word is explicit (renderer resolves pages for QA).

## Source patterns
Title: document.xml body child 6, Title style, Georgia 40pt bold centered. Compact dossier title uses the same style/Georgia but a 24pt direct size and black to obey title requirement; cover white space and separator drawing are removed as requested by task scope (no blank cover).
Heading: child 30, Heading1, Georgia 18pt bold, source green 1A703A; keep-before 18pt/after 4pt and keepNext/keepLines. Apply black text per document style requirement; typography and pattern otherwise unchanged.
Body: child 31, Georgia 12pt, justified, 12pt before/after. Clones may use 6pt before/after to fit compact dossiers, no font shrink. Plain lead-ins may be bold. Subheads: same body pattern with bold text and keepNext.
List: child 53, Georgia 12pt, native numId1 bullet, hanging 360 twips and left 720, single line, 12pt before. Clones can remove excess paragraph spacing to 4pt for consecutive lists.
Metadata table: child 28, two columns 2405/6945 twips, 9350 total. Georgia 10pt, label bold, top/bottom/min row 432twips, center vertical. Table padding from original styles. Clone label/value row as needed; maintain source borders 999999 and table style Table1. Set cantSplit to true for individual rows; no fixed exact height. This compact table is for comparable field values only, longer prose stays outside.
Tables with header: child39 first row light gray F3F3F3, green bold 10pt, body rows Georgia10, used if helpful. No unsupported experiment results tables retained.

## Content and slots
Only word/document.xml body contents are editable. Reconstruct the body from cloned source patterns, retaining the original final sectPr. Remove all unused experiment result/control placeholders and decorative cover spacers. Title is persona name, subtitle indicates A/B/C simulation and synthetic persona. Main flow: identity/background; skills and limits; job goals and fixed/soft criteria; literal starting user profile and custom advisor settings; three exact wording foundations and disclosure sequence, actual adaptive messages logged separately; constant target and relevance assessment rule. All factual content comes from the new synthetic persona JSON. No metrics invented or filled before measurement.
Footer word/footer1.xml SDT tag goog_rdk_0 remains intact; only Report Name changes to DIANA plus persona ID. Preserve PAGE structure and all controls, relationships, styles, numbering, media, embedded fonts, theme, fontTable and empty header. Source cover drawings removed only from editable body; image and relationship parts retained.

## Package inventory and fidelity gates
All parts in template-parts.json except word/document.xml, word/footer1.xml and word/settings.xml are preserve-only, byte-identical. No new styles/theme/relationships/media. Original reference remains byte-identical. Body section count remains 1 and page geometry unchanged. All original editable text slots removed or replaced, no English placeholders. Table and text patterns derive from source with density adjustments documented above. Final DOCX content must contain every literal initial profile field and each of 3 planned messages; explain fictional status and constant target judging.

Render each final through render_docx.py using bundled runtime and packaged LibreOffice only. Inspect every page at full resolution. Compare reference/final with render_and_diff for first dossier as reusable pattern scope check; run section/style/field/control audits on all final docs and compare preserve-only byte hashes. Expected all dossiers about 4–5 pages; final page count varies with content, no unnecessary blank page.

## Final scope change
The user reduced scope to one persona (Mara Seidel P01) across A/B/C, so produce one DOCX only. Use selected-personas.json three execution cases for the same source person, B Top-Berufsberater and C custom Mein Einstiegscoach. All four measured states in each variant share the ideal pool of all returned jobs across all twelve snapshots. Planned wording is illustrative, actual replies are adaptive and saved separately. Final document target is four to five substantive pages. The operation-start marker originally declared twelve outputs; do not rerun it. Record the user-requested one-output scope in document-manifest.json.

Latest user steering expands final scope to two dossiers: Mara P01 and Leonie P03, each across A/B/C, grouping the six execution cases by source_id. B is career for Mara and expert for Leonie. The initial operation marker is not repeated. Final output count two is recorded in document-manifest.json.

Final confirmed scope and source: two dossiers P01 Mara Seidel and P06 Nora Peters, each across A/B/C, input ../selected-personas.json (six cases). B Top-Berufsberater for both; C contains their custom settings. Both final documents have four pages. Every page visually reviewed after the second render and no defects remain. Only two DOCX are in the final documents directory; superseded generated P03 was removed. All preserve-only package parts are byte-identical to source. Body heading text is black as mandated by DOCX authoring skill, source green footer text is retained. No measurements or actual transcript content are invented.
