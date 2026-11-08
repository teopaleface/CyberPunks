'use client';
import {useEffect, useState} from 'react';
import {getTask, type TaskView} from './client';
export function useTask(accountKey: string, scenario: string, taskId: string | null) {
  const key = JSON.stringify([accountKey, scenario, taskId]);
  const [state, setState] = useState<{key: string; task?: TaskView; error?: string}>({key});
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const task = await getTask(taskId!, scenario, controller.signal);
        if (controller.signal.aborted) return;
        setState({key, task});
        if (['queued', 'running'].includes(task.status)) timer = setTimeout(poll, 1500);
      } catch (error) {
        if (!controller.signal.aborted) setState({key, error: String(error)});
      }
    }
    if (taskId) void poll();
    return () => {controller.abort(); clearTimeout(timer);};
  }, [key, scenario, taskId]);
  return state.key === key ? state : {key};
}
