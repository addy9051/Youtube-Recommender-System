import os
import re
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import random
import datetime
import requests

# Load environment variables
load_dotenv()

class YouTubeAPI:
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.youtube = None
        self.init_api()
    
    def init_api(self):
        """Initialize the YouTube API client"""
        try:
            if self.api_key:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                print("YouTube API initialized successfully")
            else:
                print("No YouTube API key found. Using mock data.")
        except Exception as e:
            print(f"Error initializing YouTube API: {e}")
            self.youtube = None
    
    def search_videos(self, query, category_id=None, max_results=10):
        """Search for videos based on a query and optional category"""
        try:
            if not self.youtube:
                return self.get_mock_videos(count=max_results)
            
            search_params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'relevanceLanguage': 'en'
            }
            
            if category_id:
                search_params['videoCategoryId'] = category_id
            
            search_response = self.youtube.search().list(**search_params).execute()
            
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            # Get video details for the search results
            if video_ids:
                videos_response = self.youtube.videos().list(
                    part='snippet,contentDetails,statistics',
                    id=','.join(video_ids)
                ).execute()
                
                return [self._convert_youtube_video(item) for item in videos_response['items']]
            else:
                return []
                
        except HttpError as e:
            print(f"YouTube API search error: {e}")
            return self.get_mock_videos(count=max_results)
    
    def get_trending_videos(self, category_id=None, max_results=10):
        """Get trending videos, optionally filtered by category"""
        try:
            if not self.youtube:
                return self.get_mock_videos(count=max_results)
            
            videos_params = {
                'part': 'snippet,contentDetails,statistics',
                'chart': 'mostPopular',
                'maxResults': max_results,
                'regionCode': 'US'
            }
            
            if category_id:
                videos_params['videoCategoryId'] = category_id
                
            videos_response = self.youtube.videos().list(**videos_params).execute()
            
            return [self._convert_youtube_video(item) for item in videos_response['items']]
            
        except HttpError as e:
            print(f"YouTube API trending error: {e}")
            return self.get_mock_videos(count=max_results)
    
    def get_video_details(self, video_id):
        """Get detailed information about a specific video"""
        try:
            if not self.youtube:
                return self.get_mock_videos(count=1)[0]
            
            videos_response = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            ).execute()
            
            if videos_response['items']:
                return self._convert_youtube_video(videos_response['items'][0])
            else:
                return None
                
        except HttpError as e:
            print(f"YouTube API video details error: {e}")
            return self.get_mock_videos(count=1)[0]
    
    def get_categories(self):
        """Get available video categories"""
        try:
            if not self.youtube:
                return self._get_mock_categories()
            
            categories_response = self.youtube.videoCategories().list(
                part='snippet',
                regionCode='US'
            ).execute()
            
            return [
                {
                    'id': item['id'],
                    'title': item['snippet']['title']
                }
                for item in categories_response['items']
                if item['snippet']['assignable']  # Only return assignable categories
            ]
            
        except HttpError as e:
            print(f"YouTube API categories error: {e}")
            return self._get_mock_categories()
    
    def _convert_youtube_video(self, item):
        """Convert YouTube API response to our standardized video format"""
        # Extract video duration in ISO 8601 format (e.g. PT1H2M3S)
        duration = item.get('contentDetails', {}).get('duration', 'PT0M0S')
        
        # Extract statistics with fallbacks to 0
        statistics = item.get('statistics', {})
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        comment_count = int(statistics.get('commentCount', 0))
        
        # Get video publish date
        published_at = item.get('snippet', {}).get('publishedAt', '')
        
        # Get formatted thumbnail URL (highest quality available)
        thumbnails = item.get('snippet', {}).get('thumbnails', {})
        thumbnail_url = ''
        for quality in ['maxres', 'high', 'medium', 'default']:
            if quality in thumbnails:
                thumbnail_url = thumbnails[quality]['url']
                break
        
        # Return standardized video object
        return {
            'id': item['id'],
            'title': item.get('snippet', {}).get('title', 'Untitled Video'),
            'description': item.get('snippet', {}).get('description', ''),
            'thumbnail_url': thumbnail_url,
            'channel_id': item.get('snippet', {}).get('channelId', ''),
            'channel_title': item.get('snippet', {}).get('channelTitle', 'Unknown Channel'),
            'category_id': item.get('snippet', {}).get('categoryId', ''),
            'tags': item.get('snippet', {}).get('tags', []),
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'published_at': published_at
        }
    
    def get_mock_videos(self, count=10):
        """Generate mock videos for testing or when API is unavailable"""
        mock_videos = []
        categories = ['Music', 'Sports', 'Gaming', 'News', 'Education', 'Science & Technology', 'Entertainment']
        channels = ['TechChannel', 'MusicVibes', 'SportsCenter', 'GamingDaily', 'NewsNow', 'Learn101', 'ScienceExplained']
        
        for i in range(count):
            video_id = f"mock{i+1}{random.randint(10000, 99999)}"
            category_index = random.randint(0, len(categories) - 1)
            
            # Generate random duration between 1 minute and 1 hour
            minutes = random.randint(1, 60)
            seconds = random.randint(0, 59)
            if minutes >= 60:
                hours = minutes // 60
                minutes = minutes % 60
                duration = f"PT{hours}H{minutes}M{seconds}S"
            else:
                duration = f"PT{minutes}M{seconds}S"
            
            # Random date within last year
            days_ago = random.randint(1, 365)
            published_date = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).isoformat() + 'Z'
            
            # Generate random stats
            views = random.randint(100, 1000000)
            likes = int(views * random.uniform(0.01, 0.2))
            comments = int(views * random.uniform(0.001, 0.05))
            
            video = {
                'id': video_id,
                'title': f"Mock Video {i+1}: All About {categories[category_index]}",
                'description': f"This is a mock video about {categories[category_index].lower()} topics created for testing purposes.",
                'thumbnail_url': f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                'channel_id': f"channel{i+1}",
                'channel_title': channels[category_index],
                'category_id': str(category_index + 1),
                'tags': [categories[category_index], 'Mock', 'Testing'],
                'duration': duration,
                'view_count': views,
                'like_count': likes,
                'comment_count': comments,
                'published_at': published_date
            }
            mock_videos.append(video)
        
        return mock_videos
    
    def _get_mock_categories(self):
        """Return mock video categories when the API is unavailable"""
        return [
            {'id': '1', 'title': 'Film & Animation'},
            {'id': '2', 'title': 'Autos & Vehicles'},
            {'id': '10', 'title': 'Music'},
            {'id': '15', 'title': 'Pets & Animals'},
            {'id': '17', 'title': 'Sports'},
            {'id': '18', 'title': 'Short Movies'},
            {'id': '19', 'title': 'Travel & Events'},
            {'id': '20', 'title': 'Gaming'},
            {'id': '21', 'title': 'Videoblogging'},
            {'id': '22', 'title': 'People & Blogs'},
            {'id': '23', 'title': 'Comedy'},
            {'id': '24', 'title': 'Entertainment'},
            {'id': '25', 'title': 'News & Politics'},
            {'id': '26', 'title': 'Howto & Style'},
            {'id': '27', 'title': 'Education'},
            {'id': '28', 'title': 'Science & Technology'},
            {'id': '29', 'title': 'Nonprofits & Activism'}
        ]