# MNP Reports System

A comprehensive system for generating analytical reports from Minnesota Pinball League data, incorporating insights from extensive data structure analysis and match mechanics understanding.

## Data Organization Overview

The MNP data follows a structured hierarchy optimized for league management and competitive analysis:

### Data Sources & Structure
- **Primary Source**: Individual match JSON files in `mnp-data-archive/season-XX/matches/`
- **Preprocessed Source**: Flattened CSV file `matches.csv` for rapid analysis
- **Reference Data**: `machines.json` (900+ machine definitions) and `venues.json` for lookups
- **Match Structure**: 4 rounds per match with alternating machine selection rights

### Score Data Architecture
Each score record contains comprehensive context:
- **Machine Context**: Machine name/key, venue location, available machine pool
- **Player Context**: Name, team affiliation, IPR rating (1-6 scale), substitution status
- **Match Context**: Season, week, round number, game completion status
- **Competitive Context**: Home/away designation, strategic positioning

### Data Quality & Reliability Framework

#### Score Reliability by Position (Critical for Analysis)
- **Rounds 1 & 4 (4-player games)**: Players 1-3 scores highly reliable; Player 4 may be inflated due to strategic early completion
- **Rounds 2 & 3 (2-player games)**: Player 1 scores most reliable; Player 2 may show strategic variations
- **Game Completion**: Only `done: true` games should be included in statistical analysis
- **Cross-Machine Comparisons**: Invalid due to vastly different scoring mechanisms

#### Strategic Context Understanding
- **Machine Selection**: Away team selects in rounds 1,3; home team in rounds 2,4
- **Home Venue Advantage**: Teams play on familiar machine pools with known characteristics
- **IPR System**: Individual Player Rating (1-6) correlates with skill but varies by machine type

## Available Reports

### Simple Distribution Report (`simple_distribution_report.py`)
Fast, anonymized score distribution analysis using preprocessed CSV data. **Recommended for most analytical needs.**

**Key Features:**
- Machine-specific score distribution with statistical depth
- Multiple outlier detection methods optimized for pinball data
- Density-based tail removal for cleaner visualizations
- Anonymous output preserving competitive confidentiality
- Comprehensive statistical profiling

**Usage Examples:**
```bash
# Basic analysis with full score range
python simple_distribution_report.py --machine "Attack From Mars" --seasons 4 --output-dir charts

# Clean visualization removing extreme outlier tail
python simple_distribution_report.py --machine "Medieval Madness" --seasons 6 --outlier-method density --outlier-threshold 0.01 --output-dir charts

# Aggressive tail trimming for presentation clarity
python simple_distribution_report.py --machine "Twilight Zone" --seasons 4 --outlier-method density --outlier-threshold 0.05 --output-dir charts
```

**Arguments & Configuration:**
- `--machine, -m`: Full machine name from CSV (e.g., "Attack From Mars", "Medieval Madness")
- `--seasons, -s`: Number of latest seasons (default: 4, range: 1-21)
- `--outlier-method`: Detection approach
  - `none` (default): Include all positive scores - recommended for pinball
  - `iqr`: Remove scores beyond 1.5×IQR from quartiles
  - `percentile`: Remove top/bottom percentiles  
  - `density`: Remove where distribution density drops below threshold (excellent for long tails)
- `--outlier-threshold`: Method-specific threshold (1.5 for IQR, 5.0 for percentile, 0.01-0.1 for density)
- `--output-dir, -o`: Chart output directory
- `--csv-path`: Custom CSV data path

### Legacy Distribution Report (`machine_distribution_report.py`)
Comprehensive JSON-based analysis with detailed data access. Slower but provides maximum analytical depth.

**Features:**
- Direct JSON parsing for granular data access
- Machine key-based selection system
- Advanced outlier detection suite
- Dual visualization (histogram + distribution curve)
- Season-specific output identification

## Output Formats & Visualization

### Chart Components
- **Primary Visualization**: Smooth KDE distribution curve with fill
- **Secondary Analysis**: Box plot showing quartiles and statistical outliers
- **Statistics Panel**: Positioned to avoid overlap, includes:
  - Sample size and data completeness
  - Central tendency (mean, median)
  - Variability measures (standard deviation, IQR)
  - Range information (min/max, quartiles)

