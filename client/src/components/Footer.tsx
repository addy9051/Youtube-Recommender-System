export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 py-6">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="mb-4 md:mb-0">
            <div className="flex items-center">
              <span className="material-icons text-[#FF0000] mr-2">smart_display</span>
              <span className="font-bold">YouRecommend</span>
            </div>
            <p className="text-sm text-[#606060] mt-2">A personalized YouTube video recommender</p>
          </div>
          <div className="flex flex-col items-center md:items-end">
            <div className="flex space-x-4 mb-2">
              <a href="#" className="text-[#606060] hover:text-[#030303]">About</a>
              <a href="#" className="text-[#606060] hover:text-[#030303]">Privacy</a>
              <a href="#" className="text-[#606060] hover:text-[#030303]">Terms</a>
            </div>
            <p className="text-xs text-[#606060]">© {new Date().getFullYear()} YouRecommend. Not affiliated with YouTube.</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
