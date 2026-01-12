/**
 * React Query hooks for MNP Analyzer API
 *
 * Provides automatic caching, background refetching, and request deduplication.
 *
 * Cache Strategy:
 * - staleTime: 5 minutes (data considered fresh, no refetch)
 * - gcTime: 30 minutes (data kept in memory for instant navigation)
 *
 * Usage:
 *   import { usePlayer, usePlayerMachineStats } from '@/lib/queries';
 *   const { data, isLoading, error } = usePlayer(playerKey);
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { api } from './api';
import {
  ApiInfo,
  PlayerDetail,
  PlayerListResponse,
  PlayerMachineStatsList,
  PlayerMachineScoreHistory,
  PlayerMachineGamesResponse,
  PlayerQueryParams,
  PlayerMachineStatsParams,
  Machine,
  MachineListResponse,
  MachineQueryParams,
  MachinePercentilesParams,
  GroupedPercentiles,
  MachineScoreListResponse,
  MachineScoresParams,
  MachineVenue,
  MachineTeam,
  Venue,
  VenueDetail,
  VenueListResponse,
  VenueWithStatsListResponse,
  VenueMachineStats,
  VenueQueryParams,
  VenueMachinesParams,
  Team,
  TeamListResponse,
  TeamQueryParams,
  TeamMachineStatsList,
  TeamMachineStatsParams,
  TeamPlayerList,
  SeasonsResponse,
  MatchupAnalysis,
  MatchupQueryParams,
  SeasonSchedule,
} from './types';

// Default cache times
const STALE_TIME = 5 * 60 * 1000; // 5 minutes
const GC_TIME = 30 * 60 * 1000; // 30 minutes

// Query key factory for consistent keys
export const queryKeys = {
  // Root
  apiInfo: ['apiInfo'] as const,
  seasons: ['seasons'] as const,

  // Players
  players: (params?: PlayerQueryParams) => ['players', params] as const,
  player: (playerKey: string) => ['player', playerKey] as const,
  playerMachineStats: (playerKey: string, params?: PlayerMachineStatsParams) =>
    ['player', playerKey, 'machines', params] as const,
  playerMachineScoreHistory: (
    playerKey: string,
    machineKey: string,
    params?: { venue_key?: string; seasons?: number[] }
  ) => ['player', playerKey, 'machines', machineKey, 'scores', params] as const,
  playerMachineGames: (
    playerKey: string,
    machineKey: string,
    params?: { venue_key?: string; seasons?: number[]; limit?: number; offset?: number }
  ) => ['player', playerKey, 'machines', machineKey, 'games', params] as const,

  // Machines
  machines: (params?: MachineQueryParams) => ['machines', params] as const,
  machine: (machineKey: string) => ['machine', machineKey] as const,
  machinePercentiles: (machineKey: string, params?: MachinePercentilesParams) =>
    ['machine', machineKey, 'percentiles', params] as const,
  machineScores: (machineKey: string, params?: MachineScoresParams) =>
    ['machine', machineKey, 'scores', params] as const,
  machineVenues: (machineKey: string) => ['machine', machineKey, 'venues'] as const,
  machineTeams: (machineKey: string) => ['machine', machineKey, 'teams'] as const,

  // Venues
  venues: (params?: VenueQueryParams) => ['venues', params] as const,
  venuesWithStats: (params?: VenueQueryParams & { season?: number }) =>
    ['venues', 'withStats', params] as const,
  venue: (venueKey: string) => ['venue', venueKey] as const,
  venueMachines: (venueKey: string, params?: VenueMachinesParams) =>
    ['venue', venueKey, 'machines', params] as const,

  // Teams
  teams: (params?: TeamQueryParams) => ['teams', params] as const,
  team: (teamKey: string, season?: number) => ['team', teamKey, season] as const,
  teamMachineStats: (teamKey: string, params?: TeamMachineStatsParams) =>
    ['team', teamKey, 'machines', params] as const,
  teamPlayers: (teamKey: string, seasons?: number[], venue_key?: string, exclude_subs?: boolean) =>
    ['team', teamKey, 'players', { seasons, venue_key, exclude_subs }] as const,

  // Matchups
  matchup: (params: MatchupQueryParams) => ['matchup', params] as const,

  // Season Schedule
  seasonSchedule: (season: number) => ['season', season, 'schedule'] as const,
};

// =============================================================================
// API Info & Seasons
// =============================================================================

export function useApiInfo(options?: Omit<UseQueryOptions<ApiInfo>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.apiInfo,
    queryFn: () => api.getApiInfo(),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    ...options,
  });
}

export function useSeasons(options?: Omit<UseQueryOptions<SeasonsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.seasons,
    queryFn: () => api.getSeasons(),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    ...options,
  });
}

// =============================================================================
// Players
// =============================================================================

export function usePlayers(
  params?: PlayerQueryParams,
  options?: Omit<UseQueryOptions<PlayerListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.players(params),
    queryFn: () => api.getPlayers(params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    ...options,
  });
}

export function usePlayer(
  playerKey: string,
  options?: Omit<UseQueryOptions<PlayerDetail>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.player(playerKey),
    queryFn: () => api.getPlayer(playerKey),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!playerKey,
    ...options,
  });
}

export function usePlayerMachineStats(
  playerKey: string,
  params?: PlayerMachineStatsParams,
  options?: Omit<UseQueryOptions<PlayerMachineStatsList>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.playerMachineStats(playerKey, params),
    queryFn: () => api.getPlayerMachineStats(playerKey, params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!playerKey,
    ...options,
  });
}

export function usePlayerMachineScoreHistory(
  playerKey: string,
  machineKey: string,
  params?: { venue_key?: string; seasons?: number[] },
  options?: Omit<UseQueryOptions<PlayerMachineScoreHistory>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.playerMachineScoreHistory(playerKey, machineKey, params),
    queryFn: () => api.getPlayerMachineScoreHistory(playerKey, machineKey, params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!playerKey && !!machineKey,
    ...options,
  });
}

export function usePlayerMachineGames(
  playerKey: string,
  machineKey: string,
  params?: { venue_key?: string; seasons?: number[]; limit?: number; offset?: number },
  options?: Omit<UseQueryOptions<PlayerMachineGamesResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.playerMachineGames(playerKey, machineKey, params),
    queryFn: () => api.getPlayerMachineGames(playerKey, machineKey, params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!playerKey && !!machineKey,
    ...options,
  });
}

// =============================================================================
// Machines
// =============================================================================

export function useMachines(
  params?: MachineQueryParams,
  options?: Omit<UseQueryOptions<MachineListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.machines(params),
    queryFn: () => api.getMachines(params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    ...options,
  });
}

export function useMachine(
  machineKey: string,
  options?: Omit<UseQueryOptions<Machine>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.machine(machineKey),
    queryFn: () => api.getMachine(machineKey),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!machineKey,
    ...options,
  });
}

export function useMachinePercentiles(
  machineKey: string,
  params?: MachinePercentilesParams,
  options?: Omit<UseQueryOptions<GroupedPercentiles[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.machinePercentiles(machineKey, params),
    queryFn: () => api.getMachinePercentiles(machineKey, params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!machineKey,
    ...options,
  });
}

export function useMachineScores(
  machineKey: string,
  params?: MachineScoresParams,
  options?: Omit<UseQueryOptions<MachineScoreListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.machineScores(machineKey, params),
    queryFn: () => api.getMachineScores(machineKey, params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!machineKey,
    ...options,
  });
}

export function useMachineVenues(
  machineKey: string,
  options?: Omit<UseQueryOptions<MachineVenue[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.machineVenues(machineKey),
    queryFn: () => api.getMachineVenues(machineKey),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!machineKey,
    ...options,
  });
}

export function useMachineTeams(
  machineKey: string,
  options?: Omit<UseQueryOptions<MachineTeam[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.machineTeams(machineKey),
    queryFn: () => api.getMachineTeams(machineKey),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!machineKey,
    ...options,
  });
}

// =============================================================================
// Venues
// =============================================================================

export function useVenues(
  params?: VenueQueryParams,
  options?: Omit<UseQueryOptions<VenueListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.venues(params),
    queryFn: () => api.getVenues(params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    ...options,
  });
}

export function useVenuesWithStats(
  params?: VenueQueryParams & { season?: number },
  options?: Omit<UseQueryOptions<VenueWithStatsListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.venuesWithStats(params),
    queryFn: () => api.getVenuesWithStats(params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    ...options,
  });
}

export function useVenue(
  venueKey: string,
  options?: Omit<UseQueryOptions<VenueDetail>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.venue(venueKey),
    queryFn: () => api.getVenue(venueKey),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!venueKey,
    ...options,
  });
}

export function useVenueMachines(
  venueKey: string,
  params?: VenueMachinesParams,
  options?: Omit<UseQueryOptions<VenueMachineStats[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.venueMachines(venueKey, params),
    queryFn: () => api.getVenueMachines(venueKey, params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!venueKey,
    ...options,
  });
}

// =============================================================================
// Teams
// =============================================================================

export function useTeams(
  params?: TeamQueryParams,
  options?: Omit<UseQueryOptions<TeamListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.teams(params),
    queryFn: () => api.getTeams(params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    ...options,
  });
}

export function useTeam(
  teamKey: string,
  season?: number,
  options?: Omit<UseQueryOptions<Team>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.team(teamKey, season),
    queryFn: () => api.getTeam(teamKey, season),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!teamKey,
    ...options,
  });
}

export function useTeamMachineStats(
  teamKey: string,
  params?: TeamMachineStatsParams,
  options?: Omit<UseQueryOptions<TeamMachineStatsList>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.teamMachineStats(teamKey, params),
    queryFn: () => api.getTeamMachineStats(teamKey, params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!teamKey,
    ...options,
  });
}

export function useTeamPlayers(
  teamKey: string,
  seasons?: number[],
  venue_key?: string,
  exclude_subs?: boolean,
  options?: Omit<UseQueryOptions<TeamPlayerList>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.teamPlayers(teamKey, seasons, venue_key, exclude_subs),
    queryFn: () => api.getTeamPlayers(teamKey, seasons, venue_key, exclude_subs),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!teamKey,
    ...options,
  });
}

// =============================================================================
// Matchups
// =============================================================================

export function useMatchup(
  params: MatchupQueryParams,
  options?: Omit<UseQueryOptions<MatchupAnalysis>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.matchup(params),
    queryFn: () => api.getMatchupAnalysis(params),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!params.home_team && !!params.away_team && !!params.venue,
    ...options,
  });
}

// =============================================================================
// Season Schedule
// =============================================================================

export function useSeasonSchedule(
  season: number,
  options?: Omit<UseQueryOptions<SeasonSchedule>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.seasonSchedule(season),
    queryFn: () => api.getSeasonSchedule(season),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: !!season,
    ...options,
  });
}
