// API Client for MNP Analyzer Backend

import {
  ApiInfo,
  HealthCheck,
  SeasonsResponse,
  Player,
  PlayerDetail,
  PlayerListResponse,
  PlayerMachineStat,
  PlayerMachineStatsList,
  PlayerMachineScoreHistory,
  Machine,
  MachineListResponse,
  GroupedPercentiles,
  Percentile,
  PlayerQueryParams,
  PlayerMachineStatsParams,
  MachineQueryParams,
  MachinePercentilesParams,
  RawPercentilesParams,
  MachineScoreListResponse,
  MachineScoresParams,
  MachineVenue,
  MachineTeam,
  Venue,
  VenueDetail,
  VenueListResponse,
  VenueMachineStats,
  VenueQueryParams,
  VenueMachinesParams,
  Team,
  TeamListResponse,
  TeamQueryParams,
  TeamMachineStatsList,
  TeamMachineStatsParams,
  TeamPlayerList,
  MatchupAnalysis,
  MatchupQueryParams,
  SeasonSchedule,
  SeasonMatchesResponse,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Build query string from parameters
 * Handles arrays by repeating the key for each value (e.g., seasons=21&seasons=22)
 */
function buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        // For arrays, add each value with the same key
        value.forEach((v) => searchParams.append(key, String(v)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
  const queryString = params ? buildQueryString(params) : '';
  const url = `${API_BASE_URL}${endpoint}${queryString}`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
}

// API Methods

export const api = {
  /**
   * Get API information and data summary
   */
  getApiInfo: (): Promise<ApiInfo> => {
    return fetchAPI<ApiInfo>('/');
  },

  /**
   * Health check endpoint
   */
  getHealthCheck: (): Promise<HealthCheck> => {
    return fetchAPI<HealthCheck>('/health');
  },

  /**
   * Get all available seasons
   */
  getSeasons: (): Promise<SeasonsResponse> => {
    return fetchAPI<SeasonsResponse>('/seasons');
  },

  // Player Endpoints

  /**
   * Get list of players with optional filtering
   */
  getPlayers: (params?: PlayerQueryParams): Promise<PlayerListResponse> => {
    return fetchAPI<PlayerListResponse>('/players', params);
  },

  /**
   * Get detailed information about a specific player
   */
  getPlayer: (playerKey: string): Promise<PlayerDetail> => {
    return fetchAPI<PlayerDetail>(`/players/${playerKey}`);
  },

  /**
   * Get player's machine statistics
   */
  getPlayerMachineStats: (
    playerKey: string,
    params?: PlayerMachineStatsParams
  ): Promise<PlayerMachineStatsList> => {
    return fetchAPI<PlayerMachineStatsList>(`/players/${playerKey}/machines`, params);
  },

  /**
   * Get player's score history on a specific machine
   */
  getPlayerMachineScoreHistory: (
    playerKey: string,
    machineKey: string,
    params?: { venue_key?: string; seasons?: number[] }
  ): Promise<PlayerMachineScoreHistory> => {
    return fetchAPI<PlayerMachineScoreHistory>(
      `/players/${playerKey}/machines/${machineKey}/scores`,
      params
    );
  },

  // Machine Endpoints

  /**
   * Get list of machines with optional filtering
   */
  getMachines: (params?: MachineQueryParams): Promise<MachineListResponse> => {
    return fetchAPI<MachineListResponse>('/machines', params);
  },

  /**
   * Get detailed information about a specific machine
   */
  getMachine: (machineKey: string): Promise<Machine> => {
    return fetchAPI<Machine>(`/machines/${machineKey}`);
  },

  /**
   * Get machine percentiles (grouped by venue/season)
   */
  getMachinePercentiles: (
    machineKey: string,
    params?: MachinePercentilesParams
  ): Promise<GroupedPercentiles[]> => {
    return fetchAPI<GroupedPercentiles[]>(`/machines/${machineKey}/percentiles`, params);
  },

  /**
   * Get raw percentile records for a machine
   */
  getMachinePercentilesRaw: (
    machineKey: string,
    params?: RawPercentilesParams
  ): Promise<Percentile[]> => {
    return fetchAPI<Percentile[]>(`/machines/${machineKey}/percentiles/raw`, params);
  },

  /**
   * Get individual scores for a machine
   */
  getMachineScores: (
    machineKey: string,
    params?: MachineScoresParams
  ): Promise<MachineScoreListResponse> => {
    return fetchAPI<MachineScoreListResponse>(`/machines/${machineKey}/scores`, params);
  },

  /**
   * Get venues where a machine has been played
   */
  getMachineVenues: (machineKey: string): Promise<MachineVenue[]> => {
    return fetchAPI<MachineVenue[]>(`/machines/${machineKey}/venues`);
  },

  /**
   * Get teams that have played on a machine
   */
  getMachineTeams: (machineKey: string): Promise<MachineTeam[]> => {
    return fetchAPI<MachineTeam[]>(`/machines/${machineKey}/teams`);
  },

  // Venue Endpoints

  /**
   * Get list of venues with optional filtering
   */
  getVenues: (params?: VenueQueryParams): Promise<VenueListResponse> => {
    return fetchAPI<VenueListResponse>('/venues', params);
  },

  /**
   * Get detailed information about a specific venue
   */
  getVenue: (venueKey: string): Promise<VenueDetail> => {
    return fetchAPI<VenueDetail>(`/venues/${venueKey}`);
  },

  /**
   * Get machines at a venue with score statistics
   */
  getVenueMachines: (
    venueKey: string,
    params?: VenueMachinesParams
  ): Promise<VenueMachineStats[]> => {
    return fetchAPI<VenueMachineStats[]>(`/venues/${venueKey}/machines`, params);
  },

  /**
   * Get current machine lineup at venue
   */
  getVenueCurrentMachines: (venueKey: string): Promise<string[]> => {
    return fetchAPI<string[]>(`/venues/${venueKey}/current-machines`);
  },

  // Team Endpoints

  /**
   * Get list of teams with optional filtering
   */
  getTeams: (params?: TeamQueryParams): Promise<TeamListResponse> => {
    return fetchAPI<TeamListResponse>('/teams', params);
  },

  /**
   * Get detailed information about a specific team
   */
  getTeam: (teamKey: string, season?: number): Promise<Team> => {
    return fetchAPI<Team>(`/teams/${teamKey}`, season ? { season } : undefined);
  },

  /**
   * Get team machine statistics
   */
  getTeamMachineStats: (
    teamKey: string,
    params?: TeamMachineStatsParams
  ): Promise<TeamMachineStatsList> => {
    return fetchAPI<TeamMachineStatsList>(`/teams/${teamKey}/machines`, params);
  },

  /**
   * Get team roster with player statistics
   */
  getTeamPlayers: (
    teamKey: string,
    season?: number,
    venue_key?: string
  ): Promise<TeamPlayerList> => {
    const params: any = {};
    if (season) params.season = season;
    if (venue_key) params.venue_key = venue_key;
    return fetchAPI<TeamPlayerList>(`/teams/${teamKey}/players`, params);
  },

  // Matchup Endpoints

  /**
   * Get matchup analysis between two teams at a venue
   */
  getMatchupAnalysis: (params: MatchupQueryParams): Promise<MatchupAnalysis> => {
    return fetchAPI<MatchupAnalysis>('/matchups', params);
  },

  // Season Schedule Endpoints

  /**
   * Get complete season schedule from season.json
   */
  getSeasonSchedule: (season: number): Promise<SeasonSchedule> => {
    return fetchAPI<SeasonSchedule>(`/seasons/${season}/schedule`);
  },

  /**
   * Get all matches for a season, optionally filtered by week
   */
  getSeasonMatches: (season: number, week?: number): Promise<SeasonMatchesResponse> => {
    const params = week ? { week } : undefined;
    return fetchAPI<SeasonMatchesResponse>(`/seasons/${season}/matches`, params);
  },
};

export default api;
