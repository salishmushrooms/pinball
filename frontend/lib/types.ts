// API Response Types

export interface ApiInfo {
  message: string;
  version: string;
  docs_url: string;
  redoc_url: string;
  endpoints: {
    players: string;
    machines: string;
  };
  data_summary: {
    description: string;
    players: number;
    machines: number;
    venues: number;
    teams: number;
    matches: number;
    total_scores: string;
  };
}

export interface HealthCheck {
  status: string;
  database: string;
  api_version: string;
}

export interface SeasonsResponse {
  seasons: number[];
  count: number;
}

// Player Types
export interface Player {
  player_key: string;
  name: string;
  current_ipr: number | null;
  first_seen_season: number;
  last_seen_season: number;
}

export interface PlayerListResponse {
  players: Player[];
  total: number;
  limit: number;
  offset: number;
}

export interface PlayerDetail extends Player {
  matches_played?: number;
  games_played?: number;
  total_matches?: number;
  total_games?: number;
}

export interface PlayerMachineStat {
  player_key: string;
  machine_key: string;
  machine_name: string;
  venue_key: string;
  season: number;
  games_played: number;
  total_score: number;
  median_score: number;
  avg_score: number;
  best_score: number;
  worst_score: number;
  median_percentile: number | null;
  avg_percentile: number | null;
  win_percentage: number | null;
}

export interface PlayerMachineStatsList {
  stats: PlayerMachineStat[];
  total: number;
  limit: number;
  offset: number;
}

export interface PlayerMachineScore {
  score: number;
  season: number;
  week: number;
  date: string | null;
  venue_key: string;
  venue_name: string;
  round_number: number;
  player_position: number;
  match_key: string;
}

export interface SeasonStats {
  season: number;
  games_played: number;
  min_score: number;
  max_score: number;
  median_score: number;
  mean_score: number;
  q1_score: number;
  q3_score: number;
}

export interface PlayerMachineScoreHistory {
  player_key: string;
  player_name: string;
  machine_key: string;
  machine_name: string;
  total_games: number;
  scores: PlayerMachineScore[];
  season_stats: SeasonStats[];
}

// Machine Types
export interface Machine {
  machine_key: string;
  machine_name: string;
  manufacturer: string | null;
  year: number | null;
  game_type: string | null;
  ipdb_id?: string | null;
  total_scores?: number;
  unique_players?: number;
  median_score?: number | null;
  max_score?: number | null;
  game_count?: number | null;
}

export interface MachineListResponse {
  machines: Machine[];
  total: number;
  limit: number;
  offset: number;
}

export interface Percentile {
  machine_key: string;
  venue_key: string;
  season: number;
  percentile: number;
  score_threshold: number;
  sample_size: number;
}

export interface GroupedPercentiles {
  machine_key: string;
  venue_key: string;
  season: number;
  percentiles: {
    [key: number]: number; // percentile -> score_threshold
  };
  sample_size: number;
}

