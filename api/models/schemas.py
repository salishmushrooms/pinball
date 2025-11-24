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
    ipdb_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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
    home_venue_key: str
    season: int


class TeamDetail(TeamBase):
    """Detailed team information"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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


# Error Models
class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