### File Organization
- **Simple Reports**: `{Machine_Name}_distribution.png` (anonymous)
- **Legacy Reports**: `{Machine_Key}_distribution_seasons_{XX}-{YY}.png` (detailed)
- **Directory Structure**: Configurable output organization

## Analytical Framework & Best Practices

### Pinball-Specific Considerations

#### Score Validation Pipeline
1. **Positive Score Filter**: Eliminate negative/zero scores (data entry errors)
2. **Completion Status**: Only analyze completed games (`done: true`)
3. **Position Reliability**: Weight Player 1 scores higher in analysis
4. **Machine Context**: Never compare scores across different machine types

#### Statistical Interpretation for Pinball Data
- **Distribution Shape**: Typically right-skewed with long upper tails
- **Median vs. Mean**: Median more robust for skewed pinball distributions
- **Outlier Philosophy**: High scores may represent legitimate exceptional play
- **Variance Sources**: Skill differences, machine knowledge, strategic play

### Outlier Handling Philosophy

#### Recommended Approach by Use Case
1. **Research/Analysis**: Use `--outlier-method none` to preserve all legitimate data
2. **Visualization**: Use `--outlier-method density --outlier-threshold 0.01` for clarity
3. **Presentation**: Use `--outlier-method density --outlier-threshold 0.05` for focus

#### Density-Based Removal Explained
- Calculates KDE across full score range
- Identifies peak density (mode region)
- Sets threshold as percentage of maximum density
- Removes scores where density falls below threshold
- **Result**: Natural cutoff where "interesting" distribution ends

### Advanced Analytical Opportunities

#### Machine-Specific Analysis
- **Difficulty Classification**: Coefficient of variation analysis
- **Skill vs. Luck Components**: Score consistency patterns
- **Strategic Value**: Impact on match outcomes by selection round

#### Competitive Intelligence
- **Home Venue Analysis**: Performance advantages on familiar machines
- **IPR Correlation Studies**: Skill rating validation through performance
- **Team Composition Effects**: Lineup optimization insights

#### Temporal Analysis
- **Learning Curves**: Performance improvement over seasons
- **Meta Evolution**: Strategic shifts in machine selection
- **New Machine Integration**: Adoption and mastery patterns

## Performance & Scalability

### Processing Capabilities
- **CSV Analysis**: Handles 50,000+ score records in seconds
- **JSON Parsing**: Suitable for detailed research but slower for large datasets
- **Memory Efficiency**: Minimal footprint through selective data loading
- **Concurrent Analysis**: Multiple machine reports can be generated simultaneously

### Data Volume Handling
- **Current Scale**: 21 seasons, 900+ machines, 50,000+ individual scores
- **Growth Accommodation**: Architecture scales linearly with data volume
- **Storage Requirements**: Minimal - generates reports on-demand without intermediate storage

## Future Enhancements & Research Directions

### Planned Report Types
- **Player Performance Profiling**: Individual skill progression analysis
- **Team Dynamics Study**: Lineup optimization and chemistry analysis
- **Venue Advantage Quantification**: Home field advantage measurement
- **Machine Selection Strategy**: Competitive advantage analysis

### Technical Improvements
- **Interactive Visualizations**: Web-based exploration tools
- **Automated Report Generation**: Scheduled league summary production
- **Real-time Analysis**: Live match data integration
- **Machine Learning Integration**: Predictive performance modeling

## Configuration Templates

### High-Level Research Analysis
```bash
# Comprehensive machine analysis across maximum seasons
python simple_distribution_report.py --machine "Medieval Madness" --seasons 10 --outlier-method none --output-dir research_output
```

### Presentation-Ready Visualizations
```bash
# Clean, focused charts for league presentations
python simple_distribution_report.py --machine "Attack From Mars" --seasons 4 --outlier-method density --outlier-threshold 0.02 --output-dir presentation_charts
```

### Comparative Machine Studies
```bash
# Generate standardized reports for multiple machines
for machine in "Medieval Madness" "Attack From Mars" "Twilight Zone"; do
  python simple_distribution_report.py --machine "$machine" --seasons 4 --outlier-method density --outlier-threshold 0.01 --output-dir comparative_analysis
done
```

---

**System Version**: 2.0  
**Data Coverage**: Seasons 14-21 (Current)  
**Last Updated**: Analysis framework updated with density-based outlier removal and anonymized output
**Maintainer**: MNP Analytics Team

*This documentation evolves with system capabilities and analytical insights. Refer to individual script documentation for implementation-specific details.*