"""Approved-future Pilot composition. No model or AIG framework is duplicated."""

from pathlib import Path

from pactlens.agents.deepseek_provider import CampaignLedger, DeepSeekProvider
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.sufficiency import select_common
from pactlens.evidence.views import View
from pactlens.research.detector_runner import exclusive_json, predict
from pactlens.research.study_launch import StudyEpisodeConfig, launch_verified, verify_launch


async def execute_pilot(manifest, root, output):
    verify_launch(manifest, root)
    output = Path(output)
    ledger_path = output.parent / (output.name + "-inference.sqlite3")
    if ledger_path.exists() or output.exists():
        raise ValueError("FRESH_PILOT_REQUIRED_NO_AUTOMATIC_RESUME")
    ledger = CampaignLedger.authorized_pilot(ledger_path, manifest, root)
    profile = {
        "phase5a1-native-v1": "phase5a1",
        "phase5a2-reason-v1": "phase5a2",
        "phase5a3-context-v1": "phase5a3",
    }.get(manifest["configuration"]["provider"].get("version"), "phase4e")
    candidate = profile != "phase4e"
    providers = []

    def provider_factory(episode_id):
        if providers and providers[-1].blocked:
            raise ValueError("PROVIDER_STOP_NO_RECOVERY_REPLAY")
        p = DeepSeekProvider(ledger, "agent", context_id=episode_id, profile=profile)
        providers.append(p)
        return p

    async def detector_step(run, episode, permit):
        if providers[-1].blocked:
            raise ValueError("PROVIDER_STOP_NO_FALLBACK")
        inv = build_inventory(
            run.record,
            run.observations,
            run.deliveries,
            public_id=run.public_id,
            policy=ObservationPolicy.DELIVERED,
            status=run.status,
            shared_capture=True,
        )
        if profile == "phase5a3":
            from pactlens.research.context_profile import full_packets

            packets = {p.view: p for p in full_packets(inv)}
        elif candidate:
            from pactlens.evidence.tight_views import render
            from pactlens.research.native_detector import envelope

            if profile == "phase5a2":
                from pactlens.research.reason_detector import envelope

            selected = select_common(inv, envelope=envelope(), renderer=render)
            packets = {p.view: p for p in selected.packets}
        else:
            selected = select_common(inv)
            packets = {p.view: p for p in selected.packets}
        model = DeepSeekProvider(ledger, "detector", context_id=episode.episode_id, profile=profile)
        config = StudyEpisodeConfig(episode, manifest["configuration_hash"])
        for view in View:
            await predict(
                output / "predictions",
                packets[view],
                model,
                engineering_id=None,
                formal_config=config,
                formal_permit=permit,
                sufficiency_policy=manifest["configuration"].get("sufficiency_policy"),
            )
            if model.blocked:
                raise ValueError("DETECTOR_PROVIDER_STOP")

    try:
        return await launch_verified(manifest, root, output, provider_factory, detector_step)
    finally:
        if output.exists():
            exclusive_json(output / "usage-terminal.json", ledger.report())
