# Fact Lock

Before polish freeze a version, source data/facts hashes, core results/n/parameters/
conditions/statistics and display factual meanings, citations and claim boundaries.
Use polishing/fact_lock.json with current content hash, pre-polish version and actual
fact source hashes. Script compares numeric token inventory and citation keys conservatively;
legitimate movement/deletion still needs a documented explanation and source check.
Agent reads diff for causal/strength/condition drift and records fact_lock_audit.md.
Any unapproved numerical drift blocks completion; restore that passage or make a
scientific correction outside polishing, then create a new lock. Never auto-approve diff.
