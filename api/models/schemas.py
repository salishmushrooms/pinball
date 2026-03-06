"""
Pydantic models for API request/response schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Player Models
class PlayerBase(BaseModel):
    """Base player information"""

    player_key: str
    name: str
    current_ipr: float | None = None
    first_seen_season: int
    last_seen_season: int


class PlayerDetail(PlayerBase):
    """Detailed player information"""

    created_at: datetime | None = None
    updated_at: datetime | None = None
    current_team_key: str | None = Field(None, description="Team key for most recent season")
    current_team_name: str | None = Field(None, description="Team name for most recent season")

    class Config:
        from_attributes = True


class PlayerList(BaseModel):
    """List of players with pagination info"""

    players: list[PlayerBase]
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
    team_key: str | None = None
    team_name: str | None = None
    venue_key: str | None = None
    venue_name: str | None = None
    ipr: float | None = None
    season: int = Field(..., description="Season for the highlight stats")
    best_machine_key: str = Field(..., description="Machine with highest percentile score")
    best_machine_name: str = Field(..., description="Name of the best machine")
    best_score: int = Field(..., description="The score achieved")
    best_percentile: float = Field(..., description="Percentile ranking of the score")


class PlayerDashboardStats(BaseModel):
    """Dashboard statistics for players page"""

    total_players: int
    ipr_distribution: list[IPRDistribution]
    new_players_count: int = Field(..., description="Players first seen in latest season")
    latest_season: int = Field(..., description="The latest season number")
    player_highlights: list[PlayerHighlight] = Field(
        default_factory=list, description="Featured players with highlight stats"
    )


# Machine Models
class MachineBase(BaseModel):
    """Base machine information"""

    machine_key: str
    machine_name: str
    manufacturer: str | None = None
    year: int | None = None
    game_type: str | None = None
    game_count: int | None = Field(None, description="Number of games played on this machine")
    median_score: int | None = Field(None, description="Median score for this machine")


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

    machines: list[MachineBase]
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
    total_machines_latest_season: int = Field(
        ..., description="Total unique machines in latest season"
    )
    new_machines_count: int = Field(
        ..., description="New machines in latest season (not in prior seasons)"
    )
    rare_machines_count: int = Field(..., description="Machines that only exist at 1 venue")
    latest_season: int = Field(..., description="The latest season number")
    top_machines_by_scores: list[MachineTopScore] = Field(
        default_factory=list, description="Top 10 machines by total scores in latest season"
    )


# Score Percentile Models
class ScorePercentile(BaseModel):
    """Score percentile for a machine"""

    machine_key: str
    machine_name: str | None = None
    venue_key: str | None = None
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
    player_name: str | None = None
    machine_key: str
    machine_name: str | None = None
    venue_key: str
    season: int
    games_played: int = Field(..., gt=0)
    total_score: int
    median_score: int | None = None
    avg_score: int | None = None
    best_score: int | None = None
    worst_score: int | None = None
    median_percentile: float | None = Field(None, ge=0, le=100)
    avg_percentile: float | None = Field(None, ge=0, le=100)
    win_percentage: float | None = Field(
        None, ge=0, le=100, description="Percentage of head-to-head wins vs opponents"
    )

    class Config:
        from_attributes = True


class PlayerMachineStatsList(BaseModel):
    """List of player machine stats"""

    stats: list[PlayerMachineStats]
    total: int
    limit: int
    offset: int


class PlayerMachineScore(BaseModel):
    """Individual score record for a player on a machine"""

    score: int
    season: int
    week: int
    date: str | None = None
    venue_key: str
    venue_name: str
    round_number: int
    player_position: int
    match_key: str
    percentile: int | None = Field(
        None, description="Score percentile rank (0-99) across the league for this machine"
    )


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
    scores: list[PlayerMachineScore]
    season_stats: list[SeasonStats]


# Team Models
class TeamBase(BaseModel):
    """Base team information"""

    team_key: str
    team_name: str
    home_venue_key: str | None = None
    home_venue_name: str | None = None
    season: int
    team_ipr: int | None = Field(None, description="Sum of roster player IPRs")


class TeamDetail(TeamBase):
    """Detailed team information"""

    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TeamList(BaseModel):
    """List of teams with pagination info"""

    teams: list[TeamBase]
    total: int
    limit: int
    offset: int


# Venue Models
class VenueBase(BaseModel):
    """Base venue information"""

    venue_key: str
    venue_name: str
    address: str | None = None
    neighborhood: str | None = None


class VenueHomeTeam(BaseModel):
    """Team that uses this venue as home"""

    team_key: str
    team_name: str
    season: int


class VenueDetail(VenueBase):
    """Detailed venue information"""

    created_at: datetime | None = None
    updated_at: datetime | None = None
    pinballmap_location_id: int | None = Field(
        None, description="Pinball Map location ID for live machine data"
    )
    home_teams: list[VenueHomeTeam] = Field(
        default_factory=list, description="Teams that use this venue as home"
    )

    class Config:
        from_attributes = True


class VenueList(BaseModel):
    """List of venues with pagination info"""

    venues: list[VenueBase]
    total: int
    limit: int
    offset: int


class VenueWithStats(VenueBase):
    """Venue with additional statistics"""

    machine_count: int = Field(0, description="Number of machines currently at this venue")
    home_teams: list[VenueHomeTeam] = Field(
        default_factory=list, description="Teams that use this venue as home"
    )


class VenueWithStatsList(BaseModel):
    """List of venues with stats and pagination info"""

    venues: list[VenueWithStats]
    total: int
    limit: int
    offset: int


class VenueMachineStats(BaseModel):
    """Machine statistics at a specific venue"""

    machine_key: str
    machine_name: str
    manufacturer: str | None = None
    year: int | None = None
    venue_key: str
    venue_name: str
    total_scores: int
    unique_players: int
    median_score: int
    max_score: int
    min_score: int
    avg_score: int
    is_current: bool | None = Field(
        None, description="Whether this machine is currently at the venue"
    )

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
    match_date: datetime | None = None


class MatchDetail(MatchBase):
    """Detailed match information"""

    home_points: int | None = None
    away_points: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# Score Models
class MachineScore(BaseModel):
    """Individual score for a machine"""

    score_id: int
    score: int
    player_key: str
    player_name: str | None = None
    venue_key: str
    venue_name: str | None = None
    season: int
    week: int
    round_number: int
    match_key: str
    date: datetime | None = None
    player_position: int
    team_key: str

    class Config:
        from_attributes = True


class MachineScoreList(BaseModel):
    """List of machine scores with pagination"""

    scores: list[MachineScore]
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
    confidence_interval: ConfidenceInterval | None = None
    insufficient_data: bool = False
    message: str | None = None


class TeamMachineConfidence(BaseModel):
    """Team's expected performance on a machine with confidence interval"""

    team_key: str
    team_name: str
    machine_key: str
    machine_name: str
    confidence_interval: ConfidenceInterval | None = None
    insufficient_data: bool = False
    message: str | None = None


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
    top_machines: list[MachinePickFrequency]


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
    season: int | str  # Can be single season (22) or range (21-22)

    # Available machines at venue (keys for backwards compatibility)
    available_machines: list[str]
    # Available machines with full names
    available_machines_info: list[MachineInfo] | None = None

    # Team machine pick frequency - doubles rounds (limited to available machines)
    home_team_pick_frequency: list[MachinePickFrequency]
    away_team_pick_frequency: list[MachinePickFrequency]

    # Team machine pick frequency - singles rounds (limited to available machines)
    home_team_singles_pick_frequency: list[MachinePickFrequency] = []
    away_team_singles_pick_frequency: list[MachinePickFrequency] = []

    # Player machine preferences (limited to available machines)
    home_team_player_preferences: list[PlayerMachinePreference]
    away_team_player_preferences: list[PlayerMachinePreference]

    # Player-specific confidence intervals
    home_team_player_confidence: list[PlayerMachineConfidence]
    away_team_player_confidence: list[PlayerMachineConfidence]

    # Team-level confidence intervals (aggregate of all players)
    home_team_machine_confidence: list[TeamMachineConfidence]
    away_team_machine_confidence: list[TeamMachineConfidence]


