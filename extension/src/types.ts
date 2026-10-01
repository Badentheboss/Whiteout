export type Vector = 'display' | 'visibility' | 'opacity' | 'offscreen' | 'tiny-font' | 'low-contrast' | 'clip' | 'occlusion' | 'comment' | 'attribute' | 'unicode' | 'pseudo';
export type Finding = { selector: string; text: string; vector: Vector; reasons: string[]; score: number; detector: string; sanitized: boolean };
export type Visibility = { humanVisible: boolean; agentVisible: boolean; vector?: Vector; reasons: string[] };
export interface Detector { id: string; detect(root: ParentNode): Finding[] }
