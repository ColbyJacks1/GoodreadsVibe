# Archived Files

This directory contains files that were moved from the main codebase because they are no longer being used.

## App Modules (app/)

### enrich.py
- **Reason**: The OpenLibraryEnricher class is defined but never imported or used anywhere in the codebase
- **Status**: Completely unused
- **Action**: Can be safely deleted if enrichment functionality is not needed

### insights.py  
- **Reason**: Only used in tests, not in the main application
- **Status**: Unused in production
- **Action**: Can be safely deleted if insights functionality is not needed

### profile_insights.py
- **Reason**: Only used in tests, not in the main application  
- **Status**: Unused in production
- **Action**: Can be safely deleted if profile insights functionality is not needed

### recommend.py
- **Reason**: Only used in tests, not in the main application
- **Status**: Unused in production  
- **Action**: Can be safely deleted if recommendation functionality is not needed

## Test Files (tests/)

### test_insights.py
- **Reason**: Tests for unused insights module
- **Status**: Unused
- **Action**: Can be safely deleted

### test_recommend.py  
- **Reason**: Tests for unused recommend module
- **Status**: Unused
- **Action**: Can be safely deleted

## Data Files

### sample-data.csv
- **Reason**: Not referenced anywhere in the codebase
- **Status**: Unused sample data
- **Action**: Can be safely deleted

## Prompt Files (prompts/)

### comprehensive_analysis_prompt.md
- **Reason**: Generates all 4 sections in 1 prompt (not wanted)
- **Status**: Replaced by 2-generation workflow
- **Action**: Can be safely deleted

### profile_prompt.md
- **Reason**: Only used by archived profile_insights.py module
- **Status**: Unused in production
- **Action**: Can be safely deleted

### recommendation_prompt.md
- **Reason**: Only used by archived recommend.py module
- **Status**: Unused in production
- **Action**: Can be safely deleted

### insight_prompt.md
- **Reason**: Only used by archived insights.py module
- **Status**: Unused in production
- **Action**: Can be safely deleted

## Recovery

If you need to restore any of these files, simply move them back to their original locations:

```bash
# Restore app modules
mv archive/enrich.py app/
mv archive/insights.py app/  
mv archive/profile_insights.py app/
mv archive/recommend.py app/

# Restore test files
mv archive/test_insights.py tests/
mv archive/test_recommend.py tests/

# Restore data file
mv archive/sample-data.csv ./

# Restore prompt files
mv archive/comprehensive_analysis_prompt.md prompts/
mv archive/profile_prompt.md prompts/
mv archive/recommendation_prompt.md prompts/
mv archive/insight_prompt.md prompts/

## Current Active Files

The following files are still actively used:

### App Modules
- `app/comprehensive_analysis.py` - Main analysis engine
- `app/session_db.py` - Session management  
- `app/ingest.py` - CSV ingestion
- `app/db.py` - Database models
- `app/cluster.py` - Clustering (deprecated but still imported)

### Test Files
- `tests/test_ingest.py` - Tests for ingestion
- `tests/test_cluster.py` - Tests for clustering

### Configuration
- Active prompt files in `prompts/` directory:
  - `comprehensive_analysis_prompt_parallel.md` - Used by comprehensive_analysis.py for insights + profile
  - `quick_analysis_prompt.md` - Used by comprehensive_analysis.py for roast + recommendations
- `create_sample_db.py` - Database setup
- Configuration files (pyproject.toml, requirements.txt, etc.) 