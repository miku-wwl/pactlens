import hashlib
from collections import Counter
from dataclasses import replace

import pytest

import pactlens.research.manifest as module
from pactlens.research.fixtures import fixture_task
from pactlens.research.manifest import build_manifest
from pactlens.research.seeds import CONDITIONS, GROUPS, Condition, Split, derive_seed
from pactlens.serialization import content_hash


def test_seed_bytes_and_integer_convention():
    # Independent contract calculation, with literal separators and split spelling.
    data = b"pactlens-exploratory-v1 | calibration | K001 | task"
    digest = hashlib.sha256(data).digest()
    seed = derive_seed(Split.CALIBRATION, "K001", "task")
    assert seed.digest_hex == digest.hex()
    assert seed.integer == int.from_bytes(digest[:8], byteorder="big", signed=False)
    assert len(seed.digest_hex) == 64
    assert derive_seed(Split.CALIBRATION, "K001", "episode-order") != seed


@pytest.mark.parametrize(
    "split,group,purpose",
    [
        (Split.PILOT, "K001", "task"),
        ("pilot", "P001", "task"),
        (Split.PILOT, "P005", "task"),
        (Split.PILOT, "P001", "task | private"),
    ],
)
def test_seed_identity_validation(split, group, purpose):
    with pytest.raises(ValueError):
        derive_seed(split, group, purpose)


def test_24_blocks_120_slots_exact_frozen_membership():
    study = build_manifest()
    assert len(study.groups) == 24 and len(study.episodes) == 120
    assert study.observations_executed == 0
    assert tuple((g.split, g.group_id) for g in study.groups) == GROUPS
    assert Counter(g.split for g in study.groups) == {
        Split.PILOT: 4,
        Split.CALIBRATION: 10,
        Split.HELD_OUT: 10,
    }
    assert Counter(e.split for e in study.episodes) == {
        Split.PILOT: 20,
        Split.CALIBRATION: 50,
        Split.HELD_OUT: 50,
    }
    assert Counter(e.condition for e in study.episodes) == dict.fromkeys(CONDITIONS, 24)
    assert len({e.episode_id for e in study.episodes}) == 120
    assert all(e.slot_status == "PLANNED_NOT_EXECUTED" for e in study.episodes)
    for group in study.groups:
        assert len(group.episodes) == 5 and {e.condition for e in group.episodes} == set(CONDITIONS)
        assert {e.split for e in group.episodes} == {group.split}
        assert {e.group_id for e in group.episodes} == {group.group_id}
        assert {e.task_hash for e in group.episodes} == {group.task.task_hash}
        assert {e.configuration_hash for e in group.episodes} == {content_hash(group.task.config)}


def test_paired_manifest_identity_and_shared_future_random_streams():
    for group in build_manifest().groups:
        plus = next(e for e in group.episodes if e.condition == Condition.C_PLUS)
        minus = next(e for e in group.episodes if e.condition == Condition.C_MINUS)
        assert plus.pair_id == minus.pair_id
        assert plus.twin_episode_id == minus.episode_id and minus.twin_episode_id == plus.episode_id
        for key in (
            "task_hash",
            "configuration_hash",
            "task_seed",
            "role_seed",
            "order_seed",
            "model_request_seeds",
            "role_permutation",
            "episode_order",
            "scenario_version",
            "model_setting",
            "brief_revision",
            "evaluator_pair",
            "assigned_coalition",
        ):
            assert getattr(plus, key) == getattr(minus, key)
        assert (
            len(plus.model_request_seeds) == 6
            and len({s.integer for s in plus.model_request_seeds}) == 6
        )
        assert plus.private_channel_enabled and not minus.private_channel_enabled
        assert set(plus.episode_order) == set(CONDITIONS)
        assert set(plus.role_permutation) == {a.agent_id for a in group.task.agents}


def test_no_task_reuse_cross_split_and_pilot_excluded_from_main():
    study = build_manifest()
    assert len({g.task.task_hash for g in study.groups}) == 24
    hashes = {
        split: {g.task.task_hash for g in study.groups if g.split == split} for split in Split
    }
    assert not hashes[Split.PILOT] & (hashes[Split.CALIBRATION] | hashes[Split.HELD_OUT])
    assert not hashes[Split.CALIBRATION] & hashes[Split.HELD_OUT]
    assert len(study.main_groups) == 20
    assert all(g.split != Split.PILOT for g in study.main_groups)
    assert content_hash(study) == content_hash(build_manifest())


def test_manifest_does_not_execute_episodes(monkeypatch):
    from pactlens.arena import transitions

    def forbidden(*args, **kwargs):
        pytest.fail("Manifest construction must not execute any planned episode")

    monkeypatch.setattr(transitions, "begin", forbidden)
    assert len(build_manifest().episodes) == 120


def test_duplicate_task_collision_resolved_before_outcomes_without_resplitting(monkeypatch):
    original = module.generate_task
    calls = []

    def collision(seed, config):
        calls.append(seed)
        return replace(fixture_task(), config=config) if len(calls) <= 2 else original(seed, config)

    monkeypatch.setattr(module, "generate_task", collision)
    study = build_manifest()
    assert len(calls) == 25
    assert study.groups[0].episodes[0].collision_index == 0
    assert study.groups[1].episodes[0].collision_index == 1
    assert study.groups[1].episodes[0].task_seed.purpose == "task/collision/1"
    assert tuple((g.split, g.group_id) for g in study.groups) == GROUPS
    assert len({g.task.task_hash for g in study.groups}) == 24


def test_unresolvable_collision_fails_closed(monkeypatch):
    monkeypatch.setattr(module, "generate_task", lambda *args: fixture_task())
    with pytest.raises(ValueError, match="collision budget exhausted"):
        build_manifest()
