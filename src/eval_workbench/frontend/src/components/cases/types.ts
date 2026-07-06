export type InputMode = 'turns' | 'json';

export interface ConversationTurn {
  role: string;
  content: string;
  media_mime?: string;
  media_base64?: string;
  fileName?: string;
}

export interface MetricRow {
  id: string;
  name: string;
  strategy: string;
  result_type: string;
  rubric_ref: string;
  extractor_ref: string;
  ground_truth: string;
}