# Team Machine Stats Models
class TeamMachineStats(BaseModel):
    """Team statistics for a specific machine"""

    team_key: str
    team_name: str | None = None
    machine_key: str
    machine_name: str | None = None
    venue_key: str | None = None
    season: int | None = None
    games_played: int = Field(..., gt=0)
    total_score: int
    median_score: int | None = None
    avg_score: int | None = None
    best_score: int | None = None
    worst_score: int | None = None
    median_percentile: float | None = Field(None, ge=0, le=100)
    avg_percentile: float | None = Field(None, ge=0, le=100)
    win_percentage: float | None = Field(
        None, ge=0, le=100, description="Percentage of head-to-head wins vs opponents"
    )
    rounds_played: list[int] | None = Field(None, description="List of rounds played (1-4)")

    class Config:
        from_attributes = True


class TeamMachineStatsList(BaseModel):
    """List of team machine stats"""

    stats: list[TeamMachineStats]
    total: int
    limit: int
    offset: int


class TeamPlayer(BaseModel):
    """Player roster information for a team"""

    player_key: str
    player_name: str
    current_ipr: float | None = None
    games_played: int
    win_percentage: float | None = Field(None, ge=0, le=100)
    most_played_machine_key: str | None = None
    most_played_machine_name: str | None = None
    most_played_machine_games: int | None = None
    seasons_played: list[int]

    class Config:
        from_attributes = True


