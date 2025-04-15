import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import random
from datetime import datetime
import pandas as pd

class RecommendationEngine:
    def __init__(self):
        """Initialize the recommendation engine"""
        # Store all videos for content-based filtering
        self.videos = {}
        
        # Store watch history for collaborative filtering
        # Format: {user_id: [{video_id, timestamp, watched_percentage}]}
        self.watch_history = {}
        
        # Content vectors for similarity comparison
        self.content_vectors = None
        self.video_ids = []
        self.tfidf_matrix = None
        
        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )

    def add_videos(self, videos_list):
        """Add videos to the recommendation engine"""
        if not videos_list:
            return
            
        # Add videos to our collection
        for video in videos_list:
            self.videos[video["id"]] = video
            
        # Update content vectors when new videos are added
        self._update_content_vectors()
        
        print(f"Added {len(videos_list)} videos to recommendation engine. Total: {len(self.videos)}")

    def add_to_history(self, user_id, video_id, timestamp=None, watched_percentage=0):
        """Add a video to a user's watch history"""
        if not timestamp:
            timestamp = datetime.now().isoformat()
            
        if user_id not in self.watch_history:
            self.watch_history[user_id] = []
            
        # Check if the video exists in our collection
        if video_id not in self.videos:
            print(f"Warning: Video {video_id} not found in video collection")
            return
            
        # Add to watch history
        history_item = {
            "video_id": video_id,
            "timestamp": timestamp,
            "watched_percentage": watched_percentage
        }
        
        # Remove previous entries of the same video for this user
        self.watch_history[user_id] = [
            item for item in self.watch_history[user_id] 
            if item["video_id"] != video_id
        ]
        
        # Add the new history item
        self.watch_history[user_id].append(history_item)
        
        print(f"Added video {video_id} to user {user_id}'s history")

    def get_user_history(self, user_id, limit=20):
        """Get a user's watch history"""
        if user_id not in self.watch_history:
            return []
            
        # Sort by timestamp (most recent first)
        sorted_history = sorted(
            self.watch_history[user_id],
            key=lambda x: x["timestamp"],
            reverse=True
        )
        
        # Get the full video objects
        result = []
        for item in sorted_history[:limit]:
            video_id = item["video_id"]
            if video_id in self.videos:
                video = self.videos[video_id].copy()
                video["watched_percentage"] = item["watched_percentage"]
                result.append(video)
                
        return result

    def clear_history(self, user_id=None):
        """Clear watch history for a user or all users"""
        if user_id:
            if user_id in self.watch_history:
                self.watch_history[user_id] = []
                print(f"Cleared history for user {user_id}")
        else:
            self.watch_history = {}
            print("Cleared all user history")

    def _update_content_vectors(self):
        """Update content vectors for similarity calculations"""
        if not self.videos:
            return
            
        # Create content text for each video
        video_ids = []
        content_texts = []
        
        for video_id, video in self.videos.items():
            # Combine title, description, tags, and channel into a single text
            text_elements = [
                video.get("title", ""),
                video.get("description", ""),
                video.get("channelTitle", ""),
                # Add category name if available
                video.get("categoryId", ""),
            ]
            
            # Add tags (if available)
            tags = video.get("tags", [])
            if tags:
                text_elements.extend(tags)
                
            # Join all text elements with spaces
            content_text = " ".join([str(elem) for elem in text_elements if elem])
            
            video_ids.append(video_id)
            content_texts.append(content_text)
            
        # Update stored video IDs
        self.video_ids = video_ids
        
        # Create TF-IDF matrix
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(content_texts)
            print(f"Updated content vectors for {len(video_ids)} videos")
        except Exception as e:
            print(f"Error creating content vectors: {e}")
            self.tfidf_matrix = None

    def calculate_similarity(self, video_a, video_b):
        """Calculate similarity score between two videos"""
        # Basic content-based similarity using text features
        # Combine title, channel, category and tags
        features_a = [
            video_a.get("title", ""),
            video_a.get("channelTitle", ""),
            video_a.get("categoryId", ""),
            " ".join(video_a.get("tags", []))
        ]
        
        features_b = [
            video_b.get("title", ""),
            video_b.get("channelTitle", ""),
            video_b.get("categoryId", ""),
            " ".join(video_b.get("tags", []))
        ]
        
        # Count matching features
        score = 0
        
        # Exact matches
        if video_a.get("channelTitle") == video_b.get("channelTitle"):
            score += 0.5  # Same channel is a strong signal
            
        if video_a.get("categoryId") == video_b.get("categoryId"):
            score += 0.3  # Same category is a medium signal
            
        # Tags overlap
        tags_a = set(video_a.get("tags", []))
        tags_b = set(video_b.get("tags", []))
        
        if tags_a and tags_b:
            jaccard = len(tags_a.intersection(tags_b)) / len(tags_a.union(tags_b))
            score += jaccard * 0.2
            
        return min(score, 1.0)  # Cap at 1.0

    def get_content_based_recommendations(self, source_video_id, limit=8, category_id=None):
        """Get recommendations based on content similarity to a source video"""
        if source_video_id not in self.videos:
            print(f"Video {source_video_id} not found")
            return []
            
        if not self.tfidf_matrix is not None and len(self.video_ids) != self.tfidf_matrix.shape[0]:
            self._update_content_vectors()
            
        source_video = self.videos[source_video_id]
        recommendations = []
        
        # Method 1: Use TF-IDF similarity if available
        if self.tfidf_matrix is not None:
            try:
                # Get index of the source video
                source_index = self.video_ids.index(source_video_id)
                
                # Calculate similarity scores
                similarity_scores = cosine_similarity(
                    self.tfidf_matrix[source_index], 
                    self.tfidf_matrix
                ).flatten()
                
                # Get indices of top similar videos
                similar_indices = similarity_scores.argsort()[:-limit-1:-1]
                
                # Filter out the source video itself
                similar_indices = [idx for idx in similar_indices 
                                  if self.video_ids[idx] != source_video_id]
                
                # Filter by category if specified
                if category_id:
                    filtered_videos = []
                    for idx in similar_indices:
                        video_id = self.video_ids[idx]
                        video = self.videos[video_id]
                        if video.get("categoryId") == category_id:
                            video_copy = video.copy()
                            video_copy["score"] = float(similarity_scores[idx])
                            filtered_videos.append(video_copy)
                    recommendations = filtered_videos[:limit]
                else:
                    # Get videos and add similarity score
                    for idx in similar_indices[:limit]:
                        video_id = self.video_ids[idx]
                        video = self.videos[video_id].copy()
                        video["score"] = float(similarity_scores[idx])
                        recommendations.append(video)
                        
                return recommendations
            except Exception as e:
                print(f"Error in TF-IDF similarity: {e}")
                # Fall back to manual similarity
        
        # Method 2: Manual similarity calculation (fallback)
        # Calculate similarity for each video
        for video_id, video in self.videos.items():
            # Skip the source video
            if video_id == source_video_id:
                continue
                
            # Filter by category if specified
            if category_id and video.get("categoryId") != category_id:
                continue
                
            # Calculate similarity
            similarity = self.calculate_similarity(source_video, video)
            
            # Add to recommendations if there's some similarity
            if similarity > 0:
                video_copy = video.copy()
                video_copy["score"] = similarity
                recommendations.append(video_copy)
        
        # Sort by similarity score (descending)
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations[:limit]

    def get_collaborative_recommendations(self, user_id, limit=8, category_id=None):
        """Get recommendations based on collaborative filtering"""
        if user_id not in self.watch_history or not self.watch_history[user_id]:
            return []
            
        # Get user's watched videos
        user_videos = set(item["video_id"] for item in self.watch_history[user_id])
        
        # Find other users who have watched similar videos
        similar_users = []
        for other_id, history in self.watch_history.items():
            if other_id == user_id:
                continue
                
            other_videos = set(item["video_id"] for item in history)
            
            # Calculate Jaccard similarity (overlap of watched videos)
            if user_videos and other_videos:
                overlap = len(user_videos.intersection(other_videos))
                similarity = overlap / len(user_videos.union(other_videos))
                
                if similarity > 0:
                    similar_users.append({
                        "user_id": other_id,
                        "similarity": similarity
                    })
        
        # Sort by similarity
        similar_users.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Get recommendations from similar users
        candidate_videos = {}
        
        for similar_user in similar_users[:5]:  # Consider top 5 similar users
            other_id = similar_user["user_id"]
            user_similarity = similar_user["similarity"]
            
            for history_item in self.watch_history[other_id]:
                video_id = history_item["video_id"]
                
                # Skip videos the user has already watched
                if video_id in user_videos:
                    continue
                    
                # Skip videos not in our collection
                if video_id not in self.videos:
                    continue
                    
                # Filter by category if specified
                if category_id and self.videos[video_id].get("categoryId") != category_id:
                    continue
                
                # Add the video to candidates with weighted score
                watched_pct = history_item.get("watched_percentage", 0)
                candidate_score = user_similarity * (0.5 + 0.5 * watched_pct / 100)
                
                if video_id in candidate_videos:
                    candidate_videos[video_id] += candidate_score
                else:
                    candidate_videos[video_id] = candidate_score
        
        # Create recommendation list with scores
        recommendations = []
        for video_id, score in candidate_videos.items():
            video = self.videos[video_id].copy()
            video["score"] = float(score)
            recommendations.append(video)
            
        # Sort by score (descending)
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations[:limit]

    def get_hybrid_recommendations(self, user_id=None, video_id=None, category_id=None, limit=8):
        """Get hybrid recommendations using both content-based and collaborative filtering"""
        content_recs = []
        collab_recs = []
        
        # Get content-based recommendations if video_id is provided
        if video_id and video_id in self.videos:
            content_recs = self.get_content_based_recommendations(
                video_id, 
                limit=limit,
                category_id=category_id
            )
        
        # Get collaborative recommendations if user_id is provided
        if user_id and user_id in self.watch_history:
            collab_recs = self.get_collaborative_recommendations(
                user_id,
                limit=limit,
                category_id=category_id
            )
            
        # If we have both types of recommendations
        if content_recs and collab_recs:
            # Combine both recommendation sets
            all_recs = {}
            
            # Add content-based recommendations
            for video in content_recs:
                all_recs[video["id"]] = {
                    "video": video,
                    "content_score": video["score"],
                    "collab_score": 0
                }
                
            # Add/update with collaborative recommendations
            for video in collab_recs:
                if video["id"] in all_recs:
                    all_recs[video["id"]]["collab_score"] = video["score"]
                else:
                    all_recs[video["id"]] = {
                        "video": video,
                        "content_score": 0,
                        "collab_score": video["score"]
                    }
            
            # Calculate hybrid scores (60% content, 40% collaborative)
            hybrid_recs = []
            for rec_data in all_recs.values():
                video = rec_data["video"].copy()
                hybrid_score = 0.6 * rec_data["content_score"] + 0.4 * rec_data["collab_score"]
                video["score"] = float(hybrid_score)
                hybrid_recs.append(video)
                
            # Sort by hybrid score
            hybrid_recs.sort(key=lambda x: x["score"], reverse=True)
            return hybrid_recs[:limit]
            
        # If we only have one type, return that
        elif content_recs:
            return content_recs
        elif collab_recs:
            return collab_recs
        
        # If no recommendations, return trending videos
        return self.get_trending_videos(category_id, limit)

    def get_trending_videos(self, category_id=None, limit=10):
        """Get trending videos based on view counts"""
        if not self.videos:
            return []
            
        # Create a list of videos
        trending_videos = []
        for video_id, video in self.videos.items():
            # Filter by category if specified
            if category_id and video.get("categoryId") != category_id:
                continue
                
            # Add to trending list
            trending_videos.append(video.copy())
            
        # Sort by view count (descending)
        trending_videos.sort(key=lambda x: x.get("viewCount", 0), reverse=True)
        
        # Apply a scoring based on views + recent publishing
        for video in trending_videos:
            # Get view count (default to 0)
            view_count = video.get("viewCount", 0)
            
            # Calculate a trending score
            # Score is primarily based on view count, scaled logarithmically
            log_views = np.log1p(view_count) if view_count > 0 else 0
            video["score"] = float(log_views / 20)  # Normalize to 0-1 range
            
        return trending_videos[:limit]