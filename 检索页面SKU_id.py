import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def load_data(file_path):
    """
    读取文件，每行数据可能包含多个查询内容（用逗号分隔），返回一个列表
    """
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                # 如果一行中存在逗号，则拆分多个项
                if ',' in line:
                    parts = [p.strip() for p in line.split(',') if p.strip()]
                    data.extend(parts)
                else:
                    data.append(line)
    return data

def setup_driver():
    """
    使用 Selenium 自动匹配浏览器驱动，初始化 Chrome 浏览器（这里设置为无界面模式）
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无界面模式
    chrome_options.add_argument("--disable-gpu")
    # 若需要调试可以取消 headless
    driver = webdriver.Chrome(options=chrome_options)
    # 设置隐式等待时间，确保元素加载
    driver.implicitly_wait(10)
    return driver

def check_page(driver, url, search_terms):
    """
    加载指定网站页面，等待动态内容加载后，在页面源码中检查每个查询内容是否存在
    返回一个字典，key 为查询内容，value 为 True/False（是否存在）
    """
    results = {}
    driver.get(url)
    # 等待一段时间，确保 AJAX 动态内容加载完毕（可根据情况调整等待时间）
    time.sleep(5)
    page_source = driver.page_source
    for term in search_terms:
        results[term] = term in page_source
    return results

def main():
    # 请确保两个数据文件和脚本在同一目录下
    websites_file = "网站链接.txt"       # 存放网站链接，每行一个链接
    search_terms_file = "SKU_ID或链接.txt" # 存放待查询的 SKU_ID 或按钮链接，每行一个或多个（用逗号分隔）

    # 读取数据
    websites = load_data(websites_file)
    search_terms = load_data(search_terms_file)
    print("读取的网站链接：", websites)
    print("读取的查询内容：", search_terms)
    
    # 初始化浏览器驱动
    driver = setup_driver()

    # 保存结果，每行记录一个网站的检测结果
    data = []
    for website in websites:
        print(f"正在检查：{website}")
        try:
            result = check_page(driver, website, search_terms)
            # 构造一行数据，第一列为网站链接，后续列为各查询内容的检测结果（转换为中文）
            row = {"网站链接": website}
            for term, exists in result.items():
                if exists is True:
                    row[term] = "存在"
                elif exists is False:
                    row[term] = "不存在"
                else:
                    row[term] = "错误"
            data.append(row)
        except Exception as e:
            print(f"访问 {website} 时发生错误：{e}")
            row = {"网站链接": website}
            for term in search_terms:
                row[term] = "错误"
            data.append(row)
    
    # 关闭浏览器
    driver.quit()

    # 使用 pandas 导出 Excel 文件
    df = pd.DataFrame(data)
    output_file = "SKU检查结果.xlsx"
    df.to_excel(output_file, index=False)
    print(f"结果已导出至 {output_file}")

if __name__ == "__main__":
    main()
