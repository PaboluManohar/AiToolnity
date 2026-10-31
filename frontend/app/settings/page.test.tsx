import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SettingsPage from "@/app/settings/page";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {
    status = 401;
  },
  api: vi.fn(),
  googleLoginUrl: () => "http://localhost:8000/api/auth/google/start",
}));

describe("AI settings", () => {
  beforeEach(() => vi.clearAllMocks());

  it("does not render private settings controls while signed out", async () => {
    vi.mocked(api).mockResolvedValue(null as never);
    render(<SettingsPage />);
    expect(
      await screen.findByText("Sign in to manage your AI settings."),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "Continue with Google Login" })).toBeVisible();
    expect(screen.queryByRole("textbox", { name: "OpenRouter API key" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save settings" })).not.toBeInTheDocument();
  });
});
