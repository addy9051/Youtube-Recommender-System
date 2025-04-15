import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import os
import sys

# Add current directory to path to fix import issues
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from youtube_api import youtube_api
from recommendation_engine import recommendation_engine
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Print API key status for debugging
if os.getenv('YOUTUBE_API_KEY'):
    print("YouTube API key found! Using real YouTube data.")
else:
    print("WARNING: YouTube API key not found. Using mock data instead.")

# Set page config
st.set_page_config(
    page_title="YouTube Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f9f9f9;
    }
    .stApp {
        font-family: 'Roboto', sans-serif;
    }
    .video-card {
        border-radius: 8px;
        transition: transform 0.2s;
        cursor: pointer;
    }
    .video-card:hover {
        transform: translateY(-5px);
    }
    .category-pill {
        background-color: #e0e0e0;
        border-radius: 16px;
        padding: 5px 12px;
        margin: 5px;
        cursor: pointer;
        display: inline-block;
        font-size: 0.8em;
    }
    .category-pill.active {
        background-color: #4285f4;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0 0;
        padding: 10px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4285f4;
        color: white;
    }
    .search-box {
        border-radius: 24px;
        border: 1px solid #dfe1e5;
        box-shadow: none;
        padding: 10px 16px;
    }
    .metric-card {
        background-color: white;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        text-align: center;
    }
    .video-title {
        font-weight: 500;
        font-size: 1.1em;
        margin-top: 8px;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    .channel-name {
        color: #606060;
        font-size: 0.9em;
        margin-top: 4px;
    }
    .view-count {
        color: #606060;
        font-size: 0.8em;
    }
    .similarity-score {
        position: absolute;
        top: 10px;
        right: 10px;
        background-color: rgba(0,0,0,0.7);
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8em;
    }
    .iframe-container {
        position: relative;
        overflow: hidden;
        width: 100%;
        padding-top: 56.25%; /* 16:9 Aspect Ratio */
    }
    .responsive-iframe {
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        right: 0;
        width: 100%;
        height: 100%;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_video' not in st.session_state:
    st.session_state.current_video = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'current_category' not in st.session_state:
    st.session_state.current_category = "all"
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1  # Default user ID for demo
if 'videos' not in st.session_state:
    st.session_state.videos = []
if 'trending_videos' not in st.session_state:
    st.session_state.trending_videos = []
if 'history_videos' not in st.session_state:
    st.session_state.history_videos = []
if 'recommended_videos' not in st.session_state:
    st.session_state.recommended_videos = []
if 'categories' not in st.session_state:
    st.session_state.categories = youtube_api.get_categories()
if 'api_key_set' not in st.session_state:
    st.session_state.api_key_set = bool(os.getenv('YOUTUBE_API_KEY'))

# Formatting helper functions
def format_count(count):
    """Format large numbers with K, M, B suffixes"""
    count = int(count) if count.isdigit() else 0
    if count < 1000:
        return str(count)
    elif count < 1000000:
        return f"{count/1000:.1f}K".replace('.0K', 'K')
    elif count < 1000000000:
        return f"{count/1000000:.1f}M".replace('.0M', 'M')
    else:
        return f"{count/1000000000:.1f}B".replace('.0B', 'B')

def format_duration(duration):
    """Format YouTube duration (PT1H2M3S) into readable format (1:02:03)"""
    if not duration:
        return "Unknown"
    
    duration = duration.replace('PT', '')
    hours, minutes, seconds = 0, 0, 0
    
    if 'H' in duration:
        hours, duration = duration.split('H')
        hours = int(hours)
    
    if 'M' in duration:
        minutes, duration = duration.split('M')
        minutes = int(minutes)
    
    if 'S' in duration:
        seconds = int(duration.replace('S', ''))
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def render_video_card(video, show_score=False, score=None, show_progress=False, progress=0):
    """Render a video card with thumbnail and metadata"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Calculate image dimensions and aspect ratio
        thumbnail_url = video.get('thumbnail', '')
        if thumbnail_url:
            if show_score and score is not None:
                score_html = f'<div class="similarity-score">{score:.1f}%</div>'
            else:
                score_html = ''
                
            if show_progress and progress > 0:
                progress_pct = min(progress, 100)
                progress_bar = f'''
                <div style="height: 3px; width: 100%; background-color: #e0e0e0; position: absolute; bottom: 0; left: 0;">
                    <div style="height: 100%; width: {progress_pct}%; background-color: red;"></div>
                </div>
                '''
            else:
                progress_bar = ''
                
            # Create a container with relative positioning
            st.markdown(f'''
            <div style="position: relative; cursor: pointer;" onclick="handleVideoClick('{video['id']}')">
                <img src="{thumbnail_url}" width="100%" style="border-radius: 8px;">
                {score_html}
                {progress_bar}
                <div style="position: absolute; bottom: 5px; right: 5px; background-color: rgba(0,0,0,0.8); color: white; padding: 2px 4px; border-radius: 2px; font-size: 0.8em;">
                    {format_duration(video.get('duration', ''))}
                </div>
            </div>
            ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div style="cursor: pointer;" onclick="handleVideoClick('{video['id']}')">
            <div class="video-title">{video.get('title', 'No Title')}</div>
            <div class="channel-name">{video.get('channelTitle', '')}</div>
            <div class="view-count">{format_count(video.get('viewCount', '0'))} views • {format_count(video.get('likeCount', '0'))} likes</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")

def load_initial_data():
    """Load initial data for the application"""
    # Load trending videos
    trending_videos = youtube_api.get_trending_videos(st.session_state.current_category)
    
    # Add to recommendation engine
    recommendation_engine.add_videos(trending_videos)
    
    # Store in session state
    st.session_state.trending_videos = trending_videos
    
    # Load or reset recommended videos based on if we have a current video
    if st.session_state.current_video:
        recommended_videos = recommendation_engine.get_hybrid_recommendations(
            user_id=st.session_state.user_id,
            video_id=st.session_state.current_video.get('id'),
            category_id=st.session_state.current_category
        )
    else:
        recommended_videos = []
    
    st.session_state.recommended_videos = recommended_videos
    
    # Get user watch history
    history_videos = recommendation_engine.get_user_history(st.session_state.user_id)
    st.session_state.history_videos = history_videos

def handle_search():
    """Handle search functionality"""
    if st.session_state.search_query:
        search_results = youtube_api.search_videos(
            st.session_state.search_query,
            st.session_state.current_category
        )
        
        # Add videos to recommendation engine
        recommendation_engine.add_videos(search_results)
        
        # Update session state
        st.session_state.videos = search_results
        
        # Reset current video if needed
        if st.session_state.current_video and st.session_state.current_video.get('id') not in [v.get('id') for v in search_results]:
            st.session_state.current_video = None

def handle_video_selection(video_id):
    """Handle video selection and update recommendations"""
    # Get video details
    video = youtube_api.get_video_details(video_id)
    
    if video:
        # Update current video
        st.session_state.current_video = video
        
        # Add to recommendation engine
        recommendation_engine.add_videos([video])
        
        # Add to watch history
        now = datetime.now()
        recommendation_engine.add_to_history(
            st.session_state.user_id, 
            video_id,
            now,
            0  # Initial watch percentage
        )
        
        # Update recommendations
        recommended_videos = recommendation_engine.get_hybrid_recommendations(
            user_id=st.session_state.user_id,
            video_id=video_id,
            category_id=st.session_state.current_category
        )
        st.session_state.recommended_videos = recommended_videos
        
        # Update watch history
        history_videos = recommendation_engine.get_user_history(st.session_state.user_id)
        st.session_state.history_videos = history_videos

def clear_history():
    """Clear user watch history"""
    recommendation_engine.clear_history(st.session_state.user_id)
    st.session_state.history_videos = []
    
    # Show success message
    st.success("Watch history cleared successfully!")

def render_api_key_form():
    """Render form for user to input YouTube API key"""
    st.markdown("## YouTube API Key Setup")
    st.warning("""
    The YouTube Recommender requires a YouTube Data API key to fetch real video data.
    Without an API key, the app will use mock data for demonstration purposes.
    """)
    
    with st.form("api_key_form"):
        api_key = st.text_input("Enter YouTube API Key:", 
                               type="password", 
                               help="Get a key from https://console.developers.google.com/")
        submitted = st.form_submit_button("Save API Key")
        
        if submitted and api_key:
            # Save the API key (in a real app, store securely)
            os.environ['YOUTUBE_API_KEY'] = api_key
            
            # Update session state
            st.session_state.api_key_set = True
            
            # Reload the YouTube API
            youtube_api.api_key = api_key
            youtube_api.init_api()
            
            # Show success message
            st.success("API Key saved successfully! Reloading data...")
            load_initial_data()
            st.experimental_rerun()

def render_header():
    """Render the application header"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown("""
        <h1 style="color: #4285f4; margin-bottom: 0;">
            <span style="color: #ea4335;">Y</span><span style="color: #fbbc05;">o</span><span style="color: #4285f4;">u</span><span style="color: #34a853;">T</span><span style="color: #ea4335;">u</span><span style="color: #fbbc05;">b</span><span style="color: #4285f4;">e</span>
            <span style="font-weight: 400;">Recommender</span>
        </h1>
        """, unsafe_allow_html=True)
    
    with col2:
        search_query = st.text_input(
            "Search for videos", 
            value=st.session_state.search_query,
            key="search_input",
            placeholder="Search..."
        )
        
        if search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
            handle_search()
    
    with col3:
        if not st.session_state.api_key_set:
            st.button("Set YouTube API Key", on_click=lambda: st.session_state.update({"show_api_form": True}))
        
        # Add settings gear and about button
        cols = st.columns(2)
        with cols[0]:
            st.button("⚙️", help="Settings")
        with cols[1]:
            st.button("ℹ️", help="About")

def render_categories():
    """Render category selection pills"""
    st.markdown("### Categories")
    
    # Create columns for categories
    cols = st.columns(5)
    
    for i, category in enumerate(st.session_state.categories):
        col_idx = i % 5
        
        with cols[col_idx]:
            active_class = "active" if category['id'] == st.session_state.current_category else ""
            category_name = category['title']
            
            if st.button(category_name, key=f"cat_{category['id']}"):
                st.session_state.current_category = category['id']
                # Reload trending videos with the new category
                st.session_state.trending_videos = youtube_api.get_trending_videos(category['id'])
                
                # Update recommendations if we have a current video
                if st.session_state.current_video:
                    st.session_state.recommended_videos = recommendation_engine.get_hybrid_recommendations(
                        user_id=st.session_state.user_id,
                        video_id=st.session_state.current_video.get('id'),
                        category_id=category['id']
                    )

def render_current_video():
    """Render the currently selected video"""
    if not st.session_state.current_video:
        return
    
    video = st.session_state.current_video
    
    st.markdown("## Now Playing")
    
    # Embed YouTube player
    video_id = video.get('id', '')
    st.markdown(f'''
    <div class="iframe-container">
        <iframe class="responsive-iframe" 
                src="https://www.youtube.com/embed/{video_id}?autoplay=1" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
        </iframe>
    </div>
    ''', unsafe_allow_html=True)
    
    # Video metadata
    st.markdown(f"### {video.get('title', 'No Title')}")
    st.markdown(f"**{video.get('channelTitle', '')}**")
    
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Views", format_count(video.get('viewCount', '0')))
    with col2:
        st.metric("Likes", format_count(video.get('likeCount', '0')))
    with col3:
        st.metric("Comments", format_count(video.get('commentCount', '0')))
    
    # Description (expandable)
    with st.expander("Description"):
        st.markdown(video.get('description', 'No description available'))
    
    # Tags
    if video.get('tags'):
        with st.expander("Tags"):
            tags_html = ' '.join([f'<span class="category-pill">{tag}</span>' for tag in video.get('tags', [])])
            st.markdown(tags_html, unsafe_allow_html=True)

def render_video_grid(videos, title, empty_message="No videos available", show_progress=False):
    """Render a grid of video cards"""
    if not videos:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background-color: white; border-radius: 8px;">
            <p>{empty_message}</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Create a 3-column grid
    cols = st.columns(3)
    
    for i, video in enumerate(videos):
        col_idx = i % 3
        
        with cols[col_idx]:
            progress = video.get('watchedPercentage', 0) if show_progress else 0
            render_video_card(video, show_progress=show_progress, progress=progress)

def render_recommendations():
    """Render recommendation sections"""
    if st.session_state.current_video:
        st.markdown("## Recommendations")
        render_video_grid(
            st.session_state.recommended_videos,
            "Recommendations",
            "No recommendations available. Try watching some videos first."
        )
    
    # Trending section
    st.markdown("## Trending")
    render_video_grid(
        st.session_state.trending_videos,
        "Trending Videos",
        "No trending videos available for this category."
    )
    
    # Watch history section
    st.markdown("## Watch History")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Recently Watched")
    with col2:
        if st.session_state.history_videos:
            st.button("Clear History", on_click=clear_history)
    
    render_video_grid(
        st.session_state.history_videos,
        "Watch History",
        "No watch history yet. Videos you watch will appear here.",
        show_progress=True
    )

def render_search_results():
    """Render search results"""
    if st.session_state.search_query and st.session_state.videos:
        st.markdown(f"## Search Results for '{st.session_state.search_query}'")
        render_video_grid(
            st.session_state.videos,
            "Search Results",
            f"No results found for '{st.session_state.search_query}'."
        )

def render_insights():
    """Render insights and analytics based on user watch history"""
    if not st.session_state.history_videos:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background-color: white; border-radius: 8px;">
            <p>No watch history available. Watch some videos to see insights.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Create some basic insights
    history = st.session_state.history_videos
    
    # Category distribution
    categories = {}
    for video in history:
        cat_id = video.get('categoryId', 'Unknown')
        cat_name = next((c['title'] for c in st.session_state.categories if c['id'] == cat_id), 'Unknown')
        categories[cat_name] = categories.get(cat_name, 0) + 1
    
    # Create dataframe for plotting
    df_categories = pd.DataFrame({
        'Category': list(categories.keys()),
        'Count': list(categories.values())
    })
    
    # Channels distribution
    channels = {}
    for video in history:
        channel = video.get('channelTitle', 'Unknown')
        channels[channel] = channels.get(channel, 0) + 1
    
    # Sort and get top channels
    top_channels = dict(sorted(channels.items(), key=lambda x: x[1], reverse=True)[:5])
    df_channels = pd.DataFrame({
        'Channel': list(top_channels.keys()),
        'Count': list(top_channels.values())
    })
    
    # Create visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Category Distribution")
        fig = px.pie(df_categories, values='Count', names='Category', 
                     title='Videos Watched by Category',
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Top Channels")
        fig = px.bar(df_channels, x='Channel', y='Count', 
                     title='Most Watched Channels',
                     color='Count',
                     color_continuous_scale='blues')
        st.plotly_chart(fig, use_container_width=True)
    
    # Watch time metrics
    total_videos = len(history)
    
    st.markdown("### Watch Metrics")
    metric_cols = st.columns(3)
    
    with metric_cols[0]:
        st.markdown("""
        <div class="metric-card">
            <h3>Total Videos Watched</h3>
            <h2>{}</h2>
        </div>
        """.format(total_videos), unsafe_allow_html=True)
    
    with metric_cols[1]:
        avg_completion = sum(video.get('watchedPercentage', 0) for video in history) / max(total_videos, 1)
        st.markdown("""
        <div class="metric-card">
            <h3>Average Completion</h3>
            <h2>{:.1f}%</h2>
        </div>
        """.format(avg_completion), unsafe_allow_html=True)
    
    with metric_cols[2]:
        # Calculate a mock engagement score
        engagement_score = min(100, (total_videos * 10) + (avg_completion / 2))
        st.markdown("""
        <div class="metric-card">
            <h3>Engagement Score</h3>
            <h2>{:.1f}</h2>
        </div>
        """.format(engagement_score), unsafe_allow_html=True)

def main():
    """Main application function"""
    # Check if we need to show API form
    if not st.session_state.api_key_set and st.session_state.get('show_api_form', False):
        render_api_key_form()
        return
    
    # Load initial data if needed
    if not st.session_state.trending_videos:
        load_initial_data()
    
    # Add JavaScript for handling video clicks
    st.markdown("""
    <script>
    function handleVideoClick(videoId) {
        // Use Streamlit's postMessage to communicate with Python
        window.parent.postMessage({
            type: "streamlit:setComponentValue",
            value: videoId,
            dataType: "string",
            key: "selected_video_id"
        }, "*");
    }
    </script>
    """, unsafe_allow_html=True)
    
    # Handle video selection via callback
    selected_video_id = st.empty()
    if selected_video_id:
        handle_video_selection(selected_video_id)
    
    # Render header with search
    render_header()
    
    # Render category selection
    render_categories()
    
    # Create tab navigation
    tab1, tab2, tab3 = st.tabs(["Home", "Search", "Insights"])
    
    with tab1:
        # Render current video if any
        if st.session_state.current_video:
            render_current_video()
        
        # Render recommendations and trending
        render_recommendations()
    
    with tab2:
        # Search form
        st.markdown("## Video Search")
        search_query = st.text_input(
            "Search for videos", 
            value=st.session_state.search_query,
            key="search_input_tab",
            placeholder="Enter keywords..."
        )
        
        if search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
            handle_search()
        
        # Render search results
        render_search_results()
    
    with tab3:
        st.markdown("## Watch Insights")
        render_insights()

if __name__ == "__main__":
    main()