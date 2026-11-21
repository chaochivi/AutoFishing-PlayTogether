import { useEffect, useState } from "react";
import CodeBlock from "./components/CodeBlock";
import ConfigBuilder from "./components/ConfigBuilder";
import Simulator from "./components/Simulator";
import { Card, Ic, Pill, Section, Tabs } from "./components/ui";
import { cn } from "./utils/cn";

const NAV = [
  ["overview", "Overview"],
  ["platforms", "Platforms"],
  ["how", "How it works"],
  ["prereq", "Prerequisites"],
  ["install", "Installation"],
  ["emulator", "Emulator setup"],
  ["config", "Configuration"],
  ["usage", "Usage"],
  ["classes", "Detection classes"],
  ["flow", "Control flow"],
  ["training", "Training"],
  ["alternatives", "Alternatives"],
  ["troubleshooting", "Troubleshooting"],
  ["structure", "Structure"],
  ["related", "Related"],
  ["disclaimer", "Disclaimer"],
] as const;

const CLASSES: [string, string, string][] = [
  ["exclamation-mark", "Detects fish bites", "🎣"],
  ["store-button", "Detects the Store popup", "🛒"],
  ["too-late-run-away", "Detects missed catches", "💨"],
  ["tool-is-broken", "Detects broken fishing rods", "💥"],
  ["tool-tab", "Detects the inventory tools tab", "🧰"],
  ["repair-button", "Detects the repair action", "🔧"],
  ["paid-repair-button", "Detects paid repair confirmation", "💎"],
  ["paid-repair-text", "Detects paid repair text", "📝"],
  ["repair-done-button", "Detects completed repairs", "✅"],
  ["repair-done-text", "Detects repair completion text", "🏁"],
];

const FAQ: { q: string; a: string[] }[] = [
  {
    q: "Bot cannot detect fish bites",
    a: [
      "Check the detection ROI.",
      "Verify the screen resolution.",
      "Recalibrate coordinates.",
      "Lower the YOLO confidence threshold.",
      "Run preview mode.",
      "Check that the trained model contains the correct classes.",
    ],
  },
  {
    q: "Bot clicks incorrectly",
    a: [
      "Verify emulator resolution.",
      "Check coordinate calibration.",
      "Ensure the correct game window is active.",
      "Check input permissions.",
      "Adjust click delays.",
    ],
  },
  {
    q: "Rod does not repair automatically",
    a: [
      "Verify backpack coordinates.",
      "Check repair button detection.",
      "Verify the inventory layout.",
      "Check allow_paid_repair.",
      "Increase repair_timeout_ms if necessary.",
    ],
  },
  {
    q: "High detection latency",
    a: [
      "Prefer MSS window capture over ADB.",
      "Reduce model.imgsz.",
      "Reduce the detection ROI.",
      "Use GPU inference if supported.",
      "Avoid unnecessary full-screen detection.",
    ],
  },
];

