mini：先判断是否需要修改。语言合格时按 mini-operations.md 记录 NOT_NEEDED；如需修改，以下保事实规则完整适用。

> Humanizer is optional, never the default. Use `routes.optional_humanizer` only for explicit
> humanize/去 AI 味, supplied author prose voice, or concrete residue after nature-polishing.
> Read project-coordination.md. Seal equations/numbers/citations and exclude tables/code/facts;
> use prepare_prose/restore_prose and check_prose plus actual semantic comparison. Revert drift.
> Accuracy > evidence > journal > nature-polishing > Humanizer. Never optimize detector scores.

# Polishing Policy

Only after scientific/structural/major-display revision, load nature-polishing
manifest, always_load and matching paper-type/section/language/journal prose fragments.
Its LaTeX-layout route is forbidden here. Use clarity, concision, flow, terminology and
redundancy guidance. Do not change numbers, n, metrics, methods, parameters, conditions,
causality or evidence strength, and never invent a citation. Fact lock before, diff-aware
comparison after. Roll back offending passages on semantic drift and redo those passages.
Strong words and numerical token checks are alerts, not substitutes for reading meaning.
