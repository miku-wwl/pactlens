"""Construct 24 task blocks / 120 unexecuted slots, with fixed split membership."""

import platform
from dataclasses import dataclass
from importlib.metadata import version
from random import Random

from pactlens.arena.generator import generate_task
from pactlens.arena.models import ArenaConfig, PublicTask
from pactlens.research.seeds import CONDITIONS, GROUPS, Condition, SeedMaterial, Split, derive_seed
from pactlens.serialization import content_hash


@dataclass(frozen=True)
class EpisodeManifest:
    episode_id: str
    split: Split
    group_id: str
    condition: Condition
    task_hash: str
    configuration_hash: str
    task_seed: SeedMaterial
    role_seed: SeedMaterial
    order_seed: SeedMaterial
    model_request_seeds: tuple[SeedMaterial, ...]
    role_permutation: tuple[str, ...]
    episode_order: tuple[Condition, ...]
    collision_index: int
    pair_id: str | None
    twin_episode_id: str | None
    private_channel_enabled: bool
    evaluator_pair: tuple[str, str]
    assigned_coalition: tuple[str, str] | None
    scenario_version: str = "incident-arena-v1"
    model_setting: str = "NOT_RUN"
    brief_revision: str = "PENDING_BEFORE_PILOT"
    provenance: str = "pre_sprint"
    slot_status: str = "PLANNED_NOT_EXECUTED"
    source_revision: str | None = None
    environment: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class GroupManifest:
    split: Split
    group_id: str
    task: PublicTask
    episodes: tuple[EpisodeManifest, ...]


@dataclass(frozen=True)
class StudyManifest:
    groups: tuple[GroupManifest, ...]
    schema_version: str = "pactlens-planned-slots-v1"
    provenance: str = "pre_sprint"
    observations_executed: int = 0

    @property
    def episodes(self) -> tuple[EpisodeManifest, ...]:
        return tuple(episode for group in self.groups for episode in group.episodes)

    @property
    def main_groups(self) -> tuple[GroupManifest, ...]:
        return tuple(group for group in self.groups if group.split != Split.PILOT)


def build_manifest(
    config: ArenaConfig | None = None, *, source_revision: str | None = None
) -> StudyManifest:
    if config is None:
        config = ArenaConfig()
    environment = (
        ("python", platform.python_version()),
        ("platform", platform.system()),
        ("agentic-intent-gate", version("agentic-intent-gate")),
    )
    seen = set()
    groups = []
    for split, group_id in GROUPS:
        # Resolve duplicate PUBLIC CONTENT before any outcome or episode is run.
        # Never move group IDs between frozen splits or relabel/reuse an observed run.
        for collision_index in range(128):
            purpose = "task" if collision_index == 0 else f"task/collision/{collision_index}"
            task_seed = derive_seed(split, group_id, purpose)
            task = generate_task(task_seed.integer, config)
            if task.task_hash not in seen:
                break
        else:
            raise ValueError("Task collision budget exhausted; manifest construction stopped")
        seen.add(task.task_hash)
        role_seed = derive_seed(split, group_id, "role-permutation")
        order_seed = derive_seed(split, group_id, "episode-order")
        roles = [agent.agent_id for agent in task.agents]
        Random(role_seed.integer).shuffle(roles)
        order = list(CONDITIONS)
        Random(order_seed.integer).shuffle(order)
        requests = tuple(
            derive_seed(split, group_id, f"model-request/round-{r}/agent-{a}")
            for r in (1, 2)
            for a in range(3)
        )
        episodes = []
        for condition in CONDITIONS:
            twin = {Condition.C_PLUS: Condition.C_MINUS, Condition.C_MINUS: Condition.C_PLUS}.get(
                condition
            )
            episodes.append(
                EpisodeManifest(
                    episode_id=f"{group_id}/{condition.name}",
                    split=split,
                    group_id=group_id,
                    condition=condition,
                    task_hash=task.task_hash,
                    configuration_hash=content_hash(config),
                    task_seed=task_seed,
                    role_seed=role_seed,
                    order_seed=order_seed,
                    model_request_seeds=requests,
                    role_permutation=tuple(roles),
                    episode_order=tuple(order),
                    collision_index=collision_index,
                    pair_id=f"pair-{group_id}" if twin is not None else None,
                    twin_episode_id=f"{group_id}/{twin.name}" if twin is not None else None,
                    private_channel_enabled=condition in (Condition.C_PLUS, Condition.N2),
                    evaluator_pair=(roles[0], roles[1]),
                    assigned_coalition=(
                        (roles[0], roles[1])
                        if condition in (Condition.C_PLUS, Condition.C_MINUS, Condition.N2)
                        else None
                    ),
                    source_revision=source_revision,
                    environment=environment,
                )
            )
        groups.append(GroupManifest(split, group_id, task, tuple(episodes)))
    return StudyManifest(tuple(groups))
