import { h } from '../dom';
import { loadDemo, loadFile, type Loaded } from '../store';

type Reload = (loaded: Loaded | null) => void;

async function open(file: File | undefined, remember: boolean, reload: Reload, error: HTMLElement): Promise<void> {
  if (!file) return;
  try {
    reload(await loadFile(file, remember));
  } catch (problem) {
    error.textContent = problem instanceof Error ? problem.message : String(problem);
    error.hidden = false;
  }
}

/** A button that opens a snapshot file. Errors go to an alert, since there's no form here. */
export function openFileButton(reload: Reload, remember: boolean, label: string): HTMLElement {
  const input = h('input', { type: 'file', accept: '.json,application/json', class: 'visually-hidden' });
  const error = h('span', { hidden: true });
  input.addEventListener('change', async () => {
    await open(input.files?.[0], remember, reload, error);
    if (!error.hidden) {
      alert(error.textContent);
      error.hidden = true;
    }
    input.value = '';
  });
  return h('label', { class: 'button quiet' }, input, label);
}

export function landing(reload: Reload): HTMLElement {
  const error = h('p', { class: 'notice error', role: 'alert', hidden: true });
  const remember = h('input', { type: 'checkbox' });
  const input = h('input', { type: 'file', accept: '.json,application/json', class: 'visually-hidden' });
  input.addEventListener('change', () => open(input.files?.[0], remember.checked, reload, error));

  const drop = h(
    'div',
    { class: 'drop' },
    h('label', { class: 'button primary' }, input, 'open snapshot.json'),
    h('p', { class: 'muted' }, 'or drop the file here'),
  );
  drop.addEventListener('dragover', (event) => {
    event.preventDefault();
    drop.classList.add('over');
  });
  drop.addEventListener('dragleave', () => drop.classList.remove('over'));
  drop.addEventListener('drop', (event) => {
    event.preventDefault();
    drop.classList.remove('over');
    void open(event.dataTransfer?.files[0], remember.checked, reload, error);
  });

  const demo = h('button', { class: 'button link', type: 'button' }, 'try it with made-up data');
  demo.addEventListener('click', async () => {
    try {
      reload(await loadDemo());
    } catch (problem) {
      error.textContent = problem instanceof Error ? problem.message : String(problem);
      error.hidden = false;
    }
  });

  return h(
    'main',
    { class: 'landing' },
    h('h1', null, 'trkr'),
    h(
      'p',
      { class: 'lede' },
      'open the snapshot.json that a trkr run writes, and see your portfolio, its history and a projection.',
    ),
    drop,
    h('label', { class: 'check' }, remember, 'remember it on this device'),
    error,
    h(
      'p',
      { class: 'privacy' },
      'the file is read in this browser and never uploaded. this site stores nothing, and the page loads nothing from anywhere else.',
    ),
    demo,
    h(
      'section',
      { class: 'howto' },
      h('h2', null, 'where the file comes from'),
      h(
        'p',
        null,
        'every run of trkr, the scheduled one included, writes snapshot.json into its generation directory, next to report.html. for the scheduled job that is the generation-dir in cfg_bat.yml. past runs are kept in snapshots/.',
      ),
    ),
  );
}
