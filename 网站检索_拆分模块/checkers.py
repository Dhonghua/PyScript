# checkers.py
# 此模块用于对页面内容进行检索检查，包括标签组合、文本内容以及正则表达式匹配，并返回匹配结果与上下文信息。

import re
from bs4 import BeautifulSoup

def check_tag_combinations(page_source, tag_combinations, exit_on_found):
    """
    检查页面是否包含特定标签组合，并在找到时退出。
    """
    soup = BeautifulSoup(page_source, 'html.parser')
    results = {}
    matching_combinations_count = 0

    for combination in tag_combinations:
        combination_name = combination['name']
        tags = combination['tags']
        relation = combination.get('relation', 'sibling')
        found = False
        count = 0
        matched_contents = []
        if len(tags) == 1:
            tag_name = tags[0]['tag_name']
            tag_attrs = tags[0].get('attributes', {})
            found_tags = soup.find_all(tag_name) if not tag_attrs else soup.find_all(tag_name, attrs=tag_attrs)
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

        first_tag_name = tags[0]['tag_name']
        first_tag_attrs = tags[0].get('attributes', {})
        first_tags = soup.find_all(first_tag_name) if not first_tag_attrs else soup.find_all(first_tag_name, attrs=first_tag_attrs)
        matched_tags = set()

        for first_tag in first_tags:
            current_tag = first_tag
            match = True
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
                combination_hash = hash(str(first_tag) + str(next_tag))
                if combination_hash not in matched_tags:
                    count += 1
                    matched_tags.add(combination_hash)
                    matched_contents.append(str(first_tag) + str(next_tag))
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
    results['matching_combinations_count'] = matching_combinations_count
    return results

def check_text_content(page_source, text_contents, exit_on_found, context_size=40):
    """
    检查页面是否包含特定文案，并保存对应文本的前后更多信息。
    """
    results = {}
    for text_content in text_contents:
        exists = text_content in page_source
        count = page_source.count(text_content) if exists else 0
        matched_contents = []
        if exists:
            for match in re.finditer(re.escape(text_content), page_source):
                start = max(0, match.start() - context_size)
                end = min(len(page_source), match.end() + context_size)
                context = page_source[start:end]
                matched_contents.append(context)
        results[text_content] = {'exists': exists, 'count': count, 'matched_contents': matched_contents}
        if exit_on_found and exists:
            break
    return results

def check_regex_patterns(page_source, regex_patterns, exit_on_found, context_size=40):
    """
    检查页面是否包含特定正则表达式匹配，并保存匹配内容的上下文信息。
    """
    results = {}
    for regex_pattern in regex_patterns:
        pattern_name = regex_pattern['name']
        pattern = regex_pattern['pattern']
        matches = []
        for match in re.finditer(pattern, page_source, re.DOTALL):
            start = max(0, match.start() - context_size)
            end = min(len(page_source), match.end() + context_size)
            context = page_source[start:end]

            # matches.append(context)  #包含上下文信息
            matches.append(match.group())  #仅目标内容

        count = len(matches)
        results[pattern_name] = {'count': count, 'matched_contents': matches}
        if exit_on_found and count > 0:
            break
    return results
