import { createContext, useCallback, useContext, useState } from "react";
import {
  hasConnection,
  setConnection as saveConnection,
  clearConnection as clearStored,
} from "../api/client";

type ConnectionContextValue = {
  connected: boolean;
  demo: boolean;
  selectedProjectId: string | null;
  setConnection: (connectionId: string, provider: string) => void;
  clearConnection: () => void;
  enterDemo: () => void;
  setSelectedProjectId: (id: string | null) => void;
};

const ConnectionContext = createContext<ConnectionContextValue | null>(null);

export function ConnectionProvider({ children }: { children: React.ReactNode }) {
  const [connected, setConnected] = useState(hasConnection());
  const [demo, setDemo] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  const setConnection = useCallback((connectionId: string, provider: string) => {
    saveConnection(connectionId, provider);
    setConnected(true);
  }, []);

  const clearConnection = useCallback(() => {
    clearStored();
    setConnected(false);
    setDemo(false);
    setSelectedProjectId(null);
  }, []);

  const enterDemo = useCallback(() => {
    setDemo(true);
  }, []);

  return (
    <ConnectionContext.Provider value={{
      connected, demo, selectedProjectId,
      setConnection, clearConnection, enterDemo, setSelectedProjectId,
    }}>
      {children}
    </ConnectionContext.Provider>
  );
}

export function useConnection(): ConnectionContextValue {
  const ctx = useContext(ConnectionContext);
  if (!ctx) throw new Error("useConnection must be used within ConnectionProvider");
  return ctx;
}
