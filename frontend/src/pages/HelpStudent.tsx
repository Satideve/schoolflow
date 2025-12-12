import React, { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

export default function HelpStudent() {
  const [content, setContent] = useState("");

  useEffect(() => {
    fetch("/help-student.md")
      .then((res) => res.text())
      .then((txt) => setContent(txt))
      .catch(() => setContent("# Error loading help content"));
  }, []);

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 prose prose-slate">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
