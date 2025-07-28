# Genre Normalization System

## Overview

The genre normalization system addresses the problem of inconsistent and granular genre data from Goodreads. The original `bookshelves` field contains user-defined tags that are often inconsistent, case-sensitive, and overly specific (e.g., "1939-1945", "World War", "Fiction" vs "fiction").

## Problem

The original genre processing showed issues like:
- **Inconsistent capitalization**: "Fiction" vs "fiction"
- **Overly specific categories**: "1939-1945", "World War", "military-history"
- **Granular subcategories**: "epic-fantasy", "high-fantasy", "urban-fantasy"
- **User-defined variations**: "sci-fi", "scifi", "science fiction", "sf"
- **Negative percentages** in charts due to data quality issues

## Solution

The `GenreNormalizer` class provides a comprehensive mapping system that:

1. **Standardizes 33 main categories** from hundreds of variants
2. **Handles case sensitivity** and common variations
3. **Maps specific subcategories** to broader, meaningful categories
4. **Provides fallback logic** for unrecognized genres

## Standardized Categories

### Fiction Categories
- `fiction` - General fiction, literary fiction, contemporary fiction
- `science_fiction` - Science fiction, sci-fi, scifi, sf
- `fantasy` - Fantasy, epic-fantasy, high-fantasy, urban-fantasy
- `mystery` - Mystery, detective, crime, thriller, suspense
- `romance` - Romance, romantic, love-story, chick-lit
- `historical_fiction` - Historical fiction, period fiction
- `young_adult` - Young adult, YA, teen, adolescent
- `children` - Children's books, middle-grade, juvenile
- `classics` - Literary classics, canon works

### Non-Fiction Categories
- `non_fiction` - General non-fiction
- `biography` - Biography, memoir, autobiography
- `history` - History, military history, world war
- `philosophy` - Philosophy, ethics, metaphysics
- `science` - Science, physics, chemistry, biology
- `psychology` - Psychology, mental health
- `self_help` - Self-help, personal development, motivation
- `business` - Business, economics, finance, management
- `politics` - Politics, government, current events
- `religion` - Religion, spirituality, theology
- `travel` - Travel, travelogue, exploration
- `cookbook` - Cookbooks, cooking, food, recipes
- `art` - Art, photography, design, architecture
- `education` - Education, academic, textbook, reference

### Special Categories
- `poetry` - Poetry, poems, verse
- `drama` - Drama, plays, theater
- `comics` - Comics, graphic novels, manga
- `horror` - Horror, supernatural, paranormal
- `western` - Western, cowboy, wild west
- `war` - War, military, battle, conflict
- `adventure` - Adventure, action, exploration
- `satire` - Satire, humor, comedy
- `dystopian` - Dystopian, post-apocalyptic
- `steampunk` - Steampunk, cyberpunk, alternate history

## Usage

### During Ingestion

The normalization happens automatically during CSV ingestion:

```python
from app.ingest import GoodreadsIngester

ingester = GoodreadsIngester()
stats = ingester.ingest_csv("your_goodreads_export.csv")
```

### Manual Normalization

```python
from app.ingest import GenreNormalizer

normalizer = GenreNormalizer()

# Normalize a single genre
normalized = normalizer.normalize_genre("sci-fi")  # Returns "science_fiction"

# Normalize a bookshelves string
bookshelves = "fiction, fantasy, science-fiction"
normalized = normalizer.normalize_bookshelves(bookshelves)
# Returns ["fiction", "fantasy", "science_fiction"]
```

### Updating Existing Data

To update existing books in the database:

```bash
poetry run python update_existing_genres.py
```

## Benefits

1. **Consistent Categories**: Reduces hundreds of variants to 33 meaningful categories
2. **Better Analytics**: Enables meaningful genre distribution analysis
3. **Improved Visualizations**: Cleaner pie charts and statistics
4. **Enhanced Recommendations**: Better genre-based book recommendations
5. **Data Quality**: Eliminates negative percentages and inconsistent data

## Statistics

The normalization system provides:
- **33 standardized categories** vs hundreds of original variants
- **134 variant mappings** covering common Goodreads tags
- **Automatic case handling** and common pattern recognition
- **Fallback logic** for unrecognized genres

## Testing

Run the test script to see the normalization in action:

```bash
poetry run python test_genre_normalization.py
```

Compare original vs normalized genres:

```bash
poetry run python compare_genres.py
```

## Migration

For existing databases, the `update_existing_genres.py` script will:
1. Read all existing books
2. Normalize their bookshelves
3. Update the `genres` field with standardized categories
4. Preserve original `bookshelves` for reference

## Future Enhancements

The system can be extended by:
1. Adding new genre mappings to the `genre_mappings` dictionary
2. Implementing machine learning for automatic genre detection
3. Adding support for multi-language genre normalization
4. Creating genre hierarchies (e.g., subgenres within fantasy) 