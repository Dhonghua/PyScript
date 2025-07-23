def retain_duplicates(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    line_counts = {}
    for line in lines:
        line = line.strip()
        if line in line_counts:
            line_counts[line] += 1
        else:
            line_counts[line] = 1
    
    unique = [line + '\n' for line, count in line_counts.items() if count == 1] #唯一项
    # duplicates = [line + '\n' for line, count in line_counts.items() if count > 1] #重复项
    save_content = unique # 修改保存内容

    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(save_content)

if __name__ == "__main__":
    input_file = '内容文本.txt'  # 输入文件路径
    output_file = '过滤内容.txt'  # 输出文件路径
    retain_duplicates(input_file, output_file)