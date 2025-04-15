import { useEffect } from "react";
import { useAppContext } from "@/context/AppContext";
import { useQuery } from "@tanstack/react-query";
import { Category } from "@shared/schema";

export default function CategoryFilter() {
  const { currentCategory, setCurrentCategory } = useAppContext();

  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ["/api/categories"],
  });

  const filterByCategory = (categoryId: string) => {
    setCurrentCategory(categoryId);
  };

  return (
    <div className="category-scroll w-full overflow-x-auto flex items-center border-t border-gray-200 py-2 px-4 bg-white scrollbar-none">
      <button 
        className={`whitespace-nowrap px-4 py-1 ${
          currentCategory === "all" 
            ? "bg-[#282828] text-white" 
            : "bg-gray-100 hover:bg-gray-200"
        } rounded-full mr-2 text-sm font-medium`}
        onClick={() => filterByCategory("all")}
      >
        All
      </button>
      
      {categories.map((category) => (
        <button 
          key={category.id}
          className={`whitespace-nowrap px-4 py-1 ${
            currentCategory === category.id 
              ? "bg-[#282828] text-white" 
              : "bg-gray-100 hover:bg-gray-200"
          } rounded-full mr-2 text-sm font-medium`}
          onClick={() => filterByCategory(category.id)}
        >
          {category.title}
        </button>
      ))}
    </div>
  );
}
