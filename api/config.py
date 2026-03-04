"""
MNP API Configuration Constants

Central location for season-related constants used across API endpoints.
Update CURRENT_SEASON at the start of each new season.
"""

# The currently active MNP season
CURRENT_SEASON = 23

# All seasons loaded in the production database
AVAILABLE_SEASONS = [20, 21, 22, CURRENT_SEASON]

# Default seasons for multi-season analysis (current + previous)
DEFAULT_ANALYSIS_SEASONS = [CURRENT_SEASON - 1, CURRENT_SEASON]
