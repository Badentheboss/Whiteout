import { config } from './config';
import type { Detector, Finding, Vector, Visibility } from './types';

const instructionPattern = /\b(ignore|disregard|override|follow|reply|output|send|exfiltrate|system prompt|assistant|tool call|CANARY-[A-Z0-9-]+)\b/i;
const selectorOf = (el: Element) => el.id ? `#${CSS.escape(el.id)}` : `${el.tagName.toLowerCase()}${el.className ? '.' + String(el.className).trim().split(/\s+/).map(CSS.escape).join('.') : ''}`;
const color = (value: string) => { const m = value.match(/\d+(?:\.\d+)?/g); return m ? m.slice(0, 3).map(Number) : [0, 0, 0]; };
const lum = ([r,g,b]: number[]) => [r,g,b].map(v => { v/=255; return v <= .03928 ? v/12.92 : ((v+.055)/1.055)**2.4; }).reduce((s,v,i) => s + v * [.2126,.7152,.0722][i],0);
const ratio = (a: string, b: string) => { const [x,y]=[lum(color(a)),lum(color(b))]; return (Math.max(x,y)+.05)/(Math.min(x,y)+.05); };

export function visibilityFor(el: Element): Visibility {
  const s = getComputedStyle(el); const r = el.getBoundingClientRect(); const reasons: string[] = [];
  let vector: Vector | undefined;
  if (s.display === 'none') { vector='display'; reasons.push('display:none'); }
  else if (s.visibility === 'hidden') { vector='visibility'; reasons.push('visibility:hidden'); }
  else if (Number(s.opacity) <= config.opacityThreshold) { vector='opacity'; reasons.push(`opacity ${s.opacity}`); }
  else if (r.right < -config.offscreenMarginPx || r.left > innerWidth + config.offscreenMarginPx || r.bottom < -config.offscreenMarginPx || r.top > innerHeight + config.offscreenMarginPx) { vector='offscreen'; reasons.push('outside viewport'); }
  else if (parseFloat(s.fontSize) < config.minFontPx) { vector='tiny-font'; reasons.push(`font ${s.fontSize}`); }
  else if (s.clipPath !== 'none' || (s.position === 'absolute' && (s.clip === 'rect(0px, 0px, 0px, 0px)' || r.width <= 1 || r.height <= 1))) { vector='clip'; reasons.push('clipped'); }
  else if (ratio(s.color, s.backgroundColor === 'rgba(0, 0, 0, 0)' ? '#fff' : s.backgroundColor) < config.contrastRatio) { vector='low-contrast'; reasons.push('low effective contrast'); }
  return { humanVisible: !vector, agentVisible: true, vector, reasons };
}

function walk(root: ParentNode, classifier: boolean): Finding[] {
  const findings: Finding[] = [];
  const inspect = (el: Element, text: string, vectorOverride?: Vector) => {
    const clean = text.replace(/[\u200B-\u200F\u2060\u{E0000}-\u{E007F}]/gu, '');
    const visibility = visibilityFor(el); const vector = vectorOverride || visibility.vector;
    const hidden = !!vector || clean !== text;
    const score = instructionPattern.test(clean) ? .9 : .15;
    if (hidden && (!classifier || score >= config.classifierCutoff)) findings.push({ selector: selectorOf(el), text: clean.trim().slice(0, 500), vector: vector || 'unicode', reasons: [...visibility.reasons, clean !== text ? 'zero-width or Unicode tag characters' : '', instructionPattern.test(clean) ? 'instruction-like' : ''].filter(Boolean), score, detector: classifier ? 'classifier' : 'rules', sanitized: false });
  };
  root.querySelectorAll('*').forEach(el => {
    const ownText = [...el.childNodes].filter(n => n.nodeType === Node.TEXT_NODE).map(n => n.textContent || '').join(' ').trim();
    if (ownText) inspect(el, ownText);
    for (const attr of ['alt','aria-label','title']) { const value=el.getAttribute(attr); if (value && instructionPattern.test(value)) inspect(el, value, 'attribute'); }
    const pseudo = [getComputedStyle(el,'::before').content, getComputedStyle(el,'::after').content].filter(x => x && x !== 'none' && x !== 'normal').join(' ');
    if (pseudo && instructionPattern.test(pseudo)) inspect(el, pseudo.replace(/^['"]|['"]$/g,''), 'pseudo');
  });
  const comments = document.createTreeWalker(root, NodeFilter.SHOW_COMMENT);
  for (let node=comments.nextNode(); node; node=comments.nextNode()) if (instructionPattern.test(node.textContent || '')) findings.push({selector:'<!--comment-->',text:(node.textContent||'').trim(),vector:'comment',reasons:['HTML comment','instruction-like'],score:.9,detector:classifier?'classifier':'rules',sanitized:false});
  return findings;
}
export const registry: Record<string, Detector> = {
  rules: { id:'rules', detect: root => walk(root, false) },
  classifier: { id:'classifier', detect: root => walk(root, true) },
  'llm-judge-skeleton': { id:'llm-judge-skeleton', detect: () => [] }
};
