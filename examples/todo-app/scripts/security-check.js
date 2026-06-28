import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const scanDirs = ['src', 'scripts', 'test'];
const secretPatterns = [
  /api[_-]?key\s*=\s*['"][^'"]+/i,
  /secret\s*=\s*['"][^'"]+/i,
  /password\s*=\s*['"][^'"]+/i,
  /-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----/,
];

function walk(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const absolute = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      return walk(absolute);
    }
    return [absolute];
  });
}

const failures = [];
for (const scanDir of scanDirs) {
  for (const file of walk(path.join(root, scanDir))) {
    const text = fs.readFileSync(file, 'utf8');
    for (const pattern of secretPatterns) {
      if (pattern.test(text)) {
        failures.push(path.relative(root, file));
      }
    }
  }
}

if (failures.length > 0) {
  console.error(`Potential secret patterns found:\n${failures.join('\n')}`);
  process.exitCode = 1;
} else {
  console.log('security ok');
}

