import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import datetime
import random

class RecommendationEngine:
    def __init__(self):
        """Initialize the recommendation engine"""
        self.videos = {}  # video_id -> video_data
        self.user_history = {}  # user_id -> list of (video_id, timestamp, watched_percentage)
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        self.content_vectors = None
        self.video_ids = []
    
    def add_videos(self, videos_list):
        """Add videos to the recommendation engine"""
        for video in videos_list:
            self.videos[video['id']] = video
        
        # Update content vectors if we have videos
        if self.videos:
            self._update_content_vectors()
    
    def add_to_history(self, user_id, video_id, timestamp, watched_percentage=0):
        """Add a video to a user's watch history"""
        if user_id not in self.user_history:
            self.user_history[user_id] = []
        
        # Check if video_id exists in our videos database
        if video_id not in self.videos:
            print(f"Warning: Adding unknown video {video_id} to history")
        
        # Add to history, update if already exists
        history_entry = (video_id, timestamp, watched_percentage)
        
        # Remove existing entry for this video if it exists
        self.user_history[user_id] = [
            entry for entry in self.user_history[user_id] 
            if entry[0] != video_id
        ]
        
        # Add new entry
        self.user_history[user_id].append(history_entry)
        
        # Sort by timestamp, most recent first
        self.user_history[user_id].sort(key=lambda x: x[1], reverse=True)
    
    def get_user_history(self, user_id, limit=20):
        """Get a user's watch history"""
        if user_id not in self.user_history:
            return []
        
        # Return history entries with video data
        history = []
        for video_id, timestamp, watched_percentage in self.user_history[user_id][:limit]:
            if video_id in self.videos:
                history.append({
                    'video': self.videos[video_id],
                    'timestamp': timestamp,
                    'watched_percentage': watched_percentage
                })
        
        return history
    
    def clear_history(self, user_id=None):
        """Clear watch history for a user or all users"""
        if user_id:
            if user_id in self.user_history:
                self.user_history[user_id] = []
        else:
            self.user_history = {}
    
    def _update_content_vectors(self):
        """Update content vectors for similarity calculations"""
        if not self.videos:
            return
        
        self.video_ids = list(self.videos.keys())
        documents = []
        
        for video_id in self.video_ids:
            video = self.videos[video_id]
            # Combine title, description, tags, and channel for content-based filtering
            content = f"{video['title']} {video['description']} {' '.join(video.get('tags', []))} {video['channel_title']}"
            documents.append(content)
        
        try:
            # Use TF-IDF to create content vectors
            self.content_vectors = self.tfidf_vectorizer.fit_transform(documents)
        except Exception as e:
            print(f"Error creating content vectors: {e}")
            self.content_vectors = None
    
    def calculate_similarity(self, video_a, video_b):
        """Calculate similarity score between two videos"""
        if not video_a or not video_b:
            return 0.0
        
        # Category similarity (exact match = higher score)
        category_similarity = 1.0 if video_a.get('category_id') == video_b.get('category_id') else 0.0
        
        # Channel similarity
        channel_similarity = 1.0 if video_a.get('channel_id') == video_b.get('channel_id') else 0.0
        
        # Tag similarity - calculate Jaccard similarity between tag sets
        tags_a = set(video_a.get('tags', []))
        tags_b = set(video_b.get('tags', []))
        tag_similarity = 0.0
        if tags_a and tags_b:
            intersection = len(tags_a.intersection(tags_b))
            union = len(tags_a.union(tags_b))
            tag_similarity = intersection / union if union > 0 else 0.0
        
        # Calculate weights - prioritize channel and category
        weights = {
            'category': 0.3,
            'channel': 0.4,
            'tags': 0.3
        }
        
        # Weighted similarity
        similarity = (
            weights['category'] * category_similarity +
            weights['channel'] * channel_similarity +
            weights['tags'] * tag_similarity
        )
        
        return similarity
    
    def get_content_based_recommendations(self, source_video_id, limit=8, category_id=None):
        """Get recommendations based on content similarity to a source video"""
        if not self.videos or source_video_id not in self.videos:
            return []
        
        source_video = self.videos[source_video_id]
        candidates = []
        
        # If we have content vectors, use them for similarity
        if self.content_vectors is not None and len(self.video_ids) > 1:
            try:
                source_idx = self.video_ids.index(source_video_id)
                similarities = cosine_similarity(
                    self.content_vectors[source_idx:source_idx+1], 
                    self.content_vectors
                )[0]
                
                # Create (video_id, similarity) pairs
                video_similarities = list(zip(self.video_ids, similarities))
                
                # Sort by similarity descending
                video_similarities.sort(key=lambda x: x[1], reverse=True)
                
                # Filter by category if needed
                if category_id:
                    video_similarities = [
                        (vid, sim) for vid, sim in video_similarities 
                        if self.videos[vid].get('category_id') == category_id
                    ]
                
                # Skip the source video itself
                candidates = [
                    self.videos[vid] for vid, sim in video_similarities 
                    if vid != source_video_id
                ][:limit]
                
            except Exception as e:
                print(f"Error in content-based recommendation: {e}")
                candidates = []
        
        # Fall back to manual similarity calculation if needed
        if not candidates:
            all_videos = list(self.videos.values())
            
            # Calculate similarity for each video
            video_similarities = [
                (video, self.calculate_similarity(source_video, video))
                for video in all_videos
                if video['id'] != source_video_id
            ]
            
            # Filter by category if needed
            if category_id:
                video_similarities = [
                    (video, sim) for video, sim in video_similarities 
                    if video.get('category_id') == category_id
                ]
            
            # Sort by similarity score (descending)
            video_similarities.sort(key=lambda x: x[1], reverse=True)
            
            candidates = [video for video, sim in video_similarities[:limit]]
        
        return candidates
    
    def get_collaborative_recommendations(self, user_id, limit=8, category_id=None):
        """Get recommendations based on collaborative filtering"""
        if user_id not in self.user_history or not self.user_history[user_id]:
            # User has no history, return empty list
            return []
        
        # Get videos this user has watched
        user_videos = set(entry[0] for entry in self.user_history[user_id])
        
        # Candidate videos the user hasn't watched yet
        candidates = []
        
        # Simple collaborative approach - find users with similar viewing history
        for other_user_id, other_history in self.user_history.items():
            if other_user_id == user_id:
                continue
            
            # Get videos the other user has watched
            other_videos = set(entry[0] for entry in other_history)
            
            # Calculate intersection (videos both users have watched)
            common_videos = user_videos.intersection(other_videos)
            
            # If users have common videos, recommend other user's videos
            if common_videos:
                # Calculate similarity between users based on common videos
                similarity = len(common_videos) / max(len(user_videos), len(other_videos))
                
                # Add videos this user hasn't watched yet
                new_videos = other_videos - user_videos
                
                for video_id in new_videos:
                    if video_id in self.videos:
                        video = self.videos[video_id]
                        
                        # Filter by category if needed
                        if category_id and video.get('category_id') != category_id:
                            continue
                        
                        candidates.append((video, similarity))
        
        # Sort by similarity score (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Return top recommendations
        return [video for video, _ in candidates[:limit]]
    
    def get_hybrid_recommendations(self, user_id=None, video_id=None, category_id=None, limit=8):
        """Get hybrid recommendations using both content-based and collaborative filtering"""
        if not self.videos:
            return []
        
        content_recommendations = []
        collaborative_recommendations = []
        
        # If we have a source video, get content-based recommendations
        if video_id and video_id in self.videos:
            content_recommendations = self.get_content_based_recommendations(
                video_id, limit=limit, category_id=category_id
            )
        
        # If we have a user, get collaborative recommendations
        if user_id and user_id in self.user_history:
            collaborative_recommendations = self.get_collaborative_recommendations(
                user_id, limit=limit, category_id=category_id
            )
        
        # Combine recommendations (avoid duplicates)
        seen_ids = set()
        hybrid_recommendations = []
        
        # Add content-based recommendations first (2/3 of the limit)
        content_limit = min(len(content_recommendations), int(limit * 2/3))
        for video in content_recommendations[:content_limit]:
            if video['id'] not in seen_ids:
                hybrid_recommendations.append(video)
                seen_ids.add(video['id'])
        
        # Then add collaborative recommendations
        for video in collaborative_recommendations:
            if video['id'] not in seen_ids and len(hybrid_recommendations) < limit:
                hybrid_recommendations.append(video)
                seen_ids.add(video['id'])
        
        # If we still need more recommendations, add trending or similar videos
        if len(hybrid_recommendations) < limit:
            all_videos = list(self.videos.values())
            
            # Filter by category if needed
            if category_id:
                all_videos = [v for v in all_videos if v.get('category_id') == category_id]
            
            # Sort by view count (descending) as a proxy for popularity
            all_videos.sort(key=lambda x: x.get('view_count', 0), reverse=True)
            
            # Add popular videos not already in recommendations
            for video in all_videos:
                if video['id'] not in seen_ids and len(hybrid_recommendations) < limit:
                    hybrid_recommendations.append(video)
                    seen_ids.add(video['id'])
        
        return hybrid_recommendations
    
    def get_trending_videos(self, category_id=None, limit=10):
        """Get trending videos based on view counts"""
        if not self.videos:
            return []
        
        # Get all videos
        all_videos = list(self.videos.values())
        
        # Filter by category if needed
        if category_id:
            all_videos = [video for video in all_videos if video.get('category_id') == category_id]
        
        # Sort by view count (descending)
        all_videos.sort(key=lambda x: x.get('view_count', 0), reverse=True)
        
        # Return top trending videos
        return all_videos[:limit]