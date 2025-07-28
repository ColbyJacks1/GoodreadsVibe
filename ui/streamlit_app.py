"""Streamlit UI for book-mirror-plus."""

import streamlit as st
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import os

# Configure page
st.set_page_config(
    page_title="Book Mirror Plus",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = "http://localhost:8000"

def make_api_request(endpoint, method="GET", data=None, files=None):
    """Make API request to FastAPI backend."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=300)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, timeout=300)
            else:
                response = requests.post(url, json=data, timeout=300)
        else:
            return None
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Please make sure the FastAPI backend is running on http://localhost:8000")
        return None
    except requests.exceptions.Timeout:
        st.error("⏰ API request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def main():
    st.title("📚 Book Mirror Plus")
    st.markdown("Deep literary psychology insights from your Goodreads data")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Upload & Process", "Dashboard", "Insights", "Profile Analysis", "Recommendations"]
    )
    
    if page == "Upload & Process":
        show_upload_page()
    elif page == "Dashboard":
        show_dashboard_page()
    elif page == "Insights":
        show_insights_page()
    elif page == "Profile Analysis":
        show_profile_analysis_page()
    elif page == "Recommendations":
        show_recommendations_page()

def show_upload_page():
    st.header("📤 Upload & Process")
    
    # Database reset option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Upload your Goodreads CSV file to analyze your reading data.")
    with col2:
        if st.button("🗑️ Reset Database", type="secondary"):
            with st.spinner("Resetting database..."):
                result = make_api_request("/reset", method="GET")
                if result and result.get('status') == 'success':
                    st.success("✅ Database reset successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to reset database")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload your Goodreads CSV file",
        type=['csv'],
        help="Export your Goodreads library as CSV and upload it here"
    )
    
    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")
        
        # Process buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Ingest Data"):
                with st.spinner("Ingesting CSV data..."):
                    files = {"file": uploaded_file}
                    result = make_api_request("/upload", method="POST", files=files)
                    if result:
                        st.success(f"✅ Ingested {result['processed_books']} books")
                        st.json(result)
        
        with col2:
            if st.button("🔍 Enrich Metadata"):
                with st.spinner("Enriching with Open Library data..."):
                    result = make_api_request("/enrich", method="POST")
                    if result:
                        st.success(f"✅ Enriched {result['enriched']} books")
                        st.json(result)

def show_dashboard_page():
    st.header("📊 Dashboard")
    
    # Get statistics
    stats_data = {}
    stat_endpoints = [
        ("ingestion", "📥 Ingestion", "total_books"),
        ("enrichment", "🔍 Enrichment", "total_books"),
    ]
    
    cols = st.columns(len(stat_endpoints))
    for i, (endpoint, title, stat_key) in enumerate(stat_endpoints):
        with cols[i]:
            result = make_api_request(f"/stats/{endpoint}")
            if result and result.get('success'):
                stats = result.get('stats', {})
                st.metric(title, stats.get(stat_key, 0))
            else:
                st.metric(title, "N/A")
    
    # Get books data
    books_result = make_api_request("/books")
    if books_result and isinstance(books_result, list):
        books_df = pd.DataFrame(books_result)
    else:
        books_df = pd.DataFrame()
    
    # Add table view for books
    if not books_df.empty:
        st.subheader("📚 Book List")
        table_df = books_df[[
            'title',
            'author',
            'date_read',
            'my_rating'
        ]].copy() if all(col in books_df.columns for col in ['title', 'author', 'date_read', 'my_rating']) else pd.DataFrame()
        if not table_df.empty:
            table_df = table_df.rename(columns={
                'title': 'Title',
                'author': 'Author',
                'date_read': 'Date Read',
                'my_rating': 'Rating'
            })
            st.dataframe(table_df, use_container_width=True)
        
        # Reading timeline
        st.subheader("📅 Reading Timeline")
        if 'date_read' in books_df.columns:
            timeline_df = books_df[books_df['date_read'].notna()].copy()
            if not timeline_df.empty:
                timeline_df['date_read'] = pd.to_datetime(timeline_df['date_read'])
                timeline_df = timeline_df.sort_values('date_read')
                
                # Group by year and count books
                timeline_df['year'] = timeline_df['date_read'].dt.year
                yearly_counts = timeline_df['year'].value_counts().sort_index()
                
                fig = px.bar(
                    x=yearly_counts.index,
                    y=yearly_counts.values,
                    title="Books Read by Year",
                    labels={'x': 'Year', 'y': 'Number of Books'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Ratings heatmap
        st.subheader("⭐ Ratings Heatmap")
        if 'my_rating' in books_df.columns:
            ratings_df = books_df[books_df['my_rating'].notna()]
            if not ratings_df.empty:
                # Create rating distribution
                rating_counts = ratings_df['my_rating'].value_counts().sort_index()
                
                fig = px.bar(
                    x=rating_counts.index,
                    y=rating_counts.values,
                    title="Rating Distribution",
                    labels={'x': 'Rating', 'y': 'Number of Books'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Genre sunburst (if available)
        st.subheader("📚 Genre Distribution")
        if 'genres' in books_df.columns:
            genres_df = books_df[books_df['genres'].notna()]
            if not genres_df.empty:
                # Extract genres
                all_genres = []
                for genres in genres_df['genres']:
                    if genres:
                        genre_list = [g.strip() for g in genres.split(',')]
                        all_genres.extend(genre_list)
                
                if all_genres:
                    genre_counts = pd.Series(all_genres).value_counts()
                    
                    fig = px.pie(
                        values=genre_counts.values,
                        names=genre_counts.index,
                        title="Genre Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)





def show_insights_page():
    st.header("🧠 Literary Psychology Insights")
    
    # Check if insights can be generated
    insights_stats = make_api_request("/stats/insights")
    if insights_stats and insights_stats.get('success'):
        stats = insights_stats['stats']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Books", stats.get('total_books', 0))
        with col2:
            st.metric("Books with Ratings", stats.get('books_with_ratings', 0))
        
        if stats.get('can_generate_insights'):
            # Add Clear Insights button
            if 'insights_result' in st.session_state or 'insights_raw_response' in st.session_state:
                if st.button("🧹 Clear Insights"):
                    st.session_state.pop('insights_result', None)
                    st.session_state.pop('insights_raw_response', None)
                    st.rerun()
            
            # Show stored insights if present
            if 'insights_result' in st.session_state or 'insights_raw_response' in st.session_state:
                st.success("✨ Insights generated successfully!")
                if 'insights_raw_response' in st.session_state and st.session_state['insights_raw_response']:
                    st.subheader("🪵 Raw LLM Output")
                    st.markdown(st.session_state['insights_raw_response'])
                else:
                    st.warning("No LLM output available.")
            
            # Generate Insights button
            if st.button("🔮 Generate Insights"):
                with st.spinner("Generating deep literary psychology insights..."):
                    result = make_api_request("/insights", method="POST", data={})
                    if result and result.get('success'):
                        st.session_state['insights_result'] = result['insights']
                        st.session_state['insights_raw_response'] = result.get('raw_response', '')
                        st.session_state['insights_data_summary'] = result.get('data_summary', {})
                        st.rerun()
        else:
            st.warning(f"⚠️ {stats.get('reason', 'Insufficient data for insights')}")
            st.info("You need at least 5 books with ratings to generate insights.")


def show_profile_analysis_page():
    st.header("👤 Personal Profile Analysis")
    
    # Check if profile insights can be generated
    profile_stats = make_api_request("/stats/profile-insights")
    if profile_stats and profile_stats.get('success'):
        stats = profile_stats['stats']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Books", stats.get('total_books', 0))
        with col2:
            st.metric("Books with Ratings", stats.get('books_with_ratings', 0))
        
        if stats.get('can_generate_profile'):
            # Add Clear Profile Insights button
            if 'profile_insights_result' in st.session_state or 'profile_insights_raw_response' in st.session_state:
                if st.button("🧹 Clear Profile Analysis"):
                    st.session_state.pop('profile_insights_result', None)
                    st.session_state.pop('profile_insights_raw_response', None)
                    st.rerun()
            
            # Show stored profile insights if present
            if 'profile_insights_result' in st.session_state or 'profile_insights_raw_response' in st.session_state:
                st.success("✨ Profile analysis completed successfully!")
                if 'profile_insights_raw_response' in st.session_state and st.session_state['profile_insights_raw_response']:
                    st.subheader("📊 Your Personal Profile")
                    st.markdown(st.session_state['profile_insights_raw_response'])
                else:
                    st.warning("No profile analysis available.")
            
            # Generate Profile Analysis button
            if st.button("🔍 Analyze My Profile"):
                with st.spinner("Analyzing your reading patterns for personal insights..."):
                    result = make_api_request("/profile-insights", method="POST", data={})
                    if result and result.get('success'):
                        st.session_state['profile_insights_result'] = result['profile_insights']
                        st.session_state['profile_insights_raw_response'] = result.get('raw_response', '')
                        st.session_state['profile_insights_data_summary'] = result.get('data_summary', {})
                        st.rerun()
        else:
            st.warning(f"⚠️ {stats.get('reason', 'Insufficient data for profile analysis')}")
            st.info("You need at least 10 books with 5 rated books to generate a profile analysis.")

def show_recommendations_page():
    st.header("📚 Book Recommendations")
    
    # Recommendation interface
    query = st.text_input(
        "What kind of book are you looking for?",
        placeholder="e.g., science fiction with strong female characters, psychological thrillers, books about time travel..."
    )
    
    limit = st.slider("Number of recommendations", 5, 20, 10)
    
    if st.button("🔍 Get Recommendations") and query:
        with st.spinner("Finding personalized recommendations..."):
            result = make_api_request(f"/recommend?q={query}&limit={limit}")
            if result and result.get('success'):
                recommendations = result['recommendations']
                
                st.success(f"Found {len(recommendations)} recommendations for: '{query}'")
                
                for i, rec in enumerate(recommendations, 1):
                    with st.expander(f"{i}. {rec['title']} by {rec['author']}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Author:** {rec['author']}")
                            if rec.get('genres'):
                                st.write(f"**Genres:** {rec['genres']}")
                            if rec.get('description'):
                                st.write(f"**Description:** {rec['description'][:200]}...")
                            if rec.get('publisher'):
                                st.write(f"**Publisher:** {rec['publisher']}")
                            if rec.get('year_published'):
                                st.write(f"**Year:** {rec['year_published']}")
                        
                        with col2:
                            if rec.get('relevance_score'):
                                st.write(f"**Relevance Score:** {rec['relevance_score']:.3f}")
                            if rec.get('average_rating'):
                                st.write(f"**Average Rating:** {rec['average_rating']:.1f}")
                            if rec.get('rating'):
                                st.write(f"**Your Rating:** {'⭐' * rec['rating']}")
                            
                            # Show themes
                            if rec.get('themes'):
                                st.write(f"**Themes:** {', '.join(rec['themes'])}")
                        
                        # Recommendation explanation
                        if st.button(f"Why this recommendation?", key=f"explain_{i}"):
                            if rec.get('explanation'):
                                st.info(rec['explanation'])
                            elif rec.get('connections'):
                                st.info(rec['connections'])
                            else:
                                st.info("Recommended based on your reading preferences and query analysis")
    
    # Recommendation stats
    st.subheader("📊 Recommendation System Stats")
    rec_stats = make_api_request("/stats/recommendations")
    if rec_stats and rec_stats.get('success'):
        stats = rec_stats['stats']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Books", stats.get('total_books', 0))
        with col2:
            st.metric("Rated Books", stats.get('rated_books', 0))
        with col3:
            st.metric("Average Rating", f"{stats.get('average_rating', 0):.1f}")
        with col4:
            model_status = "✅ Available" if stats.get('model_available', False) else "❌ Unavailable"
            st.metric("AI Model", model_status)
    
    # Reading preferences analysis
    st.subheader("🧠 Reading Preferences Analysis")
    if st.button("🔍 Analyze My Reading Preferences"):
        with st.spinner("Analyzing your reading patterns..."):
            analysis_result = make_api_request("/recommendations/preferences")
            if analysis_result and analysis_result.get('success'):
                analysis = analysis_result.get('analysis', {})
                
                if 'error' not in analysis:
                    # Display analysis results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if 'genre_analysis' in analysis:
                            st.write("**Favorite Genres:**")
                            genres = analysis['genre_analysis'].get('favorite_genres', [])
                            for genre in genres[:5]:
                                st.write(f"• {genre}")
                        
                        if 'author_analysis' in analysis:
                            st.write("**Favorite Authors:**")
                            authors = analysis['author_analysis'].get('favorite_authors', [])
                            for author in authors[:5]:
                                st.write(f"• {author}")
                    
                    with col2:
                        if 'rating_analysis' in analysis:
                            avg_rating = analysis['rating_analysis'].get('average_rating', 0)
                            st.write(f"**Average Rating:** {avg_rating:.1f}")
                        
                        if 'recommendations' in analysis:
                            st.write("**Suggested Genres:**")
                            suggested_genres = analysis['recommendations'].get('suggested_genres', [])
                            for genre in suggested_genres[:3]:
                                st.write(f"• {genre}")
                    
                    # Show detailed analysis
                    if 'genre_analysis' in analysis and analysis['genre_analysis'].get('genre_patterns'):
                        st.write("**Genre Patterns:**")
                        st.write(analysis['genre_analysis']['genre_patterns'])
                    
                    if 'author_analysis' in analysis and analysis['author_analysis'].get('author_patterns'):
                        st.write("**Author Patterns:**")
                        st.write(analysis['author_analysis']['author_patterns'])
                    
                    if 'timeline_analysis' in analysis and analysis['timeline_analysis'].get('reading_pace'):
                        st.write("**Reading Pace:**")
                        st.write(analysis['timeline_analysis']['reading_pace'])
                else:
                    st.error(f"Analysis failed: {analysis.get('error', 'Unknown error')}")
            else:
                st.error("Failed to analyze reading preferences")

if __name__ == "__main__":
    main() 