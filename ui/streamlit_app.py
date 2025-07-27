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
        ["Upload & Process", "Dashboard", "Insights", "Recommendations"]
    )
    
    if page == "Upload & Process":
        show_upload_page()
    elif page == "Dashboard":
        show_dashboard_page()
    elif page == "Insights":
        show_insights_page()
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

def show_clusters_page():
    st.header("🎯 Book Clusters")
    
    # Get clustering stats
    cluster_stats = make_api_request("/stats/clustering")
    if cluster_stats and cluster_stats.get('success'):
        stats = cluster_stats['stats']
        st.metric("Total Books", stats.get('total_books', 0))
        st.metric("Clustered Books", stats.get('clustered_books', 0))
        st.metric("Number of Clusters", stats.get('num_clusters', 0))
    
    # Get books with clustering data
    books_result = make_api_request("/books")
    if books_result:
        books_df = pd.DataFrame(books_result)
        
        # Filter books with clustering data
        clustered_df = books_df[
            (books_df['cluster_id'].notna()) & 
            (books_df['umap_x'].notna()) & 
            (books_df['umap_y'].notna())
        ]
        
        if not clustered_df.empty:
            st.subheader("📊 Cluster Visualization")
            
            # Create scatter plot
            fig = px.scatter(
                clustered_df,
                x='umap_x',
                y='umap_y',
                color='cluster_id',
                hover_data=['title', 'author', 'my_rating'],
                title="Book Clusters (UMAP Projection)",
                labels={'umap_x': 'UMAP X', 'umap_y': 'UMAP Y'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Cluster details
            st.subheader("📋 Cluster Details")
            cluster_exemplars = make_api_request("/clusters/exemplars")
            if cluster_exemplars and cluster_exemplars.get('success'):
                exemplars = cluster_exemplars['exemplars']
                
                for cluster_id, books in exemplars.items():
                    with st.expander(f"Cluster {cluster_id} ({len(books)} books)"):
                        for book in books:
                            st.write(f"**{book['title']}** by {book['author']}")
                            if book.get('rating'):
                                st.write(f"Rating: {'⭐' * book['rating']}")
                            if book.get('genres'):
                                st.write(f"Genres: {book['genres']}")
                            st.write("---")

PROMPT_FILE = os.path.join(os.path.dirname(__file__), '../prompts/insight_prompt.md')

def load_default_prompt():
    with open(PROMPT_FILE, 'r') as f:
        return f.read()

def show_insights_page():
    st.header("🧠 Literary Psychology Insights")
    
    # Prompt editor section
    if 'prompt_templates' not in st.session_state:
        st.session_state['prompt_templates'] = {}
    if 'current_prompt' not in st.session_state:
        st.session_state['current_prompt'] = load_default_prompt()
    if 'prompt_name' not in st.session_state:
        st.session_state['prompt_name'] = 'Default'

    st.subheader("📝 Prompt Editor")
    prompt_name = st.text_input("Prompt Name", st.session_state['prompt_name'])
    prompt_text = st.text_area("Prompt Template", st.session_state['current_prompt'], height=300, key="prompt_text_area")
    col_save, col_load, col_reset = st.columns([1,1,1])
    with col_save:
        if st.button("💾 Save Prompt"):
            st.session_state['prompt_templates'][prompt_name] = prompt_text
            st.session_state['prompt_name'] = prompt_name
            st.session_state['current_prompt'] = prompt_text
            st.success(f"Prompt '{prompt_name}' saved.")
    with col_load:
        if st.button("📂 Load Prompt") and prompt_name in st.session_state['prompt_templates']:
            st.session_state['current_prompt'] = st.session_state['prompt_templates'][prompt_name]
            st.session_state['prompt_name'] = prompt_name
            st.rerun()
    with col_reset:
        if st.button("🔄 Reset to Default"):
            st.session_state['current_prompt'] = load_default_prompt()
            st.session_state['prompt_name'] = 'Default'
            st.rerun()
    if st.session_state['prompt_templates']:
        st.markdown("**Saved Prompts:** " + ", ".join(st.session_state['prompt_templates'].keys()))

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
            # Remove clustering toggle
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
            # Always show Generate Insights button
            if st.button("🔮 Generate Insights"):
                with st.spinner("Generating deep literary psychology insights..."):
                    result = make_api_request("/insights", method="POST", data={"prompt": st.session_state['current_prompt']})
                    if result and result.get('success'):
                        st.session_state['insights_result'] = result['insights']
                        st.session_state['insights_raw_response'] = result.get('raw_response', '')
                        st.session_state['insights_data_summary'] = result.get('data_summary', {})
                        st.rerun()
        else:
            st.warning(f"⚠️ {stats.get('reason', 'Insufficient data for insights')}")
            st.info("You need at least 5 books with ratings to generate insights.")

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
                            st.write(f"**Score:** {rec['score']:.3f}")
                            st.write(f"**Similarity:** {rec['cosine_similarity']:.3f}")
                            if rec.get('rating'):
                                st.write(f"**Rating:** {'⭐' * rec['rating']}")
                            
                            # Show shared keywords
                            if rec.get('shared_keywords'):
                                st.write(f"**Shared keywords:** {', '.join(rec['shared_keywords'])}")
                        
                        # Recommendation explanation
                        if st.button(f"Why this recommendation?", key=f"explain_{i}"):
                            # Create simple explanation based on available data
                            explanation_parts = []
                            if rec.get('cosine_similarity', 0) > 0.6:
                                explanation_parts.append("Similar to your query")
                            if rec.get('rating') and rec['rating'] >= 4:
                                explanation_parts.append("Highly rated")
                            if rec.get('shared_keywords'):
                                explanation_parts.append(f"Shares keywords: {', '.join(rec['shared_keywords'])}")
                            if rec.get('genres'):
                                explanation_parts.append(f"Genre: {rec['genres']}")
                            
                            explanation = " | ".join(explanation_parts) if explanation_parts else "Recommended based on similarity and rating"
                            st.info(explanation)
    
    # Recommendation stats
    st.subheader("📊 Recommendation System Stats")
    rec_stats = make_api_request("/stats/recommendations")
    if rec_stats and rec_stats.get('success'):
        stats = rec_stats['stats']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Books", stats.get('total_books', 0))
        with col2:
            st.metric("Books with Embeddings", stats.get('books_with_embeddings', 0))
        with col3:
            st.metric("Embedding Rate", f"{stats.get('embedding_rate', 0)}%")

if __name__ == "__main__":
    main() 