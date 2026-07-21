import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useTasks } from '../context/TaskContext';
import { cn } from '../utils/cn';

const TRUST_PHRASES = [
  '俺を信じろって',
  'ガチだから',
  'ソースは俺',
  '信じてくれよ',
  '내 말 믿어',
  '내가 해봐서 아는데',
  '진짜야',
  '오빠 말만 믿어',
  'Fais-moi confiance',
  "T'inquiète, poto",
  "T'inquiète, cedl'IA",
  'Trust me, bro',
  'Just trust me on this one',
  'Take my word for it',
] as const;

function pickTrustPhrase(): string {
  return TRUST_PHRASES[Math.floor(Math.random() * TRUST_PHRASES.length)];
}

const NAV_ITEMS = [
  { to: '/agents', icon: 'account_tree', label: 'Agents' },
  { to: '/cases', icon: 'fact_check', label: 'View Cases' },
  { to: '/cases_editor', icon: 'edit_note', label: 'Case Editor' },
  { to: '/runs', icon: 'play_circle', label: 'Run Generation' },
  { to: '/evals', icon: 'checklist', label: 'Run Evals' },
  { to: '/compare', icon: 'difference', label: 'Compare' },
  { to: '/campaigns', icon: 'rocket_launch', label: 'Campaigns' },
  { to: '/registries', icon: 'storage', label: 'Registries' },
  { to: '/human-eval', icon: 'person', label: 'Human Eval' },
];

function taskProgressLabel(task: { label: string; progress?: { done: number; total: number } }) {
  if (!task.progress || task.progress.total <= 1) {
    return task.label;
  }
  return `${task.label} (${task.progress.done}/${task.progress.total})`;
}

export function Layout() {
  const location = useLocation();
  const [repo, setRepo] = useState('...');
  const [headline, setHeadline] = useState(pickTrustPhrase);
  const { activeTasks, failedTasks } = useTasks();

  useEffect(() => {
    setHeadline(pickTrustPhrase());
  }, [location.pathname]);

  useEffect(() => {
    fetch('/api/repo')
      .then(res => res.json())
      .then(data => setRepo(data.repo_path))
      .catch(console.error);
  }, []);

  const headerTasks = [
    ...activeTasks,
    ...failedTasks.map(task => ({ ...task, status: 'failed' as const })),
  ];

  return (
    <div className="flex h-screen bg-background font-body text-on-surface overflow-hidden w-full">
      <nav className="bg-surface-container docked left-0 h-screen w-64 border-r border-outline-variant flex flex-col py-4 z-10 shrink-0">
        <div className="px-6 mb-8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-primary-container text-on-primary-container flex items-center justify-center">
              <span className="material-symbols-outlined font-bold">science</span>
            </div>
            <div>
              <div className="font-headline font-bold text-on-surface tracking-tight text-lg leading-tight">{headline}</div>
              <div className="font-mono text-on-surface-variant text-xs mt-0.5">TrustMeBro</div>
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col gap-1 px-3 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/cases'}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm font-body",
                  isActive
                    ? "text-primary-fixed border-r-2 border-primary-fixed bg-surface-container-high opacity-80 font-headline font-bold"
                    : "text-on-surface-variant hover:bg-surface-container-highest hover:text-on-surface"
                )
              }
            >
              <span className="material-symbols-outlined text-xl">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="flex-1 flex flex-col min-w-0 bg-background relative z-0">
        <header className="bg-surface top-0 w-full border-b border-outline-variant shrink-0 z-10">
          <div className="h-12 flex justify-between items-center px-4">
            <div className="font-headline font-bold text-primary-fixed text-lg truncate">
              Target: {repo}
            </div>
          </div>
          {headerTasks.length > 0 && (
            <div className="px-4 pb-2 space-y-1 border-t border-outline-variant/40">
              {headerTasks.map(task => (
                <div
                  key={task.id}
                  className={cn(
                    'text-xs font-mono truncate flex items-center gap-2',
                    task.status === 'failed'
                      ? 'text-semantic-fail'
                      : 'text-on-surface-variant',
                  )}
                  title={task.error || task.label}
                >
                  <span className="material-symbols-outlined text-sm shrink-0">
                    {task.status === 'failed' ? 'error' : 'progress_activity'}
                  </span>
                  <span className="truncate">
                    {task.status === 'failed'
                      ? `${task.label}: ${task.error || 'failed'}`
                      : taskProgressLabel(task)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </header>

        <main className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
