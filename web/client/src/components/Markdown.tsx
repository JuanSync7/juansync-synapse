// Render markdown to styled HTML. react-markdown is sanitize-safe by default
// (no raw HTML passthrough); remark-gfm adds tables/strikethrough/task-lists.
// All visual styling lives in the .prose-lab class in theme.css.
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function Markdown({ children }: { children: string }) {
  return (
    <div className="prose-lab">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
