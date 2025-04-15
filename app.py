import streamlit as st
import pandas as pd
import numpy as np
import re
import time
import json
from datetime import datetime
import random
import plotly.express as px
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import our modules
from youtube_api import YouTubeAPI
from recommendation_engine import RecommendationEngine

# Initialize global instances
youtube_api = YouTubeAPI()
recommendation_engine = RecommendationEngine()

# Set page config
st.set_page_config(
    page_title="YouTube Recommendation Engine",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f9f9f9;
    }
    .video-card {
        border-radius: 10px;
        overflow: hidden;
        transition: transform 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        background-color: white;
        height: 100%;
    }
    .video-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .video-title {
        font-weight: 600;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    .video-meta {
        font-size: 0.8rem;
        color: #606060;
    }
    .channel-name {
        font-weight: 500;
        color: #030303;
    }
    .category-pill {
        background-color: #f0f0f0;
        border-radius: 20px;
        padding: 5px 15px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.9rem;
    }
    .category-pill:hover, .category-pill.active {
        background-color: #ff0000;
        color: white;
    }
    .sidebar-content {
        padding: 20px 10px;
    }
    .progress-bar-container {
        height: 4px;
        background-color: #e0e0e0;
        border-radius: 2px;
        overflow: hidden;
        margin-top: 5px;
    }
    .progress-bar {
        height: 100%;
        background-color: #ff0000;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 2px solid #f0f0f0;
    }
    .search-container {
        margin-bottom: 20px;
    }
    .header-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .current-video-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .video-player-container {
        position: relative;
        padding-bottom: 56.25%; /* 16:9 Aspect Ratio */
        height: 0;
        overflow: hidden;
    }
    .video-player-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border-radius: 8px;
    }
    .insights-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

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
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None
if 'categories' not in st.session_state:
    st.session_state.categories = []


def format_count(count):
    """Format large numbers with K, M, B suffixes"""
    if count is None:
        return "0"
    
    count = int(count)
    if count < 1000:
        return str(count)
    elif count < 1000000:
        return f"{count/1000:.1f}K".replace(".0K", "K")
    elif count < 1000000000:
        return f"{count/1000000:.1f}M".replace(".0M", "M")
    else:
        return f"{count/1000000000:.1f}B".replace(".0B", "B")


def format_duration(duration):
    """Format YouTube duration (PT1H2M3S) into readable format (1:02:03)"""
    if not duration or duration == "PT0M0S":
        return "0:00"
    
    # Extract hours, minutes, seconds
    hours_match = re.search(r'(\d+)H', duration)
    minutes_match = re.search(r'(\d+)M', duration)
    seconds_match = re.search(r'(\d+)S', duration)
    
    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    seconds = int(seconds_match.group(1)) if seconds_match else 0
    
    # Format based on duration
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def render_video_card(video, show_score=False, score=None, show_progress=False, progress=0):
    """Render a video card with thumbnail and metadata"""
    score_display = ""
    if show_score and score is not None:
        score_display = f"<div style='position:absolute;top:5px;right:5px;background:rgba(0,0,0,0.7);color:white;padding:2px 6px;border-radius:3px;font-size:0.8rem;'>{score:.2f}</div>"
    
    progress_bar = ""
    if show_progress and progress > 0:
        progress_bar = f"""
        <div class="progress-bar-container">
            <div class="progress-bar" style="width: {progress}%;"></div>
        </div>
        """
    
    duration = format_duration(video.get("duration", ""))
    duration_display = f"<div style='position:absolute;bottom:8px;right:8px;background:rgba(0,0,0,0.7);color:white;padding:2px 6px;border-radius:3px;font-size:0.8rem;'>{duration}</div>"
    
    html = f"""
    <div class="video-card">
        <div style="position:relative;">
            <img src="{video['thumbnails']['medium']['url']}" style="width:100%;height:180px;object-fit:cover;" alt="{video['title']}">
            {duration_display}
            {score_display}
            {progress_bar}
        </div>
        <div style="padding:10px;">
            <div class="video-title">{video['title']}</div>
            <div class="video-meta">
                <div class="channel-name">{video['channelTitle']}</div>
                <div>{format_count(video['viewCount'])} views</div>
            </div>
        </div>
    </div>
    """
    return html


def load_initial_data():
    """Load initial data for the application"""
    # Get categories
    categories = youtube_api.get_categories()
    st.session_state.categories = categories
    
    # Get trending videos
    trending_videos = youtube_api.get_trending_videos(max_results=20)
    
    # Add videos to recommendation engine
    recommendation_engine.add_videos(trending_videos)
    
    # Store recommendations
    st.session_state.recommendations = trending_videos
    
    return trending_videos


