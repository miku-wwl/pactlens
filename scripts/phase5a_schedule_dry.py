"""Provision isolated engineering stores for every planned slot; no inference/effects."""

import argparse
import hashlib
import json
from pathlib import Path

from pactlens.aig.consumer import provision
from pactlens.research.detector_runner import exclusive_json
from pactlens.research.manifest import build_manifest
from pactlens.research.study_launch import freeze_candidate, schedule
from pactlens.serialization import content_hash


def main(final=False):
    root = Path.cwd()
    suffix = "-final" if final else ""
    private = root / (".runtime/phase5a-full-schedule-dry" + suffix)
    private.mkdir(parents=True, exist_ok=False)
    freeze = freeze_candidate(root)
    planned = schedule(freeze["configuration_hash"])
    assert planned == schedule(freeze["configuration_hash"])
    tasks = {g.group_id: g.task for g in build_manifest().groups}
    scopes = set()
    stores = set()
    paths = set()
    rows = []
    for slot in planned["slots"]:
        directory = private / slot["store"]
        directory.mkdir(parents=True, exist_ok=False)
        exclusive_json(
            directory / "intent.json",
            {"slot": slot["episode_id"], "mode": "ENGINEERING_PROVISION_ONLY_NO_FORMAL_DISPATCH"},
        )
        actor_scopes = []
        for actor in tasks[slot["group"]].agents:
            p = directory / actor.agent_id
            store = provision(p, tasks[slot["group"]], actor.agent_id)
            scope = store.identity["binding"]["execution_scope"]
            assert (
                scope not in scopes
                and store.identity["store_id"] not in stores
                and str(p) not in paths
            )
            scopes.add(scope)
            stores.add(store.identity["store_id"])
            paths.add(str(p))
            assert not store.committed()
            actor_scopes.append(hashlib.sha256(scope.encode()).hexdigest())
        try:
            exclusive_json(directory / "intent.json", {})
        except FileExistsError:
            restart = "DENIED_EXISTING_INTENT_NO_REDISPATCH"
        else:
            raise AssertionError("restart fence")
        rows.append(
            {
                **slot,
                "scope_fingerprints": actor_scopes,
                "provisioned_stores": 3,
                "restart_test": restart,
            }
        )
    output = {
        "schedule": planned,
        "schedule_hash": content_hash(planned),
        "provisioned": rows,
        "unique_stores": len(stores),
        "unique_scopes": len(scopes),
        "model_calls": 0,
        "effects": 0,
        "formal_slots_used": 0,
        "heldout_truth_or_outputs_opened": 0,
        "actual_model_responses_reused": 0,
        "metadata_only_split_access": True,
        "status": "PASS_ENGINEERING_DRY_RUN",
    }
    exclusive_json(root / ("review/phase4e5a/full-schedule-dry" + suffix + ".json"), output)
    print(json.dumps({k: v for k, v in output.items() if k not in ("schedule", "provisioned")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final", action="store_true")
    main(parser.parse_args().final)
