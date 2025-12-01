"""
Sandbagging detection service for identifying potential handicap manipulation.

This module implements algorithms to detect suspicious scoring patterns that may
indicate a golfer is intentionally inflating their handicap to gain competitive
advantages.
"""

import statistics
from typing import List, Tuple, Optional
from scipy import stats

from app.models.requests import SandbaggerRedFlag


def calculate_sandbagging_risk_score(
    tournament_avg_vs_expected: float,
    tournament_percentile: float,
    volatility_ratio: float,
    num_red_flags: int,
    critical_flags: int
) -> Tuple[float, str]:
    """
    Calculate overall sandbagging risk score (0-100) and risk level.
    
    Args:
        tournament_avg_vs_expected: Average strokes better than expected in tournaments
        tournament_percentile: Average percentile of tournament performances
        volatility_ratio: Ratio of actual to expected volatility
        num_red_flags: Total number of red flags detected
        critical_flags: Number of critical severity flags
    
    Returns:
        Tuple of (risk_score, risk_level)
    """
    risk_score = 0.0
    
    # Factor 1: Tournament performance (0-40 points)
    # Consistently performing better than expected is suspicious
    if tournament_avg_vs_expected < -2.0:  # More than 2 strokes better
        risk_score += 40
    elif tournament_avg_vs_expected < -1.0:
        risk_score += 30
    elif tournament_avg_vs_expected < -0.5:
        risk_score += 20
    elif tournament_avg_vs_expected < 0:
        risk_score += 10
    
    # Factor 2: Percentile performance (0-25 points)
    # Low percentile (playing better than expected) in tournaments
    if tournament_percentile < 5:
        risk_score += 25
    elif tournament_percentile < 15:
        risk_score += 20
    elif tournament_percentile < 25:
        risk_score += 15
    elif tournament_percentile < 40:
        risk_score += 10
    
    # Factor 3: Score volatility (0-20 points)
    # Low volatility suggests consistent "good" performances (suspicious)
    if volatility_ratio < 0.5:
        risk_score += 20
    elif volatility_ratio < 0.7:
        risk_score += 15
    elif volatility_ratio < 0.9:
        risk_score += 10
    
    # Factor 4: Red flags (0-15 points)
    risk_score += min(num_red_flags * 3, 15)
    
    # Critical flags add extra weight
    risk_score += critical_flags * 10
    
    # Cap at 100
    risk_score = min(risk_score, 100.0)
    
    # Determine risk level
    if risk_score >= 75:
        risk_level = "SEVERE"
    elif risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 25:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"
    
    return risk_score, risk_level


def detect_tournament_excellence_pattern(
    tournament_avg_vs_expected: float,
    tournament_percentile: float,
    num_tournaments: int
) -> Optional[SandbaggerRedFlag]:
    """
    Detect if golfer consistently outperforms handicap in tournaments.
    
    This is the #1 indicator of sandbagging - playing much better when it counts.
    """
    if tournament_avg_vs_expected >= -0.5:
        return None  # No issue
    
    # Calculate probability of this consistent performance
    z_score = tournament_avg_vs_expected
    prob_this_good = stats.norm.cdf(z_score)
    
    if tournament_avg_vs_expected <= -2.5 and tournament_percentile < 10:
        return SandbaggerRedFlag(
            flag_type="TOURNAMENT_EXCELLENCE",
            severity="CRITICAL",
            description="Exceptionally consistent tournament performance far exceeds handicap",
            evidence=f"Averages {abs(tournament_avg_vs_expected):.1f} strokes better than expected in {num_tournaments} tournaments (top {tournament_percentile:.1f}%)",
            probability_note=f"Probability of this consistent excellence: {prob_this_good*100:.2f}% - Highly unusual"
        )
    elif tournament_avg_vs_expected <= -1.5 and tournament_percentile < 20:
        return SandbaggerRedFlag(
            flag_type="TOURNAMENT_EXCELLENCE",
            severity="HIGH",
            description="Strong tournament performance consistently exceeds handicap",
            evidence=f"Averages {abs(tournament_avg_vs_expected):.1f} strokes better than expected in {num_tournaments} tournaments (top {tournament_percentile:.1f}%)",
            probability_note=f"Probability of this performance: {prob_this_good*100:.2f}%"
        )
    elif tournament_avg_vs_expected <= -1.0 and tournament_percentile < 30:
        return SandbaggerRedFlag(
            flag_type="TOURNAMENT_EXCELLENCE",
            severity="MEDIUM",
            description="Tournament performance notably better than expected",
            evidence=f"Averages {abs(tournament_avg_vs_expected):.1f} strokes better than expected in {num_tournaments} tournaments",
            probability_note=None
        )
    
    return None


