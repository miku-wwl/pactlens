"""PactLens — Evidence-Based Multi-Agent Collusion Detection.

Research project for the Apart Research AI Collusion Research Sprint
(2026-10-23 to 2026-10-25), Track 2 (Detection and Audit of Collusion),
research questions 2.2 and 2.3.

This package is a consumer of the installed ``agentic-intent-gate`` runtime
(v0.2.0, pinned release commit
``7261fdd2f47d2b15fabe8faac527eeee37338eb1``). It does not reimplement,
fork, or monkeypatch the shared runtime; all runtime integration goes through
the public ``agentic_intent_gate.runtime`` API.

Phase 0 status: repository scaffolding only. No experimental components,
datasets, or research results exist yet. See docs/PHASE0_REPORT.md.
"""

__version__ = "0.0.0"
