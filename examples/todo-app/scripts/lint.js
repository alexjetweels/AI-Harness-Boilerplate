import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const files = [
  'src/store.js',
  'src/cli.js',
  'test/todo.test.js',
  'scripts/acceptance.js',
  'scripts/lint.js',
  'scripts/security-check.js',
];

const failures = [];

for (const relative of files) {
  const absolute = path.join(root, relative);
  const text = fs.readFileSync(absolute, 'utf8');
  const lines = text.split('\n');

  lines.forEach((line, index) => {
    if (line.includes('\t')) {
      failures.push(`${relative}:${index + 1}: tabs are not allowed`);
    }
    if (line.length > 120) {
      failures.push(`${relative}:${index + 1}: line exceeds 120 characters`);
    }
  });
}

if (failures.length > 0) {
  console.error(failures.join('\n'));
  process.exitCode = 1;
} else {
  console.log('lint ok');
}

