"""
Pydantic models for API request/response schemas
"""
from typing import Optional, List, Union, Dict
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
    current_team_key: Optional[str] = Field(None, description="Team key for most recent season")
    current_team_name: Optional[str] = Field(None, description="Team name for most recent season")

    class Config:
        from_attributes = True


class PlayerList(BaseModel):
    """List of players with pagination info"""
    players: List[PlayerBase]
    total: int
    limit: int
    offset: int


class IPRDistribution(BaseModel):
    """Count of players by IPR level"""
    ipr_level: int = Field(..., description="IPR level (1-6)")
    count: int = Field(..., description="Number of players at this level")


class PlayerHighlight(BaseModel):
    """Featured player with highlight stats"""
    player_key: str
    player_name: str
    team_key: Optional[str] = None
    team_name: Optional[str] = None
    venue_key: Optional[str] = None
    venue_name: Optional[str] = None
    ipr: Optional[float] = None
    season: int = Field(..., description="Season for the highlight stats")
    best_machine_key: str = Field(..., description="Machine with highest percentile score")
    best_machine_name: str = Field(..., description="Name of the best machine")
    best_score: int = Field(..., description="The score achieved")
    best_percentile: float = Field(..., description="Percentile ranking of the score")


class PlayerDashboardStats(BaseModel):
    """Dashboard statistics for players page"""
    total_players: int
    ipr_distribution: List[IPRDistribution]
    new_players_count: int = Field(..., description="Players first seen in latest season")
    latest_season: int = Field(..., description="The latest season number")
    player_highlights: List[PlayerHighlight] = Field(default_factory=list, description="Featured players with highlight stats")


# Machine Models
class MachineBase(BaseModel):
    """Base machine information"""
    machine_key: str
    machine_name: str
    manufacturer: Optional[str] = None
    year: Optional[int] = None
    game_type: Optional[str] = None
    game_count: Optional[int] = Field(None, description="Number of games played on this machine")
    median_score: Optional[int] = Field(None, description="Median score for this machine")


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


class MachineTopScore(BaseModel):
    """Top machine by total scores"""
    machine_key: str
    machine_name: str
    total_scores: int


class MachineDashboardStats(BaseModel):
    """Dashboard statistics for machines page"""
    total_machines: int = Field(..., description="Total unique machines across all seasons")
    total_machines_latest_season: int = Field(..., description="Total unique machines in latest season")
    new_machines_count: int = Field(..., description="New machines in latest season (not in prior seasons)")
    rare_machines_count: int = Field(..., description="Machines that only exist at 1 venue")
    latest_season: int = Field(..., description="The latest season number")
    top_machines_by_scores: List[MachineTopScore] = Field(default_factory=list, description="Top 10 machines by total scores in latest season")


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


class PlayerMachineScore(BaseModel):
    """Individual score record for a player on a machine"""
    score: int
    season: int
    week: int
    date: Optional[str] = None
    venue_key: str
    venue_name: str
    round_number: int
    player_position: int
    match_key: str


class SeasonStats(BaseModel):
    """Aggregated statistics for a season (for candlestick charts)"""
    season: int
    games_played: int
    min_score: int
    max_score: int
    median_score: int
    mean_score: int
    q1_score: int  # 25th percentile
    q3_score: int  # 75th percentile


class PlayerMachineScoreHistoryResponse(BaseModel):
    """Complete score history for a player on a specific machine"""
    player_key: str
    player_name: str
    machine_key: str
    machine_name: str
    total_games: int
    scores: List[PlayerMachineScore]
    season_stats: List[SeasonStats]


# Team Models
class TeamBase(BaseModel):
    """Base team information"""
    team_key: str
    team_name: str
    home_venue_key: Optional[str] = None
    home_venue_name: Optional[str] = None
    season: int
    team_ipr: Optional[int] = Field(None, description="Sum of roster player IPRs")


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
    address: Optional[str] = None
    neighborhood: Optional[str] = None


class VenueHomeTeam(BaseModel):
    """Team that uses this venue as home"""
    team_key: str
    team_name: str
    season: int


