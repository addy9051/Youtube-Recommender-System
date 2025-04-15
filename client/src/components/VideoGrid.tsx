import { Video, WatchHistory } from "@shared/schema";
import VideoCard from "./VideoCard";
import { Skeleton } from "@/components/ui/skeleton";

interface VideoGridProps {
  videos: Video[] | undefined;
  watchHistory?: WatchHistory[];
  isLoading: boolean;
  error: Error | null;
  onRetry: () => void;
  showProgress?: boolean;
  emptyMessage?: string;
}

export default function VideoGrid({ 
  videos, 
  watchHistory,
  isLoading, 
  error, 
  onRetry,
  showProgress = false,
  emptyMessage = "No videos available"
}: VideoGridProps) {
  // Generate skeletons for loading state
  const renderSkeletons = () => {
    return Array.from({ length: 4 }).map((_, i) => (
      <div key={i} className="bg-white rounded-lg shadow-sm overflow-hidden animate-pulse">
        <div className="bg-gray-300 w-full h-48"></div>
        <div className="p-3">
          <div className="bg-gray-300 h-5 w-3/4 mb-2 rounded"></div>
          <div className="bg-gray-300 h-4 w-1/2 mb-2 rounded"></div>
          <div className="bg-gray-300 h-4 w-1/4 rounded"></div>
        </div>
      </div>
    ));
  };

  // Error state
  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
        <strong className="font-bold">Error!</strong>
        <span className="block sm:inline ml-2">
          {error.message || "Unable to fetch videos. Please try again later."}
        </span>
        <button 
          onClick={onRetry} 
          className="underline ml-2"
        >
          Retry
        </button>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {renderSkeletons()}
      </div>
    );
  }

  // Empty state
  if (!videos || videos.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8 text-center">
        <span className="material-icons text-4xl text-[#606060] mb-2">videocam_off</span>
        <h3 className="text-lg font-medium mb-2">{emptyMessage}</h3>
        <p className="text-[#606060] text-sm">Try searching for something else</p>
      </div>
    );
  }

  // Find watch data for a video
  const getWatchData = (videoId: string) => {
    if (!watchHistory) return undefined;
    return watchHistory.find(item => item.videoId === videoId);
  };

  // Normal state with videos
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {videos.map((video) => (
        <VideoCard 
          key={video.id} 
          video={video} 
          watchData={getWatchData(video.id)}
          showProgress={showProgress}
        />
      ))}
    </div>
  );
}
