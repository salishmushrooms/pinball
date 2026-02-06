/**
 * Team logo configuration
 * Maps team_key to Cloudflare Images IDs
 *
 * Cloudflare Images URL structure:
 * https://imagedelivery.net/6xApIkGdPK3UoS1ME8gCmA/{imageId}/{variant}
 *
 * Available Variants:
 * - thumb (350 x 219): Small version for lists/tables
 * - full (1600 x 1000): Large version for headers/detail pages
 * - modal (800 x 500): Medium version for modals
 * - gallery (800 x auto): Gallery thumbnail
 * - galleryfull (1600 x auto): Full gallery image
 * - gallerythumb (200 x auto): Tiny gallery thumbnail
 *
 * To add a new team logo:
 * 1. Upload logo to Cloudflare Images
 * 2. Get image ID from Cloudflare dashboard
 * 3. Add entry below with primary image ID, alt text, and optional alternatives
 */

export interface TeamLogoConfig {
  primary: string;
  alternatives?: string[];
  alt: string;
}

const CLOUDFLARE_BASE_URL = 'https://imagedelivery.net/6xApIkGdPK3UoS1ME8gCmA';

/**
 * Team logo mapping
 * Keys are team_key values from the database (e.g., 'TRL', 'SKP', 'ADB')
 *
 * Structure:
 * - primary: The main image ID to use for rendering
 * - alternatives: Optional array of alternative image IDs for reference
 * - alt: Alt text for accessibility
 */
export const TEAM_LOGOS: Record<string, TeamLogoConfig> = {
  'TRL': {
    primary: 'ed44ee29-7e35-490a-1c05-e9063b046400',
    alternatives: ['2f8859bc-ff90-40d3-9376-4bd469b2ca00'],
    alt: 'TRL Team Logo'
  },
  'TBT': {
    primary: 'f7a7ceaa-841a-41b7-a89f-3120ff628000',
    alt: 'TBT Team Logo'
  },

  // Season 22 Teams - Add Cloudflare image IDs as logos become available:
  // 'ADB': { primary: 'xxx', alt: 'Admiraballs Logo' },
  // 'BAD': { primary: 'xxx', alt: 'Bad Cats Logo' },
  // 'CPO': { primary: 'xxx', alt: 'Pants Optional Logo' },
  // 'CRA': { primary: 'xxx', alt: 'Castle Crashers Logo' },
  // 'DIH': { primary: 'xxx', alt: 'Drain in Hell Logo' },
  // 'DOG': { primary: 'xxx', alt: 'The Stray Dogs Logo' },
  // 'DSV': { primary: 'xxx', alt: 'Death Savers Logo' },
  // 'DTP': { primary: 'xxx', alt: 'DTP Logo' },
  // 'ETB': { primary: 'xxx', alt: 'Eighteen Ball Deluxe Logo' },
  // 'FBP': { primary: 'xxx', alt: 'Flippin Big Points Logo' },
  // 'HHS': { primary: 'xxx', alt: 'Hellhounds Logo' },
  // 'ICB': { primary: 'xxx', alt: 'Incrediballs Logo' },
  // 'JMF': { primary: 'xxx', alt: 'Middle Flippers Logo' },
  // 'KNR': { primary: 'xxx', alt: 'Knight Riders Logo' },
  // 'LAS': { primary: 'xxx', alt: 'Little League All Stars Logo' },
  // 'NLT': { primary: 'xxx', alt: 'Northern Lights Logo' },
  // 'NMC': { primary: 'xxx', alt: 'Neuromancers Logo' },
  // 'PBR': { primary: 'xxx', alt: 'Point Breakers Logo' },
  // 'PGN': { primary: 'xxx', alt: 'Pinguins Logo' },
  // 'PKT': { primary: 'xxx', alt: 'Pocketeers Logo' },
  // 'POW': { primary: 'xxx', alt: 'The Power Logo' },
  'PYC': { primary: '0dffc7ea-23b0-4867-5900-99ff8d31ef00', alt: 'Pinballycule Logo' },
  // 'RMS': { primary: 'xxx', alt: 'Magic Saves Logo' },
  // 'RTR': { primary: 'xxx', alt: 'Ramp Tramps Logo' },
  // 'SCN': { primary: 'xxx', alt: 'Seacorns Logo' },
  // 'SHK': { primary: 'xxx', alt: 'Sharks Logo' },
  'SKP': { primary: '51ef7ca6-4c20-4490-2a75-295cbd202900', alt: 'Slap Kraken Pop Logo' },
  // 'SSD': { primary: 'xxx', alt: 'Salty Sea Dogs Logo' },
  // 'SSS': { primary: 'xxx', alt: 'Silverball Slayers Logo' },
  // 'SWL': { primary: 'xxx', alt: 'Specials When Lit Logo' },
  // 'TTT': { primary: 'xxx', alt: 'The Trailer Trashers Logo' },
  // 'TWC': { primary: 'xxx', alt: 'The Wrecking Crew Logo' },
};

/**
 * Get logo URL for a team with the specified Cloudflare variant
 * @param teamKey - Team key (e.g., 'TRL', 'SKP')
 * @param variant - Cloudflare variant (default: 'thumb')
 * @returns Logo URL or null if no logo configured
 */
export function getTeamLogoUrl(
  teamKey: string,
  variant: 'thumb' | 'full' | 'modal' | 'gallery' | 'galleryfull' | 'gallerythumb' = 'thumb'
): string | null {
  const config = TEAM_LOGOS[teamKey];
  if (!config) return null;
  return `${CLOUDFLARE_BASE_URL}/${config.primary}/${variant}`;
}

/**
 * Check if a team has a configured logo
 * @param teamKey - Team key to check
 * @returns True if logo exists in configuration
 */
export function hasTeamLogo(teamKey: string): boolean {
  return teamKey in TEAM_LOGOS;
}

/**
 * Get alt text for a team logo
 * @param teamKey - Team key
 * @returns Alt text or null if no logo configured
 */
export function getTeamLogoAlt(teamKey: string): string | null {
  const config = TEAM_LOGOS[teamKey];
  return config?.alt || null;
}

/**
 * Get all image IDs for a team (primary + alternatives)
 * Useful for managing multiple logo versions
 * @param teamKey - Team key
 * @returns Object with primary and alternatives, or null if no logo configured
 */
export function getTeamLogoImages(teamKey: string): { primary: string; alternatives: string[] } | null {
  const config = TEAM_LOGOS[teamKey];
  if (!config) return null;
  return {
    primary: config.primary,
    alternatives: config.alternatives || []
  };
}
