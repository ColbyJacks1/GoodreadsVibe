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
        ["Upload & Process", "Dashboard", "Comprehensive Analysis", "Insights", "Profile Analysis", "Recommendations"]
    )
    
    if page == "Upload & Process":
        show_upload_page()
    elif page == "Dashboard":
        show_dashboard_page()
    elif page == "Comprehensive Analysis":
        show_comprehensive_analysis_page()
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
            if 'insights_result' in st.session_state:
                if st.button("🧹 Clear Insights"):
                    st.session_state.pop('insights_result', None)
                    st.rerun()
            
            # Show stored insights if present
            if 'insights_result' in st.session_state:
                st.success("✨ Insights generated successfully!")
                if 'insights_result' in st.session_state and st.session_state['insights_result']:
                    st.subheader("🧠 Literary Psychology Insights")
                    st.markdown(st.session_state['insights_result'])
                else:
                    st.warning("No insights available.")
            
            # Generate Insights button
            if st.button("🔮 Generate Insights"):
                with st.spinner("Generating deep literary psychology insights..."):
                    result = make_api_request("/insights", method="POST", data={})
                    if result and result.get('success'):
                        st.session_state['insights_result'] = result['insights']
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
            if 'profile_insights_result' in st.session_state:
                if st.button("🧹 Clear Profile Analysis"):
                    st.session_state.pop('profile_insights_result', None)
                    st.rerun()
            
            # Show stored profile insights if present
            if 'profile_insights_result' in st.session_state:
                st.success("✨ Profile analysis completed successfully!")
                if 'profile_insights_result' in st.session_state and st.session_state['profile_insights_result']:
                    st.subheader("👤 Your Personal Profile")
                    st.markdown(st.session_state['profile_insights_result'])
                else:
                    st.warning("No profile analysis available.")
            
            # Generate Profile Analysis button
            if st.button("🔍 Analyze My Profile"):
                with st.spinner("Analyzing your reading patterns for personal insights..."):
                    result = make_api_request("/profile-insights", method="POST", data={})
                    if result and result.get('success'):
                        st.session_state['profile_insights_result'] = result['profile_insights']
                        st.session_state['profile_insights_data_summary'] = result.get('data_summary', {})
                        st.rerun()
        else:
            st.warning(f"⚠️ {stats.get('reason', 'Insufficient data for profile analysis')}")
            st.info("You need at least 10 books with 5 rated books to generate a profile analysis.")


def show_comprehensive_analysis_page():
    st.header("🔮 Comprehensive Analysis")
    
    # Check if comprehensive analysis can be generated
    analysis_stats = make_api_request("/stats/comprehensive-analysis")
    if analysis_stats and analysis_stats.get('success'):
        stats = analysis_stats['stats']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Books", stats.get('total_books', 0))
        with col2:
            st.metric("Books with Ratings", stats.get('books_with_ratings', 0))
        
        if stats.get('can_generate_analysis'):
            # Add Clear Analysis button
            if 'comprehensive_analysis_result' in st.session_state or 'comprehensive_analysis_sections' in st.session_state:
                if st.button("🧹 Clear Analysis"):
                    st.session_state.pop('comprehensive_analysis_result', None)
                    st.session_state.pop('comprehensive_analysis_sections', None)
                    st.rerun()
            
            # Show stored analysis if present
            if 'comprehensive_analysis_result' in st.session_state or 'comprehensive_analysis_sections' in st.session_state:
                st.success("✨ Comprehensive analysis completed successfully!")
                
                # Create tabs for different sections
                if 'comprehensive_analysis_sections' in st.session_state:
                    sections = st.session_state['comprehensive_analysis_sections']
                    
                    tab1, tab2, tab3 = st.tabs(["📖 Literary Insights", "👤 Personal Profile", "📚 Recommendations"])
                    
                    with tab1:
                        if sections.get('insights'):
                            st.markdown(sections['insights'])
                        else:
                            st.warning("No insights available.")
                    
                    with tab2:
                        if sections.get('profile'):
                            st.markdown(sections['profile'])
                        else:
                            st.warning("No profile analysis available.")
                    
                    with tab3:
                        if sections.get('recommendations'):
                            st.markdown(sections['recommendations'])
                        else:
                            st.warning("No recommendations available.")
            
            # Generate Comprehensive Analysis button
            if st.button("🔮 Generate Comprehensive Analysis"):
                with st.spinner("Generating comprehensive analysis (this may take a moment)..."):
                    result = make_api_request("/comprehensive-analysis", method="POST", data={})
                    if result and result.get('success'):
                        st.session_state['comprehensive_analysis_result'] = result['comprehensive_analysis']
                        st.session_state['comprehensive_analysis_sections'] = result.get('parsed_sections', {})
                        st.session_state['comprehensive_analysis_data_summary'] = result.get('data_summary', {})
                        st.rerun()
                    else:
                        st.error(f"Failed to generate analysis: {result.get('error', 'Unknown error')}")
        else:
            st.warning(f"⚠️ {stats.get('reason', 'Insufficient data for analysis')}")
            st.info("You need at least 5 books with 3 rated books to generate comprehensive analysis.")


def show_recommendations_page():
    st.header("📚 Book Recommendations")
    
    # Recommendation interface
    query = st.text_input(
        "What kind of book are you looking for?",
        placeholder="e.g., science fiction with strong female characters, psychological thrillers, books about time travel..."
    )
    
    limit = st.slider("Number of recommendations", 5, 20, 10)
    
    if st.button("🔍 Get AI Recommendations") and query:
        with st.spinner("Analyzing your reading history and generating personalized recommendations..."):
            result = make_api_request(f"/recommend?q={query}&limit={limit}")
            if result and result.get('success'):
                recommendations_text = result['recommendations']
                
                st.success(f"Generated personalized recommendations for: '{query}'")
                st.markdown(recommendations_text)
            else:
                st.error(f"Failed to generate recommendations: {result.get('error', 'Unknown error')}")
    
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

if __name__ == "__main__":
    main() 