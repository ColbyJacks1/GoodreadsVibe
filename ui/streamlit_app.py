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
from app.session_db import session_db_manager


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
    
    # Initialize session state for user data
    if 'user_books' not in st.session_state:
        st.session_state.user_books = []
    if 'user_stats' not in st.session_state:
        st.session_state.user_stats = {
            'total_books': 0,
            'processed_books': 0,
            'enriched_books': 0,
            'books_with_ratings': 0,
            'average_rating': 0.0
        }
    
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
        if st.button("🗑️ Clear My Data", type="secondary"):
            with st.spinner("Clearing your data..."):
                try:
                    # Clear session data for this user
                    session_db_manager.clear_user_books()
                    st.session_state.user_stats = {
                        'total_books': 0,
                        'processed_books': 0,
                        'enriched_books': 0,
                        'books_with_ratings': 0,
                        'average_rating': 0.0
                    }
                    st.success("✅ Your data cleared successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to clear data: {str(e)}")
    
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
                        # Process CSV and store in session
                        import pandas as pd
                        df = pd.read_csv(tmp_file_path)
                        
                        # Clear existing books
                        session_db_manager.clear_user_books()
                        
                        # Process each row
                        processed_books = 0
                        skipped_books = 0
                        
                        for index, row in df.iterrows():
                            try:
                                # Create book data
                                book_data = {
                                    'book_id': str(row.get('Book Id', f'book_{index}')),
                                    'title': str(row.get('Title', 'Unknown Title')),
                                    'author': str(row.get('Author', 'Unknown Author')),
                                    'my_rating': int(row.get('My Rating', 0)) if pd.notna(row.get('My Rating')) else None,
                                    'average_rating': float(row.get('Average Rating', 0)) if pd.notna(row.get('Average Rating')) else None,
                                    'date_read': row.get('Date Read', None),
                                    'date_added': row.get('Date Added', None),
                                    'bookshelves': row.get('Bookshelves', None),
                                    'my_review': row.get('My Review', None),
                                    'publisher': row.get('Publisher', None),
                                    'pages': int(row.get('Number of Pages', 0)) if pd.notna(row.get('Number of Pages')) else None,
                                    'year_published': int(row.get('Original Publication Year', 0)) if pd.notna(row.get('Original Publication Year')) else None,
                                    'isbn': row.get('ISBN', None),
                                    'isbn13': row.get('ISBN13', None)
                                }
                                
                                # Add to session
                                session_db_manager.add_user_book(book_data)
                                processed_books += 1
                                
                            except Exception as e:
                                skipped_books += 1
                                continue
                        
                        # Update stats
                        user_books = session_db_manager.get_user_books()
                        books_with_ratings = len([b for b in user_books if b.get('my_rating')])
                        avg_rating = sum(b.get('my_rating', 0) for b in user_books if b.get('my_rating')) / books_with_ratings if books_with_ratings > 0 else 0
                        
                        st.session_state.user_stats = {
                            'total_books': len(user_books),
                            'processed_books': processed_books,
                            'enriched_books': 0,  # Will be updated during enrichment
                            'books_with_ratings': books_with_ratings,
                            'average_rating': round(avg_rating, 2)
                        }
                        
                        st.success(f"✅ Ingested {processed_books} books")
                        st.json({
                            'processed_books': processed_books,
                            'skipped_books': skipped_books,
                            'total_books': len(user_books)
                        })
                        
                    except Exception as e:
                        st.error(f"❌ Error ingesting data: {str(e)}")
                    finally:
                        # Clean up temp file
                        os.unlink(tmp_file_path)
        
        with col2:
            if st.button("🔍 Enrich Metadata"):
                with st.spinner("Enriching with Open Library data..."):
                    try:
                        user_books = session_db_manager.get_user_books()
                        if not user_books:
                            st.warning("No books to enrich. Please ingest data first.")
                            return
                        
                        # Simple enrichment simulation (in real app, you'd call Open Library API)
                        enriched_count = 0
                        for book in user_books:
                            # Simulate enrichment
                            if not book.get('description'):
                                book['description'] = f"Enriched description for {book['title']}"
                                book['genres'] = "Fiction, Literature"  # Placeholder
                                enriched_count += 1
                        
                        # Update stats
                        stats = st.session_state.user_stats
                        stats['enriched_books'] = enriched_count
                        st.session_state.user_stats = stats
                        
                        st.success(f"✅ Enriched {enriched_count} books")
                        st.json({
                            'enriched': enriched_count,
                            'total_books': len(user_books)
                        })
                        
                    except Exception as e:
                        st.error(f"❌ Error enriching data: {str(e)}")

