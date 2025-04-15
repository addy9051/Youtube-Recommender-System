import streamlit as st
import pandas as pd
import numpy as np
import re
import time
import json
from dotenv import load_dotenv
import os
from datetime import datetime
import random

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="YouTube Recommendation Engine",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global state for the application
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1  # Default user ID
if 'current_video' not in st.session_state:
    st.session_state.current_video = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []
if 'categories' not in st.session_state:
    st.session_state.categories = []
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None
if 'trending_videos' not in st.session_state:
    st.session_state.trending_videos = []
if 'api_key_confirmed' not in st.session_state:
    st.session_state.api_key_confirmed = os.getenv("YOUTUBE_API_KEY") is not None

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
    }
    .video-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 1rem;
    }
    .video-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
        transition: transform 0.2s;
    }
    .video-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .thumbnail-container {
        position: relative;
        width: 100%;
        padding-top: 56.25%; /* 16:9 aspect ratio */
    }
    .thumbnail {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .video-info {
        padding: 0.75rem;
    }
    .video-title {
        font-weight: bold;
        margin-bottom: 0.5rem;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .video-meta {
        color: #666;
        font-size: 0.8rem;
    }
    .video-stats {
        display: flex;
        justify-content: space-between;
        margin-top: 0.5rem;
        font-size: 0.8rem;
    }
    .category-pills {
        display: flex;
        flex-wrap: nowrap;
        overflow-x: auto;
        padding: 0.5rem 0;
        gap: 0.5rem;
    }
    .pill {
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        white-space: nowrap;
        font-size: 0.85rem;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .pill:hover {
        background-color: #f0f0f0;
    }
    .pill.active {
        background-color: #4CAF50;
        color: white;
    }
    .sidebar .sidebar-content {
        background-color: #f5f5f5;
    }
    .progress-bar {
        height: 4px;
        background-color: #e0e0e0;
        border-radius: 2px;
        width: 100%;
    }
    .progress-value {
        height: 100%;
        background-color: #ff0000;
        border-radius: 2px;
    }
    h1, h2, h3 {
        color: #333;
    }
    .st-emotion-cache-16txtl3 h1 {
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 1rem;
        color: #212121;
    }
    .search-container {
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

def format_count(count):
    """Format large numbers with K, M, B suffixes"""
    if count is None:
        return "0"
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
    if not duration or duration == 'PT0M0S':
        return "0:00"
    
    # Extract hours, minutes, seconds using regex
    hours = re.search(r'(\d+)H', duration)
    minutes = re.search(r'(\d+)M', duration)
    seconds = re.search(r'(\d+)S', duration)
    
    # Convert to integers with default values of 0
    h = int(hours.group(1)) if hours else 0
    m = int(minutes.group(1)) if minutes else 0
    s = int(seconds.group(1)) if seconds else 0
    
    # Format based on duration length
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    else:
        return f"{m}:{s:02d}"

def load_initial_data():
    """Load initial data for the application"""
    # Import here to avoid circular imports
    from youtube_api import YouTubeAPI
    from recommendation_engine import RecommendationEngine
    
    # Initialize API and recommendation engine
    youtube_api = YouTubeAPI()
    recommendation_engine = RecommendationEngine()
    
    # Get categories if not already loaded
    if not st.session_state.categories:
        st.session_state.categories = youtube_api.get_categories()
    
    # Get trending videos
    if not st.session_state.trending_videos:
        trending = youtube_api.get_trending_videos(max_results=12)
        recommendation_engine.add_videos(trending)
        st.session_state.trending_videos = trending
    
    return youtube_api, recommendation_engine

def handle_search():
    """Handle search functionality"""
    from youtube_api import YouTubeAPI
    from recommendation_engine import RecommendationEngine
    
    query = st.session_state.search_query
    if not query:
        return
    
    youtube_api = YouTubeAPI()
    recommendation_engine = RecommendationEngine()
    
    category_id = st.session_state.selected_category
    
    with st.spinner(f"Searching for '{query}'..."):
        search_results = youtube_api.search_videos(query, category_id, max_results=12)
        recommendation_engine.add_videos(search_results)
        st.session_state.search_results = search_results

def handle_video_selection():
    """Handle video selection and update recommendations"""
    from youtube_api import YouTubeAPI
    from recommendation_engine import RecommendationEngine
    
    video_id = st.session_state.selected_video
    if not video_id:
        return
    
    youtube_api = YouTubeAPI()
    recommendation_engine = RecommendationEngine()
    
    with st.spinner("Loading video details..."):
        # Get full video details
        video = youtube_api.get_video_details(video_id)
        if video:
            st.session_state.current_video = video
            
            # Add to history
            timestamp = datetime.now().isoformat()
            recommendation_engine.add_to_history(
                st.session_state.user_id, 
                video_id, 
                timestamp, 
                random.randint(20, 100)  # Simulate random watch percentage
            )
            
            # Update history in session state
            history = recommendation_engine.get_user_history(st.session_state.user_id)
            st.session_state.history = history
            
            # Get recommendations based on the selected video
            recommendations = recommendation_engine.get_hybrid_recommendations(
                user_id=st.session_state.user_id,
                video_id=video_id,
                category_id=st.session_state.selected_category,
                limit=8
            )
            st.session_state.recommendations = recommendations

def clear_history():
    """Clear user watch history"""
    from recommendation_engine import RecommendationEngine
    
    recommendation_engine = RecommendationEngine()
    recommendation_engine.clear_history(st.session_state.user_id)
    st.session_state.history = []
    st.success("Watch history has been cleared!")

def render_api_key_form():
    """Render form for user to input YouTube API key"""
    st.markdown("## YouTube API Configuration")
    
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if api_key:
        st.success("YouTube API key is configured! You can start using the recommendation engine.")
        if st.button("Continue to the app"):
            st.session_state.api_key_confirmed = True
            st.rerun()
    else:
        st.warning("No YouTube API key found. You need a valid API key to fetch videos from YouTube.")
        
        with st.form("api_key_form"):
            new_api_key = st.text_input("Enter your YouTube API key:", type="password")
            submitted = st.form_submit_button("Save API Key")
            
            if submitted and new_api_key:
                # Save to .env file
                with open(".env", "w") as f:
                    f.write(f"YOUTUBE_API_KEY={new_api_key}")
                st.success("API key saved! Please restart the application.")
                time.sleep(2)
                st.rerun()

def render_video_card(video, show_progress=False, progress=0):
    """Render a video card with thumbnail and metadata"""
    video_id = video['id']
    title = video['title']
    channel = video['channel_title']
    views = format_count(video['view_count'])
    duration = format_duration(video['duration'])
    
    html = f"""
    <div class="video-card" onclick="handleVideoClick('{video_id}')">
        <div class="thumbnail-container">
            <img class="thumbnail" src="{video['thumbnail_url']}" alt="{title}">
            <div style="position: absolute; bottom: 5px; right: 5px; background: rgba(0,0,0,0.7); color: white; padding: 2px 5px; border-radius: 3px; font-size: 0.8rem;">
                {duration}
            </div>
        </div>
        <div class="video-info">
            <div class="video-title">{title}</div>
            <div class="video-meta">{channel}</div>
            <div class="video-stats">
                <span>{views} views</span>
            </div>
            {"<div class='progress-bar'><div class='progress-value' style='width: " + str(progress) + "%;'></div></div>" if show_progress else ""}
        </div>
    </div>
    """
    return html

def render_video_grid(videos, title, empty_message="No videos available"):
    """Render a grid of videos in a grid layout"""
    st.markdown(f"## {title}")
    
    if not videos:
        st.info(empty_message)
        return
    
    # Create a grid of videos using HTML
    grid_html = '<div class="video-grid">'
    
    for video in videos:
        # Check if this video is in history
        progress = 0
        for h in st.session_state.history:
            if h['video']['id'] == video['id']:
                progress = h['watched_percentage']
                break
        
        show_progress = progress > 0
        grid_html += render_video_card(video, show_progress, progress)
    
    grid_html += '</div>'
    
    # Add JavaScript to handle video clicks
    js = """
    <script>
    function handleVideoClick(videoId) {
        // Use Streamlit's setComponentValue to update the session state
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: videoId,
            target: 'selected_video'
        }, '*');
    }
    </script>
    """
    
    # Render the HTML
    st.markdown(grid_html + js, unsafe_allow_html=True)
    
    # Create a container for the selected video callback
    if 'selected_video' not in st.session_state:
        st.session_state.selected_video = None
    
    # Hidden element to trigger callback when a video is clicked
    if st.session_state.selected_video:
        handle_video_selection()
        st.session_state.selected_video = None  # Reset to prevent repeated triggers

def render_video_player():
    """Render the YouTube video player"""
    if not st.session_state.current_video:
        return
    
    video = st.session_state.current_video
    video_id = video['id']
    
    # Video player container with title
    st.markdown(f"## {video['title']}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Embed YouTube player
        st.markdown(f"""
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 8px;">
            <iframe 
                src="https://www.youtube.com/embed/{video_id}?autoplay=1" 
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;"
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>
        </div>
        """, unsafe_allow_html=True)
        
        # Video stats
        st.markdown(f"""
        <div style="margin-top: 1rem;">
            <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">{video['channel_title']}</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="font-size: 0.9rem;">{format_count(video['view_count'])} views</div>
                    <div style="font-size: 0.9rem;">👍 {format_count(video['like_count'])}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Video description (collapsed)
        with st.expander("Description"):
            st.write(video['description'])
    
    with col2:
        # Show tags if available
        if video.get('tags'):
            st.markdown("### Tags")
            tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;">'
            for tag in video['tags'][:10]:  # Limit to first 10 tags
                tags_html += f'<span style="background: #f1f1f1; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem;">{tag}</span>'
            tags_html += '</div>'
            st.markdown(tags_html, unsafe_allow_html=True)

def render_categories():
    """Render category selection pills"""
    if not st.session_state.categories:
        return
    
    # Create the HTML for the category pills
    html = '<div class="category-pills">'
    html += f'<div class="pill {"active" if not st.session_state.selected_category else ""}" onclick="selectCategory(null)">All Categories</div>'
    
    for category in st.session_state.categories:
        is_active = st.session_state.selected_category == category['id']
        html += f'<div class="pill {("active" if is_active else "")}" onclick="selectCategory(\'{category["id"]}\')">'\
                f'{category["title"]}</div>'
    
    html += '</div>'
    
    # Add JavaScript to handle category selection
    js = """
    <script>
    function selectCategory(categoryId) {
        // Use Streamlit's setComponentValue to update the session state
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: categoryId,
            target: 'selected_category'
        }, '*');
    }
    </script>
    """
    
    # Render the HTML
    st.markdown(html + js, unsafe_allow_html=True)
    
    # Create a container for the category callback
    category_placeholder = st.empty()
    
    # If a category was selected, reload data
    if st.session_state.get('last_category') != st.session_state.selected_category:
        st.session_state['last_category'] = st.session_state.selected_category
        # Reload trending videos with selected category
        youtube_api, recommendation_engine = load_initial_data()
        st.session_state.trending_videos = youtube_api.get_trending_videos(
            category_id=st.session_state.selected_category,
            max_results=12
        )
        recommendation_engine.add_videos(st.session_state.trending_videos)
        
        # Update recommendations if we have a current video
        if st.session_state.current_video:
            st.session_state.recommendations = recommendation_engine.get_hybrid_recommendations(
                user_id=st.session_state.user_id,
                video_id=st.session_state.current_video['id'],
                category_id=st.session_state.selected_category,
                limit=8
            )
        
        # Clear search results when category changes
        st.session_state.search_results = []

def main():
    """Main application function"""
    # Check if API key is configured
    if not st.session_state.api_key_confirmed:
        render_api_key_form()
        return
    
    # Initialize API and recommendation engine
    youtube_api, recommendation_engine = load_initial_data()
    
    # Header
    st.markdown("# 🎬 YouTube Recommendation Engine")
    
    # Search bar and categories
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("Search for videos", key="search_query", on_change=handle_search)
    with col2:
        if st.button("Clear History"):
            clear_history()
    
    # Render category pills
    render_categories()
    
    # Current video (if any)
    if st.session_state.current_video:
        render_video_player()
    
    # Search results
    if st.session_state.search_results:
        render_video_grid(
            st.session_state.search_results, 
            "Search Results",
            "No results found. Try a different search term."
        )
    
    # Recommendations (if current video is set)
    if st.session_state.current_video and st.session_state.recommendations:
        render_video_grid(
            st.session_state.recommendations,
            "Recommended for You",
            "No recommendations available. Try watching more videos."
        )
    
    # Trending videos
    render_video_grid(
        st.session_state.trending_videos,
        "Trending Videos",
        "No trending videos available. Check back later."
    )
    
    # Watch history
    if st.session_state.history:
        st.markdown("## Watch History")
        history_videos = [h['video'] for h in st.session_state.history]
        render_video_grid(
            history_videos,
            "Watch History",
            "No watch history yet. Start watching videos!"
        )
    
    # Footer
    st.markdown("""
    <div style="margin-top: 2rem; text-align: center; color: #666;">
        <p>YouTube Recommendation Engine | Created with ❤️ using Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()