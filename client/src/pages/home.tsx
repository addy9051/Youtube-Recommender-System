import { useEffect } from "react";
import Header from "@/components/Header";
import VideoPlayer from "@/components/VideoPlayer";
import VideoGrid from "@/components/VideoGrid";
import Footer from "@/components/Footer";
import Notification from "@/components/Notification";
import { useAppContext } from "@/context/AppContext";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useVideos } from "@/hooks/useVideos";

export default function Home() {
  const { 
    currentVideo, 
    currentCategory, 
    clearHistory, 
    showNotification 
  } = useAppContext();
  
  const { 
    forYouVideos, 
    trendingVideos, 
    historyVideos, 
    isLoading, 
    error, 
    refetchRecommendations 
  } = useVideos();

  const clearHistoryMutation = useMutation({
    mutationFn: async () => {
      await apiRequest("DELETE", "/api/history", undefined);
    },
    onSuccess: () => {
      clearHistory();
      showNotification("Watch history cleared", "delete");
    },
  });

  const handleClearHistory = () => {
    clearHistoryMutation.mutate();
  };

  const handleRefreshRecommendations = () => {
    refetchRecommendations();
    showNotification("Recommendations refreshed", "refresh");
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F9F9F9] text-[#030303] font-roboto">
      <Header />

      <main className="container mx-auto px-4 py-6 flex-grow">
        {currentVideo && <VideoPlayer />}

        {/* For You Section */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">For You</h2>
            <div 
              className="text-sm text-[#065FD4] cursor-pointer hover:underline"
              onClick={handleRefreshRecommendations}
            >
              Refresh
            </div>
          </div>
          
          <VideoGrid 
            videos={forYouVideos} 
            isLoading={isLoading} 
            error={error} 
            onRetry={refetchRecommendations}
            emptyMessage="No recommendations available"
          />
        </section>

        {/* Trending Section */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Trending</h2>
          </div>
          
          <VideoGrid 
            videos={trendingVideos} 
            isLoading={isLoading} 
            error={error} 
            onRetry={refetchRecommendations}
            emptyMessage="No trending videos available"
          />
        </section>

        {/* History Section */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Recently Watched</h2>
            <button 
              className="text-sm text-[#065FD4] hover:underline"
              onClick={handleClearHistory}
            >
              Clear History
            </button>
          </div>
          
          {historyVideos && historyVideos.length > 0 ? (
            <VideoGrid 
              videos={historyVideos} 
              isLoading={isLoading} 
              error={error}
              onRetry={refetchRecommendations}
              showProgress
            />
          ) : (
            <div className="bg-white rounded-lg shadow-sm p-8 text-center">
              <span className="material-icons text-4xl text-[#606060] mb-2">history</span>
              <h3 className="text-lg font-medium mb-2">No watch history yet</h3>
              <p className="text-[#606060] text-sm">Videos you watch will appear here</p>
            </div>
          )}
        </section>
      </main>

      <Footer />
      <Notification />
    </div>
  );
}
