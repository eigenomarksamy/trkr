# trkr web app

A page that shows the `snapshot.json` a trkr run writes: totals, holdings with a page per investment, transactions, imaginary portfolios, and a net-worth projection whose inputs can be edited. A Cloudflare Worker serves it, so it can have its own domain.

## How your data stays private

- **Nothing is uploaded.** The page reads the snapshot you open in the browser. The Worker serves the page's files and stores nothing. With "Remember it on this device", the browser keeps a copy in its local storage, and only there.
- **The page can't send the snapshot anywhere.** The Worker sends a Content-Security-Policy that limits the page to its own files and its own origin. There are no third-party scripts, fonts or analytics.
- **The deploy holds no private data.** The published files are `dist/`, built from the tracked files in this folder, plus the Worker script. The demo is made from the made-up files in `examples/`. The build ends with `scripts/check-private.mjs`, which stops the build, and so the deploy, when:
  - a file the build reads (`index.html`, `src/`, `public/`) is unknown to git, such as a real `snapshot.json` dropped into `public/`;
  - a built file contains a sheet address from your local `config/*.yml`, or your home directory;
  - `dist/` holds any trkr snapshot other than the demo, or the demo was made from a Google Sheet or has unstaged changes.

  `wrangler dev` and `wrangler deploy` both run the build first (`build.command` in `wrangler.jsonc`), so a plain `npx wrangler deploy` is checked too. The deploy workflow runs the same check, but it has no local configs, so the sheet-address part has nothing to compare against. It builds only tracked files, which the push has already made public.
- **No domain in the repo.** The repo is public, so the custom domain is passed on the command line rather than written into `wrangler.jsonc`. Its Actions logs are public too, so the deploy workflow doesn't pass the domain and hides the `workers.dev` address.
- **No telemetry from Wrangler**: `send_metrics` is off in `wrangler.jsonc`.

A snapshot holds your holdings and transactions. Keep it in `data/`, which is gitignored, and don't put it in `web/`.

## Setup

Node 22.12 or newer. From this folder:

```sh
npm ci
```

npm may warn that esbuild and workerd have install scripts it didn't run. The build and the Worker run without them.

## Commands

All from `web/`:

| What | Command |
|---|---|
| Type-check and test | `npm run check` |
| Build to `dist/` (type-check, Vite, privacy check) | `npm run build` |
| Page only, with live reload (no Worker headers) | `npm run dev` |
| Page and Worker locally, as deployed, on <http://127.0.0.1:8787> | `npm run preview` |
| Deploy by hand | `npm run deploy` |

## Deploy

A push to `main` that changes `web/` deploys the app. `.github/workflows/deploy-web.yml` runs `npm ci`, `npm run check` and `npm run deploy`, so a failing test stops the deploy. To deploy without a push, use **Run workflow** on the repo's Actions tab. `npx wrangler deployments list` shows the commit behind each deploy.

The workflow needs two repository secrets, added once under **Settings > Secrets and variables > Actions**:

| Secret | Value |
|---|---|
| `CLOUDFLARE_API_TOKEN` | An account API token made from the **Edit Cloudflare Workers** template, limited to your account and the domain's zone. |
| `CLOUDFLARE_ACCOUNT_ID` | Your account ID, shown by `npx wrangler whoami`. |

### By hand

Once per machine, sign in to Cloudflare:

```sh
npx wrangler login
```

Then deploy to `trkr.<your-subdomain>.workers.dev`:

```sh
npm run deploy
```

To serve it from your own domain as well, the domain's zone must be on the same Cloudflare account. Pass the hostname once:

```sh
npm run deploy -- --domain trkr.example.com
```

Wrangler creates the DNS record and the certificate, and later deploys leave the domain attached. Check a deploy with `https://<host>/api/health`, which answers `{"ok":true,"snapshot_schema_version":1}`. To serve only the custom domain, set `"workers_dev": false` in `wrangler.jsonc`.

New files under `src/` or `public/` must be staged (`git add`) before they build, because of the privacy check.

## The demo

`public/demo-snapshot.json` is the snapshot of `config/demo-cfg.yml`: the made-up transactions in `examples/`, priced live from Yahoo. To refresh it, from the repo root:

```sh
.venv/Scripts/python.exe run.py --cfg config/demo-cfg.yml --quiet
cp data/demo-run/snapshot.json web/public/demo-snapshot.json
git add web/public/demo-snapshot.json
```

`test/projection.test.ts` checks the browser's projection against the rows the CLI computed for the demo, so run `npm run check` after a refresh.

## How it fits together

- `src/snapshot.ts`: the snapshot's types and `parseSnapshot`. The CLI writes it in `src/snapshot.py`. A change to its shape bumps `SCHEMA_VERSION` in both.
- `src/projection.ts`: a port of `src/projection.py` and the projection checks in `src/cfg_mngr.py`, so the projection can be recomputed as you type.
- `src/worker.ts`: the Worker. It serves `dist/` through the `ASSETS` binding, adds the security headers, and answers `/api/health`.
- `src/app.ts`: the shell and the hash router. Pages are in `src/views/`, charts in `src/chart.ts` (SVG, no library). The DOM is built with `src/dom.ts`, which only ever inserts text, so values from your sheets can't inject HTML.

## Testing
