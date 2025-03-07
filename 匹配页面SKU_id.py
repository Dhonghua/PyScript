import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def load_data(file_path):
    """
    读取文件，每行数据可能只包含一个查询内容（不再拆分逗号），返回一个列表
    """
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(line)
    return data

def setup_driver():
    """
    使用 Selenium 自动匹配浏览器驱动，初始化 Chrome 浏览器（这里设置为无界面模式）
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无界面模式
    chrome_options.add_argument("--disable-gpu")
    # 若需要调试，可注释 headless
    driver = webdriver.Chrome(options=chrome_options)
    # 设置隐式等待时间，确保元素加载
    driver.implicitly_wait(10)
    return driver

def check_page(driver, url, search_terms):
    """
    加载指定网站页面，等待动态内容加载后，
    在页面源码中检查每个查询内容是否存在。
    返回一个字典: key 为查询内容，value 为 True/False（是否存在）
    """
    results = {}
    driver.get(url)
    # 等待一段时间，确保 AJAX 动态内容加载完毕（可根据情况灵活调整）
    time.sleep(5)
    page_source = driver.page_source
    for term in search_terms:
        results[term] = (term in page_source)
    return results

def main():
    # 请确保两个数据文件和脚本在同一目录下
    websites_file = "网站链接.txt"         # 存放网站链接，每行一个
    search_terms_file = "SKU_ID或链接.txt"  # 存放待查询的 SKU_ID 或按钮链接，每行一个

    # 读取数据
    websites = load_data(websites_file)
    search_terms = load_data(search_terms_file)
    print("读取的网站链接：", websites)
    print("读取的查询内容：", search_terms)
    
    # 初始化浏览器驱动
    driver = setup_driver()

    # 用于保存所有行的结果，之后用 pandas 转成 DataFrame
    all_rows = []

    for website in websites:
        print(f"正在检查：{website}")
        try:
            # 对当前网站进行检测
            result_dict = check_page(driver, website, search_terms)

            # 将 result_dict 转换成按行存储的形式
            # 第一个 SKU 对应的行显示网站链接，后续行则将网站链接列留空
            first_row = True
            for sku, exists_bool in result_dict.items():
                row = {}
                if first_row:
                    row["网站链接"] = website
                    first_row = False
                else:
                    row["网站链接"] = ""  # 同一网站的后续 SKU 不重复显示链接

                row["SKU"] = sku
                if exists_bool is True:
                    row["是否存在"] = "存在"
                else:
                    row["是否存在"] = "不存在"
                
                all_rows.append(row)

        except Exception as e:
            print(f"访问 {website} 时发生错误：{e}")
            # 若访问或检测过程出现异常，则所有 SKU 标记为 "错误"
            first_row = True
            for sku in search_terms:
                row = {}
                if first_row:
                    row["网站链接"] = website
                    first_row = False
                else:
                    row["网站链接"] = ""
                row["SKU"] = sku
                row["是否存在"] = "错误"
                all_rows.append(row)

    # 关闭浏览器
    driver.quit()

    # 使用 pandas 导出 Excel 文件
    df = pd.DataFrame(all_rows, columns=["网站链接", "SKU", "是否存在"])
    output_file = "SKU匹配结果.xlsx"
    df.to_excel(output_file, index=False)
    print(f"结果已导出至 {output_file}")

if __name__ == "__main__":
    main()
