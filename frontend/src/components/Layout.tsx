import { Outlet } from "react-router-dom";
import { useConnection } from "../contexts/ConnectionContext";

export function Layout() {
  const { clearConnection } = useConnection();

  return (
    <div className="min-h-screen bg-trim-base">
      <div className="flex justify-end px-8 py-5 pl-12">
        <button
          type="button"
          onClick={clearConnection}
          className="text-sm text-trim-muted hover:text-white py-2 px-3"
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
