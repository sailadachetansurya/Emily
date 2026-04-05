---
name: docs-md-workflow
description: 'Read, create, and summarize Markdown docs (.md). Use when asked to draft new documentation, summarize existing docs, extract action items, or improve structure and clarity across Docs files.'
argument-hint: 'Task + path + audience + desired output format (summary/checklist/full doc)'
---

# Docs Markdown Workflow

## When To Use
- User asks to read and explain one or more .md files
- User asks to create new documentation from notes or requirements
- User asks to summarize large docs into concise bullets or action items
- User asks to standardize Markdown structure (headings, sections, links)

## Inputs To Confirm
- Target file(s) or folder(s)
- Goal: read, create, summarize, or revise
- Audience: internal team, end users, or mixed
- Output style: short summary, structured outline, full draft, or changelog
- Constraints: tone, length, required sections, and date/version notes

## Defaults
- Scope: available in both workspace and personal skill locations.
- Summarize mode: default to a 5-10 bullet executive summary unless user asks otherwise.
- Create mode: keep structure flexible and adapt sections to user request.

## Procedure
1. Locate and scope docs
- Find requested Markdown files first.
- If no paths are given, ask for paths or scan the workspace docs locations.
- Confirm whether to edit existing docs or create new files.

2. Read and map content
- Identify title, purpose, key sections, and missing information.
- Capture facts, decisions, TODOs, risks, and open questions.
- Preserve domain terms and user intent; do not invent facts.

3. Choose output path by goal
- Read/explain: produce section-by-section explanation with key takeaways.
- Summarize: produce concise bullets (what, why, next actions).
- Create: draft a complete Markdown document with clear heading hierarchy.
- Revise: improve structure, remove redundancy, and keep meaning unchanged.

4. Draft in Markdown
- Use consistent heading order: H1 -> H2 -> H3.
- Keep paragraphs short and scannable.
- Use lists for steps and decisions.
- Add a small metadata block when helpful (date, owner, status).

5. Quality checks before finalizing
- Accuracy: every statement is sourced from provided content or explicit user input.
- Completeness: required sections are present.
- Readability: concise wording and no duplicated sections.
- Formatting: valid Markdown, working relative links, and clean list formatting.
- Actionability: summaries include clear next steps when relevant.

6. Final response format
- Start with the outcome (created/updated/summarized and where).
- List major changes or key points.
- Include unresolved questions and assumptions.
- Suggest practical next steps only when useful.

## Decision Points
- If information is missing: ask focused clarifying questions before drafting.
- If docs conflict: preserve source wording and flag contradictions.
- If scope is broad: summarize first, then propose phased edits.
- If user asks for brevity: provide 5-10 bullets max plus optional expanded section.

## Completion Criteria
- Output matches requested goal and audience.
- Markdown is structured and easy to scan.
- No unsupported claims were introduced.
- Any assumptions or unresolved gaps are clearly called out.

## Reference
- Use [Markdown quality checklist](./references/markdown-quality-checklist.md) for final review.
