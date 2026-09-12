import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

def fixture(identity, parent_id=None, established=True):
    goal = "说明每个未分配原因" if parent_id else "让验收人员看懂结果"
    return {
        "id": identity, "title": "解释分配缺口" if parent_id else "改善验收体验",
        "itemType": "research", "status": "in_progress", "version": 1,
        "payload": {"parentId": parent_id, "goal": goal, "scope": "只解释，不改分配规则"},
        "context": {
            "id": "context-" + identity, "currentVersionId": "version-" + identity,
            "revisionNo": 1 if parent_id else 7, "content": {"goal": goal, "scope": "只解释，不改分配规则"},
        } if established else None,
    }

async def run():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for identity, established in [("child-1", True), ("parent-1", True), ("child-1", False)]:
            context = await browser.new_context(viewport={"width": 1440, "height": 1000})
            page = await context.new_page()
            page.set_default_timeout(10000)
            payloads, errors, unhandled = [], [], []
            page.on("pageerror", lambda error: errors.append(str(error)))
            parent, child = fixture("parent-1", established=established), fixture("child-1", "parent-1")
            items = [parent, child]
            async def route_api(route):
                request = route.request
                url = request.url.split("?", 1)[0]
                data = None
                if url.endswith("/gongzuo/config"):
                    data = {"workspaces": ["personal"], "defaultWorkspace": "personal", "identityMode": "local"}
                elif url.endswith("/state"):
                    data = {"items": items, "ideas": [], "topics": [], "domains": [], "resources": [], "relations": []}
                elif url.endswith("/runs") and request.method == "POST":
                    payloads.append(request.post_data_json)
                    data = {"id": "captured-run", "itemId": request.post_data_json["itemId"], "state": "queued"}
                elif url.endswith("/runs") or url.endswith("/machines"):
                    data = {"items": []}
                elif "/items/" in url:
                    data = next((item for item in items if url.endswith("/items/" + item["id"])), None)
                if data is None:
                    unhandled.append(request.method + " " + url)
                    await route.fulfill(status=500, json={"detail": "Unhandled verification fixture request"})
                else:
                    await route.fulfill(status=200, json=data)
            await page.route("http://127.0.0.1:5176/api/**", route_api)
            await page.goto("http://127.0.0.1:5176/gongzuo/personal/items/" + identity + "/overview")
            await page.wait_for_timeout(1000)
            (OUT / "diagnostic.json").write_text(json.dumps({"url": page.url, "body": (await page.locator("body").inner_text())[:4000], "errors": errors, "unhandled": unhandled}, ensure_ascii=False, indent=2))
            if established:
                await page.get_by_role("button", name="委托 AI", exact=True).click()
                dialog = page.get_by_role("dialog", name="委托一次工作")
                await dialog.wait_for()
                text = await dialog.inner_text()
                assert "本次事项：" + identity in text, text
                if identity == "child-1":
                    assert "目标：说明每个未分配原因" in text
                    assert "共同背景：parent-1 · v7" in text
                else:
                    assert "使用共享上下文 v7" in text
                await dialog.get_by_role("textbox", name="这次具体做什么").fill("核查本次缺口解释")
                await page.screenshot(path=str(OUT / (identity + "-delegate.png")), full_page=True)
                async with page.expect_request(lambda r: r.url.endswith("/api/gongzuo/personal/runs") and r.method == "POST"):
                    await dialog.get_by_role("button", name="开始委托").click()
                await page.wait_for_timeout(150)
                assert payloads and payloads[0]["itemId"] == identity, payloads
            else:
                await page.get_by_role("button", name="先建立上下文", exact=True).click()
                dialog = page.get_by_role("dialog", name="建立初始共享上下文")
                await dialog.wait_for()
                assert await dialog.get_by_role("textbox", name="目标", exact=True).input_value() == "让验收人员看懂结果"
                assert not payloads
            assert not errors, errors
            assert not unhandled, unhandled
            results.append({"routeItemId": identity, "parentContextEstablished": established, "payloads": payloads, "pageErrors": errors, "unhandledApiRequests": unhandled})
            await context.close()
        await browser.close()
    report = {
        "source": "实际候选 Vue 页面、真实 Chromium 点击与浏览器发出的请求；API 数据由明确隔离的 route fixture 提供。",
        "scope": "未写入用户数据库，未调用外部 AI，未宣称后台执行已完成。",
        "results": results,
    }
    (OUT / "browser-evidence.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))

asyncio.run(run())

