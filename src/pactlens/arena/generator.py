"""Local seeded sampling with a constructive fully assigned feasible witness."""

from random import Random

from pactlens.arena.models import Agent, ArenaConfig, Incident, PublicTask, integer


def generate_task(seed: int, config: ArenaConfig | None = None) -> PublicTask:
    integer(seed, 0, (1 << 64) - 1)
    if config is None:
        config = ArenaConfig()
    if type(config) is not ArenaConfig:
        raise TypeError("ArenaConfig required")
    rng = Random(seed)
    count = config.incident_count if config.incident_count is not None else rng.randint(3, 5)
    requirements = [rng.choice(("network", "database")) for _ in range(count)]
    workloads = [rng.randint(1, 3) for _ in range(count)]
    witness = [index % 3 for index in range(count)]
    rng.shuffle(witness)
    rates = rng.sample(range(1, 7), 3)
    agents = []
    for index in range(3):
        skills = {requirements[k] for k in range(count) if witness[k] == index}
        if rng.randrange(2):
            skills.update(("network", "database"))
        capacity = sum(workloads[k] for k in range(count) if witness[k] == index)
        agents.append(
            Agent(
                f"a{index}",
                tuple(sorted(skills)),
                capacity + rng.randint(0, 3),
                rates[index],
                rng.randint(1, 3),
            )
        )
    incidents = []
    for index in range(count):
        allowed = {f"a{witness[index]}"}
        allowed.update(
            a.agent_id for a in agents if requirements[index] in a.skills and rng.randrange(2)
        )
        incidents.append(
            Incident(
                f"i{index}",
                workloads[index],
                rng.randint(1, 5),
                requirements[index],
                rng.randint(1, 3),
                rng.randint(10, 30),
                tuple(sorted(allowed)),
            )
        )
    return PublicTask(tuple(agents), tuple(incidents), config)
