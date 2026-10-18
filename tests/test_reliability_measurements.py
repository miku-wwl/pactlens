import asyncio

import pytest
from harness_helpers import run_fake

from pactlens.agents.reliability import response_observations


@pytest.mark.parametrize("bad", ["assignment_shape", "recipient_shape"])
def test_schema_and_routing_measurements_are_separate_from_actual_acceptance(tmp_path, task, bad):
    def transform(body, request):
        if bad == "assignment_shape":
            body["assignments"] = body["assignments"][:1]
        else:
            body["message"] = {
                "channel": "public",
                "recipients": ["a0", "a1", "a2"],
                "text": "synthetic invalid routing",
            }

    run, _ = asyncio.run(run_fake(tmp_path, task, transform=transform))
    rows = response_observations(run)
    assert len(rows) == 6
    assert all(x["json_valid"] is True and x["schema_valid"] is False for x in rows)
    assert all(not x["valid_submit"] and not x["valid_decline"] for x in rows)
    assert run.executor_calls == 0
    if bad == "recipient_shape":
        assert all(x["assignment_feasible"] is True and x["message_valid"] is False for x in rows)
