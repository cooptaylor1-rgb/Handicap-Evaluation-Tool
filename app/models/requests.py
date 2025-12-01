"""Request and response models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, Literal

from .golfer import GolferProfile, CourseSetup, ScoringTarget, EventStructure
from .team import TeamProfile, BestBallTarget, TeamEventStructure


# ============================================================================
# Individual Player Request/Response Models
# ============================================================================

class SingleRoundProbabilityRequest(BaseModel):
    """Request model for single-round probability calculation."""
    golfer: GolferProfile
    course: CourseSetup
    target: ScoringTarget
    holes_played: Literal[9, 18] = Field(
        default=18,
        description="Number of holes played (9 or 18)"
    )


class SingleRoundProbabilityResponse(BaseModel):
    """Response model for single-round probability calculation."""
    expected_score: float = Field(
        ..., 
        description="Expected gross score based on handicap and course setup"
    )
    score_std: float = Field(
        ..., 
        description="Standard deviation of score distribution"
    )
    target_score: int = Field(
        ..., 
        description="Target score threshold"
    )
    probability_score_at_or_below_target: float = Field(
        ..., 
        description="Probability of shooting target score or better (0-1)",
        ge=0.0,
        le=1.0
    )
    distribution_type: str = Field(
        default="normal_approximation", 
        description="Type of distribution used for calculation"
    )
    z_score: Optional[float] = Field(
        None, 
        description=(
            "Z-score used in normal distribution calculation. "
            "Negative values indicate target is above expected score (harder to achieve), "
            "positive values indicate target is below expected score (easier to achieve)."
        )
    )


class MultiRoundProbabilityRequest(BaseModel):
    """Request model for multi-round probability calculation."""
    golfer: GolferProfile
    course: CourseSetup
    target: ScoringTarget
    event: EventStructure
    min_success_rounds: int = Field(
        default=1, 
        description="Minimum number of rounds to achieve target score",
        ge=1
    )
    holes_played: Literal[9, 18] = Field(
        default=18,
        description="Number of holes played per round (9 or 18)"
    )


class MultiRoundProbabilityResponse(BaseModel):
    """Response model for multi-round probability calculation."""
    expected_score: float = Field(
        ..., 
        description="Expected gross score per round"
    )
    score_std: float = Field(
        ..., 
        description="Standard deviation of score distribution"
    )
    target_score: int = Field(
        ..., 
        description="Target score threshold"
    )
    num_rounds: int = Field(
        ..., 
        description="Number of rounds in the event"
    )
    min_success_rounds: int = Field(
        ..., 
        description="Minimum success rounds required"
    )
    probability_at_least_min_success_rounds: float = Field(
        ..., 
        description="Probability of achieving target in at least min_success_rounds",
        ge=0.0,
        le=1.0
    )
    probability_at_least_once: float = Field(
        ..., 
        description="Probability of achieving target at least once",
        ge=0.0,
        le=1.0
    )
    single_round_probability: float = Field(
        ..., 
        description="Probability of achieving target in a single round",
        ge=0.0,
        le=1.0
    )
    binomial_model_used: bool = Field(
        default=True, 
        description="Whether binomial model was used for multi-round calculation"
    )


class MilestoneResult(BaseModel):
    """Result for a single milestone score."""
    target_score: int = Field(
        ..., 
        description="Target score for this milestone"
    )
    prob_single_round_at_or_below: float = Field(
        ..., 
        description="Probability of achieving this score in a single round",
        ge=0.0,
        le=1.0
    )
    prob_at_least_once_in_event: float = Field(
        ..., 
        description="Probability of achieving this score at least once in the event",
        ge=0.0,
        le=1.0
    )


class MilestoneProbabilityRequest(BaseModel):
    """Request model for milestone probability calculation."""
    golfer: GolferProfile
    course: CourseSetup
    event: EventStructure
    holes_played: Literal[9, 18] = Field(
        default=18,
        description="Number of holes played per round (9 or 18)"
    )


class MilestoneProbabilityResponse(BaseModel):
    """Response model for milestone probability calculation."""
    expected_score: float = Field(
        ..., 
        description="Expected gross score per round"
    )
    score_std: float = Field(
        ..., 
        description="Standard deviation of score distribution"
    )
    num_rounds: int = Field(
        ..., 
        description="Number of rounds in the event"
    )
    milestones: list[MilestoneResult] = Field(
        ..., 
        description="Probability results for each milestone score"
    )


# ============================================================================
# Team Best-Ball Request/Response Models
# ============================================================================

class TeamBestBallSingleRoundRequest(BaseModel):
    """Request model for single-round team best-ball probability."""
    team: TeamProfile
    course: CourseSetup
    bestball_target: BestBallTarget
    num_simulations: int = Field(
        default=10000, 
        description="Number of Monte Carlo simulations to run",
        ge=1000,
        le=1000000
    )


class TeamBestBallSingleRoundResponse(BaseModel):
    """Response model for single-round team best-ball probability."""
    target_net_score: int = Field(
        ..., 
        description="Target net best-ball score"
    )
    handicap_allowance_percent: float = Field(
        ..., 
        description="Handicap allowance percentage applied"
    )
    expected_team_bestball_score_single_round: float = Field(
        ..., 
        description="Expected team net best-ball score for a single round"
    )
    std_team_bestball_score_single_round: float = Field(
        ..., 
        description="Standard deviation of team net best-ball score"
    )
    probability_net_bestball_at_or_below_target_single_round: float = Field(
        ..., 
        description="Probability of achieving target net best-ball score in a single round",
        ge=0.0,
        le=1.0
    )
    num_simulations_used: int = Field(
        ..., 
        description="Number of simulations used in calculation"
    )
    approximation_notes: str = Field(
        default="Team best-ball modeled as min of two independent net round scores (round-level approximation)",
        description="Notes about the approximation method used"
    )


class TeamBestBallMultiRoundRequest(BaseModel):
    """Request model for multi-round team best-ball probability."""
    team: TeamProfile
    course: CourseSetup
    bestball_target: BestBallTarget
    event: TeamEventStructure
    min_success_rounds: int = Field(
        default=1, 
        description="Minimum number of rounds to achieve target score",
        ge=1
    )
    num_simulations: int = Field(
        default=10000, 
        description="Number of Monte Carlo simulations to run",
        ge=1000,
        le=1000000
    )


class TeamBestBallMultiRoundResponse(BaseModel):
    """Response model for multi-round team best-ball probability."""
    target_net_score: int = Field(
        ..., 
        description="Target net best-ball score"
    )
    handicap_allowance_percent: float = Field(
        ..., 
        description="Handicap allowance percentage applied"
    )
    num_rounds: int = Field(
        ..., 
        description="Number of rounds in the event"
    )
    min_success_rounds: int = Field(
        ..., 
        description="Minimum success rounds required"
    )
    probability_net_bestball_at_or_below_target_single_round: float = Field(
        ..., 
        description="Probability of achieving target in a single round",
        ge=0.0,
        le=1.0
    )
    probability_at_least_once_in_event: float = Field(
        ..., 
        description="Probability of achieving target at least once in the event",
        ge=0.0,
        le=1.0
    )
    probability_at_least_min_success_rounds: float = Field(
        ..., 
        description="Probability of achieving target in at least min_success_rounds",
        ge=0.0,
        le=1.0
    )
    expected_team_bestball_score_single_round: float = Field(
        ..., 
        description="Expected team net best-ball score for a single round"
    )
    std_team_bestball_score_single_round: float = Field(
        ..., 
        description="Standard deviation of team net best-ball score"
    )
    num_simulations_used: int = Field(
        ..., 
        description="Number of simulations used in calculation"
    )
    approximation_notes: str = Field(
        default="Team best-ball modeled as min of two independent net round scores (round-level approximation)",
        description="Notes about the approximation method used"
    )


# ============================================================================
# Consecutive Scores Request/Response Models
# ============================================================================

class ConsecutiveScoresProbabilityRequest(BaseModel):
    """Request model for consecutive scores probability calculation."""
    golfer: GolferProfile
    course: CourseSetup
    target: ScoringTarget
    consecutive_count: int = Field(
        ..., 
        description="Number of consecutive rounds to achieve target score",
        ge=1,
        le=20
    )
    total_matches: Optional[int] = Field(
        None, 
        description="Total number of matches to play (if specified, calculates probability of achieving streak within these matches)",
        ge=1,
        le=100
    )
    holes_per_round: Literal[9, 18] = Field(
        default=18,
        description="Number of holes per round (9 or 18)"
    )


class ConsecutiveScoresProbabilityResponse(BaseModel):
    """Response model for consecutive scores probability calculation."""
    expected_score: float = Field(
        ..., 
        description="Expected gross score per round"
    )
    score_std: float = Field(
        ..., 
        description="Standard deviation of score distribution"
    )
    target_score: int = Field(
        ..., 
        description="Target score threshold"
    )
    consecutive_count: int = Field(
        ..., 
        description="Number of consecutive rounds required"
    )
    holes_per_round: int = Field(
        ...,
        description="Number of holes per round (9 or 18)"
    )
    single_round_probability: float = Field(
        ..., 
        description="Probability of achieving target in a single round",
        ge=0.0,
        le=1.0
    )
    probability_all_consecutive: float = Field(
        ..., 
        description="Probability of achieving target in ALL consecutive rounds",
        ge=0.0,
        le=1.0
    )
    total_matches: Optional[int] = Field(
        None, 
        description="Total number of matches (if specified)"
    )
    probability_streak_in_matches: Optional[float] = Field(
        None, 
        description="Probability of achieving at least one streak within total matches",
        ge=0.0,
        le=1.0
    )


# ============================================================================
# Completed Round Score Analysis Models
# ============================================================================

class CompletedRoundScore(BaseModel):
    """Model for a single completed round score."""
    round_number: int = Field(
        ...,
        description="Round number in the tournament/day",
        ge=1
    )
    gross_score: int = Field(
        ...,
        description="Actual gross score shot",
        ge=25,
        le=200
    )
    holes_played: Literal[9, 18] = Field(
        default=18,
        description="Number of holes played (9 or 18)"
    )
    round_date: Optional[str] = Field(
        None,
        description="Date of the round (YYYY-MM-DD format)"
    )
    notes: Optional[str] = Field(
        None,
        description="Optional notes about the round"
    )


class CompletedRoundAnalysisRequest(BaseModel):
    """Request model for analyzing completed round scores."""
    golfer: GolferProfile
    course: CourseSetup
    completed_scores: list[CompletedRoundScore] = Field(
        ...,
        description="List of completed round scores to analyze",
        min_length=1
    )


class RoundProbabilityAnalysis(BaseModel):
    """Probability analysis for a single completed round."""
    round_number: int = Field(
        ...,
        description="Round number"
    )
    actual_score: int = Field(
        ...,
        description="Actual score shot"
    )
    holes_played: int = Field(
        ...,
        description="Number of holes played (9 or 18)"
    )
    expected_score: float = Field(
        ...,
        description="Expected score based on handicap"
    )
    strokes_from_expected: float = Field(
        ...,
        description="Difference from expected (negative = better than expected)"
    )
    z_score: float = Field(
        ...,
        description="Z-score for this performance"
    )
    probability_at_or_below: float = Field(
        ...,
        description="Probability of shooting this score or better",
        ge=0.0,
        le=1.0
    )
    percentile: float = Field(
        ...,
        description="Percentile ranking of this round (0-100)",
        ge=0.0,
        le=100.0
    )
    performance_descriptor: str = Field(
        ...,
        description="Human-readable description of performance level"
    )


class CompletedRoundAnalysisResponse(BaseModel):
    """Response model for completed round score analysis."""
    golfer_name: str = Field(
        ...,
        description="Name of the golfer"
    )
    handicap_index: float = Field(
        ...,
        description="Golfer's handicap index"
    )
    course_name: str = Field(
        ...,
        description="Course name"
    )
    expected_score_per_round: float = Field(
        ...,
        description="Expected score for a single round"
    )
    score_std: float = Field(
        ...,
        description="Standard deviation of scoring"
    )
    num_rounds_analyzed: int = Field(
        ...,
        description="Number of rounds analyzed"
    )
    round_analyses: list[RoundProbabilityAnalysis] = Field(
        ...,
        description="Individual round probability analyses"
    )
    average_actual_score: float = Field(
        ...,
        description="Average of all actual scores"
    )
    total_strokes_from_expected: float = Field(
        ...,
        description="Total strokes above/below expected (negative = better)"
    )
    overall_probability: float = Field(
        ...,
        description="Joint probability of achieving all these scores or better",
        ge=0.0,
        le=1.0
    )
    overall_performance_descriptor: str = Field(
        ...,
        description="Overall performance assessment"
    )
    best_round: RoundProbabilityAnalysis = Field(
        ...,
        description="Best round from the set"
    )
    worst_round: RoundProbabilityAnalysis = Field(
        ...,
        description="Worst round from the set"
    )


# ============================================================================
# Sandbagging Detection Models
# ============================================================================

class SandbaggerRedFlag(BaseModel):
    """Individual red flag indicator for potential sandbagging."""
    flag_type: str = Field(
        ...,
        description="Type of red flag (e.g., 'TOURNAMENT_PERFORMANCE', 'SCORE_VOLATILITY')"
    )
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        ...,
        description="Severity level of the red flag"
    )
    description: str = Field(
        ...,
        description="Human-readable description of the issue"
    )
    evidence: str = Field(
        ...,
        description="Specific evidence supporting this flag"
    )
    probability_note: Optional[str] = Field(
        None,
        description="Statistical probability context if applicable"
    )


class SandbaggerAnalysisRequest(BaseModel):
    """Request model for sandbagging analysis."""
    golfer: GolferProfile
    course: CourseSetup
    tournament_scores: list[CompletedRoundScore] = Field(
        ...,
        description="Scores from competitive/tournament rounds",
        min_length=1
    )
    casual_scores: Optional[list[CompletedRoundScore]] = Field(
        None,
        description="Optional: Scores from casual rounds for comparison"
    )


class SandbaggerAnalysisResponse(BaseModel):
    """Response model for sandbagging analysis."""
    golfer_name: str = Field(
        ...,
        description="Name of the golfer being analyzed"
    )
    handicap_index: float = Field(
        ...,
        description="Current handicap index"
    )
    
    # Risk Assessment
    sandbagging_risk_score: float = Field(
        ...,
        description="Overall risk score (0-100, higher = more suspicious)",
        ge=0.0,
        le=100.0
    )
    risk_level: Literal["LOW", "MODERATE", "HIGH", "SEVERE"] = Field(
        ...,
        description="Overall risk level classification"
    )
    
    # Tournament Performance Analysis
    tournament_avg_score: float = Field(
        ...,
        description="Average score in tournament rounds"
    )
    tournament_avg_vs_expected: float = Field(
        ...,
        description="Average strokes better/worse than expected in tournaments"
    )
    tournament_performance_percentile: float = Field(
        ...,
        description="Average percentile of tournament performances (0-100)"
    )
    
    # Consistency Analysis
    score_volatility: float = Field(
        ...,
        description="Standard deviation of tournament scores"
    )
    volatility_vs_expected: str = Field(
        ...,
        description="Comparison of actual volatility to expected (NORMAL, LOW, HIGH)"
    )
    
    # Pattern Detection
    red_flags: list[SandbaggerRedFlag] = Field(
        ...,
        description="List of suspicious patterns detected"
    )
    
    # Comparative Analysis (if casual scores provided)
    has_casual_comparison: bool = Field(
        default=False,
        description="Whether casual round comparison was performed"
    )
    casual_vs_tournament_diff: Optional[float] = Field(
        None,
        description="Average score difference (casual - tournament)"
    )
    
    # Statistical Evidence
    probability_all_tournament_scores: float = Field(
        ...,
        description="Joint probability of all tournament scores",
        ge=0.0,
        le=1.0
    )
    
    # Summary and Recommendations
    summary: str = Field(
        ...,
        description="Overall assessment summary"
    )
    recommendation: str = Field(
        ...,
        description="Recommended action or conclusion"
    )
