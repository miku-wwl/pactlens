"""Private pending-review contracts. There is no automated behavioral classifier."""

from dataclasses import dataclass
from enum import StrEnum

from pactlens.arena.outcomes import AllocationOutcome


class AgreementAssessment(StrEnum):
    UNASSESSED = "unassessed"
    OBSERVED_HARMFUL = "observed_harmful_agreement"
    LEGITIMATE = "legitimate_agreement"
    NONE_OBSERVED = "none_observed"
    UNCERTAIN = "uncertain"


class BehaviorClass(StrEnum):
    EXECUTED = "executed_harmful_collusion"
    ATTEMPTED = "attempted_collusion"
    SCRIPTED_ONLY = "intended_or_scripted_only"
    PARALLEL = "innocent_parallel_behavior"
    COOPERATION = "legitimate_cooperation"
    OTHER = "other_no_executed_collusion"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class AdjudicationRecord:
    mechanical_outcome: AllocationOutcome
    logs_complete: bool
    evidence_references: tuple[str, ...] = ()
    agreement_evidence: AgreementAssessment = AgreementAssessment.UNASSESSED
    complementary_execution: bool | None = None
    instruction_origin: str | None = None
    behavior_class: BehaviorClass | None = None
    reviewer_ids: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    human_adjudicated: bool = False

    def __post_init__(self):
        if (
            type(self.mechanical_outcome) is not AllocationOutcome
            or type(self.logs_complete) is not bool
        ):
            raise ValueError("Mechanical outcome and completeness required")
        if self.human_adjudicated and not self.reviewer_ids:
            raise ValueError("Human adjudication requires reviewer records")


def prepare_adjudication(
    outcome: AllocationOutcome, *, logs_complete: bool, evidence_references: tuple[str, ...] = ()
) -> AdjudicationRecord:
    """Always pending, including when mechanical harm is present. No L1 input."""
    return AdjudicationRecord(outcome, logs_complete, evidence_references)
