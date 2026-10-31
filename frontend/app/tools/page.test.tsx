import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ToolsPage from "@/app/tools/page";
import { ApiError, api } from "@/lib/api";
import type { CatalogueItem, CatalogueNode, Execution, Tool } from "@/lib/types";

vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {
    status = 400;
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

const categories: CatalogueNode[] = [
  { id: "writing", name: "Writing" },
  { id: "learning", name: "Learning" },
];
const subcategories: CatalogueNode[] = [
  { id: "editing", name: "Editing" },
];
const tool: Tool = {
  id: "clarity-editor",
  name: "Clarity Editor",
  description: "Edit a draft for clarity.",
  system_prompt: "Edit the supplied text.",
  enabled: true,
  input_schema: {
    fields: [
      {
        name: "draft",
        label: "Draft",
        type: "textarea",
        required: true,
        options: [],
        max_length: 2000,
      },
      {
        name: "audience",
        label: "Audience",
        type: "select",
        required: false,
        options: ["Students", "Customers"],
      },
    ],
  },
  tones: [
    { id: "professional", name: "Professional", instructions: "Be polished." },
    { id: "concise", name: "Concise", instructions: "Keep it brief." },
  ],
};
const items: CatalogueItem[] = [
  { id: "editing-tools", name: "Editing tools", tools: [tool] },
];
const result: Execution = {
  id: 1,
  tool_id: tool.id,
  input_data: { draft: "A draft" },
  result: "An edited draft.",
  model: "openrouter/free",
  tone: "professional",
  created_at: "2026-10-31T12:00:00Z",
};

function configureApi(executionResult: Execution | Error = result) {
  vi.mocked(api).mockImplementation(async (path) => {
    if (path === "/api/catalogue/categories") return categories as never;
    if (path.endsWith("/subcategories")) return subcategories as never;
    if (path.endsWith("/items")) return items as never;
    if (path === `/api/catalogue/tools/${tool.id}`) return tool as never;
    if (path === "/api/executions") {
      if (executionResult instanceof Error) throw executionResult;
      return executionResult as never;
    }
    if (path.endsWith("/regenerate")) return { ...result, id: 2 } as never;
    if (path.endsWith("/refine")) return { ...result, id: 3, tone: "concise" } as never;
    throw new Error(`Unexpected API request: ${path}`);
  });
}

async function openTool() {
  await screen.findByRole("button", { name: "Writing" });
  await userEvent.click(screen.getByRole("button", { name: "Writing" }));
  await userEvent.click(await screen.findByRole("button", { name: "Editing" }));
  const toolButton = await screen.findByRole("button", { name: tool.name });
  await userEvent.click(toolButton);
  await screen.findByRole("textbox", { name: "Draft" });
}

describe("tool catalogue workflow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    configureApi();
  });

  it("shows categories first, then loads subcategories and tools from the API", async () => {
    render(<ToolsPage />);
    expect(await screen.findByRole("button", { name: "Writing" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Learning" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Editing" })).not.toBeInTheDocument();

    await openTool();
    expect(screen.getByRole("heading", { name: tool.name })).toBeVisible();
    expect(screen.getByRole("combobox", { name: "Tone" })).toHaveValue("professional");
    expect(screen.getByRole("combobox", { name: "Audience" })).toBeInTheDocument();
  });

  it("validates required fields and submits dynamic inputs with a replay key", async () => {
    render(<ToolsPage />);
    await openTool();
    const form = screen.getByRole("button", { name: "Generate result" }).closest("form");
    expect(form).not.toBeNull();
    expect(screen.getByRole("textbox", { name: "Draft" })).toBeRequired();
    if (!form) {
      throw new Error("Generate form was not rendered.");
    }
    fireEvent.submit(form);
    expect(await screen.findByRole("alert")).toHaveTextContent("Draft is required.");
    expect(vi.mocked(api)).not.toHaveBeenCalledWith(
      "/api/executions",
      expect.anything(),
    );

    await userEvent.type(screen.getByRole("textbox", { name: "Draft" }), "A draft");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Audience" }), "Students");
    await userEvent.click(screen.getByRole("button", { name: "Generate result" }));
    expect(await screen.findByText("An edited draft.")).toBeVisible();
    const executionCall = vi.mocked(api).mock.calls.find(([path]) => path === "/api/executions");
    expect(executionCall?.[1]?.headers).toHaveProperty("Idempotency-Key");
    expect(JSON.parse(String(executionCall?.[1]?.body))).toEqual({
      tool_id: tool.id,
      inputs: { draft: "A draft", audience: "Students" },
      tone: "professional",
    });
  });

  it("shows execution errors inline and permits retry", async () => {
    configureApi(new ApiError("OpenRouter rate limit reached.", 429));
    render(<ToolsPage />);
    await openTool();
    await userEvent.type(screen.getByRole("textbox", { name: "Draft" }), "A draft");
    await userEvent.click(screen.getByRole("button", { name: "Generate result" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "OpenRouter rate limit reached.",
    );
    expect(screen.getByText("Your result will appear here")).toBeVisible();
  });

  it("supports copy, regenerate and refinement actions", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    render(<ToolsPage />);
    await openTool();
    await user.type(screen.getByRole("textbox", { name: "Draft" }), "A draft");
    await user.click(screen.getByRole("button", { name: "Generate result" }));
    await screen.findByText("An edited draft.");
    await user.click(screen.getByRole("button", { name: "Copy" }));
    expect(writeText).toHaveBeenCalledWith("An edited draft.");

    await user.click(screen.getByRole("button", { name: "Regenerate" }));
    expect(await screen.findByRole("status")).toHaveTextContent("A new result is ready.");

    await user.type(screen.getByLabelText("Refine this result"), "Use bullets.");
    await user.selectOptions(screen.getByRole("combobox", { name: "Tone" }), "concise");
    await user.click(screen.getByRole("button", { name: "Refine result" }));
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Your refined result is ready.",
    );
    const refineCall = vi.mocked(api).mock.calls.find(([path]) => path.endsWith("/refine"));
    expect(JSON.parse(String(refineCall?.[1]?.body))).toEqual({
      tone: "concise",
      instructions: "Use bullets.",
    });
  });
});
