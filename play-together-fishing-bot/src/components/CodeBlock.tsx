import { useState } from "react";

export default function CodeBlock({
  code,
  lang = "bash",
}: {
  code: string;
  lang?: string;
}) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code);
    } catch {
      /* ignore */
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  };
  return (
    <div className="group relative my-4 overflow-hidden rounded-xl border border-white/10 bg-[#030b14]">
      <div className="flex items-center justify-between border-b border-white/5 bg-white/[0.03] px-4 py-1.5 text-xs">
        <span className="font-mono uppercase tracking-wider text-sky-300/70">{lang}</span>
        <button
          onClick={copy}
          className="rounded-md px-2 py-0.5 text-slate-400 transition hover:bg-white/10 hover:text-white"
        >
          {copied ? "✓ Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-[13px] leading-relaxed text-sky-100">
        <code className="font-mono">{code}</code>
      </pre>
    </div>
  );
}
