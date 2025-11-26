"""
Pydantic models for API request/response schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# Player Models
class PlayerBase(BaseModel):
    """Base player information"""
    player_key: str
    name: str
    current_ipr: Optional[float] = None
    first_seen_season: int
    last_seen_season: int


class PlayerDetail(PlayerBase):
    """Detailed player information"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlayerList(BaseModel):
    """List of players with pagination info"""
    players: List[PlayerBase]
    total: int
    limit: int
    offset: int


# Machine Models
class MachineBase(BaseModel):
    """Base machine information"""
    machine_key: str
    machine_name: str
    manufacturer: Optional[str] = None
    year: Optional[int] = None
    game_type: Optional[str] = None


class MachineDetail(MachineBase):
    """Detailed machine information"""
    total_scores: int = Field(0, description="Total number of scores recorded")
    unique_players: int = Field(0, description="Number of unique players")
    median_score: int = Field(0, description="Median score")
    max_score: int = Field(0, description="Maximum score recorded")

    class Config:
        from_attributes = True


class MachineList(BaseModel):
    """List of machines with pagination info"""
    machines: List[MachineBase]
    total: int
    limit: int
    offset: int


# Score Percentile Models
class ScorePercentile(BaseModel):
    """Score percentile for a machine"""
    machine_key: str
    machine_name: Optional[str] = None
    venue_key: Optional[str] = None
    percentile: int = Field(..., ge=0, le=100, description="Percentile value (0-100)")
    score_threshold: int = Field(..., description="Score at this percentile")
    sample_size: int = Field(..., gt=0, description="Number of scores used to calculate percentile")
    season: int

    class Config:
        from_attributes = True


class MachinePercentiles(BaseModel):
    """All percentiles for a machine"""
    machine_key: str
    machine_name: str
    venue_key: str
    season: int
    sample_size: int
    percentiles: dict[int, int] = Field(..., description="Map of percentile -> score")


# Player Machine Stats Models
class PlayerMachineStats(BaseModel):
    """Player statistics for a specific machine"""
    player_key: str
    player_name: Optional[str] = None
    machine_key: str
    machine_name: Optional[str] = None
    venue_key: str
    season: int
    games_played: int = Field(..., gt=0)
    total_score: int
    median_score: Optional[int] = None
    avg_score: Optional[int] = None
    best_score: Optional[int] = None
    worst_score: Optional[int] = None
    median_percentile: Optional[float] = Field(None, ge=0, le=100)
    avg_percentile: Optional[float] = Field(None, ge=0, le=100)
    win_percentage: Optional[float] = Field(None, ge=0, le=100, description="Percentage of head-to-head wins vs opponents")

    class Config:
        from_attributes = True


class PlayerMachineStatsList(BaseModel):
    """List of player machine stats"""
    stats: List[PlayerMachineStats]
    total: int
    limit: int
    offset: int


# Team Models
class TeamBase(BaseModel):
    """Base team information"""
    team_key: str
    team_name: str
    home_venue_key: Optional[str] = None
    season: int


class TeamDetail(TeamBase):
    """Detailed team information"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TeamList(BaseModel):
    """List of teams with pagination info"""
    teams: List[TeamBase]
    total: int
    limit: int
    offset: int


# Venue Models
class VenueBase(BaseModel):
    """Base venue information"""
    venue_key: str
    venue_name: str
    city: Optional[str] = None
    state: Optional[str] = None


class VenueDetail(VenueBase):
    """Detailed venue information"""
    address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VenueList(BaseModel):
    """List of venues with pagination info"""
    venues: List[VenueBase]
    total: int
    limit: int
    offset: int


class VenueMachineStats(BaseModel):
    """Machine statistics at a specific venue"""
    machine_key: str
    machine_name: str
    manufacturer: Optional[str] = None
    year: Optional[int] = None
    venue_key: str
    venue_name: str
    total_scores: int
    unique_players: int
    median_score: int
    max_score: int
    min_score: int
    avg_score: int
    is_current: Optional[bool] = Field(None, description="Whether this machine is currently at the venue")

    class Config:
        from_attributes = True


# Match Models
class MatchBase(BaseModel):
    """Base match information"""
    match_key: str
    season: int
    week: int
    home_team_key: str
    away_team_key: str
    venue_key: str
    match_date: Optional[datetime] = None


class MatchDetail(MatchBase):
    """Detailed match information"""
    home_points: Optional[int] = None
    away_points: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Score Models
class MachineScore(BaseModel):
    """Individual score for a machine"""
    score_id: int
    score: int
    player_key: str
    player_name: Optional[str] = None
    venue_key: str
    venue_name: Optional[str] = None
    season: int
    week: int
    round_number: int
    match_key: str
    date: Optional[datetime] = None
    player_position: int
    team_key: str

    class Config:
        from_attributes = True


class MachineScoreList(BaseModel):
    """List of machine scores with pagination"""
    scores: List[MachineScore]
    total: int
    limit: int
    offset: int


# Matchup Models
class ConfidenceInterval(BaseModel):
    """Confidence interval for a score prediction"""
    mean: float
    std_dev: float
    lower_bound: float
    upper_bound: float
    sample_size: int
    confidence_level: float = 95.0


class PlayerMachineConfidence(BaseModel):
    """Player's expected performance on a machine with confidence interval"""
    player_key: str
    player_name: str
    machine_key: str
    machine_name: str
    confidence_interval: Optional[ConfidenceInterval] = None
    insufficient_data: bool = False
    message: Optional[str] = None