class TeamPlayerList(BaseModel):
    """List of team players with stats"""

    players: list[TeamPlayer]
    total: int


# Error Models
class ErrorResponse(BaseModel):
    """Standard error response"""

    detail: str
    error_code: str | None = None


# Matchplay Integration Models
class MatchplayUser(BaseModel):
    """User data from Matchplay.events"""

    userId: int
    name: str
    ifpaId: int | None = None
    location: str | None = None
    avatar: str | None = None


class MatchplayMatch(BaseModel):
    """A potential match between MNP player and Matchplay user"""

    user: MatchplayUser
    confidence: float = Field(..., ge=0, le=1, description="Match confidence (1.0 = exact match)")
    auto_link_eligible: bool = Field(..., description="True if 100% name match, can auto-link")


class MatchplayLookupResult(BaseModel):
    """Result of looking up an MNP player on Matchplay"""

    mnp_player: dict[str, str] = Field(..., description="MNP player info (key, name)")
    matches: list[MatchplayMatch] = Field(
        default_factory=list, description="Potential Matchplay matches"
    )
    status: str = Field(..., description="Status: found, not_found, already_linked")
    mapping: Optional["MatchplayPlayerMapping"] = Field(
        None, description="Existing mapping if already linked"
    )


class MatchplayPlayerMapping(BaseModel):
    """Mapping between MNP player and Matchplay user"""

    id: int
    mnp_player_key: str
    matchplay_user_id: int
    matchplay_name: str | None = None
    ifpa_id: int | None = None
    match_method: str = Field(..., description="How match was made: auto or manual")
    created_at: datetime | None = None
    last_synced: datetime | None = None

    class Config:
        from_attributes = True


class MatchplayRating(BaseModel):
    """Matchplay rating data from the API"""

    rating: int | None = Field(None, description="Current Matchplay rating")
    rd: int | None = Field(None, description="Rating deviation (uncertainty)")
    game_count: int | None = Field(None, description="Total games played on Matchplay")
    win_count: int | None = Field(None, description="Total wins")
    loss_count: int | None = Field(None, description="Total losses")
    efficiency_percent: float | None = Field(None, description="Win percentage (0-1)")
    lower_bound: int | None = Field(None, description="Conservative rating estimate")
    fetched_at: datetime | None = None


class MatchplayIFPA(BaseModel):
    """IFPA data from Matchplay"""

    ifpa_id: int | None = None
    rank: int | None = Field(None, description="IFPA world rank")
    rating: float | None = Field(None, description="IFPA rating")
    womens_rank: int | None = Field(None, description="IFPA women's rank")


