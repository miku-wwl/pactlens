from pactlens.aig.contract import restore_state
from pactlens.arena.models import ArenaState
from pactlens.arena.transitions import begin, close_round
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import TraceWriter
from pactlens.serialization import canonical_json, content_hash


def test_old_request_without_new_protocol_fields_replays_without_model_or_gateway(
    tmp_path, task, monkeypatch
):
    from pactlens.agents.ollama_provider import OllamaProvider
    from pactlens.aig import consumer

    def forbidden(*args, **kwargs):
        raise AssertionError("Pure replay called a provider or Gateway composition")

    monkeypatch.setattr(OllamaProvider, "generate", forbidden)
    monkeypatch.setattr(consumer, "consumer", forbidden)
    public_id = "d6dd1a02-5135-4fd7-9844-2dd36366a68e"
    w = TraceWriter(tmp_path / "legacy-declines.jsonl", public_id)
    state = ArenaState(task)
    w.append(
        "CONFIG",
        {
            "config": {"namespace": "pre_sprint_engineering"},
            "initial_state": state,
            "formal_episodes_executed": 0,
            "actor_order": [a.agent_id for a in task.agents],
        },
    )
    state = begin(state, expected_revision=0)
    w.append("ARENA", {"state": state, "state_digest": content_hash(state)})
    for round_number in (1, 2):
        for actor in task.agents:
            # Original Phase 3 request shape; deliberately no new protocol/hash/budget fields.
            request = {
                "actor_id": actor.agent_id,
                "round_number": round_number,
                "turns": [],
                "seed": 4,
                "prompt_version": "pactlens-agent-v1",
                "derived_seed": 4,
                "seed_mapping": "UNSIGNED64_LOW63_V1",
            }
            raw = canonical_json(
                {
                    "actor_id": actor.agent_id,
                    "round_number": round_number,
                    "task_hash": task.task_hash,
                    "decision": "decline",
                    "assignments": None,
                    "message": None,
                    "end_step": True,
                }
            )
            w.append("MODEL_REQUEST", {"request": request, "request_digest": content_hash(request)})
            w.append(
                "MODEL_RESPONSE",
                {
                    "actor_id": actor.agent_id,
                    "round_number": round_number,
                    "response": {"text": raw},
                    "response_digest": content_hash(raw),
                },
            )
            w.append(
                "PROPOSAL_ATTEMPT",
                {
                    "actor_id": actor.agent_id,
                    "round_number": round_number,
                    "status": "DECLINED",
                    "proposal": None,
                },
            )
        state = close_round(state, expected_revision=state.revision)
        w.append("ARENA", {"state": state, "state_digest": content_hash(state)})
    w.append("PUBLIC_OUTCOME", {"state_digest": content_hash(state)})
    w.append(
        "TERMINAL", {"status": "COMPLETE", "finalized": True, "state_digest": content_hash(state)}
    )
    w.close()
    replay = replay_trace(w.path)
    assert replay.record.state == restore_state(canonical_json(state))
    assert replay.status == "COMPLETE" and replay.model_calls == replay.new_effects == 0
