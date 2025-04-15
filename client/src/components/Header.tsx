import { useState } from "react";
import SearchBar from "./SearchBar";
import CategoryFilter from "./CategoryFilter";
import { useAppContext } from "@/context/AppContext";

export default function Header() {
  const { toggleTheme } = useAppContext();
  
  return (
    <header className="sticky top-0 z-50 bg-white shadow-sm">
      <div className="container mx-auto px-4 py-2 flex flex-col md:flex-row items-center justify-between">
        <div className="flex items-center mb-3 md:mb-0">
          <span className="material-icons text-[#FF0000] mr-2">smart_display</span>
          <h1 className="text-xl font-bold">YouRecommend</h1>
        </div>
        
        <SearchBar />
        
        <div className="hidden md:flex items-center ml-4">
          <button 
            className="bg-[#FF0000] hover:bg-red-700 text-white px-4 py-2 rounded-full font-medium flex items-center"
            onClick={toggleTheme}
          >
            <span className="material-icons mr-1">dark_mode</span>
            Theme
          </button>
        </div>
      </div>
      
      <CategoryFilter />
    </header>
  );
}
