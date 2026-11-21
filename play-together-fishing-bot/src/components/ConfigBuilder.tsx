import { useMemo, useState } from "react";
import CodeBlock from "./CodeBlock";
import { cn } from "../utils/cn";

type Cfg = {
  confidence: number;
  imgsz: number;
  cast_delay_ms: number;
  cooldown: number;
  after_catch_timeout: number;
  paid: boolean;
  auto_cast: boolean;
  mode: "tap" | "hold" | "key";
  cast_x: number;
  cast_y: number;
  reel_x: number;
  reel_y: number;
  store_x: number;
  store_y: number;
  bag_x: number;
  bag_y: number;
};

const DEFAULT: Cfg = {
  confidence: 0.4,
  imgsz: 256,
  cast_delay_ms: 400,
  cooldown: 1200,
  after_catch_timeout: 12000,
  paid: true,
  auto_cast: true,
  mode: "tap",
  cast_x: 1268,
  cast_y: 541,
  reel_x: 1405,
  reel_y: 695,
  store_x: 1153,
  store_y: 600,
  bag_x: 1537,
  bag_y: 500,
};

function Slider({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (n: number) => void;
}) {
  return (
    <label className="block text-sm">
      <div className="mb-1 flex justify-between text-slate-300">
        <span>{label}</span>
        <span className="font-mono text-cyan-300">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-cyan-400"
      />
    </label>
  );
}

function Num({ label, value, onChange }: { label: string; value: number; onChange: (n: number) => void }) {
  return (
    <label className="block text-xs text-slate-400">
      {label}
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-1 w-full rounded-md border border-white/10 bg-white/5 px-2 py-1.5 font-mono text-sm text-white outline-none focus:border-cyan-400"
      />
    </label>
  );
}

function Toggle({ label, value, onChange }: { label: string; value: boolean; onChange: (b: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!value)}
      className="flex w-full items-center justify-between rounded-lg border border-white/10 px-3 py-2 text-sm text-slate-300 hover:bg-white/5"
    >
      <span className="font-mono">{label}</span>
      <span className={cn("h-5 w-9 rounded-full p-0.5 transition", value ? "bg-cyan-400" : "bg-slate-600")}>
        <span className={cn("block h-4 w-4 rounded-full bg-white transition", value && "translate-x-4")} />
      </span>
    </button>
  );
}

export default function ConfigBuilder() {
  const [c, setC] = useState<Cfg>(DEFAULT);
  const set = <K extends keyof Cfg>(k: K, v: Cfg[K]) => setC((p) => ({ ...p, [k]: v }));

  const yaml = useMemo(
    () => `backend: window

capture:
  image_width: 1600
  image_height: 900
  top: 50
  left: 850
  width: 500
  height: 400

model:
  path: "models/best.pt"
  confidence: ${c.confidence.toFixed(2)}
  imgsz: ${c.imgsz}
  bite_classes:
    - "exclamation-mark"

bot:
  poll_interval_ms: 0
  click_delay_ms: 0
  cast_delay_ms: ${c.cast_delay_ms}
  after_catch_min_ms: 300
  after_catch_timeout_ms: ${c.after_catch_timeout}
  cooldown_after_bite_ms: ${c.cooldown}
  min_wait_before_bite_ms: 0

allow_paid_repair: ${c.paid}
repair_timeout_ms: 25000
repair_click_gap_ms: 700
bag_x: ${c.bag_x}
bag_y: ${c.bag_y}

ui_imgsz: 416
ui_confidence: 0.35
auto_cast: ${c.auto_cast}

cast_mode: ${c.mode === "key" ? "tap" : c.mode}
jerk_mode: ${c.mode === "key" ? "tap" : c.mode}
store_mode: ${c.mode === "key" ? "tap" : c.mode}
action_mode: ${c.mode}
action_key: space

cast_x: ${c.cast_x}
cast_y: ${c.cast_y}
reel_x: ${c.reel_x}
reel_y: ${c.reel_y}
store_x: ${c.store_x}
store_y: ${c.store_y}
`,
    [c]
  );

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="space-y-5 rounded-2xl border border-white/10 bg-white/[0.035] p-5">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-white">Interactive config.yaml builder</h3>
          <button onClick={() => setC(DEFAULT)} className="text-xs text-slate-400 hover:text-white">
            Reset defaults
          </button>
        </div>
        <Slider label="model.confidence" value={c.confidence} min={0.1} max={0.95} step={0.05} onChange={(v) => set("confidence", Number(v.toFixed(2)))} />
        <Slider label="model.imgsz" value={c.imgsz} min={128} max={640} step={32} onChange={(v) => set("imgsz", v)} />
        <Slider label="bot.cast_delay_ms" value={c.cast_delay_ms} min={0} max={2000} step={50} onChange={(v) => set("cast_delay_ms", v)} />
        <Slider label="bot.cooldown_after_bite_ms" value={c.cooldown} min={0} max={5000} step={100} onChange={(v) => set("cooldown", v)} />
        <Slider label="bot.after_catch_timeout_ms" value={c.after_catch_timeout} min={2000} max={30000} step={500} onChange={(v) => set("after_catch_timeout", v)} />
        <div className="grid gap-2 sm:grid-cols-2">
          <Toggle label="allow_paid_repair" value={c.paid} onChange={(v) => set("paid", v)} />
          <Toggle label="auto_cast" value={c.auto_cast} onChange={(v) => set("auto_cast", v)} />
        </div>
        <div>
          <div className="mb-1 text-xs text-slate-400">Input mode</div>
          <div className="flex gap-2">
            {(["tap", "hold", "key"] as const).map((m) => (
              <button
                key={m}
                onClick={() => set("mode", m)}
                className={cn(
                  "rounded-md border px-3 py-1 text-sm",
                  c.mode === m ? "border-cyan-400 bg-cyan-400/15 text-cyan-200" : "border-white/10 text-slate-400"
                )}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-4 gap-2">
          <Num label="cast_x" value={c.cast_x} onChange={(v) => set("cast_x", v)} />
          <Num label="cast_y" value={c.cast_y} onChange={(v) => set("cast_y", v)} />
          <Num label="reel_x" value={c.reel_x} onChange={(v) => set("reel_x", v)} />
          <Num label="reel_y" value={c.reel_y} onChange={(v) => set("reel_y", v)} />
          <Num label="store_x" value={c.store_x} onChange={(v) => set("store_x", v)} />
          <Num label="store_y" value={c.store_y} onChange={(v) => set("store_y", v)} />
          <Num label="bag_x" value={c.bag_x} onChange={(v) => set("bag_x", v)} />
          <Num label="bag_y" value={c.bag_y} onChange={(v) => set("bag_y", v)} />
        </div>
        <p className="text-xs text-amber-300/80">
          ⚠ Coordinates are examples for a 1600×900 logical resolution — recalibrate with{" "}
          <code className="font-mono">python main.py --pick</code>.
        </p>
      </div>
      <div className="min-w-0">
        <CodeBlock code={yaml} lang="yaml" />
      </div>
    </div>
  );
}