def detect_low_volatility_pattern(
    actual_volatility: float,
    expected_volatility: float,
    volatility_ratio: float
) -> Optional[SandbaggerRedFlag]:
    """
    Detect suspiciously low score volatility.
    
    Sandbaggers often show unusually consistent "good" scoring in tournaments.
    """
    if volatility_ratio >= 0.7:
        return None  # Normal or high volatility
    
    if volatility_ratio < 0.5:
        return SandbaggerRedFlag(
            flag_type="LOW_VOLATILITY",
            severity="HIGH",
            description="Unusually consistent scoring pattern",
            evidence=f"Score volatility ({actual_volatility:.1f}) is {(1-volatility_ratio)*100:.0f}% lower than expected ({expected_volatility:.1f})",
            probability_note="Consistent excellence suggests possible handicap inflation"
        )
    elif volatility_ratio < 0.7:
        return SandbaggerRedFlag(
            flag_type="LOW_VOLATILITY",
            severity="MEDIUM",
            description="Lower than expected scoring variance",
            evidence=f"Score volatility ({actual_volatility:.1f}) is {(1-volatility_ratio)*100:.0f}% lower than expected ({expected_volatility:.1f})",
            probability_note=None
        )
    
    return None


def detect_improbable_performance(
    joint_probability: float,
    num_rounds: int
) -> Optional[SandbaggerRedFlag]:
    """
    Detect if the combination of all tournament scores is statistically improbable.
    """
    if joint_probability > 0.01:  # More than 1% probability
        return None
    
    if joint_probability < 0.0001:  # Less than 0.01%
        return SandbaggerRedFlag(
            flag_type="IMPROBABLE_CONSISTENCY",
            severity="CRITICAL",
            description="Statistically improbable consistent excellence",
            evidence=f"Combined probability of all {num_rounds} tournament performances: {joint_probability*100:.4f}%",
            probability_note="This level of consistent excellence is extremely rare - less than 1 in 10,000 golfers"
        )
    elif joint_probability < 0.001:  # Less than 0.1%
        return SandbaggerRedFlag(
            flag_type="IMPROBABLE_CONSISTENCY",
            severity="HIGH",
            description="Highly improbable performance consistency",
            evidence=f"Combined probability of all {num_rounds} tournament performances: {joint_probability*100:.3f}%",
            probability_note="This level of excellence is very rare"
        )
    elif joint_probability < 0.01:  # Less than 1%
        return SandbaggerRedFlag(
            flag_type="IMPROBABLE_CONSISTENCY",
            severity="MEDIUM",
            description="Unlikely performance consistency",
            evidence=f"Combined probability of all {num_rounds} tournament performances: {joint_probability*100:.2f}%",
            probability_note=None
        )
    
    return None


def detect_casual_vs_tournament_disparity(
    casual_avg: float,
    tournament_avg: float,
    casual_expected: float,
    tournament_expected: float,
    num_casual: int,
    num_tournaments: int
) -> Optional[SandbaggerRedFlag]:
    """
    Detect significant performance difference between casual and tournament rounds.
    
    Classic sandbagging: play poorly in casual rounds to inflate handicap,
    then play much better in tournaments.
    """
    # Calculate performance vs expected for each
    casual_vs_expected = casual_avg - casual_expected
    tournament_vs_expected = tournament_avg - tournament_expected
    
    # The disparity: if casual rounds are worse than expected but tournaments are better
    disparity = casual_vs_expected - tournament_vs_expected
    
    if disparity < 2.0:
        return None  # Not enough disparity
    
    if disparity >= 5.0:
        return SandbaggerRedFlag(
            flag_type="CASUAL_TOURNAMENT_DISPARITY",
            severity="CRITICAL",
            description="Major performance disparity between casual and tournament play",
            evidence=f"Casual rounds avg {casual_vs_expected:+.1f} vs expected, tournaments {tournament_vs_expected:+.1f} vs expected (difference: {disparity:.1f} strokes)",
            probability_note=f"Based on {num_casual} casual rounds and {num_tournaments} tournament rounds"
        )
    elif disparity >= 3.5:
        return SandbaggerRedFlag(
            flag_type="CASUAL_TOURNAMENT_DISPARITY",
            severity="HIGH",
            description="Significant performance difference between casual and competitive rounds",
            evidence=f"Casual rounds avg {casual_vs_expected:+.1f} vs expected, tournaments {tournament_vs_expected:+.1f} vs expected (difference: {disparity:.1f} strokes)",
            probability_note=f"Based on {num_casual} casual rounds and {num_tournaments} tournament rounds"
        )
    elif disparity >= 2.0:
        return SandbaggerRedFlag(
            flag_type="CASUAL_TOURNAMENT_DISPARITY",
            severity="MEDIUM",
            description="Notable performance variance between casual and tournament play",
            evidence=f"Performance {disparity:.1f} strokes better in tournaments than casual rounds",
            probability_note=None
        )
    
    return None


