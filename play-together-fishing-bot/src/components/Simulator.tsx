import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "../utils/cn";

type S = "CAST" | "WAITING_BITE" | "REEL" | "AFTER_CATCH" | "STORE" | "REPAIR" | "COOLDOWN";

const STATES: { id: S; desc: string; icon: string }[] = [
  { id: "CAST", desc: "Clicks the fishing button", icon: "🎯" },
  { id: "WAITING_BITE", desc: "Watches for the ! mark", icon: "👀" },
  { id: "REEL", desc: "Taps the jerk / reel button", icon: "🎣" },
  { id: "AFTER_CATCH", desc: "Looks for the Store popup", icon: "🔍" },
  { id: "STORE", desc: "Confirms and stores the catch", icon: "🐟" },
  { id: "REPAIR", desc: "Backpack → tools → repair", icon: "🔧" },
  { id: "COOLDOWN", desc: "Waits, then recasts", icon: "⏳" },
];

const DETECTION: Record<S, { label: string; conf: string } | null> = {
  CAST: null,
  WAITING_BITE: null,
  REEL: { label: "exclamation-mark", conf: "0.93" },
  AFTER_CATCH: { label: "store-button", conf: "0.88" },
  STORE: { label: "store-button", conf: "0.91" },
  REPAIR: { label: "tool-is-broken", conf: "0.86" },
  COOLDOWN: null,
};

