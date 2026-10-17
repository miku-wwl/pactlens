"""Explicit provisioning/composition; AIG owns every Run and Action safety gate."""

import json
from contextlib import closing, contextmanager
from pathlib import Path
from uuid import uuid4

from agentic_intent_gate.runtime import (
    BoundCapabilityAuthorization,
    CapabilityVerifier,
    ExecutableRegistry,
    ExecutionSpec,
    ToolCapability,
    open_runtime,
    provision_capability,
)

from pactlens.aig.contract import (
    ARGUMENT_SCHEMA,
    DeterministicProvider,
    ObservedAction,
    binding_for,
    uuid4_text,
)
from pactlens.aig.effect_store import ProposalStore
from pactlens.aig.executor import ProposalExecutor, no_fault
from pactlens.arena.models import validate_state
from pactlens.serialization import canonical_json


def provision(directory, task, actor_id):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()) or actor_id not in {a.agent_id for a in task.agents}:
        raise ValueError("New empty private directory and known actor required")
    identity = {
        "revision": "pactlens-consumer-v1",
        "store_id": str(uuid4()),
        "binding": vars(binding_for(str(uuid4()))),
        "actor_id": actor_id,
        "task_hash": task.task_hash,
        "subject_id": "proposal-operator-" + str(uuid4()),
    }
    # Scope is never silently regenerated when opening an existing composition.
    (directory / "identity.json").write_text(canonical_json(identity), encoding="utf-8")
    provision_capability(directory / "capability")
    ProposalStore.provision(directory / "proposals.sqlite3", identity)
    return load_store(directory)


def load_store(directory):
    directory = Path(directory)
    identity = json.loads((directory / "identity.json").read_text("utf-8"))
    if (
        set(identity) != {"revision", "store_id", "binding", "actor_id", "task_hash", "subject_id"}
        or identity["revision"] != "pactlens-consumer-v1"
    ):
        raise ValueError("Reviewed identity required")
    uuid4_text(identity["store_id"])
    binding = binding_for(identity["binding"]["execution_scope"])
    if vars(binding) != identity["binding"]:
        raise ValueError("Unreviewed binding identity")
    store = ProposalStore(directory / "proposals.sqlite3", identity)
    # An incompatible/replaced store is a startup failure, never reprovisioned.
    with closing(store.connect()) as db:
        store.check_identity(db)
    return store


@contextmanager
def consumer(
    directory,
    state,
    prepared,
    *,
    provider=None,
    predecessor_stopped=False,
    checkpoint=no_fault,
    executor_factory=ProposalExecutor,
):
    """Trusted host supplies the current public Arena view, never a Plan authority field."""
    validate_state(state)
    directory = Path(directory)
    store = load_store(directory)
    identity = store.identity
    binding = binding_for(identity["binding"]["execution_scope"])
    if (
        state.task.task_hash != identity["task_hash"]
        or prepared.proposal.agent_id != identity["actor_id"]
    ):
        raise ValueError("Composition actor/task mismatch")
    verifier = CapabilityVerifier(
        (directory / "capability").read_text("ascii"),
        subject_id=identity["subject_id"],
        binding=binding,
        operations=("read", "admit", "authorize", "execute"),
    )
    executor = executor_factory(store, binding, state, checkpoint=checkpoint)
    with open_runtime(
        gate_path=directory / "gate.sqlite3",
        provider=provider or DeterministicProvider(prepared),
        capability=ToolCapability(binding, "Record one frozen synthetic proposal", ARGUMENT_SCHEMA),
        registry=ExecutableRegistry(executor, binding=binding),
        verifier=verifier,
        policy=BoundCapabilityAuthorization(verifier, policy_revision="proposal-policy-v1"),
        predecessor_stopped=predecessor_stopped,
        # Omit execution_timeout_seconds: reviewed default is five seconds.
    ) as runtime:
        yield runtime, executor, store


def observe_action(runtime, store, action_id, principal, *, synthetic_consent):
    action = runtime.gateway.get(action_id, principal)
    run = runtime.run_service.get(action.spec.run_id)
    spec = ExecutionSpec.from_compiled(action.spec)
    binding = binding_for(store.identity["binding"]["execution_scope"])
    if not binding.matches(spec):
        raise ValueError("Action/store identity mismatch")
    effects = [e for e in store.committed() if e.effect_key == action.effect_key]
    effect = effects[0] if effects else None
    if effect and effect.payload_digest != spec.payload_digest():
        raise ValueError("Action/receipt payload mismatch")
    if action.state.value == "Failed" and effect is not None:
        raise ValueError("Confirmed failure contradicts committed receipt")
    if action.state.value == "Succeeded" and (
        effect is None or action.result["receipt_reference"] != effect.receipt_reference
    ):
        raise ValueError("Succeeded Action lacks matching verified receipt")
    return ObservedAction(
        store.identity["actor_id"],
        spec.arguments["round_number"],
        action.action_id,
        action.version,
        action.state.value,
        run.state.value,
        action.authorization is not None,
        spec.payload_digest(),
        spec.arguments["proposal_digest"],
        effect.receipt_reference if effect else None,
        "VERIFIED_COMMITTED" if effect else "MISSING",
        synthetic_consent,
    )
