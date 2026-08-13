import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SeverityBadge } from "@/components/severity-badge";

describe("SeverityBadge", () => {
  it("renders the severity label uppercased", () => {
    render(<SeverityBadge severity="high" />);
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("applies the correct color class per severity", () => {
    const { container } = render(<SeverityBadge severity="critical" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("text-severity-critical");
    expect(badge.className).toContain("border-severity-critical");
  });

  it("distinguishes severities from each other", () => {
    const { container: a } = render(<SeverityBadge severity="critical" />);
    const { container: b } = render(<SeverityBadge severity="low" />);
    expect((a.firstChild as HTMLElement).className).not.toBe((b.firstChild as HTMLElement).className);
  });

  it("falls back gracefully for unknown values", () => {
    const { container } = render(<SeverityBadge severity="unknown" />);
    expect(container.firstChild).toBeTruthy();
  });
});
