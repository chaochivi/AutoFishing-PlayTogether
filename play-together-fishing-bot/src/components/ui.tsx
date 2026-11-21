import type { ReactNode } from "react";
import { cn } from "../utils/cn";

export function Section({
  id,
  eyebrow,
  title,
  children,
}: {
  id: string;
  eyebrow?: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className="py-14">
      {eyebrow && (
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">
          {eyebrow}
        </p>
      )}
      <h2 className="mb-6 text-3xl font-bold tracking-tight text-white">{title}</h2>
      <div className="space-y-4 leading-relaxed text-slate-300">{children}</div>
    </section>
  );
}

export function Card({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/10 bg-white/[0.035] p-5 backdrop-blur",
        className
      )}
    >
      {children}
    </div>
  );
}

export function Tabs({
  tabs,
  render,
}: {
  tabs: { id: string; label: string }[];
  render: (id: string) => ReactNode;
}) {
  return <TabsInner tabs={tabs} render={render} />;
}

import { useState } from "react";
function TabsInner({
  tabs,
  render,
}: {
  tabs: { id: string; label: string }[];
  render: (id: string) => ReactNode;
}) {
  const [active, setActive] = useState(tabs[0].id);
  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActive(t.id)}
            className={cn(
              "rounded-full border px-4 py-1.5 text-sm font-medium transition",
              active === t.id
                ? "border-cyan-400 bg-cyan-400/15 text-cyan-200"
                : "border-white/10 text-slate-400 hover:border-white/30 hover:text-white"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div>{render(active)}</div>
    </div>
  );
}

export function Pill({ children, tone = "cyan" }: { children: ReactNode; tone?: "cyan" | "amber" | "rose" | "emerald" }) {
  const tones = {
    cyan: "bg-cyan-400/10 text-cyan-300 border-cyan-400/30",
    amber: "bg-amber-400/10 text-amber-300 border-amber-400/30",
    rose: "bg-rose-400/10 text-rose-300 border-rose-400/30",
    emerald: "bg-emerald-400/10 text-emerald-300 border-emerald-400/30",
  };
  return (
    <span className={cn("inline-block rounded-full border px-2.5 py-0.5 text-xs font-medium", tones[tone])}>
      {children}
    </span>
  );
}

export function Ic({ children }: { children: ReactNode }) {
  return (
    <code className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[0.85em] text-cyan-200">
      {children}
    </code>
  );
}
