"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Renders LLM chat output as real formatted markdown — headings, bold text,
 * lists, and GFM tables (remark-gfm) — instead of raw "## Heading" text.
 * Styled to fit inside the existing dark chat bubbles via Tailwind, without
 * pulling in @tailwindcss/typography (kept to core utility classes per the
 * project's styling constraints).
 */
export default function MarkdownMessage({ content }: { content: string }) {
  return (
    <div className="text-sm leading-relaxed [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: (props) => <h3 className="font-display text-base font-semibold mt-3 mb-1" {...props} />,
          h2: (props) => <h3 className="font-display text-base font-semibold mt-3 mb-1" {...props} />,
          h3: (props) => <h4 className="font-display text-sm font-semibold mt-2 mb-1" {...props} />,
          p: (props) => <p className="mb-2" {...props} />,
          ul: (props) => <ul className="list-disc pl-5 mb-2 space-y-0.5" {...props} />,
          ol: (props) => <ol className="list-decimal pl-5 mb-2 space-y-0.5" {...props} />,
          li: (props) => <li {...props} />,
          strong: (props) => <strong className="font-semibold" {...props} />,
          code: (props) => (
            <code className="bg-black/30 rounded px-1 py-0.5 text-xs font-mono" {...props} />
          ),
          pre: (props) => (
            <pre className="bg-black/30 rounded-md p-3 overflow-x-auto text-xs font-mono mb-2" {...props} />
          ),
          table: (props) => (
            <div className="overflow-x-auto mb-2">
              <table className="text-xs border-collapse w-full" {...props} />
            </div>
          ),
          th: (props) => (
            <th className="border border-[var(--border)] px-2 py-1 bg-black/20 text-left" {...props} />
          ),
          td: (props) => <td className="border border-[var(--border)] px-2 py-1" {...props} />,
          a: (props) => (
            <a className="underline text-[var(--accent)]" target="_blank" rel="noreferrer" {...props} />
          ),
          blockquote: (props) => (
            <blockquote className="border-l-2 border-[var(--accent)] pl-3 italic opacity-80 mb-2" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
