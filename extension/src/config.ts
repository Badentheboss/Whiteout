export const config = {
  detector: 'classifier' as const,
  mode: 'warn' as 'warn' | 'sanitize',
  contrastRatio: 1.35,
  minFontPx: 2,
  offscreenMarginPx: 32,
  opacityThreshold: 0.05,
  classifierCutoff: 0.42,
  mutationDebounceMs: 300,
  payloadTokenOverlap: 0.6,
  extractorProfiles: ['raw-html', 'text-content', 'inner-text', 'accessibility-tree'] as const
};
