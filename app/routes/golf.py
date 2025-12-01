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
    ConsecutiveScoresProbabilityRequest,
    ConsecutiveScoresProbabilityResponse,
    CompletedRoundAnalysisRequest,
    CompletedRoundAnalysisResponse,
    RoundProbabilityAnalysis,
    SandbaggerAnalysisRequest,
    SandbaggerAnalysisResponse,
    SandbaggerRedFlag,
)
from app.services import (
    compute_expected_score,
    estimate_score_std,
    compute_single_round_probability,
    compute_multi_round_probability_at_least_once,
    binomial_tail,
    get_standard_milestones,
    compute_nine_hole_expected_score,
    estimate_nine_hole_score_std,
    compute_consecutive_scores_probability,
    compute_consecutive_in_n_matches_probability,
    analyze_completed_round,
    compute_joint_probability_independent_rounds,
    get_overall_performance_descriptor,
    calculate_sandbagging_risk_score,
    detect_tournament_excellence_pattern,
    detect_low_volatility_pattern,
    detect_improbable_performance,
    detect_casual_vs_tournament_disparity,
    detect_all_scores_better_than_expected,
    generate_sandbagging_summary,
    generate_recommendation,
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
        f"target={request.target.target_score}, course={request.course.course_name}, "
        f"holes={request.holes_played}"
    )
    
    # Compute expected score and standard deviation based on holes played
    if request.holes_played == 9:
        expected_score = compute_nine_hole_expected_score(
            request.golfer.handicap_index,
            request.course
        )
        sigma = estimate_nine_hole_score_std(request.golfer.handicap_index)
    else:
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
        f"min_success={request.min_success_rounds}, holes={request.holes_played}"
    )
    
    # Compute expected score and standard deviation based on holes played
    if request.holes_played == 9:
        expected_score = compute_nine_hole_expected_score(
            request.golfer.handicap_index,
            request.course
        )
        sigma = estimate_nine_hole_score_std(request.golfer.handicap_index)
    else:
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
        f"rounds={request.event.num_rounds}, course={request.course.course_name}, "
        f"holes={request.holes_played}"
    )
    
    # Compute expected score and standard deviation based on holes played
    if request.holes_played == 9:
        expected_score = compute_nine_hole_expected_score(
            request.golfer.handicap_index,
            request.course
        )
        sigma = estimate_nine_hole_score_std(request.golfer.handicap_index)
    else:
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

@router.post(
    "/probability/consecutive",
    response_model=ConsecutiveScoresProbabilityResponse,
    summary="Calculate Consecutive Scores Probability",
    description=(
        "Calculate the probability of shooting at or below a target score in "
        "consecutive rounds. Supports both 9-hole and 18-hole matches."
    )
)
async def calculate_consecutive_scores_probability(
    request: ConsecutiveScoresProbabilityRequest
) -> ConsecutiveScoresProbabilityResponse:
    """
    Calculate the probability of achieving consecutive target scores.
    
    Supports:
    - Probability of shooting target in N consecutive rounds
    - Probability of having at least one streak of N in M total matches
    - Both 9-hole and 18-hole rounds
    """
    logger.info(
        f"Consecutive scores calculation: handicap={request.golfer.handicap_index}, "
        f"target={request.target.target_score}, consecutive={request.consecutive_count}, "
        f"holes={request.holes_per_round}"
    )
    
    # Compute expected score and standard deviation based on holes per round
    if request.holes_per_round == 9:
        expected_score = compute_nine_hole_expected_score(
            request.golfer.handicap_index,
            request.course
        )
        sigma = estimate_nine_hole_score_std(request.golfer.handicap_index)
    else:
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
    
    # Compute probability of all consecutive successes
    prob_all_consecutive = compute_consecutive_scores_probability(
        single_prob,
        request.consecutive_count
    )
    
    # If total_matches is specified, compute probability of streak within matches
    prob_streak_in_matches = None
    if request.total_matches is not None:
        prob_streak_in_matches = compute_consecutive_in_n_matches_probability(
            single_prob,
            request.consecutive_count,
            request.total_matches
        )
    
    logger.info(
        f"Result: expected={expected_score:.1f}, single_prob={single_prob:.4f}, "
        f"consecutive_prob={prob_all_consecutive:.6f}"
    )
    
    return ConsecutiveScoresProbabilityResponse(
        expected_score=round(expected_score, 2),
        score_std=round(sigma, 2),
        target_score=request.target.target_score,
        consecutive_count=request.consecutive_count,
        holes_per_round=request.holes_per_round,
        single_round_probability=round(single_prob, 6),
        probability_all_consecutive=round(prob_all_consecutive, 6),
        total_matches=request.total_matches,
        probability_streak_in_matches=round(prob_streak_in_matches, 6) if prob_streak_in_matches is not None else None
    )


