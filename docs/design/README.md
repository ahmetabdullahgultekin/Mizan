# Mizan Feature Design Docs

This directory contains feature design documents for the Mizan Core Engine.

## Process

Every non-trivial feature starts here — **design doc first, code second**.
The process is enforced by the template below:

| Step | Artefact | Location |
|------|----------|----------|
| 1. Design doc | `docs/design/T<N>-<slug>.md` | this directory |
| 2. ADRs (one per significant decision) | `docs/adr/NNNN-<slug>.md` | `../adr/` |
| 3. Diagrams | `docs/diagrams/*.mmd` | `../diagrams/` |
| 4. Implementation | feature branch | source tree |

## Template

Copy `/opt/projects/docs/design/_TEMPLATE_feature-design.md` for a new feature.
The template embeds the full process charter at the top — read it before coding.

## Existing Designs

| Doc | Feature | Status |
|-----|---------|--------|
| [T2-concept-cross-reference-graph.md](T2-concept-cross-reference-graph.md) | Concept Cross-Reference Graph | Draft |
