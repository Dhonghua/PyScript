# config.py
# 该模块主要负责加载 JSON 配置文件以及额外的 URL 与跳过路径文件。
import json

def load_config(config_path):
    """
    加载配置文件，解析 JSON，同时加载外部的 URL 文件与跳过路径文件。
    """
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
