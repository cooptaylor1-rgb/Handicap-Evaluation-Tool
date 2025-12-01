# Golf Scoring Probability Engine

A professional-grade backend (and simple web UI) for calculating golf scoring probabilities based on GHIN Handicap Index, course setup, and statistical models.

## Overview

This application helps golfers and tournament organizers answer questions like:

- "Given my handicap and this course, what's the probability I shoot X or better in one round?"
- "Over a 3-round tournament, what's the probability I shoot X or better at least once?"
- "What's my probability to break 100/90/85/80/75 on this course?"

For **team/member-guest best-ball** formats:
- "What's the probability our team net best-ball is X or better in a single round?"
- "What's the chance we have at least one great best-ball round over a 3-round event?"

## Features

- **Individual Player Probabilities**: Calculate single-round and multi-round probabilities based on handicap index and course setup
- **Team Best-Ball Simulation**: Monte Carlo simulation for 2-player team best-ball formats
- **Milestone Probabilities**: Automatic calculation of common milestone scores (break 100, 90, 85, 80, 75)
- **Conservative Assumptions**: Uses realistic scoring variability to avoid overstating odds of exceptional rounds
- **Simple Web UI**: Built-in browser-based testing interface
- **REST API**: Clean, documented API endpoints for mobile app integration

## Tech Stack

- **Python 3.12+** with type hints throughout
- **FastAPI** for the REST API framework
- **Pydantic** for request/response validation
- **SciPy** for statistical calculations
- **NumPy** for Monte Carlo simulations
- **pytest** for testing

## Project Structure

```
├── app/
│   ├── main.py           # FastAPI app initialization and routing
│   ├── config.py         # Configuration and environment variables
│   ├── models/           # Pydantic models
│   │   ├── golfer.py     # GolferProfile, CourseSetup, EventStructure
│   │   ├── team.py       # TeamProfile, BestBallTarget
│   │   └── requests.py   # API request/response models
│   ├── routes/           # API route definitions
│   │   ├── golf.py       # Individual player endpoints
│   │   └── team.py       # Team best-ball endpoints
│   ├── services/         # Business logic
│   │   ├── probability.py       # Individual probability calculations
│   │   └── team_probability.py  # Team simulation logic
│   └── static/           # Web UI files
│       └── index.html    # Browser-based testing interface
├── tests/                # Unit tests
├── requirements.txt      # Python dependencies
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/Handicap-Evaluation-Tool.git
cd Handicap-Evaluation-Tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

4. Open your browser to:
   - **Web UI**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc

### 📱 Mobile/iPhone Access

To use on your iPhone or mobile device:

```bash
./start_iphone.sh
```

Then on your iPhone:
1. Connect to the same Wi-Fi network
2. Open Safari and go to the displayed URL (e.g., `http://192.168.1.100:8000`)
3. Optional: Add to Home Screen for app-like experience

See [MOBILE_SETUP.md](MOBILE_SETUP.md) for detailed mobile instructions.

## API Endpoints

### Individual Player

#### POST /api/golf/probability/single-round
Calculate the probability of shooting at or below a target score in a single round.

**Request:**
```json
{
  "golfer": {"handicap_index": 15.0},
  "course": {
    "course_name": "My Local Course",
    "tee_name": "White",
    "par": 72,
    "course_rating": 72.5,
    "slope_rating": 130
  },
  "target": {"target_score": 85}
}
```

**Response:**
```json
{
  "expected_score": 89.76,
  "score_std": 3.5,
  "target_score": 85,
  "probability_score_at_or_below_target": 0.0892,
  "distribution_type": "normal_approximation",
  "z_score": -1.36
}
```

#### POST /api/golf/probability/multi-round
Calculate the probability of achieving a target score over multiple rounds.

**Request:**
```json
{
  "golfer": {"handicap_index": 15.0},
  "course": {...},
  "target": {"target_score": 85},
  "event": {"num_rounds": 3},
  "min_success_rounds": 1
}
```

**Response:**
```json
{
  "expected_score": 89.76,
  "score_std": 3.5,
  "target_score": 85,
  "num_rounds": 3,
  "min_success_rounds": 1,
  "probability_at_least_min_success_rounds": 0.2437,
  "probability_at_least_once": 0.2437,
  "single_round_probability": 0.0892,
  "binomial_model_used": true
}
```

#### POST /api/golf/probability/milestones
Calculate probabilities for standard milestone scores.

### Team Best-Ball

#### POST /api/golf/team/bestball/probability/single-round
Calculate team best-ball probability for a single round.

**Request:**
```json
{
  "team": {
    "player1": {"golfer": {"handicap_index": 12.0}},
    "player2": {"golfer": {"handicap_index": 8.0}}
  },
  "course": {
    "course_name": "Member-Guest Venue",
    "tee_name": "Blue",
    "par": 72,
    "course_rating": 73.5,
    "slope_rating": 135
  },
  "bestball_target": {
    "target_net_score": 63,
    "handicap_allowance_percent": 100.0
  },
  "num_simulations": 10000
}
```

#### POST /api/golf/team/bestball/probability/multi-round
Calculate team best-ball probability over multiple rounds.

## Mathematical Approach

### Individual Player Model

1. **Course Handicap**: `CH = handicap_index × (slope_rating / 113) + (course_rating - par)`
2. **Expected Score**: `expected = par + course_handicap`
3. **Score Distribution**: Normal distribution with conservative σ based on handicap:
   - ≤5 handicap: σ = 2.5
   - 5-10 handicap: σ = 3.0
   - 10-18 handicap: σ = 3.5
   - 18-28 handicap: σ = 4.0
   - >28 handicap: σ = 4.5
4. **Single-Round Probability**: Normal CDF with continuity correction
5. **Multi-Round Probability**: Binomial model for independent rounds

### Team Best-Ball Model

Uses **Monte Carlo simulation** at the round level:
1. Simulate gross scores for each player (Normal distribution)
2. Convert to net scores using course handicap with allowance
3. Team net best-ball = min(player1_net, player2_net)
4. Track success rates across simulations

**Note**: This is a round-level approximation, not hole-by-hole modeling. It provides reasonable estimates for tournament preparation.

## Mobile App Integration

This backend is designed to power a mobile app. Key considerations:

- All endpoints return JSON with clear, typed responses
- Probability values are normalized (0-1) for easy percentage display
- Approximation notes are included for transparency
- CORS is configured for development

Example mobile app architecture:
```
┌─────────────────┐     ┌─────────────────────┐
│  React Native   │────▶│  FastAPI Backend    │
│  or Flutter     │◀────│  (this project)     │
└─────────────────┘     └─────────────────────┘
```

## Running Tests

```bash
pytest tests/ -v
```

## Future Enhancements

- GHIN API integration for actual score history
- Hole-level modeling for more accurate best-ball
- 9-hole match formats
- Stableford scoring
- Weather/condition adjustments
- Historical performance tracking

## License

MIT License