def handle_search():
    """Handle search functionality"""
    search_query = st.session_state.search_query if 'search_query' in st.session_state else ""
    
    if search_query:
        category_id = st.session_state.selected_category if st.session_state.selected_category else None
        
        search_results = youtube_api.search_videos(
            query=search_query,
            category_id=category_id,
            max_results=20
        )
        
        # Add videos to recommendation engine
        recommendation_engine.add_videos(search_results)
        
        # Store search results
        st.session_state.search_results = search_results
        
        # Store search query
        st.session_state.last_search_query = search_query


def handle_video_selection(video_id):
    """Handle video selection and update recommendations"""
    # Get video details
    video = youtube_api.get_video_details(video_id)
    
    if video:
        # Set as current video
        st.session_state.current_video = video
        
        # Add to watch history
        user_id = st.session_state.user_id
        recommendation_engine.add_to_history(user_id, video_id)
        
        # Update history in session
        st.session_state.history = recommendation_engine.get_user_history(user_id)
        
        # Get recommendations
        recommendations = recommendation_engine.get_hybrid_recommendations(
            user_id=user_id,
            video_id=video_id,
            category_id=st.session_state.selected_category,
            limit=20
        )
        
        # Store recommendations
        st.session_state.recommendations = recommendations


def clear_history():
    """Clear user watch history"""
    user_id = st.session_state.user_id
    recommendation_engine.clear_history(user_id)
    st.session_state.history = []
    st.success("Watch history cleared")


def render_api_key_form():
    """Render form for user to input YouTube API key"""
    st.markdown("### YouTube API Key Required")
    st.write("To access YouTube data, please provide your YouTube API key.")
    
    api_key = st.text_input(
        "Enter your YouTube API key",
        type="password",
        help="You can get this from the Google Cloud Console"
    )
    
    if st.button("Save API Key"):
        if api_key:
            # Set environment variable
            os.environ["YOUTUBE_API_KEY"] = api_key
            
            # Reinitialize YouTube API
            youtube_api.api_key = api_key
            youtube_api.init_api()
            
            st.success("API key saved successfully!")
            st.experimental_rerun()
        else:
            st.error("Please enter a valid API key")


