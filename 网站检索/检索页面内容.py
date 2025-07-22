import csv
import json
import os
import time
import re  # 引入正则表达式模块
from threading import Thread, Lock
from queue import Queue
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup

NUM_THREADS = 15  # 并行线程数
lock = Lock()

# 加载配置文件
def load_config(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)

            # 加载外部URL文件
            if 'urls_file' in config:
                try:
                    with open(config['urls_file'], 'r', encoding='utf-8') as url_file:
                        config['urls'] = [line.strip() for line in url_file if line.strip()]
                except FileNotFoundError:
                    print(f"Warning: URL文件{config['urls_file']}未找到.")
                    config['urls'] = []

            # 加载跳过路径文件
            config['skip_paths'] = []
            if 'skip_paths_file' in config and config['skip_paths_file']:
                try:
                    with open(config['skip_paths_file'], 'r', encoding='utf-8') as skip_file:
                        config['skip_paths'] = [line.strip() for line in skip_file if line.strip()]
                except FileNotFoundError:
                    print(f"Warning: 跳过检索路径文件{config['skip_paths_file']}未找到.")

            return config
    except FileNotFoundError:
        print(f"Error: 没找到配置文件{config_path}.")
        return None
    except json.JSONDecodeError:
        print(f"Error: 无法从配置文件{config_path}解码 JSON.")
        return None

# 使用 Playwright 动态加载页面
def load_page(url, timeout=70000, wait_for_selectors=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until='load', timeout=timeout)
            if wait_for_selectors:
                for selector in wait_for_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=timeout)
                        break
                    except TimeoutError:
                        continue
            content = page.content()
            return content
        except TimeoutError:
            print(f"处理 {url} 时发生错误: 页面加载超时")
            return None
        except Exception as e:
            print(f"处理 {url} 时发生错误: {e}")
            return None
        finally:
            browser.close()

# 检查URL是否需要跳过
def should_skip_url(url, skip_paths):
    parsed_url = urlparse(url)
    for skip_path in skip_paths:
        if parsed_url.path.startswith(skip_path):
            return True
    return False

# 提取页面中的所有URL，确保提取的URL与初始URL路径相同且不在跳过路径中
def extract_urls(page_source, base_url, base_path, skip_paths):
    soup = BeautifulSoup(page_source, 'html.parser')
    links = soup.find_all('a', href=True)
    urls = []
    for link in links:
        href = link['href']
        if href.startswith('http://') or href.startswith('https://'):
            parsed_url = urlparse(href)
            if parsed_url.netloc == urlparse(base_url).netloc and parsed_url.path.startswith(base_path) and not should_skip_url(href, skip_paths):
                urls.append(href)
        elif href.startswith('/'):
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == urlparse(base_url).netloc and urlparse(full_url).path.startswith(base_path) and not should_skip_url(full_url, skip_paths):
                urls.append(full_url)
    return urls

