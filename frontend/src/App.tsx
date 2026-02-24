import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useConnection } from "./contexts/ConnectionContext";
import { Layout } from "./components/Layout";
import { Chat } from "./components/Chat";
import { Onboarding } from "./pages/Onboarding";
import { Overview } from "./pages/Overview";

function Protected({ children }: { children: React.ReactNode }) {
  const { connected, demo } = useConnection();
  if (!connected && !demo) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  const { connected, demo } = useConnection();
  const active = connected || demo;

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={active ? <Navigate to="/overview" replace /> : <Onboarding />} />
        <Route path="/overview" element={<Protected><Layout /></Protected>}>
          <Route index element={<Overview />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {active && <Chat />}
    </BrowserRouter>
  );
}