// Query Parameter Types
export interface PlayerQueryParams {
  season?: number;
  min_ipr?: number;
  max_ipr?: number;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface PlayerMachineStatsParams {
  seasons?: number[];
  venue_key?: string;
  min_games?: number;
  sort_by?: 'median_percentile' | 'avg_percentile' | 'games_played' | 'avg_score' | 'best_score' | 'win_percentage';
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface MachineQueryParams {
  manufacturer?: string;
  year?: number;
  game_type?: string;
  search?: string;
  has_percentiles?: boolean;
  season?: number;
  venue_key?: string;
  limit?: number;
  offset?: number;
}

export interface MachinePercentilesParams {
  season?: number;
  venue_key?: string;
}

export interface RawPercentilesParams {
  season?: number;
  venue_key?: string;
  percentile?: number;
}

// Score Types
export interface MachineScore {
  score_id: number;
  score: number;
  player_key: string;
  player_name: string | null;
  venue_key: string;
  venue_name: string | null;
  season: number;
  week: number;
  round_number: number;
  match_key: string;
  date: string | null;
  player_position: number;
  team_key: string;
}

export interface MachineScoreListResponse {
  scores: MachineScore[];
  total: number;
  limit: number;
  offset: number;
}

export interface MachineScoresParams {
  season?: number;
  venue_key?: string;
  team_keys?: string;
  limit?: number;
  offset?: number;
}

export interface MachineVenue {
  venue_key: string;
  venue_name: string;
  score_count: number;
}

export interface MachineTeam {
  team_key: string;
  team_name: string;
  score_count: number;
}

// Venue Types
export interface Venue {
  venue_key: string;
  venue_name: string;
  city: string | null;
  state: string | null;
}

export interface VenueDetail extends Venue {
  address: string | null;
}

export interface VenueListResponse {
  venues: Venue[];
  total: number;
  limit: number;
  offset: number;
}

export interface VenueMachineStats {
  machine_key: string;
  machine_name: string;
  manufacturer: string | null;
  year: number | null;
  venue_key: string;
  venue_name: string;
  total_scores: number;
  unique_players: number;
  median_score: number;
  max_score: number;
  min_score: number;
  avg_score: number;
  is_current: boolean | null;
}

export interface VenueQueryParams {
  city?: string;
  state?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface VenueMachinesParams {
  current_only?: boolean;
  seasons?: number[];
  team_key?: string;
  scores_from?: 'venue' | 'all';
}

// Team Types
export interface Team {
  team_key: string;
  team_name: string;
  home_venue_key: string | null;
  season: number;
}

export interface TeamListResponse {
  teams: Team[];
  total: number;
  limit: number;
  offset: number;
}

export interface TeamQueryParams {
  season?: number;
  limit?: number;
  offset?: number;
}

export interface TeamMachineStat {
  team_key: string;
  team_name: string | null;
  machine_key: string;
  machine_name: string | null;
  venue_key: string | null;
  season: number | null;
  games_played: number;
  total_score: number;
  median_score: number | null;
  avg_score: number | null;
  best_score: number | null;
  worst_score: number | null;
  median_percentile: number | null;
  avg_percentile: number | null;
  win_percentage: number | null;
  rounds_played: number[] | null;
}

export interface TeamMachineStatsList {
  stats: TeamMachineStat[];
  total: number;
  limit: number;
  offset: number;
}

export interface TeamMachineStatsParams {
  seasons?: number[] | string; // array of seasons or comma-separated string
  venue_key?: string;
  rounds?: string; // comma-separated rounds like "1,2,3,4"
  exclude_subs?: boolean; // exclude substitute players (default: true)
  min_games?: number;
  sort_by?: 'games_played' | 'avg_score' | 'best_score' | 'win_percentage' | 'median_score';
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface TeamPlayer {
  player_key: string;
  player_name: string;
  current_ipr: number | null;
  games_played: number;
  win_percentage: number | null;
  most_played_machine_key: string | null;
  most_played_machine_name: string | null;
  most_played_machine_games: number | null;
  seasons_played: number[];
}

export interface TeamPlayerList {
  players: TeamPlayer[];
  total: number;
}

// Matchup Types
export interface ConfidenceInterval {
  mean: number;
  std_dev: number;
  lower_bound: number;
  upper_bound: number;
  sample_size: number;
  confidence_level: number;
}

export interface PlayerMachineConfidence {
  player_key: string;
  player_name: string;
  machine_key: string;
  machine_name: string;
  confidence_interval: ConfidenceInterval | null;
  insufficient_data: boolean;
  message?: string;
}

export interface TeamMachineConfidence {
  team_key: string;
  team_name: string;
  machine_key: string;
  machine_name: string;
  confidence_interval: ConfidenceInterval | null;
  insufficient_data: boolean;
  message?: string;
}

export interface MachinePickFrequency {
  machine_key: string;
  machine_name: string;
  times_picked: number;
  total_opportunities: number;
  pick_percentage: number;
}

export interface PlayerMachinePreference {
  player_key: string;
  player_name: string;
  top_machines: MachinePickFrequency[];
}

export interface MatchupAnalysis {
  home_team_key: string;
  home_team_name: string;
  away_team_key: string;
  away_team_name: string;
  venue_key: string;
  venue_name: string;
  season: number | string;  // Can be single season (22) or range (21-22)
  available_machines: string[];
  home_team_pick_frequency: MachinePickFrequency[];
  away_team_pick_frequency: MachinePickFrequency[];
  home_team_player_preferences: PlayerMachinePreference[];
  away_team_player_preferences: PlayerMachinePreference[];
  home_team_player_confidence: PlayerMachineConfidence[];
  away_team_player_confidence: PlayerMachineConfidence[];
  home_team_machine_confidence: TeamMachineConfidence[];
  away_team_machine_confidence: TeamMachineConfidence[];
}

export interface MatchupQueryParams {
  home_team: string;
  away_team: string;
  venue: string;
  seasons?: number[];
}

// Season Schedule Types
export interface ScheduleMatch {
  match_key: string;
  away_key: string;
  away_name: string;
  away_linked: boolean;
  home_key: string;
  home_name: string;
  home_linked: boolean;
  venue: {
    key: string;
    name: string;
  };
  week?: string;
  week_label?: string;
  date?: string;
  is_playoffs?: boolean;
}

export interface SeasonWeek {
  n: string;
  label: string;
  code: string;
  isPlayoffs: boolean;
  isSpecial: boolean;
  date: string;
  matches: ScheduleMatch[];
}

export interface TeamScheduleMatch {
  match_key: string;
  week: string;
  date: string;
  side: '@' | 'vs';  // @ = away, vs = home
  opp: {
    key: string;
    name: string;
  };
}

export interface SeasonTeamData {
  key: string;
  venue: string;
  name: string;
  roster: { name: string }[];
  schedule: TeamScheduleMatch[];
}

export interface SeasonSchedule {
  key: string;
  teams: { [teamKey: string]: SeasonTeamData };
  weeks: SeasonWeek[];
  groups: any;
}

export interface SeasonMatchesResponse {
  season: number;
  week: number | null;
  matches: ScheduleMatch[];
  count: number;
}

// ============================================================================
// Prediction Types
// ============================================================================

export interface MachinePrediction {
  machine_key: string;
  machine_name: string;
  pick_count: number;
  confidence_pct: number;
  available_at_venue: boolean;
}

export interface MachinePredictionResponse {
  predictions: MachinePrediction[];
  sample_size: number;
  total_rounds: number;
  context: string;
  team_key: string;
  venue_key: string;
  venue_machines: string[];
  seasons_analyzed: number[];
  message?: string;
}

// ============================================================================
// Matchplay.events Integration Types
// ============================================================================

export interface MatchplayUser {
  userId: number;
  name: string;
  ifpaId?: number;
  location?: string;
  avatar?: string;
}

export interface MatchplayMatch {
  user: MatchplayUser;
  confidence: number;
  auto_link_eligible: boolean;
}

export interface MatchplayPlayerMapping {
  id: number;
  mnp_player_key: string;
  matchplay_user_id: number;
  matchplay_name?: string;
  ifpa_id?: number;
  match_method: 'auto' | 'manual';
  created_at?: string;
  last_synced?: string;
}

export interface MatchplayLookupResult {
  mnp_player: { key: string; name: string };
  matches: MatchplayMatch[];
  status: 'found' | 'not_found' | 'already_linked';
  mapping?: MatchplayPlayerMapping;
}

export interface MatchplayRating {
  rating: number | null;
  rd: number | null;
  game_count: number | null;
  win_count: number | null;
  loss_count: number | null;
  efficiency_percent: number | null;
  lower_bound: number | null;
  fetched_at?: string;
}

export interface MatchplayIFPA {
  ifpa_id: number | null;
  rank: number | null;
  rating: number | null;
  womens_rank: number | null;
}

export interface MatchplayMachineStat {
  machine_key?: string;
  matchplay_arena_name: string;
  games_played: number;
  wins: number;
  win_percentage: number | null;
}

export interface MatchplayPlayerStats {
  matchplay_user_id: number;
  matchplay_name: string;
  location?: string;
  avatar?: string;
  rating?: MatchplayRating;
  ifpa?: MatchplayIFPA;
  tournament_count?: number;
  machine_stats: MatchplayMachineStat[];
  profile_url: string;
}

export interface MatchplayLinkRequest {
  matchplay_user_id: number;
}

export interface MatchplayLinkResponse {
  status: string;
  mapping: MatchplayPlayerMapping;
}

export interface MatchplayStatus {
  configured: boolean;
  message: string;
  api_accessible?: boolean;
  rate_limit_remaining?: number;
  rate_limit_total?: number;
  error?: string;
}

export interface MatchplayRatingInfo {
  matchplay_user_id: number;
  matchplay_name: string;
  rating: number | null;
  rd?: number | null;
  game_count?: number | null;
  profile_url: string;
}

export interface MatchplayRatingsResponse {
  ratings: Record<string, MatchplayRatingInfo>;
}
