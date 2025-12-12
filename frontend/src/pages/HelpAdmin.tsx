import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function HelpAdmin() {
  const [content, setContent] = useState("");

  useEffect(() => {
    fetch("/help-admin.md")
      .then((res) => res.text())
      .then((txt) => setContent(txt))
      .catch(() => setContent("# Error loading help content"));
  }, []);

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 prose prose-slate">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
