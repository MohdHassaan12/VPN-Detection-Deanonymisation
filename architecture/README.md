# Architecture Folder

This directory contains system architecture assets for the VPN Detection & Deanonymisation project.

Contents:
- architecture-diagram.svg: Primary, hand-tuned SVG for professional docs & presentations.
- architecture-diagram.mmd: Mermaid source to regenerate diagrams.
- README.md: This file.

Regenerate SVG from Mermaid:
1. Install CLI: npm install -g @mermaid-js/mermaid-cli
2. Run: mmdc -i architecture-diagram.mmd -o architecture-diagram.svg -t neutral -b white
3. Optional PNG: mmdc -i architecture-diagram.mmd -o architecture-diagram.png -s 2

Editing Guidelines:
- Prefer updating the Mermaid source first; then export.
- For advanced layout control (precise spacing, side panels), edit the SVG directly.
- Keep layer naming consistent with docs/Architecture.md.

Versioning:
- Commit both .mmd and generated .svg for traceability.
- If substantial visual changes: add a short note in commit message starting with "arch:".

Embedding in Docs:
Use relative path: ![System Architecture](../architecture/architecture-diagram.svg)

Attribution & Licensing:
All diagram content is internally authored. No third-party copyrighted graphics embedded.
