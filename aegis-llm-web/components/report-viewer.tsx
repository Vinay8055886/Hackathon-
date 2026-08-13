"use client";

import { useEffect, useState } from "react";
import { Download, FileCode2, FileJson } from "lucide-react";
import { api } from "@/lib/api";
import { downloadText } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

const MIMES: Record<string, string> = {
  html: "text/html",
  sarif: "application/json",
  json: "application/json",
};

export function ReportViewer({ runId }: { runId: string }) {
  const [html, setHtml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const text = await api.getReportText(runId, "html");
        if (!cancelled) setHtml(text);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [runId]);

  const download = async (format: "html" | "sarif" | "json") => {
    try {
      const text = await api.getReportText(runId, format);
      downloadText(`aegis-run-${runId}.${format}`, text, MIMES[format]);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => download("html")}>
          <Download className="h-4 w-4" /> HTML
        </Button>
        <Button variant="outline" size="sm" onClick={() => download("sarif")}>
          <FileCode2 className="h-4 w-4" /> SARIF
        </Button>
        <Button variant="outline" size="sm" onClick={() => download("json")}>
          <FileJson className="h-4 w-4" /> JSON
        </Button>
      </div>
      {error ? <p className="text-sm text-severity-critical">{error}</p> : null}
      {html === null && !error ? (
        <Skeleton className="h-96 w-full" />
      ) : html ? (
        <iframe
          title="Aegis-LLM report"
          srcDoc={html}
          className="h-[70vh] w-full rounded-lg border bg-white"
          sandbox=""
        />
      ) : null}
    </div>
  );
}
