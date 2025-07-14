# main.py
# 主程序入口，调用各模块函数，初始化队列、线程并最终保存 CSV 文件。注意导入了前面各模块中的方法，确保整体功能一致。

import os
import time
from queue import Queue
from threading import Thread

from config import load_config
from processor import worker
from file_handler import save_results_to_csv
from utils import display_progress

NUM_THREADS = 1  # 并行线程数

def main(config_path, output_tag_csv, output_text_csv, output_regex_csv):
    config = load_config(config_path)
    if config is None:
        return

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
    display_progress(len(all_urls), 0, urls_queue.qsize(), 0)

    for _ in range(NUM_THREADS):
        thread = Thread(target=worker, args=(config, urls_queue, results, processed_urls, all_urls, active_urls))
        thread.start()
        threads.append(thread)

    urls_queue.join()

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
    # 根据实际情况修改配置文件和输出CSV文件路径
    config_path = r'E:\\pys\\网站检索脚本_拆分模块版\\config.json'
    output_tag_csv = './结果/标签组合结果.csv'
    output_text_csv = './结果/文案检索结果.csv'
    output_regex_csv = './结果/正则表达式结果.csv'
    main(config_path, output_tag_csv, output_text_csv, output_regex_csv)
