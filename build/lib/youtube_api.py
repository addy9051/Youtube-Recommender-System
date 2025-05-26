import os
import json
import random
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import time

class YouTubeAPI:
    def __init__(self):
        """Initialize the YouTube API client"""
        self.api_key = os.environ.get("YOUTUBE_API_KEY")
        self.youtube = None
        self.init_api()
        self.categories = None

    def init_api(self):
        """Initialize the YouTube API client"""
        if self.api_key:
            try:
                self.youtube = build("youtube", "v3", developerKey=self.api_key)
                print("YouTube API initialized successfully")
            except Exception as e:
                print(f"Error initializing YouTube API: {e}")
                self.youtube = None
        else:
            print("No YouTube API key found. Using mock data.")
            self.youtube = None

    def search_videos(self, query, category_id=None, max_results=10):
        """Search for videos based on a query and optional category"""
        if not self.youtube:
            print("Using mock data for search")
            return self.get_mock_videos(max_results)

        try:
            search_params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "fields": "items(id,snippet)",
            }
            
            if category_id:
                search_params["videoCategoryId"] = category_id
                
            search_response = self.youtube.search().list(**search_params).execute()
            
            video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
            
            if not video_ids:
                return []
            
            videos_response = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(video_ids)
            ).execute()
            
            return [self._convert_youtube_video(item) for item in videos_response.get("items", [])]
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            return self.get_mock_videos(max_results)
        except Exception as e:
            print(f"An error occurred: {e}")
            return self.get_mock_videos(max_results)

    def get_trending_videos(self, category_id=None, max_results=10):
        """Get trending videos, optionally filtered by category"""
        if not self.youtube:
            print("Using mock data for trending")
            return self.get_mock_videos(max_results)

        try:
            videos_params = {
                "part": "snippet,contentDetails,statistics",
                "chart": "mostPopular",
                "regionCode": "US",
                "maxResults": max_results
            }
            
            if category_id:
                videos_params["videoCategoryId"] = category_id
                
            videos_response = self.youtube.videos().list(**videos_params).execute()
            
            return [self._convert_youtube_video(item) for item in videos_response.get("items", [])]
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            return self.get_mock_videos(max_results)
        except Exception as e:
            print(f"An error occurred: {e}")
            return self.get_mock_videos(max_results)

    def get_video_details(self, video_id):
        """Get detailed information about a specific video"""
        if not self.youtube:
            print("Using mock data for video details")
            mock_videos = self.get_mock_videos(20)
            for video in mock_videos:
                if video["id"] == video_id:
                    return video
            return mock_videos[0] if mock_videos else None

        try:
            video_response = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
            ).execute()
            
            items = video_response.get("items", [])
            if items:
                return self._convert_youtube_video(items[0])
            return None
        except Exception as e:
            print(f"Error getting video details: {e}")
            return None

    def get_categories(self):
        """Get available video categories"""
        if self.categories is not None:
            return self.categories
            
        if not self.youtube:
            self.categories = self._get_mock_categories()
            return self.categories

        try:
            categories_response = self.youtube.videoCategories().list(
                part="snippet",
                regionCode="US"
            ).execute()
            
            self.categories = [
                {"id": item["id"], "title": item["snippet"]["title"]}
                for item in categories_response.get("items", [])
                if item["snippet"]["assignable"]
            ]
            return self.categories
        except Exception as e:
            print(f"Error getting categories: {e}")
            self.categories = self._get_mock_categories()
            return self.categories

    def _convert_youtube_video(self, item):
        """Convert YouTube API response to our standardized video format"""
        video_id = item["id"]
        snippet = item["snippet"]
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})
        
        # Handle potential missing values
        view_count = int(statistics.get("viewCount", 0))
        like_count = int(statistics.get("likeCount", 0))
        comment_count = int(statistics.get("commentCount", 0))
        
        return {
            "id": video_id,
            "title": snippet.get("title", "Untitled Video"),
            "description": snippet.get("description", ""),
            "publishedAt": snippet.get("publishedAt", ""),
            "channelId": snippet.get("channelId", ""),
            "channelTitle": snippet.get("channelTitle", "Unknown Channel"),
            "thumbnails": snippet.get("thumbnails", {
                "default": {"url": "https://via.placeholder.com/120x90"},
                "medium": {"url": "https://via.placeholder.com/320x180"},
                "high": {"url": "https://via.placeholder.com/480x360"}
            }),
            "categoryId": snippet.get("categoryId", ""),
            "tags": snippet.get("tags", []),
            "duration": content_details.get("duration", "PT0M0S"),
            "viewCount": view_count,
            "likeCount": like_count,
            "commentCount": comment_count,
            "score": None  # Will be used for recommendation scores
        }

    def get_mock_videos(self, count=10):
        """Generate mock videos for testing or when API is unavailable"""
        mock_videos = []
        categories = self._get_mock_categories()
        
        channels = [
            {"id": "UC1", "title": "Tech Reviews"},
            {"id": "UC2", "title": "Gaming Central"},
            {"id": "UC3", "title": "Cooking Masters"},
            {"id": "UC4", "title": "Science Explained"},
            {"id": "UC5", "title": "Travel & Adventure"},
            {"id": "UC6", "title": "Music Station"},
            {"id": "UC7", "title": "Fitness Channel"},
            {"id": "UC8", "title": "DIY Projects"}
        ]
        
        titles = [
            "Ultimate Guide to Python Programming 2025",
            "Top 10 Smartphones of the Year",
            "Easy Recipe for Beginners: Pasta Carbonara",
            "How to Build Muscle Fast - Complete Workout",
            "Exploring the Hidden Beaches of Thailand",
            "Machine Learning Explained in 10 Minutes",
            "Review: The Latest Gaming Console",
            "DIY Home Decoration Ideas",
            "Understanding Quantum Physics",
            "Top Travel Destinations for 2025",
            "The History of Rock Music",
            "5 Exercises for Better Posture",
            "Building a Web App from Scratch",
            "Healthy Breakfast Ideas for Busy People",
            "Guitar Tutorial for Beginners",
            "The Science of Sleep",
            "Photography Tips and Tricks",
            "How to Invest in Stocks for Beginners",
            "Virtual Reality: The Future of Gaming",
            "Sustainable Living Guide"
        ]
        
        for i in range(count):
            # Ensure unique video IDs even if function is called multiple times
            video_id = f"vid{int(time.time())}{i}"
            
            # Pick a random category and channel
            category = random.choice(categories)
            channel = random.choice(channels)
            
            # Randomize statistics
            view_count = random.randint(1000, 10000000)
            like_count = int(view_count * random.uniform(0.01, 0.1))
            comment_count = int(view_count * random.uniform(0.001, 0.01))
            
            # Generate a random publication date (within the last year)
            days_ago = random.randint(1, 365)
            published_date = (datetime.now() - timedelta(days=days_ago)).isoformat() + "Z"
            
            # Generate random duration (1 to 30 minutes)
            minutes = random.randint(1, 30)
            seconds = random.randint(0, 59)
            duration = f"PT{minutes}M{seconds}S"
            
            # Pick a random title or generate one with the category
            if random.random() < 0.7:
                title = random.choice(titles)
            else:
                title = f"Amazing {category['title']} Video You Must Watch"
            
            # Generate tags based on title words
            words = title.replace(":", "").replace("-", "").split()
            tags = [word for word in words if len(word) > 3 and word.lower() not in ["from", "with", "that", "this", "your", "for", "and", "the"]]
            
            # Create a mock description
            description = f"This is an amazing video about {title.lower()}. "
            description += f"Created by {channel['title']} to help you learn and enjoy {category['title']}."
            
            mock_video = {
                "id": video_id,
                "title": title,
                "description": description,
                "publishedAt": published_date,
                "channelId": channel["id"],
                "channelTitle": channel["title"],
                "thumbnails": {
                    "default": {"url": f"https://picsum.photos/seed/{video_id}/120/90"},
                    "medium": {"url": f"https://picsum.photos/seed/{video_id}/320/180"},
                    "high": {"url": f"https://picsum.photos/seed/{video_id}/480/360"}
                },
                "categoryId": category["id"],
                "tags": tags[:5],  # Limit to 5 tags
                "duration": duration,
                "viewCount": view_count,
                "likeCount": like_count,
                "commentCount": comment_count,
                "score": None
            }
            
            mock_videos.append(mock_video)
            
        return mock_videos

    def _get_mock_categories(self):
        """Return mock video categories when the API is unavailable"""
        return [
            {"id": "1", "title": "Film & Animation"},
            {"id": "2", "title": "Autos & Vehicles"},
            {"id": "10", "title": "Music"},
            {"id": "15", "title": "Pets & Animals"},
            {"id": "17", "title": "Sports"},
            {"id": "18", "title": "Short Movies"},
            {"id": "19", "title": "Travel & Events"},
            {"id": "20", "title": "Gaming"},
            {"id": "21", "title": "Videoblogging"},
            {"id": "22", "title": "People & Blogs"},
            {"id": "23", "title": "Comedy"},
            {"id": "24", "title": "Entertainment"},
            {"id": "25", "title": "News & Politics"},
            {"id": "26", "title": "Howto & Style"},
            {"id": "27", "title": "Education"},
            {"id": "28", "title": "Science & Technology"},
            {"id": "29", "title": "Nonprofits & Activism"}
        ]