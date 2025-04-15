import { useAppContext } from "@/context/AppContext";
import { Video, WatchHistory } from "@shared/schema";
import { formatDistanceToNow } from "date-fns";

interface VideoCardProps {
  video: Video;
  watchData?: WatchHistory;
  showProgress?: boolean;
}

export default function VideoCard({ video, watchData, showProgress = false }: VideoCardProps) {
  const { selectVideo } = useAppContext();

  // Format view count
  const formatViewCount = (count: string | undefined): string => {
    if (!count) return "0 views";
    const num = parseInt(count, 10);
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + "M views";
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + "K views";
    }
    return num.toString() + " views";
  };

  // Format published time
  const formatPublishedTime = (dateString: string | undefined): string => {
    if (!dateString) return "";
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch (e) {
      return dateString;
    }
  };

  // Format duration
  const formatDuration = (duration: string | undefined): string => {
    if (!duration) return "";
    // Simple formatting for ISO 8601 duration to MM:SS
    if (duration.startsWith("PT")) {
      const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
      if (match) {
        const hours = match[1] ? parseInt(match[1], 10) : 0;
        const minutes = match[2] ? parseInt(match[2], 10) : 0;
        const seconds = match[3] ? parseInt(match[3], 10) : 0;
        
        if (hours > 0) {
          return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
      }
    }
    return duration;
  };

  return (
    <div 
      className="bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-200 cursor-pointer" 
      onClick={() => selectVideo(video)}
    >
      <div className="relative">
        <div className="relative pt-[56.25%]">
          <img 
            src={video.thumbnail || `https://i.ytimg.com/vi/${video.id}/maxresdefault.jpg`}
            alt={video.title}
            className="absolute top-0 left-0 w-full h-full object-cover"
          />
          {video.duration && (
            <div className="absolute bottom-1 right-1 bg-black bg-opacity-80 text-white text-xs px-1 rounded">
              <span>{formatDuration(video.duration)}</span>
            </div>
          )}
        </div>
        
        {/* Progress bar for watched videos */}
        {showProgress && watchData && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200">
            <div 
              className="bg-red-600 h-full" 
              style={{ width: `${watchData.watchedPercentage || 0}%` }}
            ></div>
          </div>
        )}
      </div>
      
      <div className="p-3">
        <h3 className="font-medium text-base mb-1 line-clamp-2">{video.title}</h3>
        <div className="flex flex-col">
          <p className="text-[#606060] text-sm">{video.channelTitle}</p>
          <div className="flex items-center text-[#606060] text-xs mt-1">
            <span>{formatViewCount(video.viewCount)}</span>
            <span className="mx-1">•</span>
            <span>{formatPublishedTime(video.publishedAt)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