function Accordion() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div className="space-y-2">
      {FAQ.map((f, i) => (
        <div key={f.q} className="overflow-hidden rounded-xl border border-white/10 bg-white/[0.035]">
          <button
            onClick={() => setOpen(open === i ? null : i)}
            className="flex w-full items-center justify-between px-5 py-4 text-left font-semibold text-white"
          >
            🐛 {f.q}
            <span className={cn("text-cyan-300 transition", open === i && "rotate-45")}>+</span>
          </button>
          {open === i && (
            <ul className="space-y-1.5 border-t border-white/5 px-5 py-4 text-sm">
              {f.a.map((x) => (
                <li key={x} className="flex gap-2">
                  <span className="text-cyan-400">▸</span>
                  {x}
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

function Pros({ pros, cons }: { pros: string[]; cons: string[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/5 p-4">
        <div className="mb-2 text-sm font-semibold text-emerald-300">Advantages</div>
        <ul className="space-y-1 text-sm">
          {pros.map((p) => (
            <li key={p}>＋ {p}</li>
          ))}
        </ul>
      </div>
      <div className="rounded-xl border border-rose-400/20 bg-rose-400/5 p-4">
        <div className="mb-2 text-sm font-semibold text-rose-300">Disadvantages</div>
        <ul className="space-y-1 text-sm">
          {cons.map((p) => (
            <li key={p}>－ {p}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function useActive() {
  const [active, setActive] = useState("overview");
  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => e.isIntersecting && setActive(e.target.id));
      },
      { rootMargin: "-20% 0px -70% 0px" }
    );
    NAV.forEach(([id]) => {
      const el = document.getElementById(id);
      if (el) obs.observe(el);
    });
    return () => obs.disconnect();
  }, []);
  return active;
}

const TREE = `Play-Together-Auto-Fishing/
│
├── main.py
├── train.py
├── kaggle_train.ipynb
├── config.yaml
├── requirements.txt
│
├── yolov8n.pt
│
├── models/
│   └── best.pt
│
├── datasets/
│
├── autofishing/
│   ├── cli/
│   ├── bot/
│   ├── detection/
│   ├── capture/
│   ├── input/
│   ├── training/
│   ├── config.py
│   └── constants.py
│
└── src/`;

export default function App() {
  const active = useActive();
  const [menu, setMenu] = useState(false);

  return (
    <div className="min-h-screen">
      {/* top bar */}
      <header className="sticky top-0 z-40 border-b border-white/10 bg-[#04121f]/85 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
          <a href="#top" className="flex items-center gap-2 font-bold text-white">
            <span className="text-xl">🎣</span> Play Together Auto-Fishing
          </a>
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/tannguyen2k1/Play-Together-Auto-Fishing"
              target="_blank"
              rel="noreferrer"
              className="hidden rounded-lg border border-white/15 px-3 py-1.5 text-sm text-white hover:bg-white/10 sm:block"
            >
              ⭐ GitHub
            </a>
            <button className="rounded-lg border border-white/15 px-3 py-1.5 text-sm text-white lg:hidden" onClick={() => setMenu(!menu)}>
              {menu ? "✕" : "☰"}
            </button>
          </div>
        </div>
        {menu && (
          <nav className="grid grid-cols-2 gap-1 border-t border-white/10 bg-[#04121f] p-3 lg:hidden">
            {NAV.map(([id, l]) => (
              <a key={id} href={`#${id}`} onClick={() => setMenu(false)} className="rounded-md px-3 py-2 text-sm text-slate-300 hover:bg-white/10">
                {l}
              </a>
            ))}
          </nav>
        )}
      </header>

      {/* hero */}
      <div id="top" className="relative overflow-hidden border-b border-white/10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(34,211,238,0.22),transparent_60%),radial-gradient(ellipse_at_bottom_right,rgba(59,130,246,0.2),transparent_55%)]" />
        <div className="relative mx-auto max-w-7xl px-4 py-20 text-center sm:py-28">
          <div className="mb-6 text-6xl animate-bob">🎣</div>
          <h1 className="mx-auto max-w-3xl text-4xl font-extrabold tracking-tight text-white sm:text-6xl">
            Play Together <span className="bg-gradient-to-r from-cyan-300 to-blue-400 bg-clip-text text-transparent">Auto-Fishing Bot</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-300">
            A computer vision-based auto-fishing bot supporting Windows PC (Steam) and Android emulators (BlueStacks and LDPlayer). Automate
            fishing, detect fish bites, store catches and repair your rod using Python, OpenCV and YOLOv8.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <a href="#install" className="rounded-xl bg-cyan-400 px-6 py-3 font-semibold text-slate-900 shadow-lg shadow-cyan-500/30 hover:bg-cyan-300">
              Get started
            </a>
            <a href="#flow" className="rounded-xl border border-white/20 px-6 py-3 font-semibold text-white hover:bg-white/10">
              Try the simulator
            </a>
          </div>
          <div className="mt-10 flex flex-wrap justify-center gap-2 text-sm">
            {["Python", "OpenCV", "YOLOv8", "MSS", "PyAutoGUI", "Win32 API"].map((t) => (
              <span key={t} className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-slate-300">
                {t}
              </span>
            ))}
          </div>
          <div className="mx-auto mt-12 flex max-w-3xl flex-wrap items-center justify-center gap-2 font-mono text-xs text-cyan-200 sm:text-sm">
            {["CAST", "WAIT FOR BITE", "REEL", "STORE", "REPAIR", "REPEAT"].map((s, i, a) => (
              <span key={s} className="flex items-center gap-2">
                <span className="rounded-md border border-cyan-400/30 bg-cyan-400/10 px-2.5 py-1">{s}</span>
                {i < a.length - 1 && <span className="text-slate-500">→</span>}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="mx-auto flex max-w-7xl gap-10 px-4">
        {/* sidebar */}
        <aside className="sticky top-14 hidden h-[calc(100vh-3.5rem)] w-52 shrink-0 overflow-y-auto py-8 lg:block">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">Contents</p>
          <nav className="space-y-0.5">
            {NAV.map(([id, l]) => (
              <a
                key={id}
                href={`#${id}`}
                className={cn(
                  "block rounded-md border-l-2 px-3 py-1.5 text-sm transition",
                  active === id ? "border-cyan-400 bg-cyan-400/10 text-cyan-200" : "border-transparent text-slate-400 hover:text-white"
                )}
              >
                {l}
              </a>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1 pb-20">
          <Section id="overview" eyebrow="Overview" title="🎯 What this project does">
            <p>This project automates the fishing mini-game in Play Together using computer vision and input automation. The bot continuously monitors the game screen and automatically:</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                ["❗", "Detects when a fish bites using the exclamation mark (!) indicator."],
                ["🎣", "Reacts to the bite and reels in the fish."],
                ["🛒", "Detects the Store button and saves the catch."],
                ["💥", "Detects when the fishing rod breaks."],
                ["🔧", "Navigates the inventory and repairs the rod."],
                ["🔁", "Repeats the fishing process continuously."],
              ].map(([i, t]) => (
                <Card key={t} className="flex gap-3">
                  <span className="text-2xl">{i}</span>
                  <span className="text-sm">{t}</span>
                </Card>
              ))}
            </div>
            <p>The main goal is a computer vision automation system that handles the complete fishing cycle with minimal manual interaction.</p>
          </Section>

          <Section id="platforms" eyebrow="Compatibility" title="🖥️ Supported platforms">
            <div className="overflow-x-auto rounded-xl border border-white/10">
              <table className="w-full text-left text-sm">
                <thead className="bg-white/5 text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Platform</th>
                    <th className="px-4 py-3">Client / Emulator</th>
                    <th className="px-4 py-3">Capture method</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {[
                    ["Android", "BlueStacks", "MSS window capture / ADB"],
                    ["Android", "LDPlayer", "OpenCV / Win32 API"],
                    ["Windows", "Steam PC Client", "Computer Vision / OCR"],
                  ].map((r) => (
                    <tr key={r[1]}>
                      <td className="px-4 py-3">{r[0]}</td>
                      <td className="px-4 py-3 font-semibold text-white">{r[1]}</td>
                      <td className="px-4 py-3">{r[2]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <Section id="how" eyebrow="Architecture" title="⚙️ How it works">
            <p>The bot combines four main technologies.</p>
            <Tabs
              tabs={[
                { id: "capture", label: "1 · Screen capture" },
                { id: "bite", label: "2 · Bite detection" },
                { id: "input", label: "3 · Input automation" },
                { id: "loop", label: "4 · Automation loop" },
              ]}
              render={(id) => {
                if (id === "capture")
                  return (
                    <div className="grid gap-3 sm:grid-cols-3">
                      {[
                        ["MSS", ["Fast screen capture.", "Recommended for BlueStacks.", "Suitable for real-time detection."]],
                        ["ADB Screencap", ["Captures emulator screenshots.", "Useful for debugging and calibration.", "Generally slower than direct window capture."]],
                        ["Win32 API", ["Supports emulator window interaction.", "Can be used with LDPlayer."]],
                      ].map(([t, l]) => (
                        <Card key={t as string}>
                          <h4 className="mb-2 font-semibold text-white">{t as string}</h4>
                          <ul className="space-y-1 text-sm text-slate-400">
                            {(l as string[]).map((x) => (
                              <li key={x}>• {x}</li>
                            ))}
                          </ul>
                        </Card>
                      ))}
                    </div>
                  );
                if (id === "bite")
                  return (
                    <div className="space-y-4">
                      <p>The bot detects the exclamation mark (!) displayed above the character when a fish bites. Two detection methods are supported.</p>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <Card>
                          <h4 className="mb-2 font-semibold text-white">YOLOv8 object detection</h4>
                          <p className="text-sm text-slate-400">Detects the exclamation mark, Store button, broken rod notification, Repair button and inventory tabs.</p>
                        </Card>
                        <Card>
                          <h4 className="mb-2 font-semibold text-white">OpenCV pixel detection</h4>
                          <p className="text-sm text-slate-400">Monitors a predefined screen region for pixel changes. Lightweight and fast, with no ML model, but more sensitive to resolution and visual changes.</p>
                        </Card>
                      </div>
                    </div>
                  );
                if (id === "input")
                  return (
                    <div className="flex flex-wrap gap-2">
                      <p className="w-full">The bot simulates mouse clicks and keyboard actions using:</p>
                      {["PyAutoGUI", "PyDirectInput", "Win32 API"].map((x) => (
                        <Pill key={x}>{x}</Pill>
                      ))}
                    </div>
                  );
                return (
                  <div className="text-center font-mono text-sm text-cyan-200">
                    CAST → WAIT FOR BITE → REEL → STORE → REPAIR → REPEAT
                  </div>
                );
              }}
            />
          </Section>

          <Section id="prereq" eyebrow="Requirements" title="📦 Prerequisites">
            <div className="grid gap-3 sm:grid-cols-2">
              <Card>
                <h4 className="mb-2 font-semibold text-white">Hardware</h4>
                <ul className="space-y-1 text-sm text-slate-400">
                  <li>• Windows 10 or Windows 11</li>
                  <li>• At least 8 GB RAM recommended</li>
                  <li>• NVIDIA GPU optional for model training</li>
                </ul>
              </Card>
              <Card>
                <h4 className="mb-2 font-semibold text-white">Software</h4>
                <ul className="space-y-1 text-sm text-slate-400">
                  <li>• Python 3.10 or newer</li>
                  <li>• BlueStacks or LDPlayer</li>
                  <li>• Play Together installed</li>
                  <li>• Android SDK Platform Tools (optional)</li>
                </ul>
              </Card>
            </div>
            <p>
              Create a file named <Ic>requirements.txt</Ic>:
            </p>
            <CodeBlock
              lang="txt"
              code={`mss>=9.0.0
numpy>=1.24.0
opencv-python>=4.8.0
pyautogui>=0.9.54
PyGetWindow>=0.0.9
PyYAML>=6.0.0
python-dotenv>=1.0.0
ultralytics
pywin32
Pillow`}
            />
            <CodeBlock code="pip install -r requirements.txt" />
          </Section>

          <Section id="install" eyebrow="Setup" title="🚀 Installation">
            <Tabs
              tabs={[
                { id: "a", label: "A · YOLOv8 (BlueStacks)" },
                { id: "b", label: "B · OpenCV + Win32 (LDPlayer)" },
                { id: "c", label: "C · PC / Steam" },
              ]}
              render={(id) => {
                if (id === "a")
                  return (
                    <div>
                      <p>Uses a trained YOLOv8 model to detect fishing indicators and game UI elements.</p>
                      <h4 className="mt-4 font-semibold text-white">Step 1 — Clone repository</h4>
                      <CodeBlock code={`git clone https://github.com/tannguyen2k1/Play-Together-Auto-Fishing.git\ncd Play-Together-Auto-Fishing`} />
                      <h4 className="font-semibold text-white">Step 2 — Create virtual environment</h4>
                      <CodeBlock code="python -m venv .venv" />
                      <CodeBlock lang="powershell" code=".\.venv\Scripts\Activate.ps1" />
                      <CodeBlock lang="cmd" code=".venv\Scripts\activate.bat" />
                      <h4 className="font-semibold text-white">Step 3 — Install dependencies</h4>
                      <CodeBlock code="pip install -r requirements.txt" />
                      <h4 className="font-semibold text-white">Step 4 — Obtain YOLOv8 weights</h4>
                      <p>
                        Place the trained model at <Ic>models/best.pt</Ic>. Use an available checkpoint or train your own.
                      </p>
                      <h4 className="mt-4 font-semibold text-white">Step 5 — Calibrate coordinates</h4>
                      <CodeBlock code="python main.py --pick" />
                      <p>
                        Calibrate the Cast button, Reel/Jerk button, Store button and Backpack icon, then save the coordinates in <Ic>config.yaml</Ic>.
                      </p>
                      <h4 className="mt-4 font-semibold text-white">Step 6 — Test detection</h4>
                      <CodeBlock code={`python main.py --preview\npython main.py --test path/to/screenshot.png`} />
                    </div>
                  );
                if (id === "b")
                  return (
                    <div>
                      <p>Uses pixel change detection instead of a trained YOLO model.</p>
                      <h4 className="mt-4 font-semibold text-white">Step 1 — Install LDPlayer</h4>
                      <p>Download and install LDPlayer.</p>
                      <h4 className="mt-4 font-semibold text-white">Step 2 — Clone repository</h4>
                      <CodeBlock code={`git clone https://github.com/Uranium1901/Autofishing_Playtogether.git\ncd Autofishing_Playtogether`} />
                      <h4 className="font-semibold text-white">Step 3 — Install dependencies</h4>
                      <CodeBlock code="pip install pywin32 numpy imutils PyAutoGUI scipy Pillow opencv-python" />
                      <h4 className="font-semibold text-white">Step 4 — Configure LDPlayer</h4>
                      <div className="my-3 overflow-x-auto rounded-xl border border-white/10">
                        <table className="w-full text-sm">
                          <tbody className="divide-y divide-white/5">
                            {[
                              ["Resolution", "960 × 540"],
                              ["DPI", "160"],
                              ["Language", "Vietnamese"],
                              ["View", "Highest / Zoomless"],
                            ].map(([k, v]) => (
                              <tr key={k}>
                                <td className="px-4 py-2 text-slate-400">{k}</td>
                                <td className="px-4 py-2 font-mono text-cyan-200">{v}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <h4 className="font-semibold text-white">Step 5 — Start the bot</h4>
                      <CodeBlock code="python Autofishing.py" />
                    </div>
                  );
                return (
                  <div>
                    <p>PTFish is a commercial alternative for the native Windows version. Features may include:</p>
                    <ul className="mt-3 grid gap-1 text-sm sm:grid-cols-2">
                      {["Automatic fishing", "Bite detection", "Store detection", "Gigantic fish support", "Automatic rod repair", "Session statistics", "Adjustable detection regions"].map((f) => (
                        <li key={f}>✓ {f}</li>
                      ))}
                    </ul>
                    <p className="mt-3 text-sm text-slate-400">Check the provider's official page for availability, licensing and compatibility.</p>
                  </div>
                );
              }}
            />
          </Section>

          <Section id="emulator" eyebrow="Setup" title="🎮 Emulator setup">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <h4 className="mb-3 font-semibold text-white">BlueStacks</h4>
                <ol className="list-inside list-decimal space-y-1.5 text-sm text-slate-300">
                  <li>Install BlueStacks.</li>
                  <li>Sign in to Google Play.</li>
                  <li>Install Play Together.</li>
                  <li>Set the resolution to match <Ic>config.yaml</Ic>.</li>
                  <li>Enable the Keymap Overlay if required.</li>
                  <li>Use windowed mode for easier capture.</li>
                  <li>Launch the game and enter a fishing area.</li>
                </ol>
              </Card>
              <Card>
                <h4 className="mb-3 font-semibold text-white">LDPlayer</h4>
                <ol className="list-inside list-decimal space-y-1.5 text-sm text-slate-300">
                  <li>Install LDPlayer.</li>
                  <li>Set resolution to 960 × 540.</li>
                  <li>Set DPI to 160.</li>
                  <li>Change language to Vietnamese if required by pixel detection.</li>
                  <li>Set the game view to maximum.</li>
                  <li>Configure the input mapping.</li>
                  <li>Launch Play Together.</li>
                </ol>
              </Card>
            </div>
          </Section>

          <Section id="config" eyebrow="Settings" title="🔧 Configuration">
            <p>
              The YOLOv8 implementation uses <Ic>config.yaml</Ic> to control detection, screen capture, timing and automation. Tweak the values below and copy the generated file.
            </p>
            <ConfigBuilder />
            <p className="text-sm text-slate-400">
              Set <Ic>allow_paid_repair</Ic> to <Ic>false</Ic> if you do not want the bot to use paid repairs.
            </p>
          </Section>

          <Section id="usage" eyebrow="Run" title="▶️ Usage">
            <p>Activate your virtual environment, then run:</p>
            <CodeBlock lang="powershell" code={`.\\.venv\\Scripts\\Activate.ps1\npython main.py\n# or\npython -m autofishing`} />
            <div className="overflow-x-auto rounded-xl border border-white/10">
              <table className="w-full text-left text-sm">
                <thead className="bg-white/5 text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Command</th>
                    <th className="px-4 py-3">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {[
                    ["python main.py --pick", "Calibrate UI coordinates"],
                    ["python main.py --preview", "Preview screen capture"],
                    ["python main.py --test image.png", "Test detection"],
                    ["python main.py", "Start automatic fishing"],
                  ].map(([c, d]) => (
                    <tr key={c}>
                      <td className="px-4 py-3 font-mono text-cyan-200">{c}</td>
                      <td className="px-4 py-3">{d}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <h4 className="pt-2 font-semibold text-white">Calibration workflow</h4>
            <ol className="grid gap-2 sm:grid-cols-3">
              {["Open Play Together.", "Equip your fishing rod.", "Move to a fishing location.", "Run python main.py --pick.", "Click the required UI elements.", "Save coordinates and start the bot."].map((s, i) => (
                <li key={s} className="flex gap-3 rounded-xl border border-white/10 bg-white/[0.035] p-3 text-sm">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-400/20 text-xs font-bold text-cyan-300">{i + 1}</span>
                  {s}
                </li>
              ))}
            </ol>
          </Section>

          <Section id="classes" eyebrow="Model" title="🔍 Detection classes">
            <p>The YOLOv8 model uses the following detection classes.</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {CLASSES.map(([n, d, i]) => (
                <div key={n} className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.035] p-3 transition hover:border-cyan-400/40">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-400/10 text-xl">{i}</span>
                  <div>
                    <div className="font-mono text-sm font-semibold text-cyan-200">{n}</div>
                    <div className="text-xs text-slate-400">{d}</div>
                  </div>
                </div>
              ))}
            </div>
          </Section>

          <Section id="flow" eyebrow="Interactive" title="🔄 Control flow">
            <p>The bot operates as a finite-state machine. Run the simulator, or force events such as a broken rod or a missed catch.</p>
            <Simulator />
            <div className="grid gap-3 pt-4 sm:grid-cols-2">
              {[
                ["CAST", "Clicks the fishing button. Starts a new fishing attempt."],
                ["WAITING_BITE", "Monitors the detection region, waits for the exclamation mark, checks for broken rod notifications."],
                ["AFTER_CATCH", "Detects the Store popup, confirms the catch, handles missed catches."],
                ["REPAIR", "Opens the backpack, navigates to the tools tab, selects the rod, executes the repair flow."],
                ["COOLDOWN", "Waits for the configured delay, then returns to the casting state."],
              ].map(([t, d]) => (
                <Card key={t}>
                  <div className="font-mono text-sm font-bold text-cyan-300">{t}</div>
                  <p className="mt-1 text-sm text-slate-400">{d}</p>
                </Card>
              ))}
            </div>
            <CodeBlock
              lang="text"
              code={`                  ┌──────────────┐
                  │     CAST     │
                  └──────┬───────┘
                         ▼
                ┌─────────────────┐
                │  WAITING_BITE   │
                └────────┬────────┘
             ┌───────────┼────────────┐
             ▼           ▼            ▼
        Bite Found   Rod Broken   Missed Catch
             ▼           ▼            ▼
          REEL         REPAIR       COOLDOWN
             ▼           │
        AFTER_CATCH      │
             ▼           │
           STORE         │
             └─────┬─────┘
                   ▼
              COOLDOWN
                   ▼
                  CAST`}
            />
          </Section>

          <Section id="training" eyebrow="Machine learning" title="🧠 Training your own model">
            <p>Train a custom YOLOv8 model to improve detection accuracy.</p>
            <h4 className="font-semibold text-white">Step 1 — Prepare dataset</h4>
            <p>
              Download the <Ic>play-together2</Ic> dataset from Roboflow, export it in YOLO format and extract it into <Ic>datasets/</Ic>.
            </p>
            <h4 className="font-semibold text-white">Step 2 — Train the model</h4>
            <CodeBlock code="python train.py" />
            <p className="text-sm text-slate-400">You can also use a GPU environment such as Kaggle for faster training.</p>
            <h4 className="font-semibold text-white">Step 3 — Deploy the model</h4>
            <CodeBlock lang="cmd" code="copy path\to\best.pt models\best.pt" />
            <h4 className="font-semibold text-white">Step 4 — Validate detection</h4>
            <CodeBlock lang="cmd" code="python main.py --test path\to\screenshot.png" />
            <p>Check the results before running the automation loop.</p>
          </Section>

          <Section id="alternatives" eyebrow="Other ideas" title="🛠️ Alternative approaches">
            <Tabs
              tabs={[
                { id: "tm", label: "Template matching" },
                { id: "px", label: "Pixel change" },
                { id: "au", label: "Audio" },
                { id: "hsv", label: "HSV color" },
              ]}
              render={(id) => {
                if (id === "tm")
                  return (
                    <div>
                      <p>Template matching can detect the exclamation mark without machine learning.</p>
                      <CodeBlock
                        lang="python"
                        code={`import cv2
import numpy as np

template = cv2.imread("exclamation_mark_template.png", 0)
screenshot = cv2.imread("screenshot.png", 0)

result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

threshold = 0.8
locations = np.where(result >= threshold)`}
                      />
                      <Pros pros={["No model training", "Easy to implement", "Lightweight"]} cons={["Sensitive to resolution changes", "Sensitive to scaling and animation"]} />
                    </div>
                  );
                if (id === "px")
                  return (
                    <div className="space-y-3">
                      <p>Monitors a specific region for changes in pixel values.</p>
                      <Pros pros={["Very fast", "Low CPU usage", "No GPU required"]} cons={["Requires precise calibration", "Can produce false detections"]} />
                    </div>
                  );
                if (id === "au")
                  return (
                    <div className="space-y-3">
                      <p>Audio processing can identify fishing sounds or splash effects. Audio detection can complement visual detection.</p>
                      <div className="flex flex-wrap gap-2">
                        {["VB-Cable", "Python audio capture", "NumPy", "SciPy"].map((x) => (
                          <Pill key={x}>{x}</Pill>
                        ))}
                      </div>
                    </div>
                  );
                return (
                  <div className="space-y-3">
                    <p>OpenCV HSV filtering can identify UI elements based on color. Potential applications:</p>
                    <div className="flex flex-wrap gap-2">
                      {["Exclamation mark detection", "Fishing bar detection", "Fish shadow detection"].map((x) => (
                        <Pill key={x} tone="emerald">{x}</Pill>
                      ))}
                    </div>
                  </div>
                );
              }}
            />
          </Section>

          <Section id="troubleshooting" eyebrow="Help" title="🐛 Troubleshooting">
            <Accordion />
          </Section>

          <Section id="structure" eyebrow="Layout" title="📁 Project structure">
            <p>Example structure for the YOLOv8 implementation:</p>
            <CodeBlock lang="text" code={TREE} />
          </Section>

          <Section id="related" eyebrow="Ecosystem" title="🔗 Related projects">
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                ["Play-Together-Auto-Fishing", "YOLOv8 + MSS + PyAutoGUI", "BlueStacks", "https://github.com/tannguyen2k1/Play-Together-Auto-Fishing"],
                ["Autofishing_Playtogether", "OpenCV + Win32 API", "LDPlayer", "https://github.com/Uranium1901/Autofishing_Playtogether"],
                ["PTFish", "Computer Vision + OCR", "Windows / Steam", ""],
              ].map(([n, a, p, u]) => {
                const inner = (
                  <>
                    <div className="font-semibold text-white">{n}</div>
                    <div className="mt-2 text-sm text-slate-400">{a}</div>
                    <div className="mt-3"><Pill>{p}</Pill></div>
                  </>
                );
                return u ? (
                  <a key={n} href={u} target="_blank" rel="noreferrer" className="rounded-2xl border border-white/10 bg-white/[0.035] p-5 transition hover:border-cyan-400/50">
                    {inner}
                  </a>
                ) : (
                  <div key={n} className="rounded-2xl border border-white/10 bg-white/[0.035] p-5">{inner}</div>
                );
              })}
            </div>
          </Section>

          <Section id="disclaimer" eyebrow="Important" title="⚠️ Disclaimer">
            <div className="rounded-2xl border border-amber-400/30 bg-amber-400/5 p-6">
              <p>This project is intended for educational and personal research purposes.</p>
              <p className="mt-2">Automating online games may violate the game's Terms of Service and could result in account restrictions or bans.</p>
              <ul className="mt-3 space-y-1 text-sm">
                <li>• Use automation at your own risk.</li>
                <li>• Always review the game's Terms of Service.</li>
                <li>• Do not use automation to disrupt other players.</li>
                <li>• This project is not affiliated with Play Together, BlueStacks, or LDPlayer.</li>
              </ul>
              <p className="mt-3 text-sm text-slate-400">
                The primary purpose is to demonstrate computer vision, object detection, Python automation and real-time image processing.
              </p>
            </div>
            <h3 className="pt-6 text-lg font-semibold text-white">📚 Additional resources</h3>
            <div className="flex flex-wrap gap-2">
              {[
                ["Play Together Wiki", "https://playtogether.fandom.com/"],
                ["YOLO Docs", "https://docs.ultralytics.com/"],
                ["OpenCV Docs", "https://docs.opencv.org/"],
                ["MSS Docs", "https://python-mss.readthedocs.io/"],
                ["Roboflow", "https://roboflow.com/"],
              ].map(([n, u]) => (
                <a key={n} href={u} target="_blank" rel="noreferrer" className="rounded-lg border border-white/15 px-3 py-1.5 text-sm text-cyan-200 hover:bg-white/10">
                  {n} ↗
                </a>
              ))}
            </div>
          </Section>
        </main>
      </div>

      <footer className="border-t border-white/10 py-10 text-center text-sm text-slate-500">
        <div className="text-2xl">🎣</div>
        <p className="mt-2 text-slate-300">Happy fishing! If you find this project useful, consider giving it a ⭐ on GitHub.</p>
        <p className="mt-1">Python · OpenCV · YOLOv8 · MSS · PyAutoGUI · Win32 API · Computer Vision</p>
      </footer>
    </div>
  );
}