@router.post(
    "/analyze/completed-rounds",
    response_model=CompletedRoundAnalysisResponse,
    summary="Analyze Completed Round Scores",
    description=(
        "Analyze completed round scores to calculate the probability of achieving "
        "those scores based on the golfer's handicap. Provides insights into "
        "performance quality and likelihood of each round."
    )
)
async def analyze_completed_rounds(
    request: CompletedRoundAnalysisRequest
) -> CompletedRoundAnalysisResponse:
    """
    Analyze completed round scores and calculate probability metrics.
    
    This endpoint allows you to input actual scores shot and calculates:
    - Probability of shooting each score or better
    - Z-scores and percentile rankings
    - Performance descriptors (e.g., "Excellent", "Average", etc.)
    - Overall tournament/day performance analysis
    - Joint probability of all scores
    """
    logger.info(
        f"Completed round analysis: golfer={request.golfer.name}, "
        f"handicap={request.golfer.handicap_index}, "
        f"num_rounds={len(request.completed_scores)}"
    )
    
    # Analyze each completed round
    round_analyses = []
    individual_probabilities = []
    total_strokes_from_expected = 0.0
    sum_actual_scores = 0.0
    
    for completed_round in request.completed_scores:
        actual_score = completed_round.gross_score
        holes_played = completed_round.holes_played
        
        # Compute expected score and standard deviation based on holes played
        if holes_played == 9:
            expected_score = compute_nine_hole_expected_score(
                request.golfer.handicap_index,
                request.course
            )
            sigma = estimate_nine_hole_score_std(request.golfer.handicap_index)
        else:
            expected_score = compute_expected_score(
                request.golfer.handicap_index,
                request.course
            )
            sigma = estimate_score_std(request.golfer.handicap_index)
        
        sum_actual_scores += actual_score
        strokes_from_expected = actual_score - expected_score
        total_strokes_from_expected += strokes_from_expected
        
        # Analyze the round
        z_score, prob_at_or_below, percentile, descriptor = analyze_completed_round(
            actual_score,
            expected_score,
            sigma
        )
        
        individual_probabilities.append(prob_at_or_below)
        
        round_analyses.append(RoundProbabilityAnalysis(
            round_number=completed_round.round_number,
            actual_score=actual_score,
            holes_played=holes_played,
            expected_score=round(expected_score, 2),
            strokes_from_expected=round(strokes_from_expected, 2),
            z_score=round(z_score, 4),
            probability_at_or_below=round(prob_at_or_below, 6),
            percentile=round(percentile, 2),
            performance_descriptor=descriptor
        ))
    
    # Calculate overall metrics
    num_rounds = len(request.completed_scores)
    average_actual_score = sum_actual_scores / num_rounds
    
    # For overall z-score, we need to compute average considering different sigmas
    # This is a simplified approach - using 18-hole metrics for the overall assessment
    overall_expected = compute_expected_score(
        request.golfer.handicap_index,
        request.course
    )
    overall_sigma = estimate_score_std(request.golfer.handicap_index)
    average_z_score = total_strokes_from_expected / (overall_sigma * num_rounds)
    
    # Compute joint probability (probability of all these scores happening)
    overall_probability = compute_joint_probability_independent_rounds(
        individual_probabilities
    )
    
    # Get overall performance descriptor
    overall_descriptor = get_overall_performance_descriptor(
        average_z_score,
        num_rounds
    )
    
    # Find best and worst rounds
    best_round = min(round_analyses, key=lambda x: x.actual_score)
    worst_round = max(round_analyses, key=lambda x: x.actual_score)
    
    logger.info(
        f"Analysis complete: avg_score={average_actual_score:.1f}, "
        f"expected={overall_expected:.1f}, overall_prob={overall_probability:.6f}"
    )
    
    return CompletedRoundAnalysisResponse(
        golfer_name=request.golfer.name,
        handicap_index=request.golfer.handicap_index,
        course_name=request.course.course_name,
        expected_score_per_round=round(overall_expected, 2),
        score_std=round(overall_sigma, 2),
        num_rounds_analyzed=num_rounds,
        round_analyses=round_analyses,
        average_actual_score=round(average_actual_score, 2),
        total_strokes_from_expected=round(total_strokes_from_expected, 2),
        overall_probability=round(overall_probability, 6),
        overall_performance_descriptor=overall_descriptor,
        best_round=best_round,
        worst_round=worst_round
    )