# 检查页面是否包含特定标签组合，并在找到时退出
def check_tag_combinations(page_source, tag_combinations, exit_on_found):
    soup = BeautifulSoup(page_source, 'html.parser')
    results = {}
    matching_combinations_count = 0

    for combination in tag_combinations:
        combination_name = combination['name']
        tags = combination['tags']
        relation = combination.get('relation', 'sibling')  # 获取组合的relation属性
        found = False
        count = 0  # 用于统计匹配的标签组合数量
        matched_contents = []  # 用于记录匹配的内容

        # 如果组合有且仅有一个标签，则查找并记录该标签
        if len(tags) == 1:
            tag_name = tags[0]['tag_name']
            tag_attrs = tags[0].get('attributes', {})
            if not tag_attrs:
                found_tags = soup.find_all(tag_name)
            else:
                found_tags = soup.find_all(tag_name, attrs=tag_attrs)
            
            for tag in found_tags:
                matched_contents.append(str(tag))
                count += 1
            
            results[combination_name] = {
                'count': count,
                'matched_contents': matched_contents
            }
            if exit_on_found and count > 0:
                break
            continue

        # 查找第一个标签
        first_tag_name = tags[0]['tag_name']
        first_tag_attrs = tags[0].get('attributes', {})
        if not first_tag_attrs:
            first_tags = soup.find_all(first_tag_name)  # 匹配所有具有指定标签名的标签
        else:
            first_tags = soup.find_all(first_tag_name, attrs=first_tag_attrs)
        # 用于记录已经匹配过的标签组合，防止重复计数
        matched_tags = set()

        for first_tag in first_tags:
            current_tag = first_tag
            match = True

            # 按顺序查找后续标签
            for tag in tags[1:]:
                next_tag_name = tag['tag_name']
                next_tag_attrs = tag.get('attributes', {})
                if not next_tag_attrs:
                    if relation == 'sibling':
                        next_tag = current_tag.find_next_sibling(next_tag_name)
                    elif relation == 'child':
                        next_tag = current_tag.find(next_tag_name)
                    else:
                        next_tag = None
                else:
                    if relation == 'sibling':
                        next_tag = current_tag.find_next_sibling(next_tag_name, attrs=next_tag_attrs)
                    elif relation == 'child':
                        next_tag = current_tag.find(next_tag_name, attrs=next_tag_attrs)
                    else:
                        next_tag = None

                if next_tag is None:
                    match = False
                    break
                current_tag = next_tag

            if match:
                # 使用标签组合内容的哈希值来确保唯一性
                combination_hash = hash(str(first_tag) + str(next_tag))
                if combination_hash not in matched_tags:
                    count += 1
                    matched_tags.add(combination_hash)
                    matched_contents.append(str(first_tag) + str(next_tag))  # 记录匹配的内容
                    found = True

                    if exit_on_found:
                        results[combination_name] = {
                            'count': 1,
                            'matched_contents': [str(first_tag) + str(next_tag)]
                        }
                        matching_combinations_count += 1
                        break

        if not exit_on_found:
            results[combination_name] = {
                'count': count if found else 0,
                'matched_contents': matched_contents
            }

    results['matching_combinations_count'] = matching_combinations_count  # 添加匹配组合的总数
    return results

# 检查页面是否包含特定文案，并在找到时退出，同时保存对应文本的前后更多信息
def check_text_content(page_source, text_contents, exit_on_found, context_size=40):  
    results = {}
    for text_content in text_contents:
        exists = text_content in page_source
        count = page_source.count(text_content) if exists else 0
        matched_contents = []
        if exists:
            for match in re.finditer(re.escape(text_content), page_source):
                start = max(0, match.start() - context_size)
                end = min(len(page_source), match.end() + context_size)
                context = page_source[start:end]  #捕获匹配内容的上下文信息（前后各 context_size 个字符）
                matched_contents.append(context)
        results[text_content] = {'exists': exists, 'count': count, 'matched_contents': matched_contents}
        if exit_on_found and exists:
            break  # 提前退出当前页面的检索
    return results

# 检查页面是否包含特定正则表达式匹配，并在找到时退出，同时保存对应文本的前后更多信息
def check_regex_patterns(page_source, regex_patterns, exit_on_found, context_size=40):
    results = {}
    for regex_pattern in regex_patterns:
        pattern_name = regex_pattern['name']
        pattern = regex_pattern['pattern']
        matches = []
        for match in re.finditer(pattern, page_source, re.DOTALL):
            start = max(0, match.start() - context_size)
            end = min(len(page_source), match.end() + context_size)
            context = page_source[start:end]  #捕获匹配内容的上下文信息（前后各 context_size 个字符）
            matches.append(context)
        count = len(matches)
        results[pattern_name] = {'count': count, 'matched_contents': matches}
        if exit_on_found and count > 0:
            break
    return results

# 保存结果为CSV文件
def save_results_to_csv(results, filename, mode='tag'):
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if mode == 'tag':
                fieldnames = ['URL', '标签组合', '存在', '数量', '匹配组合总数', '检索内容']
            elif mode == 'text':
                fieldnames = ['URL', '检索文案', '存在', '数量', '检索内容']
            elif mode == 'regex':
                fieldnames = ['URL', '正则表达式', '匹配数量', '检索内容']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for url, result in results.items():
                if mode == 'tag':
                    for combination, data in result['tags'].items():
                        if combination != 'matching_combinations_count':
                            writer.writerow({
                                'URL': url,
                                '标签组合': combination,
                                '存在': '是' if data['count'] > 0 else '否',
                                '数量': data['count'],
                                '匹配组合总数': result['tags'].get('matching_combinations_count', 0),
                                '检索内容': '\n[----] '.join(data['matched_contents'])
                            })
                elif mode == 'text':
                    for text_content, data in result['texts'].items():
                        writer.writerow({
                            'URL': url,
                            '检索文案': text_content[:20],  # 仅显示前20个字符
                            '存在': '是' if data['exists'] else '否',
                            '数量': data['count'],
                            '检索内容': '\n[----] '.join(data['matched_contents'])
                        })
                elif mode == 'regex':
                    for pattern_name, data in result['regex'].items():
                        writer.writerow({
                            'URL': url,
                            '正则表达式': pattern_name,
                            '匹配数量': data['count'],
                            '检索内容': '\n[----] '.join(data['matched_contents'])
                        })
    except Exception as e:
        print(f"Error: 未能将结果保存至 {filename}: {e}")

