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

# Add the project root to Python path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Import backend modules directly
from app.session_db import session_db_manager
from app.ingest import GenreNormalizer


def sqlmodel_to_dict(obj):
    """Convert SQLModel object to dictionary to avoid Pydantic compatibility issues."""
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return obj


def show_quick_navigation():
    """Show quick navigation buttons at the bottom of pages."""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Upload",
                    help="Upload your Goodreads CSV file",
                    use_container_width=True):
            st.session_state.selected_page = "📤 Upload"
            st.rerun()
    
    with col2:
        if st.button("📊 Books and Stats",
                    help="View your reading statistics and visualizations",
                    use_container_width=True):
            st.session_state.selected_page = "📊 Books and Stats"
            st.rerun()
    
    with col3:
        if st.button("🔮 Analyze Me",
                    help="Get deep insights and recommendations",
                    use_container_width=True):
            st.session_state.selected_page = "🔮 Analyze Me"
            st.rerun()


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
    
    # Clean Sidebar Navigation
    st.sidebar.title("📚 Navigation")
    
    # Simplified list of main pages only
    main_pages = [
        "📤 Upload", 
        "📊 Books and Stats", 
        "🔮 Analyze Me"
    ]
    
    # Check if page was selected via main buttons
    if 'selected_page' in st.session_state and st.session_state.selected_page in main_pages:
        default_index = main_pages.index(st.session_state.selected_page)
    else:
        default_index = 0
    
    page = st.sidebar.selectbox(
        "Choose a section:",
        main_pages,
        index=default_index
    )
    
    # Update session state
    st.session_state.selected_page = page
    
    # Clean up page names for routing
    page_clean = page.split(" ", 1)[1] if " " in page else page
    
    if page_clean == "Upload":
        show_upload_page()
    elif page_clean == "Books and Stats":
        show_books_and_stats_page()
    elif page_clean == "Analyze Me":
        show_comprehensive_analysis_page_parallel()

