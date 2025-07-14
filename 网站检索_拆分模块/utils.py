# utils.py
# 该模块包含辅助函数，如 URL 检查、提取页面中链接、以及进度显示函数。
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def should_skip_url(url, skip_paths):
    """
    检查URL是否需要跳过（路径匹配）。
    """
    parsed_url = urlparse(url)
    for skip_path in skip_paths:
        if parsed_url.path.startswith(skip_path):
            return True
    return False

def extract_urls(page_source, base_url, base_path, skip_paths):
    """
    提取页面中的所有URL，确保提取的URL与初始URL路径相同且不在跳过路径中。
    """
    soup = BeautifulSoup(page_source, 'html.parser')
    links = soup.find_all('a', href=True)
    urls = []
    for link in links:
        href = link['href']
        if href.startswith('http://') or href.startswith('https://'):
            parsed_url = urlparse(href)
            if parsed_url.netloc == urlparse(base_url).netloc and \
               parsed_url.path.startswith(base_path) and \
               not should_skip_url(href, skip_paths):
                urls.append(href)
        elif href.startswith('/'):
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == urlparse(base_url).netloc and \
               urlparse(full_url).path.startswith(base_path) and \
               not should_skip_url(full_url, skip_paths):
                urls.append(full_url)
    return urls

def display_progress(total_urls, processed_urls, pending_urls, active_urls):
    """
    实时显示检索进度。
    """
    print(f"总URL数量: {total_urls}, 已完成: {processed_urls}, 待检索: {pending_urls}, 正在检索: {active_urls}")
