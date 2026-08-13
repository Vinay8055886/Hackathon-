"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  ColumnDef,
  SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Download, Search } from "lucide-react";
import { Finding } from "@/lib/api/schemas";
import { downloadText, formatDate } from "@/lib/utils";
import { SeverityBadge } from "@/components/severity-badge";
import { OwaspMitreTag } from "@/components/owasp-mitre-tag";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export function FindingsTable({
  findings,
  showRunLink = true,
}: {
  findings: Finding[];
  showRunLink?: boolean;
}) {
  const [globalFilter, setGlobalFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [sorting, setSorting] = useState<SortingState>([{ id: "severity", desc: true }]);

  const columns = useMemo<ColumnDef<Finding>[]>(
    () => [
      { accessorKey: "severity", header: "Severity", cell: (c) => <SeverityBadge severity={c.getValue<string>()} /> },
      {
        accessorKey: "confidence",
        header: "Conf.",
        cell: (c) => (
          <span className="font-mono text-xs">{Math.round((c.getValue<number>() ?? 0) * 100)}%</span>
        ),
        enableSorting: true,
      },
      { accessorKey: "category", header: "Category", cell: (c) => <span className="font-mono text-xs">{String(c.getValue())}</span> },
      { accessorKey: "owasp_category", header: "OWASP", cell: (c) => <OwaspMitreTag code={String(c.getValue())} /> },
      { accessorKey: "mitre_atlas_id", header: "ATLAS", cell: (c) => <OwaspMitreTag code={String(c.getValue())} /> },
      { accessorKey: "title", header: "Finding", cell: (c) => <span className="max-w-[260px] truncate">{String(c.getValue())}</span> },
      { accessorKey: "status", header: "Status", cell: (c) => <span className="text-muted-foreground">{String(c.getValue())}</span> },
      { accessorKey: "created_at", header: "Found", cell: (c) => <span className="text-xs text-muted-foreground">{formatDate(c.getValue<string>())}</span> },
    ],
    [],
  );

  const filtered = useMemo(() => {
    if (severityFilter === "all") return findings;
    return findings.filter((f) => f.severity === severityFilter);
  }, [findings, severityFilter]);

  const table = useReactTable({
    data: filtered,
    columns,
    state: { globalFilter, sorting },
    onGlobalFilterChange: setGlobalFilter,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 10 } },
  });

  const exportCsv = () => {
    const rows = table.getFilteredRowModel().rows.map((r) => r.original);
    const header = "severity,confidence,category,owasp,mitre,title,status,created_at";
    const lines = rows.map((f) =>
      [f.severity, f.confidence, f.category, f.owasp_category, f.mitre_atlas_id, `"${f.title.replace(/"/g, '""')}"`, f.status, f.created_at ?? ""].join(","),
    );
    downloadText("aegis-findings.csv", [header, ...lines].join("\n"), "text/csv");
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            placeholder="Filter findings…"
            className="w-64 pl-8"
            aria-label="Filter findings"
          />
        </div>
        <Select value={severityFilter} onValueChange={setSeverityFilter}>
          <SelectTrigger className="w-40" aria-label="Filter by severity">
            <SelectValue placeholder="Severity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All severities</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" size="sm" onClick={exportCsv} className="ml-auto">
          <Download className="h-4 w-4" />
          Export CSV
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((hg) => (
              <TableRow key={hg.id}>
                {hg.headers.map((h) => (
                  <TableHead key={h.id} className={h.column.getCanSort() ? "cursor-pointer select-none" : ""} onClick={h.column.getToggleSortingHandler()}>
                    {flexRender(h.column.columnDef.header, h.getContext())}
                    {{
                      asc: " ↑",
                      desc: " ↓",
                    }[h.column.getIsSorted() as string] ?? null}
                  </TableHead>
                ))}
                {showRunLink ? <TableHead /> : null}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length + 1} className="h-24 text-center text-muted-foreground">
                  No findings match the current filters.
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                  ))}
                  {showRunLink ? (
                    <TableCell className="text-right">
                      <Button asChild variant="ghost" size="sm">
                        <Link href={`/findings/${row.original.id}`}>view</Link>
                      </Button>
                    </TableCell>
                  ) : null}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {table.getFilteredRowModel().rows.length} of {findings.length} findings
        </span>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
            Prev
          </Button>
          <span className="font-mono text-xs">
            page {table.getState().pagination.pageIndex + 1} / {Math.max(1, table.getPageCount())}
          </span>
          <Button variant="outline" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
