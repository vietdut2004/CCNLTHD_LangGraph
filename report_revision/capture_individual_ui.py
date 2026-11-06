import asyncio
import base64
import json
import subprocess
from pathlib import Path
import urllib.request
import time
import websockets

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'report_revision' / 'individual_assets'

async def main():
    browser = subprocess.Popen([
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
        '--remote-debugging-port=9234', f'--user-data-dir={OUT / "chrome_profile"}',
        'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                pages = json.load(urllib.request.urlopen('http://127.0.0.1:9234/json',timeout=1))
                page = next(x for x in pages if x['type']=='page')
                break
            except Exception:
                await asyncio.sleep(.2)
        else:
            raise RuntimeError('Browser debugging endpoint did not start')
        async with websockets.connect(page['webSocketDebuggerUrl'], max_size=20_000_000) as ws:
            count = 0
            async def call(method, params=None):
                nonlocal count
                count += 1
                current = count
                await ws.send(json.dumps({'id':current,'method':method,'params':params or {}}))
                while True:
                    reply = json.loads(await ws.recv())
                    if reply.get('id')==current:
                        if 'error' in reply: raise RuntimeError(reply['error'])
                        return reply.get('result',{})
            await call('Page.enable')
            await call('Runtime.enable')
            await call('Emulation.setDeviceMetricsOverride', {'width':1360,'height':800,'deviceScaleFactor':1.5,'mobile':False})
            await call('Page.navigate',{'url':'http://127.0.0.1:2024/'})
            for _ in range(80):
                result=await call('Runtime.evaluate',{'expression':'document.querySelector("#connection")?.textContent','returnByValue':True})
                if result.get('result',{}).get('value')=='Sẵn sàng': break
                await asyncio.sleep(.25)
            # Capture the real page. No messages or model answers are fabricated.
            await call('Runtime.evaluate',{'expression':'document.activeElement?.blur()'})
            await asyncio.sleep(.3)
            shot=await call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False})
            (OUT/'web_current.png').write_bytes(base64.b64decode(shot['data']))
            print('Captured current UI at localhost:2024')
            successful = 0
            for text in ['Chào bạn, mình tên là An.', 'Bạn còn nhớ tên mình không?']:
                expression = 'document.querySelector("#question").value=' + json.dumps(text) + ';document.querySelector("#chat-form").requestSubmit()'
                await call('Runtime.evaluate',{'expression':expression})
                for _ in range(240):
                    await asyncio.sleep(.25)
                    status=await call('Runtime.evaluate',{'expression':'JSON.stringify({busy:document.querySelector("#send").disabled,error:!document.querySelector("#error").hidden})','returnByValue':True})
                    state=json.loads(status['result']['value'])
                    if not state['busy']:
                        break
                else:
                    break
                if state['error']:
                    print('Provider unavailable; retained clean initial screenshot.')
                    break
                successful+=1
            if successful:
                await call('Runtime.evaluate',{'expression':'document.activeElement?.blur()'})
                shot=await call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False})
                (OUT/'web_current_conversation.png').write_bytes(base64.b64decode(shot['data']))
                print('Captured real conversation:', successful, 'turns')
    finally:
        browser.terminate()
        try: browser.wait(timeout=5)
        except subprocess.TimeoutExpired: browser.kill()

asyncio.run(main())