@router.post(
    "/analyze/sandbagging",
    response_model=SandbaggerAnalysisResponse,
    summary="Detect Potential Sandbagging",
    description=(
        "Analyze tournament scoring patterns to detect potential handicap manipulation (sandbagging). "
        "Identifies suspicious patterns like consistent over-performance, low volatility, and "
        "significant disparities between casual and competitive play."
    )
)
async def analyze_sandbagging(
    request: SandbaggerAnalysisRequest
) -> SandbaggerAnalysisResponse:
    """
    Comprehensive sandbagging detection analysis.
    
    Analyzes tournament scores for patterns that may indicate a golfer is
    intentionally inflating their handicap to gain competitive advantages.
    
    Key indicators detected:
    - Consistent over-performance in tournaments vs handicap
    - Unusually low score volatility (consistent excellence)
    - Statistically improbable performance combinations
    - Disparity between casual and tournament play (if provided)
    - Perfect or near-perfect tournament records
    """
    import statistics
    
    logger.info(
        f"Sandbagging analysis: golfer={request.golfer.name}, "
        f"handicap={request.golfer.handicap_index}, "
        f"num_tournament_rounds={len(request.tournament_scores)}"
    )
    
    # Analyze tournament scores
    tournament_scores = []
    tournament_probabilities = []
    strokes_from_expected_list = []
    
    for round_score in request.tournament_scores:
        # Get expected score for this round
        if round_score.holes_played == 9:
            expected = compute_nine_hole_expected_score(
                request.golfer.handicap_index,
                request.course
            )
            sigma = estimate_nine_hole_score_std(request.golfer.handicap_index)
        else:
            expected = compute_expected_score(
                request.golfer.handicap_index,
                request.course
            )
            sigma = estimate_score_std(request.golfer.handicap_index)
        
        actual = round_score.gross_score
        tournament_scores.append(actual)
        
        strokes_from_expected = actual - expected
        strokes_from_expected_list.append(strokes_from_expected)
        
        # Get probability
        z_score, prob, percentile, _ = analyze_completed_round(actual, expected, sigma)
        tournament_probabilities.append(prob)
    
    # Calculate tournament statistics
    tournament_avg = statistics.mean(tournament_scores)
    tournament_avg_vs_expected = statistics.mean(strokes_from_expected_list)
    tournament_percentile = statistics.mean([p * 100 for p in tournament_probabilities])
    tournament_volatility = statistics.stdev(tournament_scores) if len(tournament_scores) > 1 else 0.0
    
    # Expected volatility based on handicap
    expected_volatility = estimate_score_std(request.golfer.handicap_index)
    volatility_ratio = tournament_volatility / expected_volatility if expected_volatility > 0 else 1.0
    
    if volatility_ratio < 0.7:
        volatility_vs_expected = "LOW"
    elif volatility_ratio > 1.3:
        volatility_vs_expected = "HIGH"
    else:
        volatility_vs_expected = "NORMAL"
    
    # Joint probability of all tournament scores
    joint_prob = compute_joint_probability_independent_rounds(tournament_probabilities)
    
    # Detect red flags
    red_flags = []
    
    # Flag 1: Tournament excellence pattern
    flag = detect_tournament_excellence_pattern(
        tournament_avg_vs_expected,
        tournament_percentile,
        len(request.tournament_scores)
    )
    if flag:
        red_flags.append(flag)
    
    # Flag 2: Low volatility
    flag = detect_low_volatility_pattern(
        tournament_volatility,
        expected_volatility,
        volatility_ratio
    )
    if flag:
        red_flags.append(flag)
    
    # Flag 3: Improbable performance
    flag = detect_improbable_performance(
        joint_prob,
        len(request.tournament_scores)
    )
    if flag:
        red_flags.append(flag)
    
    # Flag 4: All scores better than expected
    flag = detect_all_scores_better_than_expected(strokes_from_expected_list)
    if flag:
        red_flags.append(flag)
    
    # Flag 5: Casual vs tournament disparity (if casual scores provided)
    has_casual_comparison = False
    casual_vs_tournament_diff = None
    
    if request.casual_scores:
        has_casual_comparison = True
        casual_scores = []
        casual_expected_list = []
        
        for round_score in request.casual_scores:
            if round_score.holes_played == 9:
                expected = compute_nine_hole_expected_score(
                    request.golfer.handicap_index,
                    request.course
                )
            else:
                expected = compute_expected_score(
                    request.golfer.handicap_index,
                    request.course
                )
            
            casual_scores.append(round_score.gross_score)
            casual_expected_list.append(expected)
        
        casual_avg = statistics.mean(casual_scores)
        casual_expected = statistics.mean(casual_expected_list)
        tournament_expected = compute_expected_score(
            request.golfer.handicap_index,
            request.course
        )
        
        casual_vs_tournament_diff = casual_avg - tournament_avg
        
        flag = detect_casual_vs_tournament_disparity(
            casual_avg,
            tournament_avg,
            casual_expected,
            tournament_expected,
            len(request.casual_scores),
            len(request.tournament_scores)
        )
        if flag:
            red_flags.append(flag)
    
    # Calculate risk score
    num_critical_flags = sum(1 for flag in red_flags if flag.severity == "CRITICAL")
    risk_score, risk_level = calculate_sandbagging_risk_score(
        tournament_avg_vs_expected,
        tournament_percentile,
        volatility_ratio,
        len(red_flags),
        num_critical_flags
    )
    
    # Generate summary and recommendation
    summary = generate_sandbagging_summary(
        risk_score,
        risk_level,
        tournament_avg_vs_expected,
        len(red_flags)
    )
    
    recommendation = generate_recommendation(risk_level, num_critical_flags)
    
    logger.info(
        f"Sandbagging analysis complete: risk_score={risk_score:.1f}, "
        f"risk_level={risk_level}, flags={len(red_flags)}"
    )
    
    return SandbaggerAnalysisResponse(
        golfer_name=request.golfer.name,
        handicap_index=request.golfer.handicap_index,
        sandbagging_risk_score=round(risk_score, 1),
        risk_level=risk_level,
        tournament_avg_score=round(tournament_avg, 2),
        tournament_avg_vs_expected=round(tournament_avg_vs_expected, 2),
        tournament_performance_percentile=round(tournament_percentile, 1),
        score_volatility=round(tournament_volatility, 2),
        volatility_vs_expected=volatility_vs_expected,
        red_flags=red_flags,
        has_casual_comparison=has_casual_comparison,
        casual_vs_tournament_diff=round(casual_vs_tournament_diff, 2) if casual_vs_tournament_diff else None,
        probability_all_tournament_scores=round(joint_prob, 8),
        summary=summary,
        recommendation=recommendation
    )
