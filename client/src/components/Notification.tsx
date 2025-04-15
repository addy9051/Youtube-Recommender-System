import { useEffect } from "react";
import { useAppContext } from "../context/AppContext";

export default function Notification() {
  const { notification, hideNotification } = useAppContext();
  
  useEffect(() => {
    if (notification.show) {
      const timer = setTimeout(() => {
        hideNotification();
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [notification, hideNotification]);
  
  if (!notification.show) return null;
  
  return (
    <div 
      className={`fixed bottom-4 right-4 bg-[#282828] text-white px-4 py-3 rounded-lg shadow-lg transform transition-all duration-300 ${
        notification.show 
          ? "translate-y-0 opacity-100" 
          : "translate-y-16 opacity-0"
      }`}
    >
      <div className="flex items-center">
        <span className="material-icons mr-2">{notification.icon}</span>
        <span>{notification.message}</span>
      </div>
    </div>
  );
}
