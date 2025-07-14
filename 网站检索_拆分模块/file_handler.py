
# file_handler.py
# 该模块用于将结果保存为 CSV 文件，不同模式下写入不同字段。

import csv
import os

def save_results_to_csv(results, filename, mode='tag'):
    """
    根据不同模式，将结果保存为 CSV 文件。
    """
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
                            '检索文案': text_content[:100],
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
                            '检索内容': '\n'.join(data['matched_contents'])
                        })
    except Exception as e:
        print(f"Error: 未能将结果保存至 {filename}: {e}")
