import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from io import StringIO

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://cms.imyfone.club",
    "Referer": "https://cms.imyfone.club/imyfoneadmin/manage_all/index.html",
    "Cookie": "admin_username=daihh; PHPSESSID=e8aolv03vcqkpapbkcijcnvsig; site_id=15"
}

url_list = [
"https://es.imyfone.com/mac-data-recovery/show-hidden-files-mac/"
]

all_records = []

for query_url in url_list:
    payload = {
        "page_category_type": "",
        "product": "",
        "status": "",
        "start_time": "",
        "end_time": "",
        "show_paging": "0",
        "id": "",
        "article_title": "",
        "full_page_url": "",
        "page_full_content": query_url,
        "operation": "",
        "limit": "1500"
    }

    response = requests.post(
        url="https://cms.imyfone.club/imyfoneadmin/manage_all/index.html",
        headers=headers,
        data=payload
    )

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        if tables:
            html_table = str(tables[0])
            df = pd.read_html(StringIO(html_table))[0]
            if 'URL' in df.columns:
                temp_df = df[['URL']].copy()
                temp_df['查询页面'] = query_url
                all_records.append(temp_df)
                print(f"✅ 成功提取 URL：{query_url}")
            else:
                print(f"⚠️ 表格中无 URL 字段：{query_url}")
        else:
            print(f"⚠️ 未发现表格：{query_url}")
    else:
        print(f"❌ 请求失败：{query_url}，状态码：{response.status_code}")

    time.sleep(1)

if all_records:
    result_df = pd.concat(all_records, ignore_index=True)
    result_df = result_df.drop_duplicates()

    # 调整列顺序
    result_df = result_df[['查询页面', 'URL']]

    # 对“查询页面”列分组，除第一条外设为空
    def blank_except_first(group):
        group = group.copy()
        group.loc[group.index[1:], '查询页面'] = ''
        return group

    result_df = result_df.groupby('查询页面', group_keys=False).apply(blank_except_first)

    result_df.to_excel("提取结果_URL及查询页面_分组显示.xlsx", index=False)
    print("📁 已保存为：提取结果_URL及查询页面_分组显示.xlsx")
else:
    print("❌ 没有提取到任何 URL")
