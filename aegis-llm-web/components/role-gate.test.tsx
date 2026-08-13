import { describe, expect, it, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { RoleGate } from "@/components/role-gate";
import { useUiStore } from "@/lib/store/use-ui-store";

function setRole(role: "viewer" | "operator" | "admin") {
  useUiStore.setState({ user: { id: "u", name: "tester", role } });
}

describe("RoleGate", () => {
  beforeEach(() => setRole("viewer"));

  it("renders children when the role clears the requirement", () => {
    setRole("admin");
    render(
      <RoleGate required="operator">
        <button>allow-list</button>
      </RoleGate>,
    );
    expect(screen.getByRole("button", { name: "allow-list" })).toBeInTheDocument();
  });

  it("hides children when the role is insufficient (hide mode)", () => {
    setRole("viewer");
    render(
      <RoleGate required="operator" fallback={<span>locked</span>}>
        <button>allow-list</button>
      </RoleGate>,
    );
    expect(screen.queryByRole("button", { name: "allow-list" })).not.toBeInTheDocument();
    expect(screen.getByText("locked")).toBeInTheDocument();
  });

  it("renders the locked wrapper in disable mode without executing the action", () => {
    setRole("viewer");
    render(
      <RoleGate required="operator" mode="disable">
        <button>stop run</button>
      </RoleGate>,
    );
    const locked = screen.getByTestId("role-gate-locked");
    expect(locked).toBeInTheDocument();
    expect(locked.getAttribute("aria-disabled")).toBe("true");
  });
});
