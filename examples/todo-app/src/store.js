import fs from 'node:fs';
import path from 'node:path';

export function resolveStorePath(filePath = process.env.TODO_FILE || '.todo.json') {
  return path.resolve(filePath);
}

export function loadTasks(filePath) {
  const storePath = resolveStorePath(filePath);
  if (!fs.existsSync(storePath)) {
    return [];
  }

  const raw = fs.readFileSync(storePath, 'utf8').trim();
  if (!raw) {
    return [];
  }

  const parsed = JSON.parse(raw);
  if (!Array.isArray(parsed)) {
    throw new Error(`Todo store must contain an array: ${storePath}`);
  }
  return parsed;
}

export function saveTasks(tasks, filePath) {
  const storePath = resolveStorePath(filePath);
  fs.mkdirSync(path.dirname(storePath), { recursive: true });
  fs.writeFileSync(storePath, `${JSON.stringify(tasks, null, 2)}\n`);
}

export function addTask(title, filePath) {
  const cleanTitle = String(title || '').trim();
  if (!cleanTitle) {
    throw new Error('Task title is required');
  }

  const tasks = loadTasks(filePath);
  const nextId = tasks.reduce((max, task) => Math.max(max, Number(task.id) || 0), 0) + 1;
  const task = { id: nextId, title: cleanTitle, done: false };
  tasks.push(task);
  saveTasks(tasks, filePath);
  return task;
}

export function listTasks(filePath) {
  return loadTasks(filePath);
}

export function completeTask(id, filePath) {
  const numericId = Number(id);
  const tasks = loadTasks(filePath);
  const task = tasks.find((item) => item.id === numericId);
  if (!task) {
    throw new Error(`Task not found: ${id}`);
  }
  task.done = true;
  saveTasks(tasks, filePath);
  return task;
}

export function deleteTask(id, filePath) {
  const numericId = Number(id);
  const tasks = loadTasks(filePath);
  const nextTasks = tasks.filter((task) => task.id !== numericId);
  if (nextTasks.length === tasks.length) {
    throw new Error(`Task not found: ${id}`);
  }
  saveTasks(nextTasks, filePath);
}

export function formatTask(task) {
  const marker = task.done ? 'x' : ' ';
  return `${task.id}. [${marker}] ${task.title}`;
}

