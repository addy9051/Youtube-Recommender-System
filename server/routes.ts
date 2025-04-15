import type { Express, Request, Response } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { youtubeApi } from "./youtube";
import { 
  videoSearchRequestSchema, 
  videoRecommendationRequestSchema,
  insertWatchHistorySchema
} from "@shared/schema";
import { ZodError } from "zod";
import { fromZodError } from "zod-validation-error";

export async function registerRoutes(app: Express): Promise<Server> {
  // Create HTTP server
  const httpServer = createServer(app);

  // Error handler middleware
  const handleError = (err: any, res: Response) => {
    console.error("API Error:", err);
    
    if (err instanceof ZodError) {
      return res.status(400).json({ 
        message: fromZodError(err).message
      });
    }
    
    const status = err.status || 500;
    const message = err.message || "Internal Server Error";
    res.status(status).json({ message });
  };

  // Get video categories
  app.get("/api/categories", async (req: Request, res: Response) => {
    try {
      const categories = await storage.getCategories();
      res.json(categories);
    } catch (err) {
      handleError(err, res);
    }
  });

  // Search for videos
  app.get("/api/videos/search", async (req: Request, res: Response) => {
    try {
      const query = req.query.query as string;
      const maxResults = req.query.maxResults ? parseInt(req.query.maxResults as string, 10) : 10;
      const categoryId = req.query.categoryId as string | undefined;
      
      const validated = videoSearchRequestSchema.parse({
        query,
        maxResults,
        categoryId
      });
      
      // First check if we have videos matching the query in our storage
      let videos = await storage.searchVideos(
        validated.query, 
        validated.categoryId, 
        validated.maxResults
      );
      
      // If we don't have enough videos, fetch from YouTube API
      if (videos.length < validated.maxResults) {
        const youtubeVideos = await youtubeApi.searchVideos(
          validated.query, 
          validated.categoryId, 
          validated.maxResults - videos.length
        );
        
        // Save the new videos to storage
        for (const video of youtubeVideos) {
          await storage.saveVideo(video);
        }
        
        // Combine local and YouTube results, removing duplicates
        const existingIds = new Set(videos.map(v => v.id));
        const uniqueYoutubeVideos = youtubeVideos.filter(v => !existingIds.has(v.id));
        
        videos = [...videos, ...uniqueYoutubeVideos];
      }
      
      res.json(videos);
    } catch (err) {
      handleError(err, res);
    }
  });

  // Get video recommendations
  app.get("/api/videos/recommendations", async (req: Request, res: Response) => {
    try {
      const videoId = req.query.videoId as string | undefined;
      const userId = req.query.userId ? parseInt(req.query.userId as string, 10) : undefined;
      const maxResults = req.query.maxResults ? parseInt(req.query.maxResults as string, 10) : 8;
      const categoryId = req.query.categoryId as string | undefined;
      
      const validated = videoRecommendationRequestSchema.parse({
        videoId,
        userId,
        maxResults,
        categoryId
      });
      
      // Get recommendations based on content-based filtering
      let recommendations = await storage.getRecommendedVideos(
        validated.videoId,
        validated.categoryId,
        validated.maxResults
      );
      
      // If we don't have enough recommendations, fetch from YouTube API
      if (recommendations.length < validated.maxResults) {
        const youtubeRecommendations = await youtubeApi.getRecommendedVideos(
          validated.videoId,
          validated.categoryId,
          validated.maxResults - recommendations.length
        );
        
        // Save the new videos to storage
        for (const video of youtubeRecommendations) {
          await storage.saveVideo(video);
        }
        
        // Combine local and YouTube results, removing duplicates
        const existingIds = new Set(recommendations.map(v => v.id));
        const uniqueYoutubeVideos = youtubeRecommendations.filter(v => !existingIds.has(v.id));
        
        recommendations = [...recommendations, ...uniqueYoutubeVideos];
      }
      
      res.json(recommendations);
    } catch (err) {
      handleError(err, res);
    }
  });

  // Get trending videos
  app.get("/api/videos/trending", async (req: Request, res: Response) => {
    try {
      const categoryId = req.query.categoryId as string | undefined;
      const maxResults = req.query.maxResults ? parseInt(req.query.maxResults as string, 10) : 10;
      
      // Get trending videos from storage
      let trendingVideos = await storage.getTrendingVideos(categoryId, maxResults);
      
      // If we don't have enough trending videos, fetch from YouTube API
      if (trendingVideos.length < maxResults) {
        const youtubeTrending = await youtubeApi.getTrendingVideos(
          categoryId,
          maxResults - trendingVideos.length
        );
        
        // Save the new videos to storage
        for (const video of youtubeTrending) {
          await storage.saveVideo(video);
        }
        
        // Combine local and YouTube results, removing duplicates
        const existingIds = new Set(trendingVideos.map(v => v.id));
        const uniqueYoutubeVideos = youtubeTrending.filter(v => !existingIds.has(v.id));
        
        trendingVideos = [...trendingVideos, ...uniqueYoutubeVideos];
      }
      
      res.json(trendingVideos);
    } catch (err) {
      handleError(err, res);
    }
  });

  // Get specific video details
  app.get("/api/videos/:id", async (req: Request, res: Response) => {
    try {
      const videoId = req.params.id;
      
      // First check if we have this video in storage
      let video = await storage.getVideo(videoId);
      
      // If not found, fetch from YouTube API
      if (!video) {
        video = await youtubeApi.getVideoDetails(videoId);
        
        // Save to storage if found
        if (video) {
          await storage.saveVideo(video);
        }
      }
      
      if (!video) {
        return res.status(404).json({ message: "Video not found" });
      }
      
      res.json(video);
    } catch (err) {
      handleError(err, res);
    }
  });

  // Get watch history
  app.get("/api/history", async (req: Request, res: Response) => {
    try {
      const userId = req.query.userId ? parseInt(req.query.userId as string, 10) : undefined;
      const { videos } = await storage.getWatchHistory(userId);
      res.json(videos);
    } catch (err) {
      handleError(err, res);
    }
  });

  // Add to watch history
  app.post("/api/history", async (req: Request, res: Response) => {
    try {
      const { videoId, userId = 1, watchedPercentage = 0 } = req.body;
      
      const validated = insertWatchHistorySchema.parse({
        videoId,
        userId,
        watchedPercentage
      });
      
      // Ensure video exists
      let video = await storage.getVideo(validated.videoId);
      
      // If video doesn't exist, fetch it
      if (!video) {
        video = await youtubeApi.getVideoDetails(validated.videoId);
        
        if (video) {
          await storage.saveVideo(video);
        } else {
          return res.status(404).json({ message: "Video not found" });
        }
      }
      
      // Add to watch history
      const historyItem = await storage.addToWatchHistory(validated);
      res.json(historyItem);
    } catch (err) {
      handleError(err, res);
    }
  });

  // Clear watch history
  app.delete("/api/history", async (req: Request, res: Response) => {
    try {
      const userId = req.query.userId ? parseInt(req.query.userId as string, 10) : undefined;
      await storage.clearWatchHistory(userId);
      res.json({ message: "Watch history cleared" });
    } catch (err) {
      handleError(err, res);
    }
  });

  // Get search suggestions
  app.get("/api/suggestions", async (req: Request, res: Response) => {
    try {
      const query = req.query.query as string;
      
      if (!query || query.length < 3) {
        return res.json([]);
      }
      
      // Generate simple suggestions based on query
      // In a real app, this would use YouTube's suggestion API
      const suggestions = [
        `${query} tutorial`,
        `how to ${query}`,
        `${query} for beginners`,
        `best ${query} videos`
      ];
      
      res.json(suggestions);
    } catch (err) {
      handleError(err, res);
    }
  });

  return httpServer;
}