def render_header():
    """Render the application header"""
    st.markdown(
        """
        <div class="header-container">
            <h1 style="text-align:center;color:#FF0000;margin-bottom:10px;font-weight:800;">
                YouTube Recommendation Engine
            </h1>
            <p style="text-align:center;color:#606060;margin-bottom:20px;">
                Discover videos tailored to your interests with advanced recommendation algorithms
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_categories():
    """Render category selection pills"""
    categories = st.session_state.categories
    
    if not categories:
        return
    
    st.markdown("### Video Categories")
    
    # Create a grid of 4 columns
    cols = st.columns(4)
    
    # Add an "All Categories" option
    if st.session_state.selected_category is None:
        class_name = "category-pill active"
    else:
        class_name = "category-pill"
        
    cols[0].markdown(
        f"""
        <div class="{class_name}" onclick="window.location.href='?category=all'">
            All Categories
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Add each category
    for i, category in enumerate(categories[:11], 1):  # Limit to 11 categories + All
        col_idx = i % 4
        
        if st.session_state.selected_category == category["id"]:
            class_name = "category-pill active"
        else:
            class_name = "category-pill"
            
        cols[col_idx].markdown(
            f"""
            <div class="{class_name}" onclick="window.location.href='?category={category['id']}'">
                {category['title']}
            </div>
            """,
            unsafe_allow_html=True
        )
        
    # Add button functionality
    query_params = st.experimental_get_query_params()
    if "category" in query_params:
        category_param = query_params["category"][0]
        
        if category_param == "all":
            st.session_state.selected_category = None
        else:
            st.session_state.selected_category = category_param
            
        # Clear query params to avoid stale state
        st.experimental_set_query_params()
        st.experimental_rerun()


def render_current_video():
    """Render the currently selected video"""
    video = st.session_state.current_video
    
    if not video:
        return
    
    st.markdown(
        """
        <div class="section-title">
            Currently Watching
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Create container for video
    st.markdown(
        """
        <div class="current-video-container">
            <div class="video-player-container">
                <iframe
                    src="https://www.youtube.com/embed/{video_id}"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen>
                </iframe>
            </div>
            <h2 style="margin-top:15px;font-weight:600;">{title}</h2>
            <div style="display:flex;justify-content:space-between;margin:10px 0;">
                <div style="font-weight:500;color:#030303;">{channel}</div>
                <div style="color:#606060;">{views} views</div>
            </div>
            <p style="color:#606060;margin-top:10px;">{description}</p>
        </div>
        """.format(
            video_id=video["id"],
            title=video["title"],
            channel=video["channelTitle"],
            views=format_count(video["viewCount"]),
            description=video["description"][:300] + "..." if len(video["description"]) > 300 else video["description"]
        ),
        unsafe_allow_html=True
    )


def render_video_grid(videos, title, empty_message="No videos available", show_progress=False):
    """Render a grid of video cards"""
    if not videos:
        st.markdown(f"<p style='text-align:center;color:#606060;'>{empty_message}</p>", unsafe_allow_html=True)
        return
    
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
    
    # Create a 3-column grid
    cols = st.columns(3)
    
    # Iterate through videos
    for i, video in enumerate(videos):
        col_idx = i % 3
        
        # Get additional attributes
        progress = video.get("watched_percentage", 0) if show_progress else 0
        score = video.get("score", None)
        
        # Render the video card
        video_card_html = render_video_card(
            video, 
            show_score=(score is not None),
            score=score,
            show_progress=show_progress,
            progress=progress
        )
        
        # Add click handling
        cols[col_idx].markdown(
            f"""
            <a href="?video={video['id']}" style="text-decoration:none;color:inherit;">
                {video_card_html}
            </a>
            """,
            unsafe_allow_html=True
        )
    
    # Add button functionality for video selection
    query_params = st.experimental_get_query_params()
    if "video" in query_params:
        video_id = query_params["video"][0]
        handle_video_selection(video_id)
        
        # Clear query params to avoid stale state
        st.experimental_set_query_params()
        st.experimental_rerun()


def render_recommendations():
    """Render recommendation sections"""
    # Render current video recommendations
    if st.session_state.current_video:
        render_video_grid(
            st.session_state.recommendations,
            "Recommended for You",
            "No recommendations available"
        )
    
    # Render history if available
    if st.session_state.history:
        render_video_grid(
            st.session_state.history,
            "Watch History",
            "No watch history",
            show_progress=True
        )
        
        # Add clear history button
        if st.button("Clear Watch History"):
            clear_history()


def render_search_results():
    """Render search results"""
    if not st.session_state.search_results:
        return
        
    search_query = st.session_state.last_search_query if 'last_search_query' in st.session_state else ""
    
    render_video_grid(
        st.session_state.search_results,
        f"Search Results for '{search_query}'",
        "No results found"
    )


def render_insights():
    """Render insights and analytics based on user watch history"""
    history = st.session_state.history
    
    if not history or len(history) < 3:
        return
    
    st.markdown("<div class='section-title'>Your Viewing Insights</div>", unsafe_allow_html=True)
    
    # Create insights container
    st.markdown("<div class='insights-container'>", unsafe_allow_html=True)
    
    # 1. Category distribution
    categories = {}
    for video in history:
        category_id = video.get("categoryId", "Unknown")
        
        if category_id != "Unknown":
            # Find category name
            category_name = "Other"
            for cat in st.session_state.categories:
                if cat["id"] == category_id:
                    category_name = cat["title"]
                    break
        else:
            category_name = "Other"
            
        if category_name in categories:
            categories[category_name] += 1
        else:
            categories[category_name] = 1
    
    # Create dataframe and plot
    if categories:
        df = pd.DataFrame({
            "Category": categories.keys(),
            "Videos Watched": categories.values()
        })
        
        fig = px.pie(
            df,
            values="Videos Watched",
            names="Category",
            title="Categories You Watch",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 2. Channel distribution
    channels = {}
    for video in history:
        channel = video.get("channelTitle", "Unknown Channel")
        if channel in channels:
            channels[channel] += 1
        else:
            channels[channel] = 1
    
    # Sort and get top 5
    top_channels = dict(sorted(channels.items(), key=lambda item: item[1], reverse=True)[:5])
    
    if top_channels:
        df = pd.DataFrame({
            "Channel": top_channels.keys(),
            "Videos Watched": top_channels.values()
        })
        
        fig = px.bar(
            df,
            x="Channel",
            y="Videos Watched",
            title="Your Top Channels",
            color="Videos Watched",
            color_continuous_scale="Reds"
        )
        fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main application function"""
    # Check if YouTube API key is available
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        render_api_key_form()
        return
    
    # Render application header
    render_header()
    
    # Load initial data if needed
    if not st.session_state.recommendations:
        with st.spinner("Loading videos..."):
            load_initial_data()
    
    # Render category selection
    render_categories()
    
    # Create search bar
    st.markdown("<div class='search-container'>", unsafe_allow_html=True)
    search_col1, search_col2 = st.columns([4, 1])
    with search_col1:
        st.text_input("Search for videos", key="search_query")
    with search_col2:
        if st.button("Search"):
            with st.spinner("Searching..."):
                handle_search()
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Render current video if selected
    render_current_video()
    
    # Render search results if available
    render_search_results()
    
    # Render recommendations and history
    render_recommendations()
    
    # Render insights
    render_insights()
    
    # Add some space at the bottom
    st.markdown("<br><br>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()