# processor.py
# 该模块负责处理单个 URL 的任务，包括页面加载、调用各检测函数，以及更新进度；同时定义工作线程函数。
import time
from threading import Lock
from page_loader import load_page
from utils import extract_urls, display_progress
from checkers import check_tag_combinations, check_text_content, check_regex_patterns

lock = Lock()

def process_url(config, url, results, processed_urls, all_urls, urls_queue, active_urls):
    """
    处理单个 URL：加载页面、执行各检测操作、更新 URL 队列及结果。
    """
    try:
        page_source = load_page(url, config.get('timeout', 30000), config.get('selectors') if config.get('wait_for_selectors') else None)
        if page_source is None:
            with lock:
                active_urls.remove(url)
            return

        result = {'tags': {}, 'texts': {}, 'regex': {}}

        if 'tag_combinations' in config and config['tag_combinations']:
            tag_results = check_tag_combinations(page_source, config['tag_combinations'], config.get('exit_on_found', False))
            result['tags'] = tag_results

        if 'text_contents' in config and config['text_contents']:
            text_results = check_text_content(page_source, config['text_contents'], config.get('exit_on_found', False))
            result['texts'] = text_results

        if 'regex_patterns' in config and config['regex_patterns']:
            regex_results = check_regex_patterns(page_source, config['regex_patterns'], config.get('exit_on_found', False))
            result['regex'] = regex_results

        # 深度检索：提取页面中其他 URL
        if config.get('depth_search', False):
            from urllib.parse import urlparse
            base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
            base_path = urlparse(url).path
            page_urls = extract_urls(page_source, base_url, base_path, config.get('skip_paths', []))
            with lock:
                for page_url in page_urls:
                    if page_url not in all_urls:
                        urls_queue.put(page_url)
                        all_urls.add(page_url)

        with lock:
            processed_urls.add(url)
            active_urls.remove(url)
            results[url] = result
            total_urls = len(all_urls)
            display_progress(total_urls, len(processed_urls), urls_queue.qsize(), len(active_urls))
    except Exception as e:
        print(f"处理 {url} 时发生错误: {e}")
        with lock:
            active_urls.remove(url)

def worker(config, urls_queue, results, processed_urls, all_urls, active_urls):
    """
    工作线程，不断从队列中取 URL 并调用 process_url 处理。
    """
    while True:
        url = urls_queue.get()
        if url is None:
            break
        with lock:
            active_urls.add(url)
        process_url(config, url, results, processed_urls, all_urls, urls_queue, active_urls)
        urls_queue.task_done()
