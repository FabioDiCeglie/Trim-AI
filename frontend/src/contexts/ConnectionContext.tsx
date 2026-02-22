import { createContext, useCallback, useContext, useState } from "react";
import {
  hasConnection,
  setConnection as saveConnection,
  clearConnection as clearStored,
} from "../api/client";

type ConnectionContextValue = {
  connected: boolean;
  setConnection: (connectionId: string, provider: string) => void;
  clearConnection: () => void;
};

const ConnectionContext = createContext<ConnectionContextValue | null>(null);

export function ConnectionProvider({ children }: { children: React.ReactNode }) {
  const [connected, setConnected] = useState(hasConnection());

  const setConnection = useCallback((connectionId: string, provider: string) => {
    saveConnection(connectionId, provider);
    setConnected(true);
  }, []);

  const clearConnection = useCallback(() => {
    clearStored();
    setConnected(false);
  }, []);

  return (
    <ConnectionContext.Provider value={{ connected, setConnection, clearConnection }}>
      {children}
    </ConnectionContext.Provider>
  );
}

export function useConnection(): ConnectionContextValue {
  const ctx = useContext(ConnectionContext);
  if (!ctx) throw new Error("useConnection must be used within ConnectionProvider");
  return ctx;
}