class VenueDetail(VenueBase):
    """Detailed venue information"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    pinballmap_location_id: Optional[int] = Field(None, description="Pinball Map location ID for live machine data")
    home_teams: List[VenueHomeTeam] = Field(default_factory=list, description="Teams that use this venue as home")

    class Config:
        from_attributes = True


class VenueList(BaseModel):
    """List of venues with pagination info"""
    venues: List[VenueBase]
    total: int
    limit: int
    offset: int


class VenueWithStats(VenueBase):
    """Venue with additional statistics"""
    machine_count: int = Field(0, description="Number of machines currently at this venue")
    home_teams: List[VenueHomeTeam] = Field(default_factory=list, description="Teams that use this venue as home")


class VenueWithStatsList(BaseModel):
    """List of venues with stats and pagination info"""
    venues: List[VenueWithStats]
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


class MachineInfo(BaseModel):
    """Machine key and name"""
    key: str
    name: str


class MatchupAnalysis(BaseModel):
    """Complete matchup analysis between two teams at a venue"""
    home_team_key: str
    home_team_name: str
    away_team_key: str
    away_team_name: str
    venue_key: str
    venue_name: str
    season: Union[int, str]  # Can be single season (22) or range (21-22)

    # Available machines at venue (keys for backwards compatibility)
    available_machines: List[str]
    # Available machines with full names
    available_machines_info: Optional[List[MachineInfo]] = None

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


# Matchplay Integration Models
class MatchplayUser(BaseModel):
    """User data from Matchplay.events"""
    userId: int
    name: str
    ifpaId: Optional[int] = None
    location: Optional[str] = None
    avatar: Optional[str] = None


class MatchplayMatch(BaseModel):
    """A potential match between MNP player and Matchplay user"""
    user: MatchplayUser
    confidence: float = Field(..., ge=0, le=1, description="Match confidence (1.0 = exact match)")
    auto_link_eligible: bool = Field(..., description="True if 100% name match, can auto-link")


class MatchplayLookupResult(BaseModel):
    """Result of looking up an MNP player on Matchplay"""
    mnp_player: Dict[str, str] = Field(..., description="MNP player info (key, name)")
    matches: List[MatchplayMatch] = Field(default_factory=list, description="Potential Matchplay matches")
    status: str = Field(..., description="Status: found, not_found, already_linked")
    mapping: Optional["MatchplayPlayerMapping"] = Field(None, description="Existing mapping if already linked")


class MatchplayPlayerMapping(BaseModel):
    """Mapping between MNP player and Matchplay user"""
    id: int
    mnp_player_key: str
    matchplay_user_id: int
    matchplay_name: Optional[str] = None
    ifpa_id: Optional[int] = None
    match_method: str = Field(..., description="How match was made: auto or manual")
    created_at: Optional[datetime] = None
    last_synced: Optional[datetime] = None

    class Config:
        from_attributes = True


class MatchplayRating(BaseModel):
    """Matchplay rating data from the API"""
    rating: Optional[int] = Field(None, description="Current Matchplay rating")
    rd: Optional[int] = Field(None, description="Rating deviation (uncertainty)")
    game_count: Optional[int] = Field(None, description="Total games played on Matchplay")
    win_count: Optional[int] = Field(None, description="Total wins")
    loss_count: Optional[int] = Field(None, description="Total losses")
    efficiency_percent: Optional[float] = Field(None, description="Win percentage (0-1)")
    lower_bound: Optional[int] = Field(None, description="Conservative rating estimate")
    fetched_at: Optional[datetime] = None


class MatchplayIFPA(BaseModel):
    """IFPA data from Matchplay"""
    ifpa_id: Optional[int] = None
    rank: Optional[int] = Field(None, description="IFPA world rank")
    rating: Optional[float] = Field(None, description="IFPA rating")
    womens_rank: Optional[int] = Field(None, description="IFPA women's rank")


class MatchplayMachineStat(BaseModel):
    """Machine statistics from Matchplay"""
    machine_key: Optional[str] = Field(None, description="MNP machine key if mapped")
    matchplay_arena_name: str = Field(..., description="Arena name from Matchplay")
    games_played: int = 0
    wins: int = 0
    win_percentage: Optional[float] = Field(None, ge=0, le=100)


class MatchplayPlayerStats(BaseModel):
    """Complete Matchplay stats for a player"""
    matchplay_user_id: int
    matchplay_name: str
    location: Optional[str] = None
    avatar: Optional[str] = None
    rating: Optional[MatchplayRating] = None
    ifpa: Optional[MatchplayIFPA] = None
    tournament_count: Optional[int] = Field(None, description="Number of tournaments played")
    machine_stats: List[MatchplayMachineStat] = Field(default_factory=list)
    profile_url: str = Field(..., description="URL to Matchplay profile")


class MatchplayLinkRequest(BaseModel):
    """Request to link an MNP player to a Matchplay user"""
    matchplay_user_id: int = Field(..., description="Matchplay userId to link")


class MatchplayLinkResponse(BaseModel):
    """Response after linking a player"""
    status: str
    mapping: MatchplayPlayerMapping


# Player Machine Game Models (with opponent details)
class GamePlayer(BaseModel):
    """A player in a game with their score and details"""
    player_key: str
    player_name: str
    player_position: int = Field(..., ge=1, le=4, description="Position in game (1-4)")
    score: int
    team_key: str
    team_name: str
    is_home_team: bool


class PlayerMachineGame(BaseModel):
    """A complete game instance with all players"""
    match_key: str
    season: int
    week: int
    date: Optional[str] = None
    venue_key: str
    venue_name: str
    round_number: int = Field(..., ge=1, le=4, description="Round number (1-4)")
    home_team_key: str
    home_team_name: str
    away_team_key: str
    away_team_name: str
    players: List[GamePlayer] = Field(..., description="All players in this game")


class PlayerMachineGamesList(BaseModel):
    """List of games with pagination"""
    player_key: str
    player_name: str
    machine_key: str
    machine_name: str
    games: List[PlayerMachineGame]
    total: int
    limit: int
    offset: int


# Pinball Map Integration Models
class PinballMapMachine(BaseModel):
    """Machine data from Pinball Map API"""
    id: int = Field(..., description="Pinball Map machine ID")
    name: str = Field(..., description="Machine name")
    year: Optional[int] = Field(None, description="Year of manufacture")
    manufacturer: Optional[str] = Field(None, description="Machine manufacturer")
    ipdb_link: Optional[str] = Field(None, description="Link to IPDB entry")
    ipdb_id: Optional[int] = Field(None, description="IPDB machine ID")
    opdb_id: Optional[str] = Field(None, description="OPDB machine ID")


class PinballMapLocation(BaseModel):
    """Location data from Pinball Map API"""
    id: int
    name: str
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    num_machines: Optional[int] = None
    description: Optional[str] = None


class PinballMapVenueMachines(BaseModel):
    """Complete Pinball Map data for a venue"""
    venue_key: str = Field(..., description="MNP venue key")
    venue_name: str = Field(..., description="MNP venue name")
    pinballmap_location_id: int = Field(..., description="Pinball Map location ID")
    pinballmap_url: str = Field(..., description="URL to view on Pinball Map website")
    machines: List[PinballMapMachine] = Field(default_factory=list, description="Current machines at venue")
    machine_count: int = Field(0, description="Number of machines")
    last_updated: Optional[datetime] = Field(None, description="When data was fetched from Pinball Map")


# Score Browse Models
class ScoreItem(BaseModel):
    """Individual score entry for browse display"""
    score: int
    player_key: str
    player_name: str
    team_key: str
    team_name: str
    venue_key: str
    venue_name: str
    date: Optional[str] = None
    season: int
    round: int


class MachineScoreStats(BaseModel):
    """Aggregate statistics for scores on a machine"""
    count: int
    median: int
    min: int
    max: int


class MachineScoreGroup(BaseModel):
    """Scores grouped by machine with aggregate stats"""
    machine_key: str
    machine_name: str
    stats: MachineScoreStats
    scores: List[ScoreItem]
    has_more: bool = False


class ScoreBrowseResponse(BaseModel):
    """Response for the score browse endpoint"""
    total_score_count: int
    filters_applied: Dict[str, Union[str, int, List[str], List[int], bool, None]]
    machine_groups: List[MachineScoreGroup]


class MachineScoresResponse(BaseModel):
    """Response for loading more scores for a specific machine"""
    machine_key: str
    machine_name: str
    total_count: int
    scores: List[ScoreItem]


# Update forward references
MatchplayLookupResult.model_rebuild()
