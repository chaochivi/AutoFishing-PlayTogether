const FILES = [
  {
    name: "phase-2a-paid-repair-safety.patch",
    href: "./phase-2a/phase-2a-paid-repair-safety.patch",
    how: "git checkout -b phase-2a-paid-repair-safety && git am --keep-cr phase-2a-paid-repair-safety.patch",
    note: "Commit-style patch. --keep-cr is REQUIRED (README.md has CRLF line endings).",
  },
  {
    name: "phase-2a-paid-repair-safety.diff",
    href: "./phase-2a/phase-2a-paid-repair-safety.diff",
    how: "git checkout -b phase-2a-paid-repair-safety && git apply phase-2a-paid-repair-safety.diff",
    note: "Plain diff against main (5e28a2d). Works with git apply; you commit it yourself.",
  },
  {
    name: "phase-2a-changed-files.zip",
    href: "./phase-2a/phase-2a-changed-files.zip",
    how: "unzip over the repository root",
    note: "Full contents of all 12 changed/new files, with repository paths.",
  },
  {
    name: "test-results.txt",
    href: "./phase-2a/test-results.txt",
    how: "",
    note: "Verbatim pytest -v output (219 passed) from a fresh clone with the patch applied.",
  },
];

const CHANGES = [
  ["config", "allow_paid_repair now defaults to false in code (config.py) and in config.yaml. Setting it to true is kept as a value but ignored, with a warning at config load and at bot start."],
  ["safety.py (new)", "Pure-Python module: dialog classifier (PAID / DONE / FREE / TAB / UNKNOWN), click-intent policy, and RepairGuardMixin. allow_paid_repair is never read here."],
  ["Paid dialogs", "Any paid-repair-button / paid-repair-text detection, at any confidence, classifies the dialog as PAID. The bot stops without clicking anything (no blind close-tap on top of a paid dialog)."],
  ["UNKNOWN / ambiguous", "Nothing recognised, low-confidence, or flickering evidence is never clicked. The blind 'retap backpack every 6 idle polls' was removed. A timeout on ambiguous evidence stops the bot."],
  ["Free repair evidence", "Repair button must be at or above repair_min_confidence (0.50) on at least 2 consecutive fresh frames at the same position, re-checked immediately before the click. The minimum of 2 is enforced in code, not just config."],
  ["DesktopInput + AdbInput", "Both use the same mixin. PAID_REPAIR_CONFIRM / UNKNOWN_DIALOG intents and any click whose target is a paid class are refused. Inside a repair session, unlabelled clicks and non-cancel keys (space/enter) are refused too."],
  ["Fail closed", "If the input backend lacks the guard, the bot refuses to start a repair. Sessions are closed in a finally block."],
  ["Tests + docs", "tests/ (219 tests, every input test runs on both backends), pytest.ini, requirements-dev.txt, README repair section."],
];

const RISKS = [
  "The model has no explicit 'free repair' class. 'Free' is inferred from a confident repair-button with no paid evidence. If the paid dialog is missed by the detector (below ui_confidence 0.35, or untrained), a paid dialog can look like an unrecognised screen, which is blocked, but it cannot be positively proven free.",
  "The input layer cannot see pixels. It blocks paid intents and paid-class targets, but a paid button that the detector reports under a non-paid class name is only caught by classification and the pre-click re-check, not by the guard alone.",
  "Raising repair_min_confidence above what your YOLO weights output for repair-button will make free repair stop being automated. Tune it with --preview.",
  "The repo's root play-together-fishing-bot.zip is a stale bundle and was not regenerated.",
];

