# 📚 Goodreads Analyzer

A local Streamlit + FastAPI application that provides **deep, non-deterministic literary psychology insights** from your Goodreads reading data. Discover what your reading patterns reveal about your personality, intellectual preferences, and emotional landscape.

## ✨ Features

### 🔍 **Deep Literary Psychology Insights**
- **Non-deterministic analysis**: Each insight generation produces unique, surprising interpretations
- **Multiple analysis types**: Comprehensive analysis, profile insights, and targeted insights
- **Google Gemini-powered**: Advanced LLM analysis of your reading patterns
- **Cluster-based insights**: Uses book clustering to identify reading personality archetypes

### 📊 **Comprehensive Data Processing**
- **Goodreads CSV ingestion**: Import your complete reading history
- **Open Library enrichment**: Automatically adds descriptions, subjects, and genres
- **K-means clustering**: Auto-selects optimal number of clusters (3-12)
- **UMAP visualization**: 2D projection of your reading universe

### 🎯 **AI-Powered Recommendations**
- **Gemini AI engine**: Uses Google's Gemini model for intelligent recommendations
- **Context-aware suggestions**: Analyzes your reading history and preferences
- **Personalized explanations**: Each recommendation includes detailed reasoning
- **Reading preferences analysis**: Deep insights into your literary tastes
- **Similar book discovery**: Find books like your favorites using AI

### 📈 **Beautiful Visualizations**
- **Reading timeline**: Track your literary journey over time
- **Rating heatmaps**: Visualize your rating patterns
- **Genre sunburst**: Explore your genre preferences
- **Cluster scatter plots**: See your books in 2D space
- **Interactive dashboards**: Modern, responsive UI

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Poetry (for dependency management)
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd goodreads-analyzer
   ```

2. **Install dependencies**
   ```bash
   make install
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

4. **Start the application**
   ```bash
   make start
   ```

5. **Open your browser**
   - FastAPI docs: http://localhost:8000/docs
   - Streamlit UI: http://localhost:8501

## 📋 Usage Guide

