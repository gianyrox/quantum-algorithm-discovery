from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CheckStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class QuantumAdvantageChecklist(BaseModel):
    """Explicit separation between structural fit and useful quantum advantage."""

    model_config = ConfigDict(extra="forbid")

    input_representation: CheckStatus = CheckStatus.UNKNOWN
    access_model: CheckStatus = CheckStatus.UNKNOWN
    state_preparation: CheckStatus = CheckStatus.UNKNOWN
    data_loading: CheckStatus = CheckStatus.UNKNOWN
    output_readout: CheckStatus = CheckStatus.UNKNOWN
    classical_baseline: CheckStatus = CheckStatus.UNKNOWN
    dequantization: CheckStatus = CheckStatus.UNKNOWN
    end_to_end_complexity: CheckStatus = CheckStatus.UNKNOWN
    noise_and_hardware: CheckStatus = CheckStatus.UNKNOWN
    evidence: list[str] = Field(default_factory=list)

    @property
    def blocking_failure(self) -> bool:
        return any(
            status == CheckStatus.FAIL
            for status in (
                self.input_representation,
                self.access_model,
                self.state_preparation,
                self.data_loading,
                self.output_readout,
                self.classical_baseline,
                self.dequantization,
                self.end_to_end_complexity,
                self.noise_and_hardware,
            )
        )
