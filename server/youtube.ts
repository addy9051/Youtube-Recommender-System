import { Video, Category } from "@shared/schema";

// Interface for YouTube API service
export interface IYoutubeApi {
  searchVideos(query: string, categoryId?: string, maxResults?: number): Promise<Video[]>;
  getRecommendedVideos(videoId?: string, categoryId?: string, maxResults?: number): Promise<Video[]>;
  getTrendingVideos(categoryId?: string, maxResults?: number): Promise<Video[]>;
  getVideoDetails(videoId: string): Promise<Video | undefined>;
  getCategories(): Promise<Category[]>;
}

// Implementation of YouTube API service
class YoutubeApiService implements IYoutubeApi {
  private apiKey: string;
  
  constructor() {
    // Get API key from environment variables
    this.apiKey = process.env.YOUTUBE_API_KEY || process.env.VITE_YOUTUBE_API_KEY || "";
    
    if (!this.apiKey) {
      console.warn("YouTube API key not found. Using mock data instead.");
    }
  }
  
  // Helper to make API requests
  private async makeRequest(url: string): Promise<any> {
    try {
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`YouTube API error: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error("YouTube API request failed:", error);
      throw error;
    }
  }
  
  // Convert YouTube API response to our Video type
  private convertYoutubeVideo(item: any): Video {
    return {
      id: item.id.videoId || item.id,
      title: item.snippet.title,
      description: item.snippet.description,
      channelId: item.snippet.channelId,
      channelTitle: item.snippet.channelTitle,
      publishedAt: item.snippet.publishedAt,
      thumbnail: item.snippet.thumbnails.high?.url || item.snippet.thumbnails.default?.url,
      duration: item.contentDetails?.duration,
      viewCount: item.statistics?.viewCount,
      likeCount: item.statistics?.likeCount,
      commentCount: item.statistics?.commentCount,
      tags: item.snippet.tags || [],
      categoryId: item.snippet.categoryId
    };
  }
  
  // Search for videos
  async searchVideos(query: string, categoryId?: string, maxResults: number = 10): Promise<Video[]> {
    if (!this.apiKey) return this.getMockVideos(maxResults);
    
    try {
      let url = `https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q=${encodeURIComponent(query)}&maxResults=${maxResults}&key=${this.apiKey}`;
      
      if (categoryId && categoryId !== "all") {
        url += `&videoCategoryId=${categoryId}`;
      }
      
      const data = await this.makeRequest(url);
      
      // Extract video IDs to get more details
      const videoIds = data.items.map((item: any) => item.id.videoId).join(',');
      
      // Get more detailed info about the videos
      const detailsUrl = `https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=${videoIds}&key=${this.apiKey}`;
      const detailsData = await this.makeRequest(detailsUrl);
      
      // Map the detailed response to our Video type
      return detailsData.items.map(this.convertYoutubeVideo);
    } catch (error) {
      console.error("Error searching videos:", error);
      return this.getMockVideos(maxResults);
    }
  }
  
  // Get recommended videos
  async getRecommendedVideos(videoId?: string, categoryId?: string, maxResults: number = 8): Promise<Video[]> {
    if (!this.apiKey) return this.getMockVideos(maxResults);
    
    try {
      if (videoId) {
        // Use the relatedToVideoId parameter to get related videos
        const url = `https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId=${videoId}&type=video&maxResults=${maxResults}&key=${this.apiKey}`;
        const data = await this.makeRequest(url);
        
        // Extract video IDs to get more details
        const videoIds = data.items.map((item: any) => item.id.videoId).join(',');
        
        // Get more detailed info about the videos
        const detailsUrl = `https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=${videoIds}&key=${this.apiKey}`;
        const detailsData = await this.makeRequest(detailsUrl);
        
        return detailsData.items.map(this.convertYoutubeVideo);
      } else {
        // If no videoId provided, get popular videos by category
        return this.getTrendingVideos(categoryId, maxResults);
      }
    } catch (error) {
      console.error("Error getting recommended videos:", error);
      return this.getMockVideos(maxResults);
    }
  }
  
  // Get trending videos
  async getTrendingVideos(categoryId?: string, maxResults: number = 10): Promise<Video[]> {
    if (!this.apiKey) return this.getMockVideos(maxResults);
    
    try {
      let url = `https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&chart=mostPopular&maxResults=${maxResults}&key=${this.apiKey}`;
      
      if (categoryId && categoryId !== "all") {
        url += `&videoCategoryId=${categoryId}`;
      }
      
      const data = await this.makeRequest(url);
      return data.items.map(this.convertYoutubeVideo);
    } catch (error) {
      console.error("Error getting trending videos:", error);
      return this.getMockVideos(maxResults);
    }
  }
  
  // Get details for a specific video
  async getVideoDetails(videoId: string): Promise<Video | undefined> {
    if (!this.apiKey) return this.getMockVideos(1)[0];
    
    try {
      const url = `https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=${videoId}&key=${this.apiKey}`;
      const data = await this.makeRequest(url);
      
      if (data.items && data.items.length > 0) {
        return this.convertYoutubeVideo(data.items[0]);
      }
      
      return undefined;
    } catch (error) {
      console.error("Error getting video details:", error);
      return this.getMockVideos(1)[0];
    }
  }
  
  // Get video categories
  async getCategories(): Promise<Category[]> {
    if (!this.apiKey) {
      return [
        { id: "10", title: "Music" },
        { id: "20", title: "Gaming" },
        { id: "25", title: "News" },
        { id: "17", title: "Sports" },
        { id: "27", title: "Education" },
        { id: "26", title: "How-to & Style" },
        { id: "28", title: "Science & Technology" }
      ];
    }
    
    try {
      const url = `https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode=US&key=${this.apiKey}`;
      const data = await this.makeRequest(url);
      
      return data.items.map((item: any) => ({
        id: item.id,
        title: item.snippet.title
      }));
    } catch (error) {
      console.error("Error getting categories:", error);
      
      // Return default categories on error
      return [
        { id: "10", title: "Music" },
        { id: "20", title: "Gaming" },
        { id: "25", title: "News" },
        { id: "17", title: "Sports" },
        { id: "27", title: "Education" },
        { id: "26", title: "How-to & Style" },
        { id: "28", title: "Science & Technology" }
      ];
    }
  }
  
  // Get mock videos for testing/fallback
  private getMockVideos(count: number): Video[] {
    const mockVideos: Video[] = [
      {
        id: "dQw4w9WgXcQ",
        title: "Rick Astley - Never Gonna Give You Up (Official Music Video)",
        description: "The official music video for 'Never Gonna Give You Up' by Rick Astley",
        channelId: "UCuAXFkgsw1L7xaCfnd5JJOw",
        channelTitle: "Rick Astley",
        publishedAt: "2009-10-25T06:57:33Z",
        thumbnail: "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        duration: "PT3M33S",
        viewCount: "1234567890",
        likeCount: "15000000",
        commentCount: "2000000",
        tags: ["Rick Astley", "Never Gonna Give You Up", "Music"],
        categoryId: "10"
      },
      {
        id: "xC-c7E5PK0Y",
        title: "YouTube API Tutorial for Beginners (2023)",
        description: "Learn how to use the YouTube API in this comprehensive tutorial",
        channelId: "UC8butISFwT-Wl7EV0hUK0BQ",
        channelTitle: "WebDev Simplified",
        publishedAt: "2023-08-15T14:00:00Z",
        thumbnail: "https://i.ytimg.com/vi/xC-c7E5PK0Y/maxresdefault.jpg",
        duration: "PT15M22S",
        viewCount: "105000",
        likeCount: "8500",
        commentCount: "350",
        tags: ["YouTube API", "Tutorial", "Web Development"],
        categoryId: "28"
      },
      {
        id: "k5E2AVpwsko",
        title: "How Recommendation Algorithms Work: Behind the Scenes",
        description: "Dive deep into how recommendation algorithms work and how they determine what content to show you",
        channelId: "UC2UXDak6o7rBm23k3Vv5dww",
        channelTitle: "Data Science Pro",
        publishedAt: "2023-05-10T08:30:00Z",
        thumbnail: "https://i.ytimg.com/vi/k5E2AVpwsko/maxresdefault.jpg",
        duration: "PT22M17S",
        viewCount: "1200000",
        likeCount: "85000",
        commentCount: "4200",
        tags: ["Algorithms", "Recommendations", "Machine Learning"],
        categoryId: "28"
      },
      {
        id: "JL7QUG6lHjY",
        title: "Content-Based Filtering vs. Collaborative Filtering Explained",
        description: "Learn the differences between content-based and collaborative filtering recommendation systems",
        channelId: "UC2UXDak6o7rBm23k3Vv5dww",
        channelTitle: "ML Mastery",
        publishedAt: "2023-03-20T10:15:00Z",
        thumbnail: "https://i.ytimg.com/vi/JL7QUG6lHjY/maxresdefault.jpg",
        duration: "PT18M05S",
        viewCount: "352000",
        likeCount: "28500",
        commentCount: "1200",
        tags: ["Machine Learning", "Recommendation Systems", "Data Science"],
        categoryId: "28"
      }
    ];
    
    return mockVideos.slice(0, count);
  }
}

export const youtubeApi: IYoutubeApi = new YoutubeApiService();
