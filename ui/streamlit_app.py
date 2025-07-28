"""Streamlit UI for Goodreads Analyzer."""

import os
import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px
from typing import Dict, Any, List, Optional
from app.ingest import GenreNormalizer
from app.session_db import session_db_manager
from app.db import db_manager

# Set page config
st.set_page_config(
    page_title="Goodreads Analyzer",
    page_icon="📚",
    layout="wide"
)

def sqlmodel_to_dict(obj):
    """Convert SQLModel object to dict."""
    return {
        col: getattr(obj, col)
        for col in obj.__class__.__table__.columns.keys()
    }

def show_quick_navigation():
    """Show quick navigation buttons at the bottom of each page."""
    st.markdown("---")
    st.markdown("### 🚀 Quick Navigation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Upload & Process", use_container_width=True):
            st.session_state.current_page = "upload"
            st.rerun()
    
    with col2:
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()
    
    with col3:
        if st.button("🔮 Comprehensive Analysis", use_container_width=True):
            st.session_state.current_page = "comprehensive"
            st.rerun()

def main():
    """Main Streamlit app."""
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "upload"
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("# 📚 Navigation")
        st.write("Choose a section:")
        
        # Navigation dropdown
        page = st.selectbox(
            "Choose a section:",
            ["📤 Upload & Process", "📊 Dashboard", "🔮 Comprehensive Analysis"],
            label_visibility="collapsed",
            key="nav_select"
        )
        
        # Update current page based on selection
        if page == "📤 Upload & Process":
            st.session_state.current_page = "upload"
        elif page == "📊 Dashboard":
            st.session_state.current_page = "dashboard"
        elif page == "🔮 Comprehensive Analysis":
            st.session_state.current_page = "comprehensive"
    
    # Main content area
    st.image("https://raw.githubusercontent.com/ColbyJacks/GoodreadsVibe/main/logo.png", width=100)
    st.title("Goodreads Analyzer")
    st.write("Deep literary psychology insights from your Goodreads data")
    
    # Show current page
    if st.session_state.current_page == "upload":
        show_upload_page()
    elif st.session_state.current_page == "dashboard":
        show_dashboard_page()
    elif st.session_state.current_page == "comprehensive":
        show_comprehensive_analysis_page_parallel()

