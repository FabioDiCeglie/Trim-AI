import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useConnection } from "./hooks/useConnection";
import { Layout } from "./components/Layout";
import { Chat } from "./components/Chat";
import { Onboarding } from "./pages/Onboarding";
import { Overview } from "./pages/Overview";

function Protected({ children }: { children: React.ReactNode }) {
  const { connected } = useConnection();
  if (!connected) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  const { connected } = useConnection();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={connected ? <Navigate to="/overview" replace /> : <Onboarding />} />
        <Route path="/overview" element={<Protected><Layout /></Protected>}>
          <Route index element={<Overview />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {connected && <Chat />}
    </BrowserRouter>
  );
}
