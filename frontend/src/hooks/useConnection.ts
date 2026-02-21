import { useCallback, useState } from "react";
import {
  hasConnection,
  setConnection as saveConnection,
  clearConnection as clearStored,
} from "../api/client";

export function useConnection() {
  const [connected, setConnected] = useState(hasConnection());

  const setConnection = useCallback((connectionId: string, provider: string) => {
    saveConnection(connectionId, provider);
    setConnected(true);
  }, []);

  const clearConnection = useCallback(() => {
    clearStored();
    setConnected(false);
  }, []);

  return { connected, setConnection, clearConnection };
}