def show_upload_page():
    """Show the upload page."""
    st.header("📤 Upload & Process")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("Upload your Goodreads CSV file to analyze your reading data.")
        # Simple instructions for getting CSV
        with st.expander("📋 How to get your Goodreads CSV file", expanded=False):
            st.markdown("""
            **Getting your Goodreads data is easy:**
            1. Go to [Goodreads My Books](https://www.goodreads.com/review/import)
            2. Click **"Export Library"** button
            3. Wait for the file to generate (may take a few minutes)
            4. Download the CSV file
            5. Upload it here!
            """)
    
    with col2:
        if st.button("🗑️ Clear My Data", type="secondary"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.current_page = "upload"
            
            # Clear session DB
            session_db_manager.clear_all()
            st.success("✅ Data cleared successfully!")
            st.rerun()
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose your Goodreads CSV file",
        type="csv",
        help="Export your Goodreads library as CSV and upload it here",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        try:
            # Save to temp file
            import tempfile
            tmp_file_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
            with open(tmp_file_path, 'wb') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
            
            # Process CSV
            df = pd.read_csv(tmp_file_path)
            
            # Clear existing data
            session_db_manager.clear_all()
            
            # Process each book
            processed_books = 0
            skipped_books = 0
            
            with st.spinner("Processing your books..."):
                for index, row in df.iterrows():
                    try:
                        def safe_str_or_none(value):
                            if pd.isna(value):
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
                
        except Exception as e:
            st.error(f"❌ Error processing data: {str(e)}")
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
    
    # Quick navigation at bottom
    show_quick_navigation()

def show_dashboard_page():
    """Show the dashboard page."""
    st.header("📊 Dashboard")
    
    # Get user data
    user_books = session_db_manager.get_user_books()
    user_stats = st.session_state.get('user_stats', {})
    
    if not user_books:
        st.warning("⚠️ No books found. Please upload your Goodreads data first.")
        show_quick_navigation()
        return
    
    # Show summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📚 Total Books", user_stats.get('total_books', 0))
    with col2:
        st.metric("⭐ Rated Books", user_stats.get('books_with_ratings', 0))
    with col3:
        avg_rating = user_stats.get('average_rating', 0)
        st.metric("📊 Average Rating", f"{avg_rating:.1f}" if avg_rating > 0 else "N/A")
    
    # Create ratings heatmap
    st.subheader("📈 Ratings Distribution")
    
    # Filter out 0-star ratings
    rated_books = [b for b in user_books if b.get('my_rating', 0) > 0]
    
    if rated_books:
        # Create ratings data
        ratings_data = []
        for book in rated_books:
            ratings_data.append({
                'My Rating': book.get('my_rating', 0),
                'Average Rating': round(book.get('average_rating', 0), 1),
                'Count': 1
            })
        
        # Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(ratings_data)
        
        # Create pivot table
        pivot = pd.pivot_table(
            df,
            values='Count',
            index='My Rating',
            columns='Average Rating',
            aggfunc='count',
            fill_value=0
        )
        
        # Create heatmap
        fig = px.imshow(
            pivot,
            labels=dict(x="Average Rating", y="My Rating", color="Number of Books"),
            title="Your Ratings vs. Average Ratings",
            color_continuous_scale="Viridis",
            aspect="auto"
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title="Average Rating",
            yaxis_title="Your Rating",
            height=400
        )
        
        # Show plot
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ No rated books found")
    
    # Show genre distribution
    st.subheader("📚 Genre Distribution")
    
    # Get genre counts
    genre_counts = {}
    for book in user_books:
        genres = book.get('genres', '').split(', ')
        for genre in genres:
            if genre and genre != "Unknown":
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    if genre_counts:
        # Convert to DataFrame
        genre_df = pd.DataFrame([
            {'Genre': genre, 'Count': count}
            for genre, count in genre_counts.items()
        ])
        
        # Sort by count
        genre_df = genre_df.sort_values('Count', ascending=True)
        
        # Create bar chart
        fig = px.bar(
            genre_df,
            x='Count',
            y='Genre',
            orientation='h',
            title="Books by Genre",
            labels={'Count': 'Number of Books', 'Genre': ''},
            color='Count',
            color_continuous_scale="Viridis"
        )
        
        # Update layout
        fig.update_layout(
            showlegend=False,
            height=max(400, len(genre_counts) * 30)
        )
        
        # Show plot
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ No genre information found")
    
    # Quick navigation at bottom
    show_quick_navigation()

def show_comprehensive_analysis_page_parallel():
    """Show the comprehensive analysis page with parallel processing."""
    st.header("�� Comprehensive Analysis")
    
    # Get user data
    user_books = session_db_manager.get_user_books()
    user_stats = st.session_state.user_stats
    
    # Check if comprehensive analysis can be generated
    total_books = user_stats.get('total_books', 0)
    books_with_ratings = user_stats.get('books_with_ratings', 0)
    
    # Debug information
    st.write(f"🔍 Debug: Analysis status = {st.session_state.get('analysis_status', 'not_started')}")
    st.write(f"🔍 Debug: Processing started = {'analysis_processing_started' in st.session_state}")
    st.write(f"🔍 Debug: Quick started = {'quick_analysis_started' in st.session_state}")
    st.write(f"🔍 Debug: Comprehensive started = {'comprehensive_analysis_started' in st.session_state}")
    st.write(f"🔍 Debug: Quick completed = {st.session_state.get('quick_analysis_completed', False)}")
    st.write(f"🔍 Debug: Comprehensive completed = {st.session_state.get('comprehensive_analysis_completed', False)}")
    if 'quick_analysis_sections' in st.session_state:
        st.write(f"🔍 Debug: Quick sections = {list(st.session_state['quick_analysis_sections'].keys())}")
    if 'comprehensive_analysis_sections_parallel' in st.session_state:
        st.write(f"🔍 Debug: Comprehensive sections = {list(st.session_state['comprehensive_analysis_sections_parallel'].keys())}")
    
    can_generate = total_books >= 5 and books_with_ratings >= 3
    
    if can_generate:
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
                st.write(f"⏱️ Estimated Time: {elapsed_seconds} seconds")
            
            st.write("📚 Analyzing your reading patterns...")
            st.write("🧠 Generating psychological insights...")
            st.write("💡 Creating personalized recommendations...")
            st.write("😂 Preparing your literary roast...")
            
            # Trigger actual processing - start both analyses in sequence but show results as they complete
            if 'analysis_processing_started' not in st.session_state:
                st.session_state.analysis_processing_started = True
                st.session_state.quick_analysis_started = True
                
                # Start quick analysis first
                with st.spinner("Generating quick analysis (roast + recommendations)..."):
                    try:
                        from app.comprehensive_analysis import comprehensive_analyzer
                        quick_result = comprehensive_analyzer.generate_quick_analysis()
                        if quick_result.get("success"):
                            st.session_state.quick_analysis_sections = quick_result.get("parsed_sections", {})
                            st.session_state.quick_analysis_completed = True
                            st.session_state.analysis_status = "quick_completed"  # Show quick results immediately
                        else:
                            st.session_state.quick_analysis_error = quick_result.get("error", "Unknown error")
                            st.session_state.analysis_status = "error"
                    except Exception as e:
                        st.session_state.quick_analysis_error = str(e)
                        st.session_state.analysis_status = "error"
                    finally:
                        st.session_state.pop("quick_analysis_started", None)
                st.rerun()  # Force refresh to show quick results
                
            # After quick analysis is shown, start comprehensive
            elif st.session_state.get('quick_analysis_completed') and 'comprehensive_analysis_started' not in st.session_state:
                st.session_state.comprehensive_analysis_started = True
                
                with st.spinner("Generating comprehensive analysis (insights + profile)..."):
                    try:
                        from app.comprehensive_analysis import comprehensive_analyzer
                        comprehensive_result = comprehensive_analyzer.generate_comprehensive_analysis_parallel()
                        if comprehensive_result.get("success"):
                            st.session_state.comprehensive_analysis_sections_parallel = comprehensive_result.get("parsed_sections", {})
                            st.session_state.comprehensive_analysis_completed = True
                            
                            # Combine sections
                            all_sections = {}
                            all_sections.update(st.session_state.get("quick_analysis_sections", {}))
                            all_sections.update(st.session_state.get("comprehensive_analysis_sections_parallel", {}))
                            st.session_state.comprehensive_analysis_sections = all_sections
                            st.session_state.analysis_status = "completed"
                        else:
                            st.session_state.comprehensive_analysis_error = comprehensive_result.get("error", "Unknown error")
                            # Keep showing quick results
                            st.session_state.comprehensive_analysis_sections = st.session_state.get("quick_analysis_sections", {})
                    except Exception as e:
                        st.session_state.comprehensive_analysis_error = str(e)
                        # Keep showing quick results
                        st.session_state.comprehensive_analysis_sections = st.session_state.get("quick_analysis_sections", {})
                    finally:
                        st.session_state.pop("comprehensive_analysis_started", None)
                st.rerun()  # Force refresh to show final results
            
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
            # Show quick analysis results while comprehensive is running
            st.success("✅ Quick analysis completed! Comprehensive analysis in progress...")
            st.info("⏱️ **AI processing may take up to 2 minutes** - please be patient!")
            
            # Show quick analysis results immediately
            if 'quick_analysis_sections' in st.session_state:
                sections = st.session_state['quick_analysis_sections']
                
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
                
                # Start comprehensive analysis in the background
                if 'comprehensive_analysis_started' not in st.session_state:
                    st.session_state.comprehensive_analysis_started = True
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
                
                tab1, tab2, tab3, tab4 = st.tabs([
                    "😂  ROAST ME  😂", 
                    "👤  PERSONAL PROFILE  ��", 
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
                st.rerun()
    
    else:
        # Show requirements
        st.warning("⚠️ Not enough data for comprehensive analysis")
        st.write("Requirements:")
        st.write("- At least 5 books total")
        st.write("- At least 3 books with ratings")
        st.write(f"Current stats:")
        st.write(f"- Total books: {total_books}")
        st.write(f"- Books with ratings: {books_with_ratings}")
    
    # Quick navigation at bottom
    show_quick_navigation()

if __name__ == "__main__":
    main()
