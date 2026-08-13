import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

const OWASP_DESCRIPTIONS: Record<string, string> = {
  LLM01: "Prompt Injection",
  LLM02: "Sensitive Information Disclosure",
  LLM03: "Supply Chain",
  LLM04: "Data and Model Poisoning",
  LLM05: "Improper Output Handling",
  LLM06: "Excessive Agency",
  LLM07: "System Prompt Leakage",
  LLM08: "Vector and Embedding Weaknesses",
  LLM09: "Misinformation",
  LLM10: "Unbounded Consumption",
};

export function OwaspMitreTag({ code }: { code: string }) {
  const description = OWASP_DESCRIPTIONS[code] || "MITRE ATLAS technique";
  return (
    <TooltipProvider delayDuration={100}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="inline-flex items-center rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground hover:bg-accent">
            {code}
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <span className="font-mono">{code}</span> — {description}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
