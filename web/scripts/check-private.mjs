// Stops a build that could publish the owner's data. It is the last step of `npm run build`,
// which `wrangler dev` and `wrangler deploy` run first (build.command in wrangler.jsonc), so
// nothing reaches Cloudflare without passing it. It never prints the private values it looks for.
//
// 1. Every file the build reads (index.html, src/, public/) is known to git, tracked or staged.
//    A file dropped there, such as a real snapshot.json, is not published by accident.
// 2. No file in dist/ or src/ contains a sheet address from the local configs (config/*.yml,
//    gitignored, except demo-cfg.yml), or this machine's home directory.
// 3. The one snapshot in dist/ is the demo: staged as it is in public/, and made from local
//    files only. A snapshot of the owner's portfolio says its sources are cloud sheets.

import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const web = join(dirname(fileURLToPath(import.meta.url)), '..');
const repo = join(web, '..');
const dist = join(web, 'dist');
const DEMO = 'demo-snapshot.json';
const problems = [];

const git = (...args) => execFileSync('git', args, { cwd: web, encoding: 'utf8' });
const posix = (path) => path.split(sep).join('/');

function files(dir) {
  if (!existsSync(dir)) return [];
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? files(path) : [path];
  });
}

// 1. Inputs known to git. --others without --exclude-standard lists ignored files too.
const unknown = git('ls-files', '--others', '-z', '--', 'index.html', 'src', 'public')
  .split('\0')
  .filter(Boolean);
for (const path of unknown) {
  problems.push(`web/${path} is not tracked by git. Stage it (git add) if it is meant to be published, or move it out of web/.`);
}

// 2. Private markers.
const markers = [];
const configDir = join(repo, 'config');
if (existsSync(configDir)) {
  for (const name of readdirSync(configDir)) {
    if (!/\.ya?ml$/.test(name) || name === 'demo-cfg.yml') continue;
    const text = readFileSync(join(configDir, name), 'utf8');
    for (const match of text.matchAll(/shareable-address:\s*['"]?([^\s'"#]+)/g)) {
      const address = match[1];
      markers.push({ value: address, what: `a sheet address from config/${name}` });
      // The sheet ID alone, out of a full link.
      const id = /\/d\/(?:e\/)?([\w-]{20,})/.exec(address)?.[1];
      if (id) markers.push({ value: id, what: `a sheet ID from config/${name}` });
    }
  }
}
const home = homedir();
if (home.length > 3) {
  for (const value of new Set([home, posix(home), home.replaceAll('\\', '\\\\')])) {
    markers.push({ value, what: "this machine's home directory" });
  }
}
const scanned = [...files(dist), ...files(join(web, 'src'))];
for (const path of scanned) {
  const text = readFileSync(path, 'latin1');
  for (const marker of markers) {
    if (text.includes(marker.value)) problems.push(`web/${posix(relative(web, path))} contains ${marker.what}.`);
  }
}

// 3. Snapshots.
for (const path of files(dist).filter((p) => p.endsWith('.json'))) {
  let data;
  try {
    data = JSON.parse(readFileSync(path, 'utf8'));
  } catch {
    continue;
  }
  if (data?.schema !== 'trkr-snapshot') continue;
  const name = posix(relative(dist, path));
  if (name !== DEMO) {
    problems.push(`web/dist/${name} is a trkr snapshot. Only public/${DEMO}, made from made-up data, is published.`);
    continue;
  }
  const sources = Object.values(data.config?.sources ?? {});
  if (sources.some((source) => source !== 'local' && source !== null)) {
    problems.push(`public/${DEMO} was made from a Google Sheet. Make it from the made-up examples/ files (see web/README.md).`);
  }
  const changed = git('diff', '--name-only', '--', `public/${DEMO}`).trim();
  if (changed) problems.push(`public/${DEMO} has changes that are not staged. Review them, then git add it.`);
}

const published = files(dist);
if (problems.length > 0) {
  console.error('check-private: not publishing, because:');
  for (const problem of problems) console.error(`  - ${problem}`);
  process.exit(1);
}
const size = published.reduce((sum, path) => sum + statSync(path).size, 0);
console.log(
  `check-private: ${published.length} files in dist/ (${(size / 1024).toFixed(0)} KB), checked against ${markers.length} private markers. OK.`,
);
for (const path of published) console.log(`  ${posix(relative(dist, path))}`);
