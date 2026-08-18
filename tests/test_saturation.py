from discovery.retrieval.saturation import SaturationObservation, SaturationPolicy


def test_saturation_uses_recent_novelty_rate() -> None:
    policy = SaturationPolicy(minimum_iterations=3, window=3, novelty_threshold=0.05)
    observations = [
        SaturationObservation(
            iteration=1, retrieved=100, new_unique_works=4, cumulative_unique_works=100
        ),
        SaturationObservation(
            iteration=2, retrieved=100, new_unique_works=3, cumulative_unique_works=103
        ),
        SaturationObservation(
            iteration=3, retrieved=100, new_unique_works=2, cumulative_unique_works=105
        ),
    ]
    assert policy.saturated(observations)