# 实时显示检索进度
def display_progress(total_urls, processed_urls, pending_urls, active_urls):
    print(f"总URL数量: {total_urls}, 已完成: {processed_urls}, 待检索: {pending_urls}, 正在检索: {active_urls}")

# 处理单个URL的任务
def process_url(config, url, results, processed_urls, all_urls, urls_queue, active_urls):
    try:
        page_source = load_page(url, config.get('timeout', 30000), config.get('selectors') if config.get('wait_for_selectors') else None)
        if page_source is None:
            with lock:
                active_urls.remove(url)  # 移除失败的URL
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

        # 如果需要检索主路径下的所有页面链接
        if config.get('depth_search', False):
            base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
            base_path = urlparse(url).path
            page_urls = extract_urls(page_source, base_url, base_path, config.get('skip_paths', []))
            with lock:
                for page_url in page_urls:
                    if page_url not in all_urls:  # 检查URL是否已经存在
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
            active_urls.remove(url)  # 移除失败的URL

# 工作线程
def worker(config, urls_queue, results, processed_urls, all_urls, active_urls):
    while True:
        url = urls_queue.get()
        if url is None:
            break
        with lock:
            active_urls.add(url)
        process_url(config, url, results, processed_urls, all_urls, urls_queue, active_urls)
        urls_queue.task_done()

def main(config_path, output_tag_csv, output_text_csv, output_regex_csv):
    config = load_config(config_path)
    if config is None:
        return

    # 验证配置文件内容
    if 'urls' not in config or not config['urls']:
        print("Error: 在配置文件中没有找到URL.")
        return

    urls_queue = Queue()
    all_urls = set()
    for url in config['urls']:
        urls_queue.put(url)
        all_urls.add(url)

    results = {}
    processed_urls = set()
    active_urls = set()
    threads = []

    start_time = time.time()

    # 初始显示进度
    display_progress(len(all_urls), 0, urls_queue.qsize(), 0)

    for _ in range(NUM_THREADS):
        thread = Thread(target=worker, args=(config, urls_queue, results, processed_urls, all_urls, active_urls))
        thread.start()
        threads.append(thread)

    # 阻塞直到所有任务完成
    urls_queue.join()

    # 停止所有工作线程
    for _ in range(NUM_THREADS):
        urls_queue.put(None)
    for thread in threads:
        thread.join()

    if 'tag_combinations' in config and config['tag_combinations']:
        save_results_to_csv(results, output_tag_csv, mode='tag')

    if 'text_contents' in config and config['text_contents']:
        save_results_to_csv(results, output_text_csv, mode='text')

    if 'regex_patterns' in config and config['regex_patterns']:
        save_results_to_csv(results, output_regex_csv, mode='regex')

    end_time = time.time()
    total_time = end_time - start_time

    # 打印最终检索信息和时长
    print(f"总检索URL数量: {len(processed_urls)}")
    if 'tag_combinations' in config and config['tag_combinations']:
        print(f"标签组合检索结果已保存至: {os.path.abspath(output_tag_csv)}")
    if 'text_contents' in config and config['text_contents']:
        print(f"文案检索结果已保存至: {os.path.abspath(output_text_csv)}")
    if 'regex_patterns' in config and config['regex_patterns']:
        print(f"正则表达式检索结果已保存至: {os.path.abspath(output_regex_csv)}")

    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"完成时间：{current_time}，总检索时长: {total_time:.2f}秒")

if __name__ == '__main__':
    config_path = 'E:\pys\check_tags\config.json'
    output_tag_csv = '标签组合结果.csv'
    output_text_csv = '文案检索结果.csv'
    output_regex_csv = '正则表达式结果.csv'
    main(config_path, output_tag_csv, output_text_csv, output_regex_csv)