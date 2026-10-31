export type User = {
  id: number;
  email: string;
  name: string;
};

export type CatalogueNode = {
  id: string;
  name: string;
};

export type InputField = {
  name: string;
  label: string;
  type: "text" | "textarea" | "email" | "url" | "number" | "select";
  required: boolean;
  placeholder?: string | null;
  options: string[];
  min_length?: number | null;
  max_length?: number | null;
  min_value?: number | null;
  max_value?: number | null;
};

export type Tone = {
  id: string;
  name: string;
  instructions: string;
};

export type Tool = {
  id: string;
  name: string;
  description: string;
  input_schema: { fields: InputField[] };
  system_prompt: string;
  tones: Tone[];
  enabled: boolean;
};

export type CatalogueItem = CatalogueNode & {
  tools: Tool[];
};

export type Execution = {
  id: number;
  tool_id: string;
  input_data: Record<string, string | number>;
  result: string;
  model: string;
  tone: string;
  created_at: string;
};

export type AISettings = {
  model: string;
  has_api_key: boolean;
};
