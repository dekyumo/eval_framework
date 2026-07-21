import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import {
  FAILED_TASK_DISPLAY_MS,
  fetchActiveTasks,
  type DomainEventHandler,
  type FailedTask,
  type Task,
} from '../lib/jobsApi';

type TaskContextValue = {
  activeTasks: Task[];
  failedTasks: FailedTask[];
  hasActiveTaskType: (type: string) => boolean;
  subscribe: (eventType: string, handler: DomainEventHandler) => () => void;
  refreshActiveTasks: () => Promise<void>;
};

const TaskContext = createContext<TaskContextValue | null>(null);

function upsertActiveTask(tasks: Task[], task: Task): Task[] {
  if (task.status === 'succeeded' || task.status === 'failed') {
    return tasks.filter(item => item.id !== task.id);
  }
  const rest = tasks.filter(item => item.id !== task.id);
  return [...rest, task];
}

export function TaskProvider({ children }: { children: ReactNode }) {
  const [activeTasks, setActiveTasks] = useState<Task[]>([]);
  const [failedTasks, setFailedTasks] = useState<FailedTask[]>([]);
  const handlersRef = useRef<Map<string, Set<DomainEventHandler>>>(new Map());

  const emit = useCallback((eventType: string, data: Record<string, unknown>) => {
    const handlers = handlersRef.current.get(eventType);
    if (!handlers) return;
    handlers.forEach(handler => handler(data));
  }, []);

  const subscribe = useCallback((eventType: string, handler: DomainEventHandler) => {
    const handlers = handlersRef.current.get(eventType) ?? new Set<DomainEventHandler>();
    handlers.add(handler);
    handlersRef.current.set(eventType, handlers);
    return () => {
      const current = handlersRef.current.get(eventType);
      if (!current) return;
      current.delete(handler);
      if (current.size === 0) {
        handlersRef.current.delete(eventType);
      }
    };
  }, []);

  const refreshActiveTasks = useCallback(async () => {
    const tasks = await fetchActiveTasks();
    setActiveTasks(tasks);
  }, []);

  useEffect(() => {
    refreshActiveTasks().catch(console.error);

    const source = new EventSource('/api/jobs/events');

    source.addEventListener('task_updated', (event) => {
      const task = JSON.parse((event as MessageEvent).data) as Task;
      setActiveTasks(prev => upsertActiveTask(prev, task));
      if (task.status === 'failed') {
        setFailedTasks(prev => [
          ...prev.filter(item => item.id !== task.id),
          { ...task, failedAt: Date.now() },
        ]);
      }
      emit('task_updated', task as unknown as Record<string, unknown>);
    });

    const domainEvents = [
      'trace_generated',
      'trace_evaluated',
      'campaign_finished',
      'snapshot_scanned',
      'cases_modified',
    ] as const;

    for (const eventType of domainEvents) {
      source.addEventListener(eventType, (event) => {
        const data = JSON.parse((event as MessageEvent).data) as Record<string, unknown>;
        emit(eventType, data);
      });
    }

    source.onerror = () => {
      refreshActiveTasks().catch(console.error);
    };

    const onFocus = () => {
      refreshActiveTasks().catch(console.error);
    };
    window.addEventListener('focus', onFocus);

    return () => {
      source.close();
      window.removeEventListener('focus', onFocus);
    };
  }, [emit, refreshActiveTasks]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      const cutoff = Date.now() - FAILED_TASK_DISPLAY_MS;
      setFailedTasks(prev => prev.filter(task => task.failedAt >= cutoff));
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const hasActiveTaskType = useCallback(
    (type: string) => activeTasks.some(task => task.type === type),
    [activeTasks],
  );

  const value = useMemo(
    () => ({
      activeTasks,
      failedTasks,
      hasActiveTaskType,
      subscribe,
      refreshActiveTasks,
    }),
    [activeTasks, failedTasks, hasActiveTaskType, subscribe, refreshActiveTasks],
  );

  return <TaskContext.Provider value={value}>{children}</TaskContext.Provider>;
}

export function useTasks() {
  const context = useContext(TaskContext);
  if (!context) {
    throw new Error('useTasks must be used within TaskProvider');
  }
  return context;
}

export function useDomainEvent(eventType: string, handler: DomainEventHandler) {
  const { subscribe } = useTasks();
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  useEffect(() => {
    return subscribe(eventType, (data) => handlerRef.current(data));
  }, [eventType, subscribe]);
}
