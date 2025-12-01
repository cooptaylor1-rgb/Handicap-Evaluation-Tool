"""
API routes for individual golf probability calculations.

This module defines the FastAPI endpoints for calculating single-round,
multi-round, and milestone probabilities for individual golfers.
"""

import logging
from fastapi import APIRouter

from app.models import (
    SingleRoundProbabilityRequest,
    SingleRoundProbabilityResponse,
    MultiRoundProbabilityRequest,
    MultiRoundProbabilityResponse,
    MilestoneProbabilityRequest,
    MilestoneProbabilityResponse,
    MilestoneResult,
)
from app.services import (
    compute_expected_score,
    estimate_score_std,
    compute_single_round_probability,
    compute_multi_round_probability_at_least_once,
    binomial_tail,
    get_standard_milestones,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/probability/single-round",
    response_model=SingleRoundProbabilityResponse,
    summary="Calculate Single Round Probability",
    description=(
        "Calculate the probability of a golfer shooting at or below a target score "
        "in a single round, based on their handicap index and course setup."
    )
)
async def calculate_single_round_probability(
    request: SingleRoundProbabilityRequest
) -> SingleRoundProbabilityResponse:
    """
    Calculate single round probability for an individual golfer.
    
    Uses normal distribution approximation with continuity correction.
    """
    logger.info(
        f"Single round calculation: handicap={request.golfer.handicap_index}, "
        f"target={request.target.target_score}, course={request.course.course_name}"
    )
    
    # Compute expected score and standard deviation
    expected_score = compute_expected_score(
        request.golfer.handicap_index,
        request.course
    )
    sigma = estimate_score_std(request.golfer.handicap_index)
    
    # Compute probability
    probability, z_score = compute_single_round_probability(
        expected_score,
        sigma,
        request.target.target_score
    )
    
    logger.info(
        f"Result: expected={expected_score:.1f}, sigma={sigma:.1f}, "
        f"probability={probability:.4f}"
    )
    
    return SingleRoundProbabilityResponse(
        expected_score=round(expected_score, 2),
        score_std=round(sigma, 2),
        target_score=request.target.target_score,
        probability_score_at_or_below_target=round(probability, 6),
        distribution_type="normal_approximation",
        z_score=round(z_score, 4)
    )


@router.post(
    "/probability/multi-round",
    response_model=MultiRoundProbabilityResponse,
    summary="Calculate Multi-Round Probability",
    description=(
        "Calculate the probability of achieving a target score at least a certain "
        "number of times over multiple rounds (e.g., a tournament)."
    )
)
async def calculate_multi_round_probability(
    request: MultiRoundProbabilityRequest
) -> MultiRoundProbabilityResponse:
    """
    Calculate multi-round probability for an individual golfer.
    
    Uses binomial model for counting successes across independent rounds.
    """
    logger.info(
        f"Multi-round calculation: handicap={request.golfer.handicap_index}, "
        f"target={request.target.target_score}, rounds={request.event.num_rounds}, "
        f"min_success={request.min_success_rounds}"
    )
    
    # Compute expected score and standard deviation
    expected_score = compute_expected_score(
        request.golfer.handicap_index,
        request.course
    )
    sigma = estimate_score_std(request.golfer.handicap_index)
    
    # Compute single round probability
    single_prob, _ = compute_single_round_probability(
        expected_score,
        sigma,
        request.target.target_score
    )
    
    # Compute multi-round probabilities
    prob_at_least_once = compute_multi_round_probability_at_least_once(
        single_prob,
        request.event.num_rounds
    )
    
    prob_at_least_min = binomial_tail(
        request.event.num_rounds,
        single_prob,
        request.min_success_rounds
    )
    
    logger.info(
        f"Result: single_prob={single_prob:.4f}, "
        f"at_least_once={prob_at_least_once:.4f}, "
        f"at_least_{request.min_success_rounds}={prob_at_least_min:.4f}"
    )
    
    return MultiRoundProbabilityResponse(
        expected_score=round(expected_score, 2),
        score_std=round(sigma, 2),
        target_score=request.target.target_score,
        num_rounds=request.event.num_rounds,
        min_success_rounds=request.min_success_rounds,
        probability_at_least_min_success_rounds=round(prob_at_least_min, 6),
        probability_at_least_once=round(prob_at_least_once, 6),
        single_round_probability=round(single_prob, 6),
        binomial_model_used=True
    )


@router.post(
    "/probability/milestones",
    response_model=MilestoneProbabilityResponse,
    summary="Calculate Milestone Probabilities",
    description=(
        "Calculate probabilities for standard milestone scores (e.g., breaking "
        "100, 90, 85, 80, 75) based on the golfer's handicap and course setup."
    )
)
async def calculate_milestone_probabilities(
    request: MilestoneProbabilityRequest
) -> MilestoneProbabilityResponse:
    """
    Calculate probabilities for standard milestone scores.
    
    Automatically selects relevant milestones based on the golfer's expected score.
    """
    logger.info(
        f"Milestone calculation: handicap={request.golfer.handicap_index}, "
        f"rounds={request.event.num_rounds}, course={request.course.course_name}"
    )
    
    # Compute expected score and standard deviation
    expected_score = compute_expected_score(
        request.golfer.handicap_index,
        request.course
    )
    sigma = estimate_score_std(request.golfer.handicap_index)
    
    # Get relevant milestone targets
    milestone_targets = get_standard_milestones(expected_score)
    
    # Calculate probabilities for each milestone
    milestones = []
    for target in milestone_targets:
        single_prob, _ = compute_single_round_probability(
            expected_score,
            sigma,
            target
        )
        multi_prob = compute_multi_round_probability_at_least_once(
            single_prob,
            request.event.num_rounds
        )
        
        milestones.append(MilestoneResult(
            target_score=target,
            prob_single_round_at_or_below=round(single_prob, 6),
            prob_at_least_once_in_event=round(multi_prob, 6)
        ))
    
    logger.info(f"Calculated {len(milestones)} milestone probabilities")
    
    return MilestoneProbabilityResponse(
        expected_score=round(expected_score, 2),
        score_std=round(sigma, 2),
        num_rounds=request.event.num_rounds,
        milestones=milestones
    )
