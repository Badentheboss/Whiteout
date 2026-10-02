"""Validated intake for diverse reviewed sources; does not infer legal approval."""
from urllib.parse import urlsplit
import re

CATEGORIES={'documentation','article','forum','storefront','interactive-app'}


def reviewed_sources(rows):
    if not rows:raise ValueError('Empty source registry')
    seen=set();result=[]
    for row in rows:
        group=row.get('source_group','')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',group) or group in seen:
            raise ValueError('Invalid or duplicate source group')
        seen.add(group)
        if row.get('category') not in CATEGORIES:raise ValueError('Unknown source category')
        for key in ['source_url','license_url','terms_url']:
            address=urlsplit(row.get(key,''))
            if address.scheme!='https' or not address.hostname or address.username or address.password:
                raise ValueError('Public HTTPS evidence URL required: '+key)
        for key in ['terms_checked','page_license_checked','asset_licenses_checked']:
            if row.get(key) is not True:raise ValueError('Pending approval: '+key)
        if not all(row.get(key,'').strip() for key in ['reviewer','reviewed_at','license','review_notes']):
            raise ValueError('Reviewer, date, license, and rationale required')
        result.append(row)
    return result
