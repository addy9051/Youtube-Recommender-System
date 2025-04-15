import { useState, useEffect, useRef } from "react";
import { useAppContext } from "@/context/AppContext";
import { useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import debounce from "lodash.debounce";

export default function SearchBar() {
  const { searchQuery, setSearchQuery, searchVideos, showNotification } = useAppContext();
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const searchMutation = useMutation({
    mutationFn: async (query: string) => {
      const response = await apiRequest("GET", `/api/videos/search?query=${encodeURIComponent(query)}`, undefined);
      return response.json();
    },
    onSuccess: (data) => {
      searchVideos(data);
      showNotification("Search results updated", "search");
      setShowSuggestions(false);
    },
  });

  const suggestionsMutation = useMutation({
    mutationFn: async (query: string) => {
      if (query.length < 3) return [];
      const response = await apiRequest("GET", `/api/suggestions?query=${encodeURIComponent(query)}`, undefined);
      return response.json();
    },
    onSuccess: (data) => {
      setSuggestions(data || []);
      if (data && data.length > 0) {
        setShowSuggestions(true);
      }
    },
  });

  const handleSearch = () => {
    if (searchQuery.trim()) {
      searchMutation.mutate(searchQuery);
    }
  };

  const debouncedSuggestions = useRef(
    debounce((query: string) => {
      if (query.length >= 3) {
        suggestionsMutation.mutate(query);
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, 300)
  ).current;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    debouncedSuggestions(value);
  };

  const handleSelectSuggestion = (suggestion: string) => {
    setSearchQuery(suggestion);
    searchMutation.mutate(suggestion);
    setShowSuggestions(false);
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (inputRef.current && !inputRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      debouncedSuggestions.cancel();
    };
  }, [debouncedSuggestions]);

  return (
    <div className="w-full md:w-2/3 lg:w-1/2 relative" ref={inputRef}>
      <div className="flex items-center">
        <input 
          type="text" 
          placeholder="Search videos..." 
          className="w-full px-4 py-2 border border-gray-300 rounded-l-full focus:outline-none focus:ring-2 focus:ring-[#065FD4] focus:border-transparent"
          value={searchQuery}
          onChange={handleInputChange}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button 
          className="bg-gray-100 px-5 py-2 border border-l-0 border-gray-300 rounded-r-full hover:bg-gray-200"
          onClick={handleSearch}
          disabled={searchMutation.isPending}
        >
          <span className="material-icons text-[#606060]">
            {searchMutation.isPending ? "hourglass_empty" : "search"}
          </span>
        </button>
      </div>
      
      {/* Search suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute w-full bg-white border border-gray-300 rounded-b-lg shadow-lg mt-1 z-10">
          {suggestions.map((suggestion, index) => (
            <div 
              key={index}
              className="px-4 py-2 hover:bg-gray-100 cursor-pointer flex items-center"
              onClick={() => handleSelectSuggestion(suggestion)}
            >
              <span className="material-icons text-[#606060] mr-2 text-sm">search</span>
              <span>{suggestion}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
