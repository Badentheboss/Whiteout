import {config} from './config';
import type {Candidate, Detector} from './types';
import {scoreTexts, modelName} from './model';
import weights from './weights.json';
export {modelName};
export const registry: Record<string,Detector> = {
 rules: {id:'rules',select:async rows=>rows.filter(r=>r.hidden)},
 classifier: {id:'classifier',select:async rows=>{
   const hidden=rows.filter(r=>r.hidden);
   const scores=await scoreTexts(hidden.map(r=>r.normalized));
   hidden.forEach((r,i)=>r.score=scores[i]);
   return hidden.filter(r=>r.score! >= ((weights as any).cutoff ?? config.classifierCutoff));
 }}
};
