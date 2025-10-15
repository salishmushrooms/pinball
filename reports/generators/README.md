# MNP Report Generators - Summary

This document provides an overview of all available report generators for MNP (Monday Night Pinball) data analysis.

*Last Updated: 2025-09-09*

---

## 📊 Core Analysis Generators

### 1. **Venue Summary Report** (`venue_summary_report.py`)
**Purpose**: Generates comprehensive venue statistics including machine-specific scoring data and player performance.

**Key Features**:
- Machine statistics (median scores, percentiles, high scores)
- Player performance records and team statistics  
- Home vs away team machine selection analysis
- Round-by-round game distribution analysis
- Two output formats: detailed (with charts/tables) and simplified

**Usage**: `python venue_summary_report.py <config_file>`

**Example Config**: Venue code, season, data filters, score reliability settings, output format preferences

**Sample Output**: `reports/output/{venue_code}_venue_summary_season_{season}.md`

---

### 2. **Score Percentile Report** (`score_percentile_report.py`)
**Purpose**: Creates charts and reports showing score vs percentile rankings for specific machines.

**Key Features**:
- Score vs percentile charts (matplotlib PNG files)
- Text reports with statistics and top scores
- Multi-machine support with auto-discovery
- Filtering by venue, IPR ranges, and outlier removal
- Aggregate grid images for multiple machines

**Usage**: `python score_percentile_report.py <config_file>`

**Key Options**: Season(s), target machine(s), venue filter, IPR filter, outlier filtering

**Sample Output**: 
- Charts: `reports/charts/{machine}_percentile_season_{season}_{venue}.png`
- Reports: `reports/output/{machine}_percentile_season_{season}_{venue}.md`

---

## 🏠 Home Field Advantage Analyzers

### 3. **Home Advantage IPR Analysis** (`home_advantage_ipr_analysis.py`)
**Purpose**: Quantifies home field advantage in IPR equivalent terms using binary win/loss outcomes.

**Key Features**:
- Logistic regression modeling P(Home Win) vs IPR Differential
- Calculates "IPR equivalent" of home advantage (~3.5 IPR points)
- Binned analysis showing win rates by IPR advantage ranges
- Statistical validation with confidence intervals

**Usage**: `python home_advantage_ipr_analysis.py <season>`

**Key Finding**: Home field advantage worth approximately 3.5 IPR points

---

### 4. **Home Advantage IPR Analysis (Point Differential)** (`home_advantage_ipr_analysis_points.py`) ⭐ **UPDATED**
**Purpose**: Enhanced version using point differentials instead of win/loss for more nuanced analysis.

**Key Features**:
- Linear regression: `point_diff = intercept + slope × ipr_diff`
- More precise quantification of home advantage in match points
- Statistical significance testing for both home advantage and IPR effects
- Better explanatory power (R² ~47% vs binary approach)

**Usage**: `python home_advantage_ipr_analysis_points.py <season>`

**Key Findings**: 
- Home advantage: 5.78 points (highly significant)
- IPR effect: 1.25 points per IPR point
- Home advantage equivalent to 4.6 IPR points

---

### 5. **Venue-Controlled IPR Analysis** (`venue_controlled_ipr_analysis.py`)
**Purpose**: Separates venue familiarity effects from skill (IPR) effects by analyzing different match types.

**Key Features**:
- Analyzes normal home/away vs "home vs home" matches
- Validates IPR predictive power when venue is controlled (0.888 correlation)
- Isolates pure venue advantage from team strength effects
- Statistical validation of analysis methodology

**Usage**: `python venue_controlled_ipr_analysis.py <season>`

**Key Insight**: 6.6 percentage point advantage from pure venue familiarity

**Future Improvement**: Consider point differentials for more nuanced analysis

---

### 6. **Venue Home Advantage Analysis** (`venue_home_advantage_analysis.py`)
**Purpose**: Analyzes home field advantage for each individual venue using win/loss outcomes.

**Key Features**:
- Ranks venues by home team win percentage
- Identifies venues with strongest/weakest home advantages
- Statistical analysis where sufficient data exists
- Visualization of venue advantages

**Usage**: `python venue_home_advantage_analysis.py <season>`

**Note**: May show inflated advantages due to using simplified point totals

---

### 7. **Corrected Venue Home Advantage Analysis** (`venue_home_advantage_corrected.py`) ⭐ **CORRECTED**
**Purpose**: Enhanced venue analysis using proper point attribution based on round structure.