class MatchplayMachineStat(BaseModel):
    """Machine statistics from Matchplay"""

    machine_key: str | None = Field(None, description="MNP machine key if mapped")
    matchplay_arena_name: str = Field(..., description="Arena name from Matchplay")
    games_played: int = 0
    wins: int = 0
    win_percentage: float | None = Field(None, ge=0, le=100)


class MatchplayPlayerStats(BaseModel):
    """Complete Matchplay stats for a player"""

    matchplay_user_id: int
    matchplay_name: str
    location: str | None = None
    avatar: str | None = None
    rating: MatchplayRating | None = None
    ifpa: MatchplayIFPA | None = None
    tournament_count: int | None = Field(None, description="Number of tournaments played")
    machine_stats: list[MatchplayMachineStat] = Field(default_factory=list)
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
    date: str | None = None
    venue_key: str
    venue_name: str
    round_number: int = Field(..., ge=1, le=4, description="Round number (1-4)")
    home_team_key: str
    home_team_name: str
    away_team_key: str
    away_team_name: str
    players: list[GamePlayer] = Field(..., description="All players in this game")


class PlayerMachineGamesList(BaseModel):
    """List of games with pagination"""

    player_key: str
    player_name: str
    machine_key: str
    machine_name: str
    games: list[PlayerMachineGame]
    total: int
    limit: int
    offset: int


# Pinball Map Integration Models
class PinballMapMachine(BaseModel):
    """Machine data from Pinball Map API"""

    id: int = Field(..., description="Pinball Map machine ID")
    name: str = Field(..., description="Machine name")
    year: int | None = Field(None, description="Year of manufacture")
    manufacturer: str | None = Field(None, description="Machine manufacturer")
    ipdb_link: str | None = Field(None, description="Link to IPDB entry")
    ipdb_id: int | None = Field(None, description="IPDB machine ID")
    opdb_id: str | None = Field(None, description="OPDB machine ID")


class PinballMapLocation(BaseModel):
    """Location data from Pinball Map API"""

    id: int
    name: str
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    phone: str | None = None
    website: str | None = None
    lat: float | None = None
    lon: float | None = None
    num_machines: int | None = None
    description: str | None = None


class PinballMapVenueMachines(BaseModel):
    """Complete Pinball Map data for a venue"""

    venue_key: str = Field(..., description="MNP venue key")
    venue_name: str = Field(..., description="MNP venue name")
    pinballmap_location_id: int = Field(..., description="Pinball Map location ID")
    pinballmap_url: str = Field(..., description="URL to view on Pinball Map website")
    machines: list[PinballMapMachine] = Field(
        default_factory=list, description="Current machines at venue"
    )
    machine_count: int = Field(0, description="Number of machines")
    last_updated: datetime | None = Field(
        None, description="When data was fetched from Pinball Map"
    )


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
    date: str | None = None
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
    scores: list[ScoreItem]
    has_more: bool = False


class ScoreBrowseResponse(BaseModel):
    """Response for the score browse endpoint"""

    total_score_count: int
    filters_applied: dict[str, str | int | list[str] | list[int] | bool | None]
    machine_groups: list[MachineScoreGroup]


class MachineScoresResponse(BaseModel):
    """Response for loading more scores for a specific machine"""

    machine_key: str
    machine_name: str
    total_count: int
    scores: list[ScoreItem]


# ---------------------------------------------------------------------------
# Live Match Models (fetched from mondaynightpinball.com, enriched with
# historical percentile data from the MNP Analyzer database)
# ---------------------------------------------------------------------------


class LiveScore(BaseModel):
    """A single player's score within a live game, with historical percentile."""

    score: int | None = None  # Raw score (None if not yet played)
    points: float | None = None  # Match points (float — can be fractional on ties)
    percentile: int | None = None  # Percentile rank (0-99) vs all historical scores on this machine
    player_key: str | None = None  # Player identifier
    player_name: str | None = None  # Player display name


class LiveGame(BaseModel):
    """One game within a round, with all player scores and percentile overlays."""

    n: int
    machine_key: str | None = None
    machine_name: str | None = None
    scores: list[LiveScore]  # 4 entries for doubles rounds, 2 for singles
    away_points: int | None = None
    home_points: int | None = None


