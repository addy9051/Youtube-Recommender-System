import { Video } from "@shared/schema";

// Simple content-based filtering recommendation engine
export class RecommendationEngine {
  // Calculate similarity between two videos
  calculateSimilarity(videoA: Video, videoB: Video): number {
    let score = 0;
    
    // Same category bonus
    if (videoA.categoryId === videoB.categoryId) {
      score += 3;
    }
    
    // Same channel bonus
    if (videoA.channelId === videoB.channelId) {
      score += 2;
    }
    
    // Tags similarity
    if (videoA.tags && videoB.tags) {
      const sharedTags = videoA.tags.filter(tag => 
        videoB.tags!.includes(tag)
      );
      score += sharedTags.length;
    }
    
    // Title similarity (simple word matching)
    const wordsA = videoA.title.toLowerCase().split(/\s+/);
    const wordsB = videoB.title.toLowerCase().split(/\s+/);
    
    const sharedWords = wordsA.filter(word => 
      wordsB.includes(word) && word.length > 3 // Only count significant words
    );
    
    score += sharedWords.length * 0.5;
    
    return score;
  }
  
  // Get recommendations based on a source video
  getRecommendations(sourceVideo: Video, candidateVideos: Video[], limit: number = 8): Video[] {
    // Calculate similarity score for each candidate
    const scoredVideos = candidateVideos
      .filter(video => video.id !== sourceVideo.id) // Exclude source video
      .map(video => ({
        video,
        score: this.calculateSimilarity(sourceVideo, video)
      }))
      .sort((a, b) => b.score - a.score) // Sort by similarity score, descending
      .slice(0, limit)
      .map(item => item.video);
    
    return scoredVideos;
  }
  
  // Get recommendations based on user watch history
  // This implements a simple content-based filtering approach
  getRecommendationsFromHistory(
    watchedVideos: Video[], 
    candidateVideos: Video[], 
    limit: number = 8
  ): Video[] {
    // If no watch history, return popular videos
    if (watchedVideos.length === 0) {
      return candidateVideos.slice(0, limit);
    }
    
    // Calculate aggregated similarity scores for each candidate
    const scoredVideos = candidateVideos
      .filter(video => !watchedVideos.some(watched => watched.id === video.id)) // Exclude already watched
      .map(video => {
        let totalScore = 0;
        
        // Calculate similarity with each watched video
        watchedVideos.forEach(watched => {
          totalScore += this.calculateSimilarity(watched, video);
        });
        
        // Average score (optionally weighted by recency)
        const avgScore = totalScore / watchedVideos.length;
        
        return { video, score: avgScore };
      })
      .sort((a, b) => b.score - a.score) // Sort by average similarity score
      .slice(0, limit)
      .map(item => item.video);
    
    return scoredVideos;
  }
}

export const recommendationEngine = new RecommendationEngine();
