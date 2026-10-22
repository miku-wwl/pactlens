# Baseline discrepancies and implementation boundary

Recorded before source edits, 2026-10-22 NZDT. HEAD, origin/main and remote main
are 65a003263cccfb3d0370db13b086de958dab0db4; initial tree was clean.

- Historical reports describe their uncommitted snapshots. Phase 4D is now
  committed; those historical reports will be preserved.
- The existing detector artifact has a host abstention flag alongside a latent
  scored PredictionRecord. Replay does not independently derive that flag.
  An additive v2 decision contract must make analysis consume only effective scores.
- Existing host logic conflates an observed missing proposal with failed capture,
  and treats observer-policy exclusions as capture failures. A prospective
  engineering policy will distinguish these; formal adoption remains pending.
- Existing operations reject all formal dispatch. A guarded Pilot command and
  frozen-manifest adapter are needed; no formal execution is authorized here.
- Larger advertised DeepSeek context/output limits do not amend 2000/4096/256
  study limits. Native schema overhead must pass the unchanged heuristic too.
- Current official pricing identifies deepseek-flash as V4.1-Flash-1017.
  API availability and returned identity still require authenticated verification.
- Documentation distinguishes Responses json_schema from Chat json_object.
  The first candidate will use /responses, reasoning.effort=none, temperature=0,
  max_output_tokens=256, no tools, one attempt and no fallback.

Smallest implementation: explicit stdlib HTTPS adapter plus atomic consumer
inference ledger; a separate v3.2 prompt retaining the strict parser; additive
authoritative detector decision/replay; frozen schedule, launch guards and
synthetic analysis/export validation. Arena, AIG, frozen study and old prompts
remain unchanged. Qualification failures will not trigger replacement profiles.