class LiveRound(BaseModel):
    """One round (1-4) of a match with its games and confirmation status."""

    n: int
    games: list[LiveGame]
    done: bool
    left_confirmed: bool
    right_confirmed: bool


class LiveMatchSummary(BaseModel):
    """Summary of a live match's current state and running point totals."""

    match_key: str
    week: int
    away_team_key: str
    away_team_name: str
    home_team_key: str
    home_team_name: str
    venue_key: str
    date: str | None = None
    state: str  # SCHEDULED/PLAYING/REVIEWING/COMPLETE/UNAVAILABLE
    away_total_points: int  # Raw game points only
    home_total_points: int
    away_handicap: int = 0  # Handicap points (0 until match complete)
    home_handicap: int = 0
    away_participation: int = 0  # Participation bonus (0 until match complete)
    home_participation: int = 0
    away_final_points: int = 0  # Game + handicap + participation
    home_final_points: int = 0
    current_round: int


class LiveRosterPlayer(BaseModel):
    """A player in a team's lineup for a live match."""

    key: str
    name: str
    ipr: float | None = None
    is_sub: bool = False
    is_captain: bool = False
    num_played: int = 0
    total_points: float = 0.0


class LiveMatchDetail(LiveMatchSummary):
    """Full live match data including round-by-round scores with percentile overlays."""

    rounds: list[LiveRound]
    away_lineup: list[LiveRosterPlayer] = []
    home_lineup: list[LiveRosterPlayer] = []


class LiveWeekResponse(BaseModel):
    """All match summaries for a given week."""

    season: int
    week: int
    matches: list[LiveMatchSummary]


# Update forward references
MatchplayLookupResult.model_rebuild()


# ============================================================================
# Weekly Analysis Models
# ============================================================================


class MatchSummary(BaseModel):
    total_matches: int
    home_wins: int
    away_wins: int
    ties: int
    home_win_pct: float
    away_win_pct: float
    # Shared-venue adjustments (away team playing at their own home venue)
    shared_venue_matches: int = 0
    true_home_wins: int | None = None
    true_away_wins: int | None = None
    true_home_win_pct: float | None = None
    true_away_win_pct: float | None = None


class MatchResult(BaseModel):
    match_key: str
    home_team_key: str
    home_team_name: str
    away_team_key: str
    away_team_name: str
    home_team_points: float
    away_team_points: float
    home_avg_ipr: float | None = None
    away_avg_ipr: float | None = None
    ipr_gap: float | None = None
    winner: str  # 'home' | 'away' | 'tie'
    venue_key: str
    # Upset-specific
    upset_team_key: str | None = None
    upset_team_name: str | None = None
    # Away-win-specific
    is_underdog: bool | None = None
    # Shared-venue flag (away team at their own home venue)
    is_shared_venue: bool | None = None


class ComebackResult(BaseModel):
    match_key: str
    home_team_key: str
    away_team_key: str
    comeback_team_key: str
    comeback_team_name: str
    other_team_key: str
    other_team_name: str
    deficit_after_r3: float
    comeback_r4_points: float
    other_r4_points: float
    final_score_comeback: float
    final_score_other: float
    venue_key: str


class ScoreOutlier(BaseModel):
    match_key: str
    player_key: str
    player_name: str
    team_key: str
    team_name: str
    machine_key: str
    machine_name: str
    score: int
    round_number: int
    player_position: int
    p95_threshold: int | None = None
    p99_threshold: int | None = None
    pctile_floor: int  # 95 or 99


class MachinePlays(BaseModel):
    machine_key: str
    machine_name: str
    games_played: int
    matches_played: int


class GroupStanding(BaseModel):
    division: str
    team_key: str
    team_name: str
    matches_played: int
    wins: int
    losses: int
    ties: int
    total_points_earned: float
    pops: float


class WeeklyRecap(BaseModel):
    season: int
    week: int
    match_summary: MatchSummary
    upsets: list[MatchResult]
    away_wins: list[MatchResult]
    comebacks: list[ComebackResult]
    score_outliers: list[ScoreOutlier]
    top_machines: list[MachinePlays]
    group_standings: list[GroupStanding]
