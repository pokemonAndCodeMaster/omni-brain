from pathlib import Path
import json,hashlib
from playwright.sync_api import sync_playwright,expect
root=Path.cwd();folder=root/'eval/trials/integrations/PERSONAL_WORKBENCH_20260912/personal-workbench';html=root/'.derived/personal-workbench/index.html'
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True);page=browser.new_page(viewport={'width':1440,'height':1050});errors=[];requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
 page.goto(html.as_uri());expect(page.locator('.item-button')).to_have_count(3)
 ids=page.locator('.item-button').evaluate_all('xs=>xs.map(x=>x.dataset.item)');assert set(ids)=={'issue:YYH-7','issue:YYH-8','issue:YYH-11'},ids
 page.locator('[data-item="issue:YYH-11"]').click();expect(page.locator('#body')).to_contain_text('保存被拒绝');assert '<issue ' not in page.locator('#body').inner_text();assert page.locator('#body a').filter(has_text='YYH-12').count()>0
 page.screenshot(path=str(folder/'final-desktop.png'),full_page=True)
 page.locator('[data-view="ideas"]').click();expect(page.locator('.item-button')).to_have_count(2)
 page.locator('[data-view="review"]').click();expect(page.locator('.item-button')).to_have_count(0)
 page.locator('[data-view="knowledge"]').click();expect(page.locator('.item-button')).to_have_count(40)
 page.locator('#search').fill('业务到代码地图');page.locator('#kind').select_option('local');page.locator('[data-item="local:quality-code-map"]').click()
 expect(page.locator('#detail-title')).to_have_text('验收业务到代码地图');expect(page.locator('#body')).to_contain_text('验收');size=len(page.locator('#body').inner_text());assert size>2000,size
 page.set_viewport_size({'width':390,'height':844});expect(page.locator('#back-to-list')).to_be_visible();assert not page.evaluate('document.documentElement.scrollWidth > innerWidth');page.screenshot(path=str(folder/'final-mobile.png'),full_page=True)
 page.locator('#back-to-list').click();expect(page.locator('.directory')).to_be_visible()
 assert not errors,errors;assert not [u for u in requests if u.startswith(('http:','https:'))]
 browser.close()
 record={'date':'2026-09-13','htmlSha256':hashlib.sha256(html.read_bytes()).hexdigest(),'fullIssues':16,'fullDocuments':21,'localEntries':19,'nowIssueIds':ids,'backlogItems':2,'reviewItems':0,'knowledgeItems':40,'localKnowledgeFullTextChars':size,'mobileWidth':390,'horizontalOverflow':False,'nativeIssueMentionsReadable':True,'pageErrors':errors,'externalRequests':0,'screenshots':['final-desktop.png','final-mobile.png']}
 (folder/'final-browser-check.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));print(json.dumps(record,ensure_ascii=False))