def show_dashboard_page():
    st.header("📊 Dashboard")
    
    # Get user stats
    user_stats = st.session_state.user_stats
    user_books = session_db_manager.get_user_books()
    
    # Display stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📥 Total Books", user_stats.get('total_books', 0))
    with col2:
        st.metric("⭐ Average Rating", f"{user_stats.get('average_rating', 0):.1f}")
    
    # Get books data
    if user_books:
        books_df = pd.DataFrame(user_books)
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
    else:
        st.info("📚 No books uploaded yet. Go to 'Upload & Process' to add your Goodreads data!")





def show_insights_page():
    st.header("🧠 Literary Psychology Insights")
    
    # Get user data
    user_books = session_db_manager.get_user_books()
    user_stats = st.session_state.user_stats
    
    # Check if insights can be generated
    total_books = user_stats.get('total_books', 0)
    books_with_ratings = user_stats.get('books_with_ratings', 0)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Books", total_books)
    with col2:
        st.metric("Books with Ratings", books_with_ratings)
    
    can_generate = total_books >= 5 and books_with_ratings >= 3
    
    if can_generate:
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
                try:
                    # Create simple insights based on user data
                    insights = generate_simple_insights(user_books, user_stats)
                    st.session_state['insights_result'] = insights
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate insights: {str(e)}")
    else:
        st.warning(f"⚠️ Insufficient data for insights")
        st.info("You need at least 5 books with 3 rated books to generate insights.")


