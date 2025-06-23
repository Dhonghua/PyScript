import openpyxl
from openpyxl.styles import PatternFill

# 打开 Excel 文件
file_path = "目标表格名.xlsx"
wb = openpyxl.load_workbook(file_path)
ws = wb.active

# 黄底填充样式
yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

# 第一步：提取 A列所有非空“查询页面”值，存入列表
query_pages = []
for row in ws.iter_rows(min_row=2):  # 跳过表头
    a_val = row[0].value
    if a_val:
        query_pages.append(str(a_val).strip())

# 第二步：对每一行的 B列（URL）进行匹配，如果包含任一查询页面，则标黄
for row in ws.iter_rows(min_row=2):
    b_cell = row[1]
    b_val = str(b_cell.value).strip() if b_cell.value else ""

    # 判断是否匹配任一查询页面（子串匹配）
    # if any(query in b_val for query in query_pages):    # 匹配任一查询页面
    if b_val in query_pages: # 完全匹配
        b_cell.fill = yellow_fill # B列单元格标黄


# 保存文件
output_path = "结果表格名.xlsx"
wb.save(output_path)
print(f"✅ 已完成标黄处理并保存：{output_path}")
