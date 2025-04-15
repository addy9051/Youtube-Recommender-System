import { Switch, Route } from "wouter";
import NotFound from "@/pages/not-found";
import Home from "@/pages/home";
import Notification from "@/components/Notification";
import { AppProvider } from "@/context/AppContext";

function App() {
  return (
    <AppProvider>
      <div className="min-h-screen flex flex-col bg-[#F9F9F9] text-[#030303] font-roboto">
        <Switch>
          <Route path="/" component={Home} />
          <Route component={NotFound} />
        </Switch>
        <Notification />
      </div>
    </AppProvider>
  );
}

export default App;
