# Fact Lock

Before polish freeze a version, source data/facts hashes, core results/n/parameters/
conditions/statistics and display factual meanings, citations and claim boundaries.
Use polishing/fact_lock.json with current content hash, pre-polish version and actual
fact source hashes. Script compares numeric token inventory and citation keys conservatively;
legitimate movement/deletion still needs a documented explanation and source check.
Agent reads diff for causal/strength/condition drift and records fact_lock_audit.md.
Any unapproved numerical drift blocks completion; restore that passage or make a
scientific correction outside polishing, then create a new lock. Never auto-approve diff.

Numeric equality is not semantic equality. In the same diff audit check independent
units versus repeated measurements, simulated versus measured results, populations,
baselines, denominators, conditions, time windows and statistical/causal scope.
A change to any of these requires source-supported scientific review even when all
numbers and citation keys are unchanged; the token checker cannot certify it.
