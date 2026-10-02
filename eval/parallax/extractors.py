"""Explicit extraction profiles. Missing evidence is unknown, never 'not exposed'."""
PROFILES = ('raw-html', 'text-content', 'inner-text', 'accessibility-tree')


async def extract(page, cdp):
    # These profiles intentionally describe the top-level document only. Chromium AX
    # may include descendants, but cannot provide candidate identity by string alone.
    result = await page.evaluate("""()=>({
      'raw-html':document.documentElement.outerHTML,
      'text-content':document.documentElement.textContent || '',
      'inner-text':document.body ? document.body.innerText : '',
      controls:document.querySelectorAll('button,input,select,textarea,a[href]').length
    })""")
    result['unavailable'] = {}
    result['scope'] = 'top-document; no explicit shadow/frame expansion'
    try:
        tree = await cdp.send('Accessibility.getFullAXTree')
        result['accessibility-tree'] = '\n'.join(
            node.get('name', {}).get('value', '') for node in tree['nodes']
            if not node.get('ignored'))
    except Exception as error:
        result['accessibility-tree'] = None
        result['unavailable']['accessibility-tree'] = str(error)
    return result


def exposure(candidate, extraction, profile):
    value = extraction.get(profile)
    if value is None:
        return None, extraction.get('unavailable', {}).get(profile, 'Profile unavailable')
    if candidate.get('frame') != 'top' or ' >>> ' in candidate.get('path', ''):
        return None, 'Top-document extractor does not resolve frame/shadow node identity'
    text = candidate['text'].strip()
    if not text:
        return None, 'Empty text cannot establish exposure'
    if text not in value:
        return False, 'Exact text absent from this extraction (escaping/normalization may differ)'
    return True, 'Text-level exposure only; repeated strings do not establish node identity'


def equality(before, after):
    return None if before is None or after is None else before == after
