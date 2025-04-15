import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { Video } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";
import { queryClient } from "@/lib/queryClient";

interface NotificationType {
  show: boolean;
  message: string;
  icon: string;
}

interface AppContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
  currentVideo: Video | null;
  selectVideo: (video: Video) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  currentCategory: string;
  setCurrentCategory: (category: string) => void;
  notification: NotificationType;
  showNotification: (message: string, icon?: string) => void;
  hideNotification: () => void;
  searchVideos: (videos: Video[]) => void;
  clearHistory: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [currentVideo, setCurrentVideo] = useState<Video | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentCategory, setCurrentCategory] = useState("all");
  const [notification, setNotification] = useState<NotificationType>({
    show: false,
    message: "",
    icon: "check_circle",
  });

  const toggleTheme = useCallback(() => {
    setIsDarkMode((prev) => !prev);
    const newMode = !isDarkMode ? 'dark' : 'light';
    showNotification(`${newMode.charAt(0).toUpperCase() + newMode.slice(1)} mode enabled`, 
      newMode === 'dark' ? 'dark_mode' : 'light_mode');
    
    // Apply dark mode class to body
    if (!isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const selectVideo = useCallback(async (video: Video) => {
    setCurrentVideo(video);
    
    // Record this video in watch history
    try {
      await apiRequest("POST", "/api/history", { videoId: video.id });
      // Invalidate history cache
      queryClient.invalidateQueries({ queryKey: ['/api/history'] });
      
      // Scroll to top
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
      console.error("Failed to record watch history:", error);
    }
  }, []);

  const showNotification = useCallback((message: string, icon: string = "check_circle") => {
    setNotification({
      show: true,
      message,
      icon,
    });
  }, []);

  const hideNotification = useCallback(() => {
    setNotification((prev) => ({
      ...prev,
      show: false,
    }));
  }, []);

  const searchVideos = useCallback((videos: Video[]) => {
    // Update search results (handled in useVideos hook)
    queryClient.setQueryData(['/api/videos/search', searchQuery], videos);
  }, [searchQuery]);

  const clearHistory = useCallback(() => {
    queryClient.setQueryData(['/api/history'], []);
  }, []);

  const value = {
    isDarkMode,
    toggleTheme,
    currentVideo,
    selectVideo,
    searchQuery,
    setSearchQuery,
    currentCategory,
    setCurrentCategory,
    notification,
    showNotification,
    hideNotification,
    searchVideos,
    clearHistory,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useAppContext must be used within an AppProvider");
  }
  return context;
}
