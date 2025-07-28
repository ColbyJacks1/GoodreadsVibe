"""Streamlit UI for book-mirror-plus."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import os
import tempfile
import sys
from pathlib import Path

# Add the app directory to the Python path so we can import modules
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

# Import backend modules directly
from app.ingest import ingester
from app.enrich import enricher
from app.cluster import clusterer
from app.insights import insights_generator
from app.profile_insights import profile_insights_generator
from app.recommend import recommender
from app.comprehensive_analysis import comprehensive_analyzer
from app.db import db_manager


def sqlmodel_to_dict(obj):
    """Convert SQLModel object to dictionary to avoid Pydantic compatibility issues."""
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return obj


# Configure page
st.set_page_config(
    page_title="Goodreads Analyzer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📚 Goodreads Analyzer")
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
                try:
                    # Create a simple reset by recreating tables
                    db_manager.create_tables()
                    st.success("✅ Database reset successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to reset database: {str(e)}")
    
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
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        result = ingester.ingest_csv(tmp_file_path)
                        if result:
                            st.success(f"✅ Ingested {result['processed_books']} books")
                            st.json(result)
                    except Exception as e:
                        st.error(f"❌ Error ingesting data: {str(e)}")
                    finally:
                        # Clean up temp file
                        os.unlink(tmp_file_path)
        
        with col2:
            if st.button("🔍 Enrich Metadata"):
                with st.spinner("Enriching with Open Library data..."):
                    try:
                        result = enricher.enrich_all_books()
                        if result:
                            st.success(f"✅ Enriched {result['enriched']} books")
                            st.json(result)
                    except Exception as e:
                        st.error(f"❌ Error enriching data: {str(e)}")

def show_dashboard_page():
    st.header("📊 Dashboard")
    
    # Get statistics
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            ingestion_stats = ingester.get_ingestion_stats()
            st.metric("📥 Ingestion", ingestion_stats.get('total_books', 0))
        except:
            st.metric("📥 Ingestion", "N/A")
    
    with col2:
        try:
            enrichment_stats = enricher.get_enrichment_stats()
            st.metric("🔍 Enrichment", enrichment_stats.get('total_books', 0))
        except:
            st.metric("🔍 Enrichment", "N/A")
    
    # Get books data
    books_result = db_manager.get_all_books()
    if books_result and isinstance(books_result, list):
        # Convert SQLModel objects to dictionaries to avoid Pydantic compatibility issues
        books_dicts = [sqlmodel_to_dict(book) for book in books_result]
        books_df = pd.DataFrame(books_dicts)
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
    insights_stats = {"success": True, "stats": insights_generator.get_insights_stats()}
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
                    result = insights_generator.generate_insights()
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
    profile_stats = {"success": True, "stats": profile_insights_generator.get_profile_insights_stats()}
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
                    result = profile_insights_generator.generate_profile_insights()
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
    analysis_stats = {"success": True, "stats": comprehensive_analyzer.get_analysis_stats()}
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
                    result = comprehensive_analyzer.generate_comprehensive_analysis()
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
            result = recommender.recommend_books(query, limit)
            if result and result.get('success'):
                recommendations_text = result['recommendations']
                
                st.success(f"Generated personalized recommendations for: '{query}'")
                st.markdown(recommendations_text)
            else:
                st.error(f"Failed to generate recommendations: {result.get('error', 'Unknown error')}")
    
    # Recommendation stats
    st.subheader("📊 Recommendation System Stats")
    rec_stats = {"success": True, "stats": recommender.get_recommendation_stats()}
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