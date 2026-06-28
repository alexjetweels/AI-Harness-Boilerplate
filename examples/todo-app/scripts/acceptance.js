import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'todo-acceptance-'));
const store = path.join(dir, 'tasks.json');
const env = { ...process.env, TODO_FILE: store };

function run(args) {
  return execFileSync(process.execPath, ['src/cli.js', ...args], {
    cwd: path.resolve(new URL('..', import.meta.url).pathname),
    env,
    encoding: 'utf8',
  }).trim();
}

assert.match(run(['list']), /No tasks/);
assert.match(run(['add', 'Write acceptance test']), /Added 1\. \[ \] Write acceptance test/);
assert.match(run(['add', 'Run harness gates']), /Added 2\. \[ \] Run harness gates/);
assert.match(run(['list']), /1\. \[ \] Write acceptance test/);
assert.match(run(['done', '1']), /Completed 1\. \[x\] Write acceptance test/);
assert.match(run(['delete', '2']), /Deleted task 2/);

const finalList = run(['list']);
assert.match(finalList, /1\. \[x\] Write acceptance test/);
assert.doesNotMatch(finalList, /Run harness gates/);

console.log('acceptance ok');

