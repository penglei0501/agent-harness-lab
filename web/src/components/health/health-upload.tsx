"use client";

import { useRef, useState } from "react";
import { FileHeart, FileUp, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type UploadState = "idle" | "dragging" | "uploading" | "success" | "error";

interface UploadResult {
  filename: string;
  reportPath: string;
  markdown: string;
}

interface HealthUploadProps {
  labels: {
    title: string;
    description: string;
    choose: string;
    uploading: string;
    success: string;
    error: string;
    markdown: string;
  };
}

const ACCEPTED_TYPES = ".pdf,.md,.txt";

export function HealthUpload({ labels }: HealthUploadProps) {
  const [state, setState] = useState<UploadState>("idle");
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  async function uploadFile(file: File) {
    setState("uploading");
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/health/analyze/", {
        method: "POST",
        body: formData,
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) {
        throw new Error(payload.error || labels.error);
      }
      setResult({
        filename: payload.filename,
        reportPath: payload.reportPath,
        markdown: payload.markdown,
      });
      setState("success");
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : labels.error);
      setState("error");
    }
  }

  function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    void uploadFile(file);
  }

  return (
    <section className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50/70 p-4 dark:border-zinc-700 dark:bg-zinc-900/50">
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        className="sr-only"
        onChange={(event) => handleFiles(event.target.files)}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setState("dragging");
        }}
        onDragLeave={() => setState((current) => (current === "dragging" ? "idle" : current))}
        onDrop={(event) => {
          event.preventDefault();
          handleFiles(event.dataTransfer.files);
        }}
        disabled={state === "uploading"}
        className={cn(
          "flex min-h-44 w-full flex-col items-center justify-center rounded-md border border-transparent px-4 py-6 text-center transition-colors",
          state === "dragging" && "border-emerald-400 bg-emerald-50 dark:bg-emerald-950/30",
          state === "uploading" && "cursor-wait opacity-80"
        )}
      >
        {state === "uploading" ? (
          <Loader2 size={32} className="mb-3 animate-spin text-emerald-500" />
        ) : (
          <FileHeart size={34} className="mb-3 text-emerald-500" />
        )}
        <span className="text-base font-semibold">{labels.title}</span>
        <span className="mt-2 max-w-xl text-sm text-zinc-500 dark:text-zinc-400">
          {state === "uploading" ? labels.uploading : labels.description}
        </span>
        <span className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-md bg-zinc-900 px-4 text-sm font-medium text-white dark:bg-white dark:text-zinc-900">
          <FileUp size={16} />
          {labels.choose}
        </span>
      </button>

      {state === "error" && (
        <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
          {error}
        </p>
      )}

      {state === "success" && result && (
        <div className="mt-4">
          <div className="mb-3 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300">
            {labels.success}: {result.reportPath}
          </div>
          <h3 className="mb-2 text-sm font-semibold">{labels.markdown}</h3>
          <pre className="max-h-[520px] overflow-auto rounded-md bg-zinc-950 p-4 text-xs leading-6 text-zinc-100">
            <code>{result.markdown}</code>
          </pre>
        </div>
      )}
    </section>
  );
}
