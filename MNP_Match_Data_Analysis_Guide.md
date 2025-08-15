# MNP Match Data Analysis Guide

## Overview
This document provides a comprehensive guide to analyzing Minnesota Pinball League (MNP) match data, including data structure, scoring mechanics, reliability considerations, and analytical opportunities.

## Season Structure

### Organization
- **Current Season**: Season 21 (`mnp-data-archive/season-21`)
- **Regular Season**: 10 weeks of matches
- **Teams**: Up to 10 players per team
- **Match Distribution**: Each team plays 5 home matches and 5 away matches

### Venue Considerations
- Teams typically play at their designated home venue
- **Exception**: When both teams share the same home venue, one team is designated as "home" and one as "away" for match purposes

## Match Structure

### Round Format
Each match consists of 4 rounds with alternating machine selection:

| Round | Machine Selection | Player Configuration | Game Type |
|-------|-------------------|---------------------|-----------|
| 1 | Away Team | 4-player (P1: Away, P2: Home, P3: Away, P4: Home) | Doubles |
| 2 | Home Team | 2-player (P1: Home, P2: Away) | Singles |
| 3 | Away Team | 2-player (P1: Away, P2: Home) | Singles |
| 4 | Home Team | 4-player (P1: Home, P2: Away, P3: Home, P4: Away) | Doubles |

### Player Positioning
- **Rounds 1 & 4 (Doubles)**: 4 players total
- **Rounds 2 & 3 (Singles)**: 2 players total
- **Strategic Importance**: Machine selection alternates to balance competitive advantage

## Scoring Mechanics & Data Reliability

### Score Reliability by Position

#### Highly Reliable Scores
- **4-player games (Rounds 1, 4)**: Players 1, 2, and 3 scores are generally reliable
- **2-player games (Rounds 2, 3)**: Player 1 scores are most reliable

#### Potentially Skewed Scores
- **4-player games**: Player 4 scores may be inflated if they don't need to complete their full game after seeing opponents' scores
- **2-player games**: Player 2 scores may be affected by strategic play once Player 1's score is known

### Cross-Machine Score Comparisons
- **Within Machine**: Scores are directly comparable and meaningful
- **Between Machines**: Scores are NOT directly comparable due to vastly different scoring mechanisms
- **Analysis Approach**: Normalize scores by machine or use percentile rankings within machine

## Player Rating System

### IPR (Individual Player Rating)
- **Scale**: 1-6 (6 = highest skill level)
- **Purpose**: Correlates with player skill level
- **Analytical Use**: Compare performance expectations vs. actual results by IPR level

## Key Analytical Opportunities

### Performance Analysis
1. **Home Venue Advantage**
   - Compare home vs. away team performance
   - Identify venues with strongest home field advantage
   - Account for venue-specific machine availability

2. **Score Variability by Machine**
   - Calculate coefficient of variation for each machine
   - Identify "high-variance" vs. "consistent" machines
   - Correlate with strategic machine selection

3. **IPR vs. Performance Correlation**
   - Machine-specific IPR performance correlation
   - Identify machines that favor higher/lower IPR players
   - Validate IPR accuracy through performance data

### Strategic Analysis
4. **Machine Selection Patterns**
   - Predict machine choices based on:
     - Team composition (IPR distribution)
     - Historical performance on specific machines
     - Venue availability
   - Identify "signature" machines for teams/players

5. **Competitive Balance**
   - Away team win percentage by machine
   - Home team win percentage by machine
   - Machine selection impact on match outcomes

### Advanced Analytics
6. **Performance Prediction Models**
   - Player performance on specific machines given IPR
   - Team performance based on lineup composition
   - Machine selection optimization

7. **Venue-Specific Analysis**
   - Machine performance consistency across venues
   - Venue-specific advantages for certain play styles
   - Impact of machine condition/maintenance on scores

## Data Processing Considerations

### Score Normalization Approaches
1. **Z-Score by Machine**: `(score - machine_mean) / machine_std`
2. **Percentile Ranking**: Position within machine score distribution
3. **IPR-Adjusted Performance**: Compare to expected performance by IPR level

### Filtering Strategies
- Exclude potentially unreliable Player 4 scores in doubles rounds
- Focus on Player 1 scores in singles rounds for most analyses
- Consider game completion status when available

### Statistical Considerations
- Account for small sample sizes on individual machines
- Consider seasonal effects and learning curves
- Handle missing data appropriately (incomplete games, etc.)

## Future Research Directions

### Machine Meta-Analysis
- Machine difficulty classification
- Skill vs. luck components by machine
- Optimal play strategies by machine type

### Team Dynamics
- Lineup optimization strategies
- Player chemistry and performance
- Captain decision-making patterns

### League Evolution
- Performance trends over seasons
- Meta-game evolution (strategy changes)
- New machine integration effects

## Implementation Notes

### Data Quality Checks
- Verify score reasonableness by machine
- Check for data entry errors
- Validate game completion status
- Cross-reference with photo evidence when available

### Performance Metrics
- Win/loss records by various dimensions
- Score-based performance metrics
- Consistency measures
- Head-to-head comparisons

---

**Last Updated**: [Current Date]  
**Version**: 1.0  
**Maintainer**: [Your Name]

*This document will be expanded and refined as analysis progresses and new insights are discovered.*