**Key Features**:
- Correct point calculation based on round structure:
  - Round 1: Away, Home, Away, Home (positions 1,2,3,4)
  - Round 2: Home, Away (positions 1,2)
  - Round 3: Away, Home (positions 1,2)
  - Round 4: Home, Away, Home, Away (positions 1,2,3,4)
- IPR-adjusted advantage using linear regression
- More realistic home advantage percentages (~52% vs previous 62%+)
- Statistical controls for team strength differences

**Usage**: `python venue_home_advantage_corrected.py <season>`

**Key Improvement**: Provides accurate venue advantages isolated from team strength

---

## 🎯 Machine-Specific Analyzers

### 8. **Home vs Away Advantage Report** (`home_away_advantage_report.py`)
**Purpose**: Compares points earned by home vs away teams for each machine at a specific venue.

**Key Features**:
- Machine-by-machine breakdown of home vs away point totals
- Calculates home/away ratios to identify machine-specific advantages
- Sorts machines by home team advantage
- Simple one-line per machine format

**Usage**: `python home_away_advantage_report.py <venue_code> <venue_name> <season>`

**Sample Output**: Shows which machines at a venue favor home teams most

**Future Improvement**: Enhance to analyze point differentials per game while controlling for IPR

---

## 🏟️ Configuration System

### Configuration Files (`reports/configs/`)
- **Comprehensive configs**: All settings in one file
- **Modular configs**: Separate files for seasons, machines, venues, IPR filters
- **Preset configs**: Pre-built configurations for common analyses
- **Example configs**: Template configurations for each generator

### Key Configuration Options:
- **Seasons**: Single or multiple seasons
- **Machines**: Specific machines, auto-discovery, or comma-separated lists
- **Venues**: Venue filtering options
- **IPR Filters**: Player skill range filtering
- **Outlier Filtering**: Multiple methods (percentile, IQR, absolute)
- **Output Formats**: Detailed vs simplified reports

---

## 📈 Data Processing Features

### Common Capabilities:
- **Machine name normalization** using variations mapping
- **Score reliability filtering** based on round structure and player positions
- **IPR-based analysis** for skill-adjusted insights
- **Statistical validation** with significance testing where applicable
- **Multiple output formats** (Markdown reports, PNG charts, aggregate images)

### Round Structure Understanding:
- **Round 1**: 4 players (Away, Home, Away, Home)
- **Round 2**: 2 players (Home, Away) 
- **Round 3**: 2 players (Away, Home)
- **Round 4**: 4 players (Home, Away, Home, Away)

### Point Attribution:
- Correct calculation based on individual player points (`points_1`, `points_2`, etc.)
- Proper home/away attribution based on round structure
- Statistical controls for team strength (IPR) differences

---

## 🔄 Future Improvements

### Identified Enhancements:
1. **Point Differential Integration**: Apply point differential analysis to venue-controlled and machine-specific analyses for more nuanced insights

2. **Enhanced Statistical Methods**: 
   - Mixed-effects models for venue and machine effects
   - Bayesian analysis for uncertainty quantification
   - Time-series analysis for trends over seasons

3. **Machine-Level Granularity**: 
   - Point differentials per game on each machine
   - IPR-adjusted machine-specific home advantages
   - Machine familiarity effects analysis

4. **Interactive Dashboards**: 
   - Web-based interfaces for dynamic filtering
   - Real-time analysis capabilities
   - Interactive visualizations

---

## 🛠️ Usage Guidelines

### Getting Started:
1. Ensure data is in `mnp-data-archive/` directory structure
2. Install required Python packages: `numpy`, `matplotlib`, `scikit-learn`, `scipy`, `pillow`
3. Choose appropriate generator based on analysis needs
4. Configure parameters via config files or command line arguments
5. Review output files in `reports/output/` and `reports/charts/`

### Best Practices:
- Use **corrected** versions of analyzers when available
- Apply **point differential** methods for more precise insights  
- Consider **IPR adjustments** when comparing teams or venues
- Validate results using **home vs home** matches where possible
- Document configuration choices for reproducible analysis

### File Organization:
```
reports/
├── generators/          # Analysis scripts
├── configs/            # Configuration files  
├── output/             # Generated reports (markdown)
├── charts/             # Generated charts (PNG)
└── README.md           # This documentation
```

---

*This documentation covers all current generators as of 2025-09-09. For specific usage examples and detailed configuration options, refer to individual script documentation and example config files.*