export default function Simulator() {
  const [state, setState] = useState<S>("CAST");
  const [log, setLog] = useState<string[]>(["Bot idle. Press Auto-run or step manually."]);
  const [stats, setStats] = useState({ catches: 0, repairs: 0, missed: 0 });
  const [auto, setAuto] = useState(false);
  const stateRef = useRef<S>(state);
  stateRef.current = state;

  const push = (m: string) => setLog((l) => [m, ...l].slice(0, 8));

  const go = useCallback((to: S, msg: string) => {
    setState(to);
    setLog((l) => [`${stateRef.current} → ${to}: ${msg}`, ...l].slice(0, 8));
  }, []);

  const step = useCallback(
    (force?: "bite" | "broken" | "missed") => {
      const s = stateRef.current;
      switch (s) {
        case "CAST":
          return go("WAITING_BITE", "line cast, polling detection region");
        case "WAITING_BITE": {
          const r = Math.random();
          const ev = force ?? (r < 0.7 ? "bite" : r < 0.85 ? "broken" : "missed");
          if (ev === "bite") return go("REEL", "exclamation-mark detected!");
          if (ev === "broken") {
            setStats((x) => ({ ...x, repairs: x.repairs + 1 }));
            return go("REPAIR", "tool-is-broken detected");
          }
          setStats((x) => ({ ...x, missed: x.missed + 1 }));
          return go("COOLDOWN", "too-late-run-away detected");
        }
        case "REEL":
          return go("AFTER_CATCH", "reel tapped, waiting for popup");
        case "AFTER_CATCH":
          if (force === "missed") {
            setStats((x) => ({ ...x, missed: x.missed + 1 }));
            return go("COOLDOWN", "fish escaped");
          }
          return go("STORE", "store-button found");
        case "STORE":
          setStats((x) => ({ ...x, catches: x.catches + 1 }));
          return go("COOLDOWN", "catch stored ✔");
        case "REPAIR":
          return go("COOLDOWN", "rod repaired");
        case "COOLDOWN":
          return go("CAST", "cooldown elapsed");
      }
    },
    [go]
  );

  useEffect(() => {
    if (!auto) return;
    const t = setInterval(() => step(), 900);
    return () => clearInterval(t);
  }, [auto, step]);

  const reset = () => {
    setAuto(false);
    setState("CAST");
    setStats({ catches: 0, repairs: 0, missed: 0 });
    setLog(["Reset."]);
  };

  const det = DETECTION[state];
  const bite = state === "REEL";

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      {/* game frame */}
      <div className="lg:col-span-2">
        <div className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-sky-300 via-sky-500 to-blue-900">
          <div className="absolute inset-x-0 top-[38%] bottom-0 bg-gradient-to-b from-cyan-500/70 to-blue-950" />
          <div className="absolute top-[38%] left-0 flex h-6 w-[200%] animate-wave opacity-60">
            {Array.from({ length: 20 }).map((_, i) => (
              <div key={i} className="mx-2 mt-1 h-3 w-[5%] rounded-full bg-white/40" />
            ))}
          </div>
          <div className="absolute left-6 top-[20%] text-5xl">🧍</div>
          <div className="absolute left-[22%] top-[26%] h-px w-[34%] origin-left rotate-[18deg] bg-white/70" />
          <div
            className={cn(
              "absolute left-[54%] top-[48%] text-3xl",
              state === "WAITING_BITE" || state === "REEL" ? "animate-bob" : ""
            )}
          >
            {state === "CAST" || state === "COOLDOWN" ? "" : "🔴"}
          </div>
          {bite && (
            <div className="animate-bang absolute left-[6%] top-[2%] flex flex-col items-center">
              <div className="rounded-md border-2 border-lime-400 px-2 text-3xl font-black text-red-500 drop-shadow">
                !
              </div>
              <span className="mt-0.5 rounded bg-lime-400 px-1 text-[10px] font-bold text-black">
                exclamation-mark 0.93
              </span>
            </div>
          )}
          {(state === "AFTER_CATCH" || state === "STORE") && (
            <div className="absolute inset-x-8 bottom-6 rounded-xl border-2 border-lime-400 bg-white/90 p-2 text-center text-sm font-semibold text-slate-800">
              🐟 You caught a fish!
              <div className="mt-1 rounded-lg bg-emerald-500 py-1 text-white">Store</div>
              <span className="absolute -top-3 left-2 rounded bg-lime-400 px-1 text-[10px] font-bold text-black">
                store-button {det?.conf}
              </span>
            </div>
          )}
          {state === "REPAIR" && (
            <div className="absolute inset-x-8 top-10 rounded-xl border-2 border-lime-400 bg-white/90 p-3 text-center text-sm font-semibold text-slate-800">
              💥 Your fishing rod is broken!
              <span className="absolute -top-3 left-2 rounded bg-lime-400 px-1 text-[10px] font-bold text-black">
                tool-is-broken {det?.conf}
              </span>
            </div>
          )}
          <div className="absolute bottom-2 right-2 rounded-full bg-black/50 px-2 py-0.5 font-mono text-[10px] text-white">
            capture 500×400 · imgsz 256
          </div>
        </div>
        <div className="mt-3 grid grid-cols-3 gap-2 text-center">
          {[
            ["Catches", stats.catches, "text-emerald-300"],
            ["Repairs", stats.repairs, "text-amber-300"],
            ["Missed", stats.missed, "text-rose-300"],
          ].map(([l, v, c]) => (
            <div key={l as string} className="rounded-xl border border-white/10 bg-white/[0.035] py-2">
              <div className={cn("text-2xl font-bold", c as string)}>{v}</div>
              <div className="text-xs text-slate-400">{l}</div>
            </div>
          ))}
        </div>
      </div>

      {/* state machine */}
      <div className="lg:col-span-3">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {STATES.map((s) => (
            <div
              key={s.id}
              className={cn(
                "rounded-xl border p-3 transition-all",
                state === s.id
                  ? "scale-[1.03] border-cyan-400 bg-cyan-400/15 shadow-lg shadow-cyan-500/20"
                  : "border-white/10 bg-white/[0.03] opacity-70"
              )}
            >
              <div className="text-xl">{s.icon}</div>
              <div className="font-mono text-[11px] font-bold text-white">{s.id}</div>
              <div className="mt-0.5 text-[11px] leading-snug text-slate-400">{s.desc}</div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={() => setAuto((a) => !a)}
            className={cn(
              "rounded-lg px-4 py-2 text-sm font-semibold transition",
              auto ? "bg-rose-500 text-white hover:bg-rose-400" : "bg-cyan-400 text-slate-900 hover:bg-cyan-300"
            )}
          >
            {auto ? "■ Stop" : "▶ Auto-run"}
          </button>
          <button onClick={() => step()} className="rounded-lg border border-white/15 px-4 py-2 text-sm text-white hover:bg-white/10">
            Step
          </button>
          <button
            onClick={() => state === "WAITING_BITE" ? step("broken") : push("Only available while WAITING_BITE")}
            className="rounded-lg border border-amber-400/40 px-3 py-2 text-sm text-amber-300 hover:bg-amber-400/10"
          >
            Break rod
          </button>
          <button
            onClick={() =>
              state === "WAITING_BITE" || state === "AFTER_CATCH"
                ? step("missed")
                : push("Only available while WAITING_BITE / AFTER_CATCH")
            }
            className="rounded-lg border border-rose-400/40 px-3 py-2 text-sm text-rose-300 hover:bg-rose-400/10"
          >
            Miss catch
          </button>
          <button
            onClick={() => state === "WAITING_BITE" ? step("bite") : push("Only available while WAITING_BITE")}
            className="rounded-lg border border-emerald-400/40 px-3 py-2 text-sm text-emerald-300 hover:bg-emerald-400/10"
          >
            Trigger bite
          </button>
          <button onClick={reset} className="ml-auto rounded-lg px-3 py-2 text-sm text-slate-400 hover:text-white">
            Reset
          </button>
        </div>

        <div className="mt-4 rounded-xl border border-white/10 bg-[#030b14] p-3 font-mono text-xs">
          {log.map((l, i) => (
            <div key={i} className={i === 0 ? "text-cyan-200" : "text-slate-500"}>
              {i === 0 ? "▸ " : "  "}
              {l}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
