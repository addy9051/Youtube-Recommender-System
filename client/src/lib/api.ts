import { apiRequest } from "./queryClient";
import { Video, VideoSearchRequest, VideoRecommendationRequest } from "@shared/schema";

// Function to search videos
export async function searchVideos(params: VideoSearchRequest): Promise<Video[]> {
  const queryParams = new URLSearchParams();
  queryParams.append("query", params.query);
  
  if (params.maxResults) {
    queryParams.append("maxResults", params.maxResults.toString());
  }
  
  if (params.categoryId) {
    queryParams.append("categoryId", params.categoryId);
  }
  
  const response = await apiRequest(
    "GET", 
    `/api/videos/search?${queryParams.toString()}`,
    undefined
  );
  
  return response.json();
}

// Function to get video recommendations
export async function getRecommendations(params: VideoRecommendationRequest): Promise<Video[]> {
  const queryParams = new URLSearchParams();
  
  if (params.videoId) {
    queryParams.append("videoId", params.videoId);
  }
  
  if (params.userId) {
    queryParams.append("userId", params.userId.toString());
  }
  
  if (params.maxResults) {
    queryParams.append("maxResults", params.maxResults.toString());
  }
  
  if (params.categoryId) {
    queryParams.append("categoryId", params.categoryId);
  }
  
  const response = await apiRequest(
    "GET", 
    `/api/videos/recommendations?${queryParams.toString()}`,
    undefined
  );
  
  return response.json();
}

// Function to get trending videos
export async function getTrendingVideos(categoryId?: string): Promise<Video[]> {
  const queryParams = new URLSearchParams();
  
  if (categoryId && categoryId !== "all") {
    queryParams.append("categoryId", categoryId);
  }
  
  const response = await apiRequest(
    "GET", 
    `/api/videos/trending?${queryParams.toString()}`,
    undefined
  );
  
  return response.json();
}

// Function to add video to watch history
export async function addToHistory(videoId: string): Promise<void> {
  await apiRequest("POST", "/api/history", { videoId });
}

// Function to clear watch history
export async function clearHistory(): Promise<void> {
  await apiRequest("DELETE", "/api/history", undefined);
}

// Function to get video details
export async function getVideoDetails(videoId: string): Promise<Video> {
  const response = await apiRequest("GET", `/api/videos/${videoId}`, undefined);
  return response.json();
}
