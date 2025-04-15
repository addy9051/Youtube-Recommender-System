import { useAppContext } from "@/context/AppContext";
import { useQuery } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import ReactPlayer from "react-player/youtube";
import { Skeleton } from "@/components/ui/skeleton";

export default function VideoPlayer() {
  const { currentVideo } = useAppContext();

  if (!currentVideo) return null;

  // Fetch detailed video information
  const { data: videoDetails, isLoading } = useQuery({
    queryKey: [`/api/videos/${currentVideo.id}`],
    enabled: !!currentVideo.id,
  });

  const video = videoDetails || currentVideo;

  // Format numbers for display
  const formatCount = (count: string | undefined): string => {
    if (!count) return "0";
    const num = parseInt(count, 10);
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + "M";
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + "K";
    }
    return num.toString();
  };

  // Format published date
  const formatPublishedDate = (dateString: string | undefined): string => {
    if (!dateString) return "";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", { 
        year: "numeric", 
        month: "short", 
        day: "numeric" 
      });
    } catch (e) {
      return dateString;
    }
  };

  return (
    <div id="current-video-section" className="mb-8">
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="aspect-w-16 aspect-h-9 relative">
          <div className="w-full h-0 pb-[56.25%] relative bg-black">
            <ReactPlayer
              url={`https://www.youtube.com/watch?v=${video.id}`}
              width="100%"
              height="100%"
              style={{ position: 'absolute', top: 0, left: 0 }}
              controls
              playing
              config={{
                youtube: {
                  playerVars: { origin: window.location.origin }
                }
              }}
            />
          </div>
        </div>
        <div className="p-4">
          {isLoading ? (
            <>
              <Skeleton className="h-7 w-3/4 mb-2" />
              <Skeleton className="h-4 w-1/2 mb-4" />
              <div className="flex mb-4">
                <Skeleton className="h-10 w-10 rounded-full mr-3" />
                <div>
                  <Skeleton className="h-4 w-32 mb-1" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </div>
              <Skeleton className="h-24 w-full mb-2" />
            </>
          ) : (
            <>
              <h2 className="text-xl font-bold mb-2">{video.title}</h2>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="w-10 h-10 rounded-full bg-gray-300 mr-3 flex items-center justify-center text-gray-600 uppercase">
                    {video.channelTitle?.charAt(0) || "C"}
                  </div>
                  <div>
                    <p className="font-medium text-[#030303]">{video.channelTitle}</p>
                    <p className="text-sm text-[#606060]">
                      {videoDetails?.subscriberCount || ""}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <button className="flex items-center text-[#606060] hover:text-[#030303]">
                    <span className="material-icons mr-1">thumb_up</span>
                    <span>{formatCount(video.likeCount)}</span>
                  </button>
                  <button className="flex items-center text-[#606060] hover:text-[#030303]">
                    <span className="material-icons mr-1">thumb_down</span>
                  </button>
                  <button className="flex items-center text-[#606060] hover:text-[#030303]">
                    <span className="material-icons mr-1">share</span>
                    <span className="hidden sm:inline">Share</span>
                  </button>
                  <button className="flex items-center text-[#606060] hover:text-[#030303]">
                    <span className="material-icons mr-1">playlist_add</span>
                    <span className="hidden sm:inline">Save</span>
                  </button>
                </div>
              </div>
              <div className="bg-gray-100 p-3 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    <span className="text-sm font-medium">{formatCount(video.viewCount)} views</span>
                    <span className="mx-1">•</span>
                    <span className="text-sm">{formatPublishedDate(video.publishedAt)}</span>
                  </div>
                </div>
                <p className="text-sm text-[#030303]">
                  {video.description?.substring(0, 300)}
                  {video.description && video.description.length > 300 ? "..." : ""}
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
