#!/usr/bin/env node
import {
  addTask,
  completeTask,
  deleteTask,
  formatTask,
  listTasks,
} from './store.js';

function printHelp() {
  console.log(`Usage:
  todo add <title>
  todo list
  todo done <id>
  todo delete <id>

Environment:
  TODO_FILE  Path to the JSON task store. Defaults to .todo.json.`);
}

function requireArg(value, message) {
  if (!value) {
    throw new Error(message);
  }
  return value;
}

export function run(argv = process.argv.slice(2)) {
  const [command, ...args] = argv;

  if (!command || command === 'help' || command === '--help' || command === '-h') {
    printHelp();
    return 0;
  }

  if (command === 'add') {
    const title = requireArg(args.join(' '), 'Task title is required');
    const task = addTask(title);
    console.log(`Added ${formatTask(task)}`);
    return 0;
  }

  if (command === 'list') {
    const tasks = listTasks();
    if (tasks.length === 0) {
      console.log('No tasks');
      return 0;
    }
    for (const task of tasks) {
      console.log(formatTask(task));
    }
    return 0;
  }

  if (command === 'done') {
    const id = requireArg(args[0], 'Task id is required');
    const task = completeTask(id);
    console.log(`Completed ${formatTask(task)}`);
    return 0;
  }

  if (command === 'delete') {
    const id = requireArg(args[0], 'Task id is required');
    deleteTask(id);
    console.log(`Deleted task ${id}`);
    return 0;
  }

  throw new Error(`Unknown command: ${command}`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    process.exitCode = run();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

