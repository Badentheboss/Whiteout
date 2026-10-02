"""Bounded declarative preservation tasks; never execute supplied JavaScript."""
from urllib.parse import urlsplit


def validate_steps(steps):
    if not isinstance(steps,list) or not 1<=len(steps)<=20:
        raise ValueError('An interaction task needs 1–20 steps')
    for step in steps:
        action=step.get('action')
        if action not in {'click','fill','assert_text','assert_url'}:
            raise ValueError('Unsupported interaction action')
        if action!='assert_url' and not isinstance(step.get('selector'),str):
            raise ValueError('A selector is required')
        if action in {'fill','assert_text','assert_url'} and not isinstance(step.get('value'),str):
            raise ValueError('A string value is required')
        if len(step.get('selector',''))>500 or len(step.get('value',''))>2000:
            raise ValueError('Interaction argument too long')
        if action=='assert_url' and (urlsplit(step['value']).scheme or urlsplit(step['value']).netloc):
            raise ValueError('URL assertion must be a local path, query, or fragment')
    return steps


async def execute(page,steps):
    validate_steps(steps)
    outcomes=[]
    origin=urlsplit(page.url)
    try:
        for step in steps:
            action=step['action']
            if action=='assert_url':
                current=urlsplit(page.url)
                actual=current.path+('?' + current.query if current.query else '')+('#'+current.fragment if current.fragment else '')
                if actual!=step['value']:raise AssertionError('URL assertion failed')
            else:
                locator=page.locator(step['selector'])
                if await locator.count()!=1:raise ValueError('Selector must identify exactly one control')
                if action=='click':await locator.click(timeout=3000)
                elif action=='fill':await locator.fill(step['value'],timeout=3000)
                elif (await locator.inner_text(timeout=3000)).strip()!=step['value']:
                    raise AssertionError('Text assertion failed')
            current=urlsplit(page.url)
            if (current.scheme,current.netloc)!=(origin.scheme,origin.netloc):
                raise ValueError('Interaction left the local replay origin')
            outcomes.append({'action':action,'success':True})
        return {'success':True,'steps':outcomes,'reason':None}
    except Exception as error:
        return {'success':False,'steps':outcomes,'reason':str(error)}