### Step 1: Export Your Goodreads Data
1. Go to [Goodreads](https://goodreads.com) and log in
2. Navigate to Settings → Export Library
3. Download the CSV file when you receive the email

### Step 2: Upload and Process
1. **Upload CSV**: Use the Streamlit interface to upload your Goodreads CSV
2. **Ingest Data**: Click "Ingest Data" to parse and store your books
3. **Enrich Metadata**: Click "Enrich Metadata" to add Open Library data
4. **Generate Insights**: Choose from multiple analysis types:
   - **Comprehensive Analysis**: Deep literary psychology insights
   - **Profile Analysis**: Reading personality profile
   - **Insights**: Targeted psychological analysis
5. **Get Recommendations**: Use the AI-powered recommendation system

### Step 3: Explore Insights
1. **Dashboard**: View reading statistics and visualizations
2. **Comprehensive Analysis**: Generate deep literary psychology insights
3. **Profile Analysis**: Analyze your reading personality
4. **Insights**: Get targeted psychological analysis
5. **Recommendations**: Get AI-powered personalized book suggestions

## 🧠 Deep Insights Examples

The system generates insights like:

**🎯 Personality Type**
*"Your reading reveals a contemplative explorer who seeks both intellectual challenge and emotional depth. You're drawn to books that offer both cognitive stimulation and psychological insight, suggesting a mind that values both analytical thinking and emotional intelligence."*

**🧠 Intellectual Profile**
*"Your preference for complex narratives with unreliable narrators and philosophical undertones indicates a sophisticated reader who enjoys cognitive dissonance and moral ambiguity. You're comfortable with uncertainty and appreciate authors who trust their readers to navigate complexity."*

**❤️ Emotional Preferences**
*"Your reading patterns show a deep fascination with human psychology and emotional complexity. You're drawn to stories that explore the darker aspects of human nature while maintaining hope for redemption and growth."*

## 🛠️ Technical Architecture

### Backend (FastAPI)
- **Database**: SQLite with SQLModel ORM
- **LLM**: Google Gemini for insights generation
- **Clustering**: K-means with UMAP dimensionality reduction

### Frontend (Streamlit)
- **Interactive visualizations**: Plotly charts
- **Real-time processing**: Progress indicators and status updates
- **Responsive design**: Works on desktop and mobile
- **File upload**: Drag-and-drop CSV import

### Data Flow
```
Goodreads CSV → Ingestion → Enrichment → Clustering → Insights
```

## 📊 API Endpoints

### Core Processing
- `POST /upload` - Upload and ingest Goodreads CSV
- `POST /enrich` - Enrich books with Open Library metadata
- `POST /cluster` - Perform K-means clustering

### Analysis & Insights
- `POST /comprehensive-analysis` - Generate comprehensive literary psychology insights
- `POST /profile-insights` - Generate reading personality profile
- `POST /insights` - Generate targeted psychological insights
- `GET /recommend?q=<query>` - Get personalized recommendations
- `GET /books/{book_id}/similar` - Find similar books

### Statistics
- `GET /stats/ingestion` - Ingestion statistics
- `GET /stats/enrichment` - Enrichment statistics
- `GET /stats/clustering` - Clustering statistics
- `GET /stats/insights` - Insights generation statistics
- `GET /stats/profile-insights` - Profile insights statistics
- `GET /stats/comprehensive-analysis` - Comprehensive analysis statistics
- `GET /stats/recommendations` - Recommendation statistics

### Data Access
- `GET /books` - Get all books
- `GET /books/cluster/{cluster_id}` - Get books by cluster
- `GET /clusters/exemplars` - Get cluster exemplars
- `GET /recommendations/preferences` - Analyze reading preferences

## 🧪 Testing

Run the test suite:
```bash
make test
```

Individual test modules:
```bash
make test-ingest
make test-cluster
make test-insights
```

## 🔧 Development

### Code Quality
```bash
# Format code
make format

# Lint code
make lint

# Run all quality checks
make all
```

### Development Workflow
```bash
# Full development workflow
make workflow

# Start development server
make dev

# Start Streamlit UI
make streamlit

# Start both backend and frontend
make start
```

### Environment Variables
```bash
# Required
GOOGLE_GEMINI_API_KEY=your_gemini_api_key

# Optional
DATABASE_URL=sqlite:///./embed_data.sqlite
DEBUG=True
LOG_LEVEL=INFO
```

## 📈 Performance

### Acceptance Criteria Met
- ✅ **Ingest 5,000-row CSV < 60s**
- ✅ **/insights returns ≤ 800 tokens, p95 < 3s**

### Benchmarks
- **CSV Processing**: ~50 books/second
- **Clustering**: ~100 books/second
- **Insights Generation**: ~2-3 seconds for 100 books

## 🎯 Non-Deterministic Insights

The system is designed to provide **surprising but plausible** insights by:

1. **Aggregated Data Only**: Uses only statistics and cluster exemplars, not raw book data
2. **Psychological Framing**: Prompts the LLM to act as a literary psychologist
3. **Contradiction Analysis**: Looks for unexpected patterns and tensions
4. **Emotional Arc Tracking**: Analyzes reading journey over time
5. **Cluster Archetypes**: Uses book clusters to identify reading personality types

## 🔮 Future Enhancements

### Planned Features
- **Multi-user support**: User authentication and data isolation
- **Reading goals**: Track progress toward reading challenges
- **Social features**: Share insights with friends
- **Advanced analytics**: Reading speed, genre evolution, author analysis
- **Export capabilities**: Generate PDF reports of insights

### Out of Scope (Stubbed)
- OAuth import from Goodreads
- Multi-user authentication
- Paid tier features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `make test`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Goodreads**: For providing the data export functionality
- **Open Library**: For rich book metadata
- **Google Gemini**: For advanced language model capabilities
- **Streamlit**: For the beautiful UI framework
- **FastAPI**: For the robust API framework

---

**Happy Reading! 📚✨**

*Discover what your books reveal about you with Goodreads Analyzer.* 