def detect_all_scores_better_than_expected(
    scores_vs_expected: List[float]
) -> Optional[SandbaggerRedFlag]:
    """
    Detect if ALL tournament scores are better than expected.
    
    While possible, having every tournament round beat your handicap is suspicious.
    """
    if not scores_vs_expected:
        return None
    
    all_better = all(score < 0 for score in scores_vs_expected)
    
    if not all_better:
        return None
    
    num_rounds = len(scores_vs_expected)
    avg_better = statistics.mean(scores_vs_expected)
    
    # Probability of ALL rounds being better than expected
    # (assuming 50% chance normally)
    prob = 0.5 ** num_rounds
    
    if num_rounds >= 5:
        return SandbaggerRedFlag(
            flag_type="PERFECT_TOURNAMENT_RECORD",
            severity="HIGH",
            description=f"Every single tournament round ({num_rounds}) exceeded expectations",
            evidence=f"All {num_rounds} rounds beat expected score by average of {abs(avg_better):.1f} strokes",
            probability_note=f"Probability of this: {prob*100:.3f}% (1 in {int(1/prob):,})"
        )
    elif num_rounds >= 3:
        return SandbaggerRedFlag(
            flag_type="PERFECT_TOURNAMENT_RECORD",
            severity="MEDIUM",
            description=f"All {num_rounds} tournament rounds exceeded expectations",
            evidence=f"Perfect record of beating expected score",
            probability_note=None
        )
    
    return None


def generate_sandbagging_summary(
    risk_score: float,
    risk_level: str,
    tournament_avg_vs_expected: float,
    num_red_flags: int
) -> str:
    """Generate human-readable summary of sandbagging analysis."""
    if risk_level == "SEVERE":
        return (
            f"⚠️ SEVERE SANDBAGGING RISK: Multiple critical indicators suggest this handicap "
            f"may be significantly inflated. Tournament performance averaging "
            f"{abs(tournament_avg_vs_expected):.1f} strokes better than handicap predicts "
            f"is highly suspicious."
        )
    elif risk_level == "HIGH":
        return (
            f"🚩 HIGH SANDBAGGING RISK: Several concerning patterns detected. "
            f"Golfer consistently outperforms their handicap in tournaments "
            f"(avg {abs(tournament_avg_vs_expected):.1f} strokes better than expected). "
            f"Further investigation recommended."
        )
    elif risk_level == "MODERATE":
        return (
            f"⚡ MODERATE RISK: Some indicators suggest potential sandbagging. "
            f"Tournament performance is {abs(tournament_avg_vs_expected):.1f} strokes "
            f"better than expected. Monitor for continued patterns."
        )
    else:
        return (
            f"✅ LOW RISK: Performance appears consistent with stated handicap. "
            f"No significant sandbagging indicators detected."
        )


def generate_recommendation(
    risk_level: str,
    num_critical_flags: int
) -> str:
    """Generate recommendation based on risk assessment."""
    if risk_level == "SEVERE":
        return (
            "RECOMMENDED ACTION: Handicap committee review strongly recommended. "
            "Consider requiring handicap verification or adjustment. "
            "This golfer should be monitored closely in future competitions."
        )
    elif risk_level == "HIGH":
        return (
            "RECOMMENDED ACTION: Investigation warranted. Request additional score history "
            "and consider informal discussion with golfer. Monitor performance in upcoming events."
        )
    elif risk_level == "MODERATE":
        return (
            "RECOMMENDED ACTION: Continue monitoring. If pattern persists over next 3-5 rounds, "
            "consider deeper investigation. Golfer may simply be improving or having a hot streak."
        )
    else:
        return (
            "RECOMMENDED ACTION: No action needed. Performance is consistent with handicap. "
            "Continue normal monitoring procedures."
        )