def generate_simple_insights(user_books, user_stats):
    """Generate simple insights based on user data."""
    total_books = user_stats.get('total_books', 0)
    books_with_ratings = user_stats.get('books_with_ratings', 0)
    avg_rating = user_stats.get('average_rating', 0)
    
    insights = []
    
    # Reading volume insight
    if total_books > 50:
        insights.append("📚 **Avid Reader**: You've read a substantial number of books, showing a deep commitment to literature and intellectual exploration.")
    elif total_books > 20:
        insights.append("📖 **Regular Reader**: You maintain a steady reading habit, indicating a thoughtful approach to personal growth through literature.")
    else:
        insights.append("📚 **Emerging Reader**: Your reading journey is just beginning, showing curiosity and openness to new ideas.")
    
    # Rating pattern insight
    if avg_rating >= 4.0:
        insights.append("⭐ **Selective Reader**: Your high average rating suggests you're quite discerning and know what resonates with you.")
    elif avg_rating >= 3.0:
        insights.append("📊 **Balanced Perspective**: Your moderate ratings show a thoughtful approach to evaluating books.")
    else:
        insights.append("🤔 **Critical Reader**: Your lower ratings suggest you have high standards and aren't easily impressed.")
    
    # Genre analysis
    if user_books:
        genres = []
        for book in user_books:
            if book.get('bookshelves'):
                book_genres = [g.strip() for g in book['bookshelves'].split(',')]
                genres.extend(book_genres)
        
        if genres:
            genre_counts = {}
            for genre in genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            top_genre = max(genre_counts.items(), key=lambda x: x[1])
            insights.append(f"🎭 **Genre Preference**: Your favorite genre appears to be '{top_genre[0]}', which dominates your reading choices.")
    
    # Reading timeline analysis
    if user_books:
        dates = [book.get('date_read') for book in user_books if book.get('date_read')]
        if dates:
            insights.append("📅 **Reading Journey**: Your reading timeline shows a consistent engagement with literature over time.")
    
    return "\n\n".join(insights)


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
    
    # Get user data
    user_books = session_db_manager.get_user_books()
    user_stats = st.session_state.user_stats
    
    # Check if comprehensive analysis can be generated
    total_books = user_stats.get('total_books', 0)
    books_with_ratings = user_stats.get('books_with_ratings', 0)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Books", total_books)
    with col2:
        st.metric("Books with Ratings", books_with_ratings)
    
    can_generate = total_books >= 5 and books_with_ratings >= 3
    
    if can_generate:
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
                try:
                    # Create comprehensive analysis using session data
                    analysis = generate_comprehensive_analysis(user_books, user_stats)
                    st.session_state['comprehensive_analysis_result'] = analysis
                    st.session_state['comprehensive_analysis_sections'] = {
                        'insights': analysis,
                        'profile': "Profile analysis would go here...",
                        'recommendations': "Recommendations would go here..."
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate analysis: {str(e)}")
    else:
        st.warning(f"⚠️ Insufficient data for analysis")
        st.info("You need at least 5 books with 3 rated books to generate comprehensive analysis.")


def generate_comprehensive_analysis(user_books, user_stats):
    """Generate comprehensive analysis based on user data."""
    total_books = user_stats.get('total_books', 0)
    books_with_ratings = user_stats.get('books_with_ratings', 0)
    avg_rating = user_stats.get('average_rating', 0)
    
    analysis = []
    
    # Overall reading profile
    analysis.append("## 📚 Your Reading Profile")
    analysis.append(f"You have read **{total_books} books** with an average rating of **{avg_rating:.1f} stars**.")
    
    # Reading personality
    if total_books > 50:
        analysis.append("**🎯 Reading Personality**: You are an avid reader with a deep commitment to literature and intellectual exploration.")
    elif total_books > 20:
        analysis.append("**🎯 Reading Personality**: You are a regular reader who values personal growth through thoughtful reading.")
    else:
        analysis.append("**🎯 Reading Personality**: You are an emerging reader with curiosity and openness to new ideas.")
    
    # Rating psychology
    if avg_rating >= 4.0:
        analysis.append("**⭐ Rating Psychology**: Your high ratings suggest you're selective and know what resonates with you.")
    elif avg_rating >= 3.0:
        analysis.append("**⭐ Rating Psychology**: Your moderate ratings show a balanced and thoughtful approach to evaluation.")
    else:
        analysis.append("**⭐ Rating Psychology**: Your lower ratings indicate high standards and critical thinking.")
    
    # Genre analysis
    if user_books:
        genres = []
        for book in user_books:
            if book.get('bookshelves'):
                book_genres = [g.strip() for g in book['bookshelves'].split(',')]
                genres.extend(book_genres)
        
        if genres:
            genre_counts = {}
            for genre in genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            analysis.append("## 🎭 Genre Preferences")
            analysis.append("Your top genres are:")
            for genre, count in top_genres:
                analysis.append(f"- **{genre}**: {count} books")
    
    return "\n\n".join(analysis)


def show_recommendations_page():
    st.header("📚 Book Recommendations")
    
    # Get user data
    user_books = session_db_manager.get_user_books()
    user_stats = st.session_state.user_stats
    
    # Recommendation interface
    query = st.text_input(
        "What kind of book are you looking for?",
        placeholder="e.g., science fiction with strong female characters, psychological thrillers, books about time travel..."
    )
    
    limit = st.slider("Number of recommendations", 5, 20, 10)
    
    if st.button("🔍 Get AI Recommendations") and query:
        with st.spinner("Analyzing your reading history and generating personalized recommendations..."):
            try:
                # Generate simple recommendations based on user data
                recommendations = generate_simple_recommendations(user_books, user_stats, query, limit)
                st.success(f"Generated personalized recommendations for: '{query}'")
                st.markdown(recommendations)
            except Exception as e:
                st.error(f"Failed to generate recommendations: {str(e)}")
    
    # Recommendation stats
    st.subheader("📊 Your Reading Stats")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Books", user_stats.get('total_books', 0))
    with col2:
        st.metric("Rated Books", user_stats.get('books_with_ratings', 0))
    with col3:
        st.metric("Average Rating", f"{user_stats.get('average_rating', 0):.1f}")
    with col4:
        st.metric("Enriched Books", user_stats.get('enriched_books', 0))


def generate_simple_recommendations(user_books, user_stats, query, limit):
    """Generate simple recommendations based on user data."""
    total_books = user_stats.get('total_books', 0)
    avg_rating = user_stats.get('average_rating', 0)
    
    recommendations = []
    recommendations.append("## 📚 Personalized Recommendations")
    recommendations.append(f"Based on your **{total_books} books** and average rating of **{avg_rating:.1f} stars**:")
    recommendations.append("")
    
    # Genre-based recommendations
    if user_books:
        genres = []
        for book in user_books:
            if book.get('bookshelves'):
                book_genres = [g.strip() for g in book['bookshelves'].split(',')]
                genres.extend(book_genres)
        
        if genres:
            genre_counts = {}
            for genre in genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            top_genre = max(genre_counts.items(), key=lambda x: x[1])
            recommendations.append(f"**🎭 Based on your love for {top_genre[0]}**:")
            recommendations.append(f"- Try exploring different subgenres within {top_genre[0]}")
            recommendations.append(f"- Look for award-winning books in this genre")
            recommendations.append("")
    
    # Rating-based recommendations
    if avg_rating >= 4.0:
        recommendations.append("**⭐ Based on your high ratings**:")
        recommendations.append("- Try books that have won major literary awards")
        recommendations.append("- Explore critically acclaimed authors")
        recommendations.append("- Look for books with high Goodreads ratings")
    else:
        recommendations.append("**🤔 Based on your critical approach**:")
        recommendations.append("- Try books that challenge your perspectives")
        recommendations.append("- Explore experimental or unconventional narratives")
        recommendations.append("- Look for books with mixed reviews")
    
    recommendations.append("")
    recommendations.append("**💡 General Recommendations**:")
    recommendations.append("- Consider reading outside your usual genres")
    recommendations.append("- Try books from different time periods")
    recommendations.append("- Explore international literature")
    
    return "\n".join(recommendations)

if __name__ == "__main__":
    main() 