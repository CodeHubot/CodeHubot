"""
Excel文件处理工具
用于批量导入教师和学生数据
"""
import pandas as pd
from typing import List, Dict, Any, Tuple
from io import BytesIO
import re
from openpyxl import Workbook

def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    if not phone:
        return True  # 手机号可选
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))

def parse_teacher_excel(file_content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    解析教师Excel文件
    
    Args:
        file_content: Excel文件内容
        
    Returns:
        (teachers_data, errors): 教师数据列表和错误信息列表
    """
    teachers = []
    errors = []
    
    try:
        # 读取Excel文件
        df = pd.read_excel(BytesIO(file_content), sheet_name=0)
        
        # 验证必需列
        required_columns = ['姓名', '工号']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"缺少必需列: {', '.join(missing_columns)}")
            return [], errors
        
        # 处理每一行
        for index, row in df.iterrows():
            row_num = index + 2  # Excel行号（从2开始，因为有表头）
            
            # 验证必填字段
            if pd.isna(row['姓名']) or not str(row['姓名']).strip():
                errors.append(f"第{row_num}行：姓名不能为空")
                continue
                
            if pd.isna(row['工号']) or not str(row['工号']).strip():
                errors.append(f"第{row_num}行：工号不能为空")
                continue
            
            # 提取数据
            teacher = {
                'real_name': str(row['姓名']).strip(),
                'teacher_number': str(row['工号']).strip(),
                'username': str(row['工号']).strip(),  # 默认用工号作为用户名
                'subject': str(row['学科']).strip() if '学科' in df.columns and not pd.isna(row.get('学科')) else None,
                'phone': str(row['手机号']).strip() if '手机号' in df.columns and not pd.isna(row.get('手机号')) else None,
                'password': str(row['初始密码']).strip() if '初始密码' in df.columns and not pd.isna(row.get('初始密码')) else '123456'
            }
            
            # 验证手机号格式
            if teacher['phone'] and not validate_phone(teacher['phone']):
                errors.append(f"第{row_num}行：手机号格式不正确")
                continue
            
            teachers.append(teacher)
        
        if not teachers and not errors:
            errors.append("Excel文件中没有有效数据")
            
    except Exception as e:
        errors.append(f"Excel文件解析失败: {str(e)}")
    
    return teachers, errors


def parse_student_excel(file_content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    解析学生Excel文件
    
    Args:
        file_content: Excel文件内容
        
    Returns:
        (students_data, errors): 学生数据列表和错误信息列表
    """
    students = []
    errors = []
    
    try:
        # 读取Excel文件
        df = pd.read_excel(BytesIO(file_content), sheet_name=0)
        
        # 验证必需列
        required_columns = ['姓名', '学号', '性别']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"缺少必需列: {', '.join(missing_columns)}")
            return [], errors
        
        # 处理每一行
        for index, row in df.iterrows():
            row_num = index + 2  # Excel行号（从2开始，因为有表头）
            
            # 验证必填字段
            if pd.isna(row['姓名']) or not str(row['姓名']).strip():
                errors.append(f"第{row_num}行：姓名不能为空")
                continue
                
            if pd.isna(row['学号']) or not str(row['学号']).strip():
                errors.append(f"第{row_num}行：学号不能为空")
                continue
                
            if pd.isna(row['性别']) or not str(row['性别']).strip():
                errors.append(f"第{row_num}行：性别不能为空")
                continue
            
            # 性别映射
            gender_map = {
                '男': 'male',
                '女': 'female',
                '其他': 'other',
                'male': 'male',
                'female': 'female',
                'other': 'other'
            }
            
            gender_str = str(row['性别']).strip()
            gender = gender_map.get(gender_str)
            if not gender:
                errors.append(f"第{row_num}行：性别必须是'男'、'女'或'其他'")
                continue
            
            # 提取数据
            student = {
                'real_name': str(row['姓名']).strip(),
                'student_number': str(row['学号']).strip(),
                'username': str(row['学号']).strip(),  # 默认用学号作为用户名
                'gender': gender,
                'password': str(row['初始密码']).strip() if '初始密码' in df.columns and not pd.isna(row.get('初始密码')) else '123456'
            }
            
            students.append(student)
        
        if not students and not errors:
            errors.append("Excel文件中没有有效数据")
            
    except Exception as e:
        errors.append(f"Excel文件解析失败: {str(e)}")
    
    return students, errors


def generate_teacher_template() -> BytesIO:
    """
    生成教师导入模板
    
    Returns:
        BytesIO: Excel文件内容
    """
    data = {
        '姓名': ['张三', '李四'],
        '工号': ['T001', 'T002'],
        '学科': ['数学', '英语'],
        '手机号': ['13800138000', '13900139000'],
        '初始密码': ['123456', '123456']
    }
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='教师数据')
    output.seek(0)
    return output


def generate_student_template() -> BytesIO:
    """
    生成学生导入模板
    
    Returns:
        BytesIO: Excel文件内容
    """
    data = {
        '姓名': ['王小明', '李小红'],
        '学号': ['S001', 'S002'],
        '性别': ['男', '女'],
        '初始密码': ['123456', '123456']
    }
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='学生数据')
    output.seek(0)
    return output


def read_excel_file(file_content: bytes) -> List[List[Any]]:
    """
    通用Excel文件读取函数
    
    Args:
        file_content: Excel文件内容（bytes）
        
    Returns:
        List[List[Any]]: 二维列表，包含所有行数据（包括表头）
    """
    try:
        df = pd.read_excel(BytesIO(file_content), sheet_name=0, header=None)
        # 转换为列表，保留所有行（包括表头）
        rows = df.values.tolist()
        # 将每行转换为字符串列表，处理NaN值
        result = []
        for row in rows:
            processed_row = []
            for cell in row:
                if pd.isna(cell):
                    processed_row.append('')
                else:
                    processed_row.append(str(cell).strip())
            result.append(processed_row)
        return result
    except Exception as e:
        raise ValueError(f"读取Excel文件失败: {str(e)}")


def generate_excel_template(columns: List[str], example_data: List[List[Any]], sheet_name: str = 'Sheet1') -> bytes:
    """
    通用Excel模板生成函数
    
    Args:
        columns: 列名列表（表头）
        example_data: 示例数据（二维列表）
        sheet_name: 工作表名称
        
    Returns:
        bytes: Excel文件内容
    """
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    
    # 写入表头
    ws.append(columns)
    
    # 写入示例数据
    for row in example_data:
        ws.append(row)
    
    # 保存到BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

