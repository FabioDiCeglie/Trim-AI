import { Outlet, Link } from "react-router-dom";
import { useConnection } from "../hooks/useConnection";

export function Layout() {
  const { clearConnection } = useConnection();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
        <Link to="/overview" className="font-semibold text-slate-800 text-lg">
          Trim
        </Link>
        <nav className="flex items-center gap-4">
          <Link to="/overview" className="text-slate-600 hover:text-slate-900">
            Overview
          </Link>
          <button
            type="button"
            onClick={clearConnection}
            className="text-sm text-slate-500 hover:text-red-600"
          >
            Disconnect
          </button>
        </nav>
      </header>
      <main className="flex-1 p-4 md:p-6">
        <Outlet />
      </main>
    </div>
  );
}
