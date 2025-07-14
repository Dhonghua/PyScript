# page_loader.py
# 此模块负责使用 Playwright 加载页面内容，并支持模拟手机浏览器访问。
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def load_page(url, timeout=70000, wait_for_selectors=None):
    """
    使用 Playwright 加载网页，模拟安卓手机访问，并返回 HTML 内容。
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/91.0.4472.101 Mobile Safari/537.36",
            viewport={"width": 412, "height": 915},
            is_mobile=True
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until='load', timeout=timeout)
            if wait_for_selectors:
                for selector in wait_for_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=timeout)
                        break
                    except PlaywrightTimeoutError:
                        continue
            return page.content()
        except PlaywrightTimeoutError:
            print(f"处理 {url} 时发生错误: 页面加载超时")
        except Exception as e:
            print(f"处理 {url} 时发生错误: {e}")
        finally:
            browser.close()
    return None