function Download({ f }: { f: (typeof FILES)[number] }) {
  return (
    <a
      href={f.href}
      download
      className="block rounded-xl border border-slate-200 bg-white p-4 transition hover:border-indigo-400 hover:shadow-md"
    >
      <div className="flex items-center justify-between gap-3">
        <span className="font-mono text-sm font-semibold text-indigo-700 break-all">{f.name}</span>
        <span className="shrink-0 rounded-md bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700">Download</span>
      </div>
      <p className="mt-1 text-sm text-slate-600">{f.note}</p>
      {f.how && (
        <code className="mt-2 block overflow-x-auto rounded-md bg-slate-900 px-3 py-2 text-xs text-emerald-300">{f.how}</code>
      )}
    </a>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-4xl px-6 py-8">
          <p className="text-sm font-medium text-indigo-600">chaochivi/AutoFishing-PlayTogether · play-together-fishing-bot/</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">Phase 2A – Paid-repair safety</h1>
          <p className="mt-2 text-slate-600">Implementation report and downloadable patch.</p>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-8 px-6 py-8">
        <section className="rounded-xl border-2 border-red-300 bg-red-50 p-5">
          <h2 className="text-lg font-bold text-red-800">Not delivered to GitHub: write access unavailable</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-red-900">
            <li>This environment has no GitHub credentials (no token, SSH key, credential helper or <code>gh</code> CLI).</li>
            <li>
              A <code>git push --dry-run</code> to the repository failed with{" "}
              <code>could not read Username for 'https://github.com'</code>.
            </li>
            <li>
              The branch <code>phase-2a-paid-repair-safety</code> was <b>not</b> pushed, <b>no commit exists on GitHub</b>, and there
              is no branch URL or GitHub commit hash. <code>main</code> was not touched.
            </li>
            <li>
              The work was done in a local sandbox clone. Its local-only commit (<code>8a1fdf8</code>) is not on GitHub, and its hash
              will differ once you commit or <code>am</code> the patch yourself.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-bold">Download the patch</h2>
          <div className="grid gap-3">
            {FILES.map((f) => (
              <Download key={f.name} f={f} />
            ))}
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Base: <code>main</code> at <code>5e28a2d</code>. Both the <code>.patch</code> (with <code>--keep-cr</code>) and the{" "}
            <code>.diff</code> were applied to fresh clones of that commit and the suite re-run there.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-bold">Test results (actually executed)</h2>
          <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-5">
            <p className="text-2xl font-bold text-emerald-800">219 passed, 0 failed, 0 errors</p>
            <p className="font-mono text-sm text-emerald-900">python -m pytest · 13.3 s · Python 3.11.2 · pytest 9.2.0 · Linux sandbox</p>
            <table className="mt-3 w-full text-left text-sm">
              <thead className="text-emerald-900">
                <tr><th className="py-1">File</th><th>Tests</th><th>Covers</th></tr>
              </thead>
              <tbody className="text-emerald-950">
                <tr><td className="py-1 font-mono">test_safety_policy.py</td><td>79</td><td>classifier, click/key policy, config defaults</td></tr>
                <tr><td className="py-1 font-mono">test_input_guard.py</td><td>74</td><td>DesktopInput + AdbInput enforcement</td></tr>
                <tr><td className="py-1 font-mono">test_repair_flow.py</td><td>66</td><td>full bot repair flow on both backends</td></tr>
              </tbody>
            </table>
            <p className="mt-3 text-sm text-emerald-900">
              <b>Mutation check:</b> 8 deliberate regressions (paid intent allowed, paid-target check removed, default flipped to true,
              shipped config true, confidence threshold ignored, re-check disabled, Adb guard removed, Desktop guard removed) were each
              caught by the suite; the code was restored and the suite re-run green.
            </p>
          </div>
        </section>

        <section className="rounded-xl border-2 border-amber-300 bg-amber-50 p-5">
          <h2 className="text-lg font-bold text-amber-900">What was NOT tested</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-950">
            <li><b>No Windows run of any kind.</b> No Windows runtime result is claimed.</li>
            <li>Real PyAutoGUI / PyDirectInput: replaced with a recording fake. The real <code>DesktopInput</code> code ran, the OS call did not.</li>
            <li>Real ADB / emulator: <code>subprocess.run</code> was replaced with a recorder; no <code>adb</code> binary was invoked.</li>
            <li>Real YOLO / OpenCV detection and the real game UI. Screens were scripted. <code>cv2</code>, <code>numpy</code> and <code>pyautogui</code> were not installed.</li>
            <li>CLI entry (<code>main.py</code>, <code>--dry-run</code>) was reviewed but not executed.</li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-bold">Change summary</h2>
          <dl className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
            {CHANGES.map(([k, v]) => (
              <div key={k} className="grid gap-1 p-4 sm:grid-cols-[11rem_1fr]">
                <dt className="font-mono text-sm font-semibold text-indigo-700">{k}</dt>
                <dd className="text-sm text-slate-700">{v}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-bold">Behaviour changes and residual risks</h2>
          <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
            {RISKS.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </section>

        <footer className="pb-8 text-sm text-slate-500">Stopped after Phase 2A as requested.</footer>
      </main>
    </div>
  );
}