class TeamMachineConfidence(BaseModel):
    """Team's expected performance on a machine with confidence interval"""
    team_key: str
    team_name: str
    machine_key: str
    machine_name: str
    confidence_interval: Optional[ConfidenceInterval] = None
    insufficient_data: bool = False
    message: Optional[str] = None


class MachinePickFrequency(BaseModel):
    """Machine pick frequency for a team"""
    machine_key: str
    machine_name: str
    times_picked: int
    total_opportunities: int
    pick_percentage: float


class PlayerMachinePreference(BaseModel):
    """Player's machine picking preferences"""
    player_key: str
    player_name: str
    top_machines: List[MachinePickFrequency]


class MatchupAnalysis(BaseModel):
    """Complete matchup analysis between two teams at a venue"""
    home_team_key: str
    home_team_name: str
    away_team_key: str
    away_team_name: str
    venue_key: str
    venue_name: str
    season: int

    # Available machines at venue
    available_machines: List[str]

    # Team machine pick frequency (limited to available machines)
    home_team_pick_frequency: List[MachinePickFrequency]
    away_team_pick_frequency: List[MachinePickFrequency]

    # Player machine preferences (limited to available machines)
    home_team_player_preferences: List[PlayerMachinePreference]
    away_team_player_preferences: List[PlayerMachinePreference]

    # Player-specific confidence intervals
    home_team_player_confidence: List[PlayerMachineConfidence]
    away_team_player_confidence: List[PlayerMachineConfidence]

    # Team-level confidence intervals (aggregate of all players)
    home_team_machine_confidence: List[TeamMachineConfidence]
    away_team_machine_confidence: List[TeamMachineConfidence]


# Team Machine Stats Models
class TeamMachineStats(BaseModel):
    """Team statistics for a specific machine"""
    team_key: str
    team_name: Optional[str] = None
    machine_key: str
    machine_name: Optional[str] = None
    venue_key: Optional[str] = None
    season: Optional[int] = None
    games_played: int = Field(..., gt=0)
    total_score: int
    median_score: Optional[int] = None
    avg_score: Optional[int] = None
    best_score: Optional[int] = None
    worst_score: Optional[int] = None
    median_percentile: Optional[float] = Field(None, ge=0, le=100)
    avg_percentile: Optional[float] = Field(None, ge=0, le=100)
    win_percentage: Optional[float] = Field(None, ge=0, le=100, description="Percentage of head-to-head wins vs opponents")
    rounds_played: Optional[List[int]] = Field(None, description="List of rounds played (1-4)")

    class Config:
        from_attributes = True


class TeamMachineStatsList(BaseModel):
    """List of team machine stats"""
    stats: List[TeamMachineStats]
    total: int
    limit: int
    offset: int


class TeamPlayer(BaseModel):
    """Player roster information for a team"""
    player_key: str
    player_name: str
    current_ipr: Optional[float] = None
    games_played: int
    win_percentage: Optional[float] = Field(None, ge=0, le=100)
    most_played_machine_key: Optional[str] = None
    most_played_machine_name: Optional[str] = None
    most_played_machine_games: Optional[int] = None
    seasons_played: List[int]

    class Config:
        from_attributes = True


class TeamPlayerList(BaseModel):
    """List of team players with stats"""
    players: List[TeamPlayer]
    total: int


# Error Models
class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
