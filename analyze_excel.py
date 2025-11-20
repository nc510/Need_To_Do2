import pandas as pd
import sys

try:
    # 读取Excel文件
    file_path = 'quiz/test_questions.xlsx'
    df = pd.read_excel(file_path)
    
    print("Excel文件分析结果：")
    print("="*50)
    
    # 显示列名
    print("\n列名：")
    for i, col in enumerate(df.columns, 1):
        print(f"{i}. '{col}'")
    
    # 显示前5行数据（不包括空行）
    print("\n前5行有效数据：")
    valid_rows = df[~df.isnull().all(axis=1)].head(5)
    for idx, row in valid_rows.iterrows():
        print(f"\n第{idx+1}行数据：")
        for col in df.columns:
            if pd.notnull(row[col]):
                print(f"  {col}: '{row[col]}' (类型: {type(row[col]).__name__})")
    
    # 特别检查正确选项列
    correct_answer_col = None
    for col in df.columns:
        if '正确' in col or 'correct' in col.lower():
            correct_answer_col = col
            break
    
    if correct_answer_col:
        print(f"\n\n'正确选项'列: '{correct_answer_col}'")
        print("前10个正确选项的值：")
        for i, val in enumerate(df[correct_answer_col].dropna().head(10), 1):
            print(f"  {i}. '{val}' (类型: {type(val).__name__})")
    
    # 检查选项列
    option_columns = []
    for col in df.columns:
        if any(opt in col for opt in ['选项', 'Option', 'option', 'A', 'B', 'C', 'D']):
            option_columns.append(col)
    
    print(f"\n\n选项相关列: {option_columns}")
    if option_columns:
        print("选项列的数据样例：")
        for col in option_columns[:4]:  # 只显示前4个选项列
            sample_values = df[col].dropna().head(3)
            print(f"  {col}: {list(sample_values)}")
    
    print("\n" + "="*50)
    print("分析完成！")
    
except Exception as e:
    print(f"读取Excel文件失败: {str(e)}")
    sys.exit(1)