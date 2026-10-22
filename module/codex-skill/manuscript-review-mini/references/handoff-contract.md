# Handoff Contract

Keep reviewed_manuscript.md and reviewed_supplementary.md as Stage3 canonical text,
references.bib, updated figures/tables/source files, blueprint, source-verification,
asset manifest, target journal profile, unresolved minor issues and publication notes.
PUBLICATION_HANDOFF is a new versioned, self-contained directory with relative paths,
readiness.json and hashes. Include input/source layers needed by asset provenance; avoid
absolute/external dependencies. Main version and current assets must match final audits.
In existing publication notes, carry the final cited counts and relevant target/coverage
decisions from the citation audit, so Stage 4 preserves the reviewed citation set.
Do not include old draft as canonical. Copy complete factual sources rather than assume
Stage4 will guess dependencies. Preserve review original snapshot. No LaTeX, PDF manuscript,
publisher templates or submission package creation; figure PDF assets already present
are allowed. Stop after delivery unless user explicitly switches to Stage4.

Mini exports review_coverage.json describing actual reviewer counts, rounds and language-check status; it does not claim original full-review coverage.

同时按 [中文终稿审阅副本](chinese-author-copy.md) 向作者交付完整中文稿；在现有出版说明注明对应正式稿版本及反馈处理状态。中文稿不替换canonical或自动加入投稿包，现有package格式不变。
