import requests
import pandas as pd
import os

url_path = "./urls.txt"

with open(url_path, 'r', encoding='utf-8') as url_file:
    urls = [line.strip() for line in url_file if line.strip()]

file_path = "./页面状态查询.xlsx"
url_statu = []
for i in urls:    
    try :
        response = requests.get(i,timeout = 10)
        statu = response.status_code
        if 200 <= statu < 300:
            print(f"{i}页面正常访问 ✅")
            url_statu.append({
                'url':i,
                '状态' : statu
            })
        elif 300 <= statu < 400 :
            url_statu.append({
                'url':i,
                '状态' : statu
            })
        elif 400 <= statu < 500:
            url_statu.append({
                'url':i,
                '状态' : statu
            })
        elif 500 <= statu < 600:
            url_statu.append({
                'url':i,
                '状态' : statu
            })
        else:
            print(f"页面访问失败 ❌，状态码：{response.status_code}")
    except requests.RequestException as e :
        print(f"{i}💥 异常: {statu}")
df = pd.DataFrame(url_statu)
df.to_excel(file_path, index=False)
print(f"文件保存至{os.path.abspath(file_path)}")
