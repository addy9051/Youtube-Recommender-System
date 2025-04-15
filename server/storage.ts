import { 
  users, type User, type InsertUser,
  videos, type Video, type InsertVideo,
  watchHistory, type WatchHistory, type InsertWatchHistory,
  Category
} from "@shared/schema";

// modify the interface with any CRUD methods
// you might need

export interface IStorage {
  // User methods
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  // Video methods
  getVideo(id: string): Promise<Video | undefined>;
  getVideos(ids: string[]): Promise<Video[]>;
  searchVideos(query: string, categoryId?: string, maxResults?: number): Promise<Video[]>;
  getTrendingVideos(categoryId?: string, maxResults?: number): Promise<Video[]>;
  getRecommendedVideos(videoId?: string, categoryId?: string, maxResults?: number): Promise<Video[]>;
  saveVideo(video: Video): Promise<Video>;
  
  // Watch history methods
  getWatchHistory(userId?: number, maxResults?: number): Promise<{videos: Video[], history: WatchHistory[]}>;
  addToWatchHistory(historyItem: InsertWatchHistory): Promise<WatchHistory>;
  clearWatchHistory(userId?: number): Promise<void>;
  
  // Categories
  getCategories(): Promise<Category[]>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private videos: Map<string, Video>;
  private history: WatchHistory[];
  private categories: Category[];
  
  currentUserId: number;
  currentHistoryId: number;

  constructor() {
    this.users = new Map();
    this.videos = new Map();
    this.history = [];
    this.categories = [
      { id: "10", title: "Music" },
      { id: "20", title: "Gaming" },
      { id: "25", title: "News" },
      { id: "17", title: "Sports" },
      { id: "27", title: "Education" },
      { id: "26", title: "How-to & Style" },
      { id: "28", title: "Science & Technology" }
    ];
    
    this.currentUserId = 1;
    this.currentHistoryId = 1;
    
    // Pre-populate with some demo videos
    this.initDemoVideos();
  }

  // Initialize with some demo videos
  private initDemoVideos() {
    const demoVideos: Video[] = [
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
      }
    ];
    
    // Add demo videos to storage
    for (const video of demoVideos) {
      this.videos.set(video.id, video);
    }
  }

  // User methods
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.currentUserId++;
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }
  
  // Video methods
  async getVideo(id: string): Promise<Video | undefined> {
    return this.videos.get(id);
  }
  
  async getVideos(ids: string[]): Promise<Video[]> {
    return ids
      .map(id => this.videos.get(id))
      .filter((video): video is Video => video !== undefined);
  }
  
  async searchVideos(query: string, categoryId?: string, maxResults: number = 10): Promise<Video[]> {
    const searchTerms = query.toLowerCase().split(' ');
    
    const results = Array.from(this.videos.values())
      .filter(video => {
        // Filter by category if provided
        if (categoryId && categoryId !== "all" && video.categoryId !== categoryId) {
          return false;
        }
        
        // Match by search terms
        const titleMatches = searchTerms.some(term => 
          video.title.toLowerCase().includes(term)
        );
        
        const descriptionMatches = video.description ? searchTerms.some(term => 
          video.description!.toLowerCase().includes(term)
        ) : false;
        
        const tagMatches = video.tags ? searchTerms.some(term => 
          video.tags!.some(tag => tag.toLowerCase().includes(term))
        ) : false;
        
        return titleMatches || descriptionMatches || tagMatches;
      })
      .slice(0, maxResults);
    
    return results;
  }
  
  async getTrendingVideos(categoryId?: string, maxResults: number = 10): Promise<Video[]> {
    // In a real app, we'd order by view count or recent popularity
    const videos = Array.from(this.videos.values())
      .filter(video => {
        if (categoryId && categoryId !== "all") {
          return video.categoryId === categoryId;
        }
        return true;
      })
      .sort((a, b) => {
        const viewsA = parseInt(a.viewCount || "0", 10);
        const viewsB = parseInt(b.viewCount || "0", 10);
        return viewsB - viewsA; // Sort by views, descending
      })
      .slice(0, maxResults);
    
    return videos;
  }
  
  async getRecommendedVideos(videoId?: string, categoryId?: string, maxResults: number = 8): Promise<Video[]> {
    // Content-based filtering implementation
    if (videoId) {
      const sourceVideo = this.videos.get(videoId);
      
      if (sourceVideo) {
        const recommendedVideos = Array.from(this.videos.values())
          .filter(video => video.id !== videoId) // Exclude the source video
          .map(video => {
            // Calculate a similarity score based on shared tags, category, and channel
            let score = 0;
            
            // Same category bonus
            if (video.categoryId === sourceVideo.categoryId) {
              score += 3;
            }
            
            // Same channel bonus
            if (video.channelId === sourceVideo.channelId) {
              score += 2;
            }
            
            // Tags similarity
            if (sourceVideo.tags && video.tags) {
              const sharedTags = sourceVideo.tags.filter(tag => 
                video.tags!.includes(tag)
              );
              score += sharedTags.length;
            }
            
            return { video, score };
          })
          .sort((a, b) => b.score - a.score) // Sort by similarity score, descending
          .slice(0, maxResults)
          .map(item => item.video);
        
        return recommendedVideos;
      }
    }
    
    // If no videoId provided or source video not found, return popular videos in category
    return this.getTrendingVideos(categoryId, maxResults);
  }
  
  async saveVideo(video: Video): Promise<Video> {
    this.videos.set(video.id, video);
    return video;
  }
  
  // Watch history methods
  async getWatchHistory(userId?: number, maxResults: number = 20): Promise<{videos: Video[], history: WatchHistory[]}> {
    // Filter by userId if provided
    const filteredHistory = userId 
      ? this.history.filter(item => item.userId === userId)
      : this.history;
    
    // Sort by most recently watched
    const sortedHistory = [...filteredHistory].sort(
      (a, b) => new Date(b.watchedAt).getTime() - new Date(a.watchedAt).getTime()
    ).slice(0, maxResults);
    
    // Get the videos for these history items
    const videoIds = sortedHistory.map(item => item.videoId);
    const videos = await this.getVideos(videoIds);
    
    // Ensure videos are in the same order as history items
    const orderedVideos = videoIds.map(id => 
      videos.find(video => video.id === id)
    ).filter((video): video is Video => video !== undefined);
    
    return { videos: orderedVideos, history: sortedHistory };
  }
  
  async addToWatchHistory(historyItem: InsertWatchHistory): Promise<WatchHistory> {
    const id = this.currentHistoryId++;
    const now = new Date();
    
    // Check if this video is already in history
    const existingIndex = this.history.findIndex(item => 
      item.videoId === historyItem.videoId && item.userId === historyItem.userId
    );
    
    if (existingIndex >= 0) {
      // Update existing history entry
      this.history[existingIndex] = {
        ...this.history[existingIndex],
        watchedAt: now,
        watchedPercentage: historyItem.watchedPercentage || this.history[existingIndex].watchedPercentage
      };
      return this.history[existingIndex];
    } else {
      // Create new history entry
      const newHistory: WatchHistory = {
        ...historyItem,
        id,
        watchedAt: now
      };
      
      this.history.push(newHistory);
      return newHistory;
    }
  }
  
  async clearWatchHistory(userId?: number): Promise<void> {
    if (userId) {
      this.history = this.history.filter(item => item.userId !== userId);
    } else {
      this.history = [];
    }
  }
  
  // Categories
  async getCategories(): Promise<Category[]> {
    return this.categories;
  }
}

export const storage = new MemStorage();
