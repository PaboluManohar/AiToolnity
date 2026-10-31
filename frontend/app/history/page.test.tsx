import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HistoryPage from "@/app/history/page";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {
    status = 401;
  },
  api: vi.fn(),
  googleLoginUrl: () => "http://localhost:8000/api/auth/google/start",
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

describe("execution history", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows a sign in prompt instead of requesting private history anonymously", async () => {
    vi.mocked(api).mockResolvedValue(null as never);
    render(<HistoryPage />);
    expect(
      await screen.findByText("Sign in to view your execution history."),
    ).toBeVisible();
    expect(vi.mocked(api)).toHaveBeenCalledTimes(1);
    expect(vi.mocked(api)).toHaveBeenCalledWith("/api/auth/status");
  });
});
