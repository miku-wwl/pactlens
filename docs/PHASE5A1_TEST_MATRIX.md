# Phase 5A.1 verification matrix

| Check | Actual result | Evidence |
|---|---|---|
| Isolated HEAD baseline | 885 passed in703.82s | review/phase5a1/logs/baseline-retry-tests.txt |
| Full current regression | 930 passed | review/phase5a1/logs/final-regression.txt |
| Locked dependency sync | PASS | logs/final-sync.txt and exit file |
| Ruff lint/format | PASS only when final exit files are0 | logs/final-ruff-check.txt; final-ruff-format.txt |
| Offline lock check | PASS only when final exit file is0 | logs/final-lock.txt |
| Installed AIG | 0.2.0/full7261fdd2 pin,57 RECORD hashes,five-second default | aig-and-tokenizer-environment.json; verification.json |
| Six-position matrix | 20 public/base/decline/long trajectories +4 private supplements, zero paid inference | offline-agent-matrix.json; offline-private-supplement.json |
| Real bounded campaign | 11 Agent +10 Detector,21/28; USD.011547 estimate | live/predeclared-plan.json; usage-final.json; campaign-summary.json |
| Genuine durable effect and replay | N3 five,C+ four committed rows; no new calls/effects during replay | verification.json |
| Final-text R/MAE parity | PASS both cases and full A/B audits | full-audit.json; prediction replay verification |
| Effective scoring | Deterministic fake path PASS; real path0/10 NO-GO | candidate-final-targeted.txt; live predictions |
| Freeze command | Real pending candidate rejects before any provider/store creation | logs/pilot-dry-run.txt; pilot-dry-run.json |
| Archive | CRC/member SHA/current-byte/secret scan verified after packaging returns | adjacent external ZIP verification receipt |

New tests cover native schema overhead, v3.3 exact reversible context, complete submit objects and pair-array rejection, six-step real local AIG, long/private history feasibility, strict score/citation/rationale/truncation branches, reliable absence versus Unknown/capture loss, required evidence omissions, effective-score bridge, R/MAE evidence eligibility parity, all28 reservations/per-context/lower-cost caps, original N1 denominators, sixteen-choice freeze integrity and manufactured approvals only. Existing leakage, matched-group, stale approval, unauthorized/duplicate/Unknown, and held-out protection tests remain unchanged. No held-out output files are used; manufactured analysis rows test arithmetic only.

Failure history is preserved: the first isolated baseline shell encountered a system OutOfMemory exception after partial progress; the independent rerun passed885. An early offline stdout print failed Windows GBK on the Unicode C-minus label after several completed fake trajectories; the full UTF-8 rerun passed and original captures remain private. Initial new Detector fake tests used integer-only Arena JSON for decimal scores and failed21 tests; the fixture now uses research numeric JSON. Expanded tests then exposed two test-code defects (missing replace import and wrong metric key); corrected final targeted40 passed. These are disclosed offline defects, not additional real-model attempts. No paid prompt tuning/retry followed real campaign outcomes.

Final source/legacy hashes, package provenance, protected files, leakage-marker checks, exact-value/pattern secret scanning and private read-only replay hashes are independently asserted by `scripts/verify_phase5a1.py` and the packaging/verification scripts. Tests do not certify empirical readiness.
