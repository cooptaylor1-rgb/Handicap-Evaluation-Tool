"""Services package for the golf probability engine."""

from .probability import (
    compute_course_handicap,
    compute_expected_score,
    estimate_score_std,
    compute_single_round_probability,
    compute_multi_round_probability_at_least_once,
    binomial_tail,
    simulate_individual_scores,
    get_standard_milestones,
)

from .team_probability import (
    compute_player_parameters,
    simulate_team_bestball_round_scores,
    get_team_approximation_notes,
)

__all__ = [
    # Individual probability functions
    "compute_course_handicap",
    "compute_expected_score",
    "estimate_score_std",
    "compute_single_round_probability",
    "compute_multi_round_probability_at_least_once",
    "binomial_tail",
    "simulate_individual_scores",
    "get_standard_milestones",
    # Team probability functions
    "compute_player_parameters",
    "simulate_team_bestball_round_scores",
    "get_team_approximation_notes",
]