def show_upload_page():
    st.header("📤 Upload & Process")
    
    # Custom CSS to make the import button taller
    st.markdown("""
    <style>
    /* Universal button styling with high specificity */
    button {
        font-size: 18px !important;
        font-weight: bold !important;
    }
    
    /* Streamlit button specific styling */
    .stButton > button {
        height: 60px !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }
    
    /* Target all buttons in the app */
    div[data-testid="stButton"] button,
    .stButton button,
    button[data-baseweb="button"] {
        font-size: 18px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.write("Upload your Goodreads CSV file to analyze your reading data.")
    
    # File upload at the top
    uploaded_file = st.file_uploader(
        "Upload your Goodreads CSV file",
        type=['csv'],
        help="Export your Goodreads library as CSV and upload it here"
    )
    
    if uploaded_file is not None:
        # Single process button - full width and taller
        if st.button("🚀 Import & Process Data", type="primary", use_container_width=True):
            with st.spinner("Processing your Goodreads data..."):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                try:
                    # Step 1: Process CSV and store in session
                    import pandas as pd
                    df = pd.read_csv(tmp_file_path)
                    
                    # Clear existing books
                    session_db_manager.clear_user_books()
                    
                    # Process each row
                    processed_books = 0
                    skipped_books = 0
                    
                    for index, row in df.iterrows():
                        try:
                            # Helper function to safely convert to string or None
                            def safe_str_or_none(value):
                                if pd.isna(value) or value is None:
                                    return None
                                return str(value)
                            
                            def safe_str(value, default=''):
                                if pd.isna(value) or value is None:
                                    return default
                                return str(value)
                            
                            # Create book data with safe string conversion
                            book_data = {
                                'book_id': safe_str(row.get('Book Id'), f'book_{index}'),
                                'title': safe_str(row.get('Title'), 'Unknown Title'),
                                'author': safe_str(row.get('Author'), 'Unknown Author'),
                                'my_rating': int(row.get('My Rating', 0)) if pd.notna(row.get('My Rating')) else None,
                                'average_rating': float(row.get('Average Rating', 0)) if pd.notna(row.get('Average Rating')) else None,
                                'date_read': safe_str_or_none(row.get('Date Read')),
                                'date_added': safe_str_or_none(row.get('Date Added')),
                                'bookshelves': safe_str_or_none(row.get('Bookshelves')),
                                'genres_raw': safe_str_or_none(row.get('Genres')),  # Use actual Genres field
                                'my_review': safe_str_or_none(row.get('My Review')),
                                'publisher': safe_str_or_none(row.get('Publisher')),
                                'pages': int(row.get('Number of Pages', 0)) if pd.notna(row.get('Number of Pages')) else None,
                                'year_published': int(row.get('Original Publication Year', 0)) if pd.notna(row.get('Original Publication Year')) else None,
                                'isbn': safe_str_or_none(row.get('ISBN')),
                                'isbn13': safe_str_or_none(row.get('ISBN13'))
                            }
                            
                            # Add to session
                            session_db_manager.add_user_book(book_data)
                            processed_books += 1
                            
                        except Exception as e:
                            skipped_books += 1
                            continue
                    
                    # Process book metadata
                    user_books = session_db_manager.get_user_books()
                    genre_normalizer = GenreNormalizer()
                    
                    for book in user_books:
                        # Process genres from the actual Genres field
                        if book.get('genres_raw'):
                            genres_raw = book['genres_raw']
                            normalized_genres = genre_normalizer.normalize_bookshelves(genres_raw)
                            book['genres'] = ", ".join(normalized_genres) if normalized_genres else "Unknown"
                        elif book.get('bookshelves'):
                            # Fallback to bookshelves if no genres field
                            bookshelves_raw = book['bookshelves']
                            normalized_genres = genre_normalizer.normalize_bookshelves(bookshelves_raw)
                            book['genres'] = ", ".join(normalized_genres) if normalized_genres else "Unknown"
                        else:
                            book['genres'] = "Unknown"
                    
                    # Update final stats
                    books_with_ratings = len([b for b in user_books if b.get('my_rating')])
                    avg_rating = sum(b.get('my_rating', 0) for b in user_books if b.get('my_rating')) / books_with_ratings if books_with_ratings > 0 else 0
                    
                    st.session_state.user_stats = {
                        'total_books': len(user_books),
                        'processed_books': processed_books,
                        'books_with_ratings': books_with_ratings,
                        'average_rating': round(avg_rating, 2)
                    }
                    
                    st.success(f"✅ Successfully processed {processed_books} books!")
                    
                    # Show meaningful summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📚 Total Books", len(user_books))
                    with col2:
                        st.metric("⭐ Rated Books", books_with_ratings)
                    with col3:
                        st.metric("📊 Average Rating", f"{avg_rating:.1f}" if avg_rating > 0 else "N/A")
                    
                    if skipped_books > 0:
                        st.warning(f"⚠️ Skipped {skipped_books} books due to formatting issues")
                    
                    # Start background comprehensive analysis if sufficient data
                    if len(user_books) >= 5 and books_with_ratings >= 3:
                        st.session_state.analysis_status = "processing"
                        st.session_state.analysis_start_time = datetime.now()
                        # Clear any existing analysis
                        st.session_state.pop('comprehensive_analysis_result', None)
                        st.session_state.pop('comprehensive_analysis_sections', None)
                        
                        # Note: Actual processing will happen when user navigates to the page
                        # due to Streamlit's architecture
                    
                    # Automatically navigate to Books and Stats after successful upload
                    st.session_state.selected_page = "📊 Books and Stats"
                    st.success("✅ Data uploaded successfully! Redirecting to Books and Stats...")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error processing data: {str(e)}")
                finally:
                    # Clean up temp file
                    os.unlink(tmp_file_path)

    # Add separator below the button
    st.markdown("---")

    # Instructions and clear data below the upload section
    col1, col2 = st.columns([3, 1])
    with col1:
        # Simple instructions for getting CSV
        with st.expander("📋 How to get your Goodreads CSV file", expanded=False):
            st.markdown("""
            **📚 Getting your Goodreads data is easy! Follow these steps:**
            
            ### Step 1: Sign in to Goodreads
            1. Go to [Goodreads.com](https://www.goodreads.com) and sign in to your account
            2. If you don't have an account, create one first
            
            ### Step 2: Export Your Library
            1. Go directly to: [Goodreads Import/Export Page](https://www.goodreads.com/review/import)
            2. Click **"Export Library"** button
            3. Wait for the file to generate (this may take a few minutes)
            
            ### Step 3: Download the File
            1. Once ready, click **"Download"** to save the CSV file
            2. The file will be named something like `goodreads_library_export.csv`
            3. Save it somewhere you can easily find (like your Desktop)
            
            ### Step 4: Upload Here
            1. Come back to this page
            2. Click **"Browse files"** or drag and drop your CSV file
            3. Click **"Import & Process Data"** to analyze your reading!
            
            **💡 Tip:** If you have a large library, the export might take 5-10 minutes to generate. Be patient!
            """)
            
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

    # Quick navigation at bottom
    show_quick_navigation()

def show_books_and_stats_page():
    st.header("📊 Books and Stats")
    
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
            # Filter out 0 star ratings
            ratings_df = books_df[(books_df['my_rating'].notna()) & (books_df['my_rating'] > 0)]
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
    
    # Quick navigation at bottom
    show_quick_navigation()





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
            st.info("⏱️ **AI processing may take up to 2 minutes** - please be patient!")
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
    
    # Quick navigation at bottom
    show_quick_navigation()


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


def generate_simple_profile_analysis(user_books, user_stats):
    """Generate simple profile analysis for session-based data."""
    if not user_books:
        return "No books available for profile analysis."
    
    try:
        # Basic profile analysis based on available data
        total_books = len(user_books)
        rated_books = [book for book in user_books if book.get('rating') and book['rating'] > 0]
        avg_rating = sum(book['rating'] for book in rated_books) / len(rated_books) if rated_books else 0
        
        profile = f"""
## 👤 Your Reading Profile

### 📊 **Reading Statistics**
- **Total Books**: {total_books}
- **Rated Books**: {len(rated_books)}
- **Average Rating**: {avg_rating:.1f}/5.0

### 🎯 **Reading Preferences**
"""
        
        if rated_books:
            # Genre preferences
            genres = {}
            for book in rated_books:
                genre = book.get('genre', 'Unknown')
                if genre not in genres:
                    genres[genre] = []
                genres[genre].append(book['rating'])
            
            if genres:
                profile += "\n**Your Favorite Genres:**\n"
                genre_ratings = [(genre, sum(ratings)/len(ratings)) for genre, ratings in genres.items()]
                genre_ratings.sort(key=lambda x: x[1], reverse=True)
                
                for genre, rating in genre_ratings[:5]:
                    profile += f"- **{genre}**: {rating:.1f}/5.0\n"
            
            # Rating distribution
            rating_counts = {}
            for book in rated_books:
                rating = int(book['rating'])
                rating_counts[rating] = rating_counts.get(rating, 0) + 1
            
            profile += "\n**Your Rating Distribution:**\n"
            for rating in sorted(rating_counts.keys(), reverse=True):
                count = rating_counts[rating]
                profile += f"- **{rating} stars**: {count} books\n"
        
        profile += "\n### 💡 **Profile Insights**\n"
        profile += "- Your reading profile shows your preferences\n"
        profile += "- Upload more books for deeper analysis\n"
        profile += "- Rate your books to get better insights\n"
        
        return profile
        
    except Exception as e:
        return f"Error generating profile analysis: {str(e)}"


def show_profile_analysis_page():
    st.header("👤 Personal Profile Analysis")
    
    # Get user data
    user_books = session_db_manager.get_user_books()
    user_stats = st.session_state.user_stats
    
    # Check if profile insights can be generated
    total_books = user_stats.get('total_books', 0)
    books_with_ratings = user_stats.get('books_with_ratings', 0)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Books", total_books)
    with col2:
        st.metric("Books with Ratings", books_with_ratings)
    
    can_generate = total_books >= 10 and books_with_ratings >= 5
    
    if can_generate:
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
            st.info("⏱️ **AI processing may take up to 2 minutes** - please be patient!")
            with st.spinner("Analyzing your reading patterns for personal insights..."):
                try:
                    # Generate simple profile analysis using session data
                    profile_analysis = generate_simple_profile_analysis(user_books, user_stats)
                    st.session_state['profile_insights_result'] = profile_analysis
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Profile analysis failed: {str(e)}")
    else:
        st.warning("⚠️ Insufficient data for profile analysis")
        st.info("You need at least 10 books with 5 rated books to generate a profile analysis.")

    # Quick navigation at bottom
    show_quick_navigation()


def show_comprehensive_analysis_page_parallel():
    st.header("🔮 Analyze Me")
    
    # Get user data
    user_books = session_db_manager.get_user_books()
    user_stats = st.session_state.user_stats
    
    # Check if comprehensive analysis can be generated
    total_books = user_stats.get('total_books', 0)
    books_with_ratings = user_stats.get('books_with_ratings', 0)
    
    can_generate = total_books >= 5 and books_with_ratings >= 3
    
    # Add custom CSS for larger tab fonts
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        padding-left: 20px;
        padding-right: 20px;
        font-size: 24px !important;
        font-weight: bold !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Show insufficient data warning if needed
    if not can_generate:
        st.warning(f"⚠️ Insufficient data for analysis")
        st.info("You need at least 5 books with 3 rated books to generate comprehensive analysis.")
    
    # Show all 4 tabs with placeholder content for insufficient data or not started
    if not can_generate or (can_generate and st.session_state.get('analysis_status', 'not_started') == "not_started"):
        tab1, tab2, tab3, tab4 = st.tabs([
            "😂  ROAST ME  😂", 
            "👤  PERSONAL PROFILE  👤", 
            "📚  RECOMMENDATIONS  📚", 
            "📖  LITERARY INSIGHTS  📖"
        ])
        
        with tab1:
            st.info("🔄 **Pending Analysis**")
            st.write("Your literary roast will appear here once analysis is complete.")
            st.write("This will include witty observations about your reading habits and personality!")
        
        with tab2:
            st.info("🔄 **Pending Analysis**")
            st.write("Your personal  analysis will appear here once analysis is complete.")
            st.write("This will include deep insights about your personality, demographics, and reading psychology!")
        
        with tab3:
            st.info("🔄 **Pending Analysis**")
            st.write("Your personalized book recommendations will appear here once analysis is complete.")
            st.write("This will include curated book suggestions based on your reading history!")
        
        with tab4:
            st.info("🔄 **Pending Analysis**")
            st.write("Your literary psychology insights will appear here once analysis is complete.")
            st.write("This will include deep analysis of your reading patterns and psychological profile!")
        
        # Generate button (only show if can_generate)
        if can_generate:
            st.markdown("---")
            if st.button("🔮 Start Analysis", type="primary", use_container_width=True):
                st.session_state.analysis_status = "processing"
                st.session_state.analysis_start_time = datetime.now()
                st.session_state.pop('analysis_processing_started', None)
                st.session_state.pop('last_refresh', None)
                st.rerun()
    
    elif can_generate:
        # Check analysis status
        analysis_status = st.session_state.get('analysis_status', 'not_started')
        
        if analysis_status == "processing":
            # Show processing state
            st.info("🔄 **Processing your comprehensive analysis...**")
            st.info("⏱️ **AI processing may take up to 2 minutes** - please be patient!")
            
            # Show progress and estimated time
            if 'analysis_start_time' in st.session_state:
                import time
                elapsed = datetime.now() - st.session_state.analysis_start_time
                elapsed_seconds = int(elapsed.total_seconds())
                st.write(f"⏱️ Processing time: {elapsed_seconds} seconds")

            
            st.write("📚 Analyzing your reading patterns...")
            st.write("🧠 Generating psychological insights...")
            st.write("💡 Creating personalized recommendations...")
            st.write("😂 Preparing your literary roast...")
            
            # Trigger actual processing - use progressive display approach
            if 'analysis_processing_started' not in st.session_state:
                st.session_state.analysis_processing_started = True
                st.session_state.analysis_start_time = datetime.now()
                
                # Start with quick analysis first (faster)
                with st.spinner("Generating quick analysis (roast + recommendations)..."):
                    try:
                        from app.comprehensive_analysis import comprehensive_analyzer
                        quick_result = comprehensive_analyzer.generate_quick_analysis()
                        if quick_result.get("success"):
                            st.session_state.quick_analysis_sections = quick_result.get("parsed_sections", {})
                            st.session_state.quick_analysis_completed = True
                            st.session_state.analysis_status = "quick_completed"
                        else:
                            st.session_state.analysis_status = "error"
                            st.session_state.analysis_error = quick_result.get("error", "Unknown error")
                    except Exception as e:
                        st.session_state.analysis_status = "error"
                        st.session_state.analysis_error = str(e)
                    finally:
                        st.session_state.pop("analysis_processing_started", None)
                st.rerun()
            
            # Auto-refresh every 3 seconds to check if complete
            import time
            current_time = time.time()
            if 'last_refresh' not in st.session_state:
                st.session_state.last_refresh = current_time
            
            if current_time - st.session_state.last_refresh > 3:
                st.session_state.last_refresh = current_time
                st.rerun()
            else:
                if st.button("🔄 Check Status"):
                    st.rerun()
        

        
        elif analysis_status == "quick_completed":
            # Show quick analysis results immediately
            st.success("✅ Quick analysis completed! Comprehensive analysis in progress...")
            st.info("⏱️ **AI processing may take up to 2 minutes** - please be patient!")
            
            # Show quick analysis results FIRST (immediate display)
            if 'quick_analysis_sections' in st.session_state:
                sections = st.session_state['quick_analysis_sections']
                
                tab1, tab2 = st.tabs([
                    "😂  ROAST ME  😂", 
                    "📚  RECOMMENDATIONS  📚"
                ])
                
                with tab1:
                    if sections.get('humorous'):
                        st.markdown(sections['humorous'])
                    else:
                        st.warning("No humorous analysis available.")
                
                with tab2:
                    if sections.get('recommendations'):
                        st.markdown(sections['recommendations'])
                    else:
                        st.warning("No recommendations available.")
                
                st.info("🔄 Comprehensive analysis (insights + profile) still in progress...")
            
            # Start comprehensive analysis if not already started (separate from display)
            if 'comprehensive_analysis_started' not in st.session_state:
                st.session_state.comprehensive_analysis_started = True
                # Run comprehensive analysis in background without blocking UI
                try:
                    from app.comprehensive_analysis import comprehensive_analyzer
                    comprehensive_result = comprehensive_analyzer.generate_comprehensive_analysis_parallel()
                    if comprehensive_result.get("success"):
                        st.session_state.comprehensive_analysis_sections_parallel = comprehensive_result.get("parsed_sections", {})
                        # Combine sections
                        all_sections = {}
                        all_sections.update(st.session_state.get("quick_analysis_sections", {}))
                        all_sections.update(st.session_state.get("comprehensive_analysis_sections_parallel", {}))
                        st.session_state.comprehensive_analysis_sections = all_sections
                        st.session_state.analysis_status = "completed"
                    else:
                        st.warning(f"⚠️ Comprehensive analysis failed: {comprehensive_result.get('error')}")
                        # Still show quick analysis results
                        st.session_state.comprehensive_analysis_sections = st.session_state.get("quick_analysis_sections", {})
                        st.session_state.analysis_status = "completed"
                except Exception as e:
                    st.warning(f"⚠️ Comprehensive analysis failed: {str(e)}")
                    # Still show quick analysis results
                    st.session_state.comprehensive_analysis_sections = st.session_state.get("quick_analysis_sections", {})
                    st.session_state.analysis_status = "completed"
                finally:
                    st.session_state.pop("comprehensive_analysis_started", None)
                st.rerun()
            
            # Auto-refresh to check for comprehensive completion
            import time
            current_time = time.time()
            if 'last_refresh' not in st.session_state:
                st.session_state.last_refresh = current_time
            
            if current_time - st.session_state.last_refresh > 3:
                st.session_state.last_refresh = current_time
                st.rerun()
            else:
                if st.button("🔄 Check Status"):
                    st.rerun()
        
        elif analysis_status == "completed":
            # Show completed analysis
            if 'comprehensive_analysis_sections' in st.session_state:
                sections = st.session_state['comprehensive_analysis_sections']
                
                tab1, tab2, tab3, tab4 = st.tabs([
                    "😂  ROAST ME  😂", 
                    "👤  PERSONAL PROFILE  👤", 
                    "📚  RECOMMENDATIONS  📚", 
                    "📖  LITERARY INSIGHTS  📖"
                ])
                
                with tab1:
                    if sections.get('humorous'):
                        st.markdown(sections['humorous'])
                    else:
                        st.warning("No humorous analysis available.")
                
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
                
                with tab4:
                    if sections.get('insights'):
                        st.markdown(sections['insights'])
                    else:
                        st.warning("No insights available.")
        
        elif analysis_status == "error":
            # Show error state
            st.error("❌ **Analysis failed**")
            error_msg = st.session_state.get('analysis_error', 'Unknown error')
            st.write(f"Error: {error_msg}")
        
            # Allow retry
            if st.button("🔄 Retry Analysis"):
                st.session_state.analysis_status = "processing"
                st.session_state.analysis_start_time = datetime.now()
                st.session_state.pop('analysis_processing_started', None)
                st.session_state.pop('last_refresh', None)
                st.rerun()
        
        else:
            # Show generate button for manual trigger
            if st.button("🔮 Generate Comprehensive Analysis"):
                st.session_state.analysis_status = "processing"
                st.session_state.analysis_start_time = datetime.now()
                st.session_state.pop('analysis_processing_started', None)
                st.session_state.pop('last_refresh', None)
                st.rerun()
        
        # Clear Analysis button at bottom (only show if analysis exists)
        if analysis_status == "completed" and 'comprehensive_analysis_sections' in st.session_state:
            st.markdown("---")
            if st.button("🧹 Clear Analysis", use_container_width=True):
                st.session_state.pop('comprehensive_analysis_result', None)
                st.session_state.pop('comprehensive_analysis_sections', None)
                st.session_state.analysis_status = "not_started"
                st.session_state.pop('analysis_start_time', None)
                st.session_state.pop('analysis_processing_started', None)
                st.session_state.pop('last_refresh', None)
                st.rerun()
    else:
        st.warning(f"⚠️ Insufficient data for analysis")
        st.info("You need at least 5 books with 3 rated books to generate comprehensive analysis.")
    
    # Quick navigation at bottom
    show_quick_navigation()



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
        st.info("⏱️ **AI processing may take up to 2 minutes** - please be patient!")
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
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Books", user_stats.get('total_books', 0))
    with col2:
        st.metric("Rated Books", user_stats.get('books_with_ratings', 0))
    with col3:
        st.metric("Average Rating", f"{user_stats.get('average_rating', 0):.1f}")
    
    # Quick navigation at bottom
    show_quick_navigation()


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