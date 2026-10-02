import asyncio
import pytest
from parallax.interactions import validate_steps,execute


class Locator:
    def __init__(self,page):self.page=page
    async def count(self):return 1
    async def click(self,**kwargs):self.page.text='Done'
    async def fill(self,value,**kwargs):self.page.text=value
    async def inner_text(self,**kwargs):return self.page.text


class Page:
    url='http://127.0.0.1:8765/demo'
    text='Ready'
    def locator(self,selector):return Locator(self)


def test_tasks_are_bounded_and_declarative():
    for steps in [[],[{'action':'evaluate','value':'arbitrary code'}],[{'action':'assert_url','value':'https://remote.invalid'}]]:
        with pytest.raises(ValueError):validate_steps(steps)
    good=[{'action':'click','selector':'#button'},{'action':'assert_text','selector':'#button','value':'Done'},{'action':'assert_url','value':'/demo'}]
    result=asyncio.run(execute(Page(),good))
    assert result['success'] and len(result['steps'])==3
    result=asyncio.run(execute(Page(),[{'action':'assert_text','selector':'#button','value':'Wrong'}]))
    assert result['success'] is False
