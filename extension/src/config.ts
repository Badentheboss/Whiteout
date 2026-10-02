import weights from './weights.json';
export const VERSION = '0.2.0';
export const config = {
  contrastRatio: 1.35, minFontPx: 2, opacityThreshold: .05,
  offscreenMarginPx: 32, classifierCutoff: weights.cutoff, mutationDebounceMs: 400,
  maxCandidates: 12000, payloadTokenOverlap: .6, batchSize: 32
};
export type DetectorId = 'rules' | 'classifier';
