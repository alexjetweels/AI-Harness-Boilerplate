import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import {
  addTask,
  completeTask,
  deleteTask,
  formatTask,
  listTasks,
} from '../src/store.js';

function tempStore() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'todo-test-'));
  return path.join(dir, 'tasks.json');
}

test('adds and lists tasks', () => {
  const file = tempStore();

  const first = addTask('Write tests', file);
  const second = addTask('Run harness', file);

  assert.deepEqual(first, { id: 1, title: 'Write tests', done: false });
  assert.deepEqual(second, { id: 2, title: 'Run harness', done: false });
  assert.equal(listTasks(file).length, 2);
});

test('marks a task complete', () => {
  const file = tempStore();
  addTask('Ship feature', file);

  const task = completeTask(1, file);

  assert.equal(task.done, true);
  assert.equal(formatTask(task), '1. [x] Ship feature');
});

test('deletes a task', () => {
  const file = tempStore();
  addTask('Temporary task', file);

  deleteTask(1, file);

  assert.deepEqual(listTasks(file), []);
});

test('rejects empty task titles', () => {
  const file = tempStore();

  assert.throws(() => addTask('   ', file), /Task title is required/);
});

