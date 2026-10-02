export type Profile = 'raw-html' | 'text-content' | 'inner-text' | 'accessibility-tree';
export type Candidate = {
 id: string; path: string; frame: string; kind: 'text'|'comment'|'attribute'|'pseudo';
 attribute?: string; text: string; normalized: string; reasons: string[];
 hidden: boolean; uncertain: string[]; rect: {x:number;y:number;width:number;height:number};
 profiles: Record<Profile,boolean|null>; score: number|null;
};
export type Scan = {
 schema_version: 2; version: string; detector: string; model: string;
 config: Record<string,number>; findings: Candidate[]; candidates: Candidate[];
 scan_ms: number; inference_ms: number; truncated: boolean; limitations: string[];
};
export interface Detector { id: string; select(candidates: Candidate[]): Promise<Candidate[]>; }
