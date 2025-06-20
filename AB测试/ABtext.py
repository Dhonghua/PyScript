# import asyncio
# from collections import Counter
# from playwright.async_api import async_playwright
# from tqdm.asyncio import tqdm_asyncio

# async def main():
#     test_url = "https://www-monimaster.ifonelab.net/whatsapp-monitoring/"
#     visit_times = 50
#     results = []

#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)  # 无头

#         for _ in tqdm_asyncio(range(visit_times), desc="访问进度"):
#             context = await browser.new_context()
#             await context.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font"] else route.continue_())
#             page = await context.new_page()
#             await page.goto(test_url, wait_until='domcontentloaded')
#             results.append(page.url)
#             await context.close()

#         await browser.close()

#     counts = Counter(results)
#     print("访问结果统计:")
#     for url, count in counts.items():
#         print(f"{url} -> {count} 次")

# if __name__ == "__main__":
#     asyncio.run(main())

# 并发
import asyncio
from collections import Counter
from playwright.async_api import async_playwright
from tqdm import tqdm

async def visit_page(browser, url, semaphore):
    async with semaphore:
        context = await browser.new_context()
        await context.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in ["image", "stylesheet", "font"]
            else route.continue_()
        )
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        final_url = page.url
        await context.close()
        return final_url

async def main():
    test_url = "https://www-monimaster.ifonelab.net/whatsapp-monitoring/"
    visit_times = 500
    concurrency = 10  # 最大并发数
    semaphore = asyncio.Semaphore(concurrency)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 创建所有任务
        tasks = [visit_page(browser, test_url, semaphore) for _ in range(visit_times)]

        results = []
        # tqdm包装异步任务完成器，实时显示进度条
        for f in tqdm(asyncio.as_completed(tasks), total=visit_times, desc="访问进度"):
            res = await f
            results.append(res)

        await browser.close()

    counts = Counter(results)
    print("访问结果统计:")
    for url, count in counts.items():
        print(f"{url} -> {count} 次")

if __name__ == "__main__":
    asyncio.run(main())
