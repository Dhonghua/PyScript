# 后台不信任前端site_id值，需手动在网站切换站点

import requests
from bs4 import BeautifulSoup
import pandas as pd

PHPSESSID = "uubp4eimnpvb4084ulvmafsgqn"  # 替换为实际的 PHPSESSID

# 替换为实际的站点 ID   
site = {
    'ES' : 15,
    'FR' : 11,
    'TW' : 9,
    'KR' : 37,
    'AR' : 59,
    'ID' : 54,
    'TH' : 53,
    'IL' : 145,
    'DE' : 156,
    'JP' : 16
} 
site_id = site["JP"] # 拿到对应站点的ID值 
print(site_id)


headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://cms.imyfone.club",
    "Referer": "https://cms.imyfone.club/imyfoneadmin/manage_all/index.html", 
    "Cookie": f"admin_username=daihh; PHPSESSID={PHPSESSID}; site_id={site_id}"  # site_id 判断查询站点
} 

# all_records = []

payload = {
    "page_category_type": "",
    "product": "",
    "status": "",
    "start_time": "",# 格式化为字符串
    "end_time": "",
    "show_paging": "0",
    "id": "",
    "article_title": "",
    "full_page_url": "",
    "page_full_content": "",
    "operation": "",
    "limit": "5000" #条数
}

response = requests.post(
    url="https://cms.imyfone.club/imyfoneadmin/manage_all/index.html",
    headers=headers,
    data=payload
)
i = True
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    aclass = soup.find_all(class_='dec_txt') # 未登录状态dec_txt会出现文案
    if aclass: #不为空时
        print('未登录或登录状态失效')

    # tables = soup.find_all('table') # 查找所有表格 
    table = soup.find('table') # 找第一个表格

    # 找出表头，并计算 "URL" 所在的列号
    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    print(headers) # ['', 'ID', 'URL', '关联产品', '页面类型', '页面类别', '页面状态', '操作人', '更新时间']
    url_index = headers.index("URL")  # 找到“URL”这一列
    sort_index = headers.index("页面类别")
    state_index = headers.index("页面状态")
    type_index = headers.index("页面类型")
    sorts = ["静态资源相关页面","","模板相关页面"]
    state = ["草稿","已下线"]
    url_cell = []
    for tr in table.find_all('tr')[1:]: # soup.find_all('tr')：查找页面中所有的 <tr>（表格行）。 
                                        # [1:]：跳过第一个 <tr>（通常是表头行），只遍历数据行。
        tds = tr.find_all('td') # 查找该行中的所有 `<td>` 单元格，返回一个列表。
        if len(tds) == len(headers): # 确保该行的单元格数量足够
            sort_cell = tds[sort_index].get_text(strip=True)
            state_cell = tds[state_index].get_text(strip=True)
            if i :
                print(tds[url_index].get_text(strip=True))
                i = False
            if sort_cell not in sorts and state_cell not in state:
                url_cell.append({
                    'URL': tds[url_index].get_text(strip=True),
                    '页面类型' : tds[type_index].get_text(strip=True),
                    '页面类别' : tds[sort_index].get_text(strip=True),
                    '页面状态' : tds[state_index].get_text(strip=True)
                })
matched_keys = [k for k, v in site.items() if v == site_id]
df = pd.DataFrame(url_cell)
file_path = f"./整站链接/{matched_keys[0]}提取结果.xlsx"
df.to_excel(file_path, index=False)
print(f"保存成功: {file_path}")