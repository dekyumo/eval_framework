import { NavLink, Outlet } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { cn } from '../utils/cn';

const NAV_ITEMS = [
  { to: '/', icon: 'smart_toy', label: 'Onboarding' },
  { to: '/agents', icon: 'account_tree', label: 'Agents' },
  { to: '/cases', icon: 'fact_check', label: 'Cases & Evals' },
  { to: '/runs', icon: 'play_circle', label: 'Run Generation' },
  { to: '/evals', icon: 'checklist', label: 'Run Evals' },
  { to: '/compare', icon: 'difference', label: 'Compare' },
  { to: '/campaigns', icon: 'rocket_launch', label: 'Campaigns' },
  { to: '/registries', icon: 'storage', label: 'Registries' },
  { to: '/human-eval', icon: 'person', label: 'Human Eval' },
  { to: '/chat', icon: 'forum', label: 'Chat Operator' },
];

export function Layout() {
  const [repo, setRepo] = useState('...');

  useEffect(() => {
    fetch('/api/repo')
      .then(res => res.json())
      .then(data => setRepo(data.repo_path))
      .catch(console.error);
  }, []);

  return (
    <div className="flex h-screen bg-background font-body text-on-surface overflow-hidden w-full">
      {/* SideNavBar */}
      <nav className="bg-surface-container docked left-0 h-screen w-64 border-r border-outline-variant flex flex-col py-4 z-10 shrink-0">
        {/* Header */}
        <div className="px-6 mb-8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-primary-container text-on-primary-container flex items-center justify-center">
              <span className="material-symbols-outlined font-bold">science</span>
            </div>
            <div>
              <div className="font-headline font-bold text-on-surface tracking-tight text-lg">Lab Instrument</div>
              <div className="font-mono text-on-surface-variant text-xs mt-0.5">Eval Workbench</div>
            </div>
          </div>
        </div>
        
        {/* Main Nav */}
        <div className="flex-1 flex flex-col gap-1 px-3 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm font-body",
                  isActive 
                    ? "text-primary-fixed border-r-2 border-primary-fixed bg-surface-container-high opacity-80 font-headline font-bold" 
                    : "text-on-surface-variant hover:bg-surface-container-highest hover:text-on-surface"
                )
              }
            >
              <span className="material-symbols-outlined text-xl" style={/* Active state logic for icons if needed */ {}}>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-background relative z-0">
        {/* TopAppBar */}
        <header className="bg-surface top-0 w-full h-12 border-b border-outline-variant flex justify-between items-center px-4 shrink-0 z-10">
          <div className="flex items-center gap-4">
            <div className="font-headline font-bold text-primary-fixed text-lg">Target: {repo}</div>
          </div>
        </header>

        {/* Main Pane */}
        <main className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

