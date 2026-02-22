import { Outlet } from "react-router-dom";
import { useConnection } from "../contexts/ConnectionContext";

export function Layout() {
  const { clearConnection } = useConnection();

  return (
    <div className="min-h-screen bg-trim-base">
      <div className="flex justify-end p-3">
        <button
          type="button"
          onClick={clearConnection}
          className="text-sm text-trim-muted hover:text-white"
        >
          Disconnect
        </button>
      </div>
      <main className="px-4 pb-8 md:px-6 md:pb-12">
        <Outlet />
      </main>
    </div>
  );
}
