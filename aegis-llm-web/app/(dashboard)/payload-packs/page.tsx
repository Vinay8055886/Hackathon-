"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Package } from "lucide-react";
import { usePayloadPacks, usePayloads } from "@/lib/hooks/use-payload-packs";
import { OwaspMitreTag } from "@/components/owasp-mitre-tag";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";

function PackDetail({ packId, name }: { packId: string; name: string }) {
  const [open, setOpen] = useState(false);
  const payloads = usePayloads(open ? packId : undefined);

  return (
    <div className="border-t">
      <Button
        variant="ghost"
        className="w-full justify-between px-3 py-2"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="text-sm font-medium">
          {name} — individual payloads
        </span>
        {open ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </Button>

      {open ? (
        <div className="space-y-2 px-3 pb-3">
          {payloads.isLoading ? <Skeleton className="h-8 w-full" /> : null}

          {(payloads.data ?? []).map((p) => (
            <div key={p.id} className="rounded border bg-muted/30 p-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs">{p.slug}</span>
                <Badge variant="secondary">{p.risk}</Badge>
                <Badge variant="outline">{p.attack_vector}</Badge>
              </div>

              <p className="mt-1 text-xs text-muted-foreground">
                {p.name}
              </p>

              <p className="mt-1 line-clamp-2 font-mono text-[11px] text-muted-foreground">
                {p.messages
                  .map(
                    (m) =>
                      `${m.role}: ${String(m.content).slice(0, 90)}…`,
                  )
                  .join(" · ")}
              </p>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export default function PayloadPacksPage() {
  const { data, isLoading, isError } = usePayloadPacks();

  const packs = data ?? [];

  const totalPayloads = packs.reduce(
    (total, pack) => total + pack.payload_count,
    0,
  );

  const owaspCategories = new Set(
    packs.flatMap((pack) => pack.owasp_categories),
  ).size;

  const mitreTechniques = new Set(
    packs.flatMap((pack) => pack.mitre_atlas_ids),
  ).size;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Payload packs</h1>
        <p className="text-sm text-muted-foreground">
          Versioned attack packs mapped to OWASP LLM Top 10 and MITRE ATLAS
          techniques.
        </p>
      </div>

      {/* Payload pack summary */}
      {!isLoading && !isError && packs.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">
                Payload packs
              </p>
              <p className="mt-1 text-2xl font-semibold">
                {packs.length}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                bundled attack libraries
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">
                Total payloads
              </p>
              <p className="mt-1 text-2xl font-semibold">
                {totalPayloads}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                security test cases
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">
                OWASP coverage
              </p>
              <p className="mt-1 text-2xl font-semibold">
                {owaspCategories}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                LLM Top 10 categories
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">
                MITRE coverage
              </p>
              <p className="mt-1 text-2xl font-semibold">
                {mitreTechniques}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                ATLAS techniques
              </p>
            </CardContent>
          </Card>
        </div>
      ) : null}

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      ) : isError ? (
        <p className="text-severity-critical">
          Failed to load payload packs.
        </p>
      ) : packs.length === 0 ? (
        <EmptyState
          title="No payload packs"
          description="Bundled packs are synced on API startup."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {packs.map((pack) => (
            <Card key={pack.id} className="flex flex-col">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Package className="h-4 w-4 text-muted-foreground" />
                    <CardTitle className="font-mono text-base">
                      {pack.name}
                    </CardTitle>
                  </div>

                  <Badge variant="secondary">
                    v{pack.version}
                  </Badge>
                </div>

                <p className="text-sm text-muted-foreground">
                  {pack.description}
                </p>
              </CardHeader>

              <CardContent className="flex flex-1 flex-col gap-3">
                <div className="flex flex-wrap items-center gap-1.5">
                  {pack.owasp_categories.map((c) => (
                    <OwaspMitreTag key={c} code={c} />
                  ))}

                  {pack.mitre_atlas_ids.map((m) => (
                    <OwaspMitreTag key={m} code={m} />
                  ))}
                </div>

                <div className="mt-auto flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {pack.payload_count} payloads ·{" "}
                    {pack.tags.join(", ")}
                  </span>

                  <span>{pack.source}</span>
                </div>

                <PackDetail
                  packId={pack.id}
                  name={pack.name}
                />
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}