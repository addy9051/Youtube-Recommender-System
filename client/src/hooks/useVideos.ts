import { useQuery } from "@tanstack/react-query";
import { Video, WatchHistory } from "@shared/schema";
import { useAppContext } from "@/context/AppContext";

export function useVideos() {
  const { currentCategory, searchQuery } = useAppContext();

  // Fetch recommendations based on current category
  const { 
    data: forYouVideos,
    isLoading: isRecommendationsLoading,
    error: recommendationsError,
    refetch: refetchRecommendations
  } = useQuery<Video[]>({
    queryKey: ['/api/videos/recommendations', currentCategory],
    enabled: currentCategory !== undefined,
  });

  // Fetch trending videos
  const {
    data: trendingVideos,
    isLoading: isTrendingLoading,
    error: trendingError
  } = useQuery<Video[]>({
    queryKey: ['/api/videos/trending', currentCategory],
    enabled: currentCategory !== undefined,
  });

  // Fetch watch history
  const {
    data: historyVideos,
    isLoading: isHistoryLoading,
    error: historyError
  } = useQuery<Video[]>({
    queryKey: ['/api/history'],
  });

  // If there's a search query, fetch search results
  const {
    data: searchResults,
    isLoading: isSearchLoading,
    error: searchError
  } = useQuery<Video[]>({
    queryKey: ['/api/videos/search', searchQuery],
    enabled: searchQuery.length > 0,
  });

  // Determine which videos to show
  const videosToShow = searchQuery.length > 0 ? searchResults : forYouVideos;

  return {
    forYouVideos: videosToShow || [],
    trendingVideos: trendingVideos || [],
    historyVideos: historyVideos || [],
    isLoading: isRecommendationsLoading || isTrendingLoading || isHistoryLoading || isSearchLoading,
    error: recommendationsError || trendingError || historyError || searchError,
    refetchRecommendations
  };
}
