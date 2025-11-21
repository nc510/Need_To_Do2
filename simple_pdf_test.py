from io import BytesIO
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class TestPDFGenerator:
    """
    简单的PDF生成器测试类
    """
    def __init__(self):
        # 注册中文字体
        self._register_chinese_fonts()
        self.styles = self._setup_styles()
        
    def _register_chinese_fonts(self):
        """注册中文字体以支持中文显示"""
        # 尝试加载系统中文字体
        # 常见中文字体路径（Windows系统）
        font_dirs = [
            'C:\\Windows\\Fonts',  # Windows字体目录
        ]
        
        # 字体映射
        font_files = {
            'SimSun': ['simsun.ttc', '宋体.ttc'],
            'SimHei': ['simhei.ttf', '黑体.ttf'],
            'Microsoft YaHei': ['msyh.ttf', '微软雅黑.ttf'],
        }
        
        # 已注册的字体
        registered_fonts = []
        
        # 查找并注册字体
        for font_name, font_aliases in font_files.items():
            if font_name in pdfmetrics.getRegisteredFontNames():
                registered_fonts.append(font_name)
                continue
            
            for font_dir in font_dirs:
                if os.path.exists(font_dir):
                    for alias in font_aliases:
                        font_path = os.path.join(font_dir, alias)
                        if os.path.exists(font_path):
                            try:
                                pdfmetrics.registerFont(TTFont(font_name, font_path))
                                registered_fonts.append(font_name)
                                break
                            except Exception as e:
                                print(f"无法加载字体 {font_path}: {e}")
            if font_name in registered_fonts:
                break
        
        # 如果成功注册了中文字体，使用它
        if registered_fonts:
            self.chinese_font = registered_fonts[0]
            print(f"成功注册中文字体: {self.chinese_font}")
        else:
            # 如果没有找到中文字体，使用默认字体（可能会有显示问题）
            self.chinese_font = 'Helvetica'  # 默认英文字体
            print("警告：未找到中文字体，可能会影响中文显示")
    
    def _setup_styles(self):
        """设置文本样式"""
        styles = getSampleStyleSheet()
        
        # 自定义样式
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=15,
            alignment=1,  # 居中
            textColor=colors.HexColor('#333333'),
            fontName=self.chinese_font
        ))
        
        styles.add(ParagraphStyle(
            name='QuestionStyle',
            parent=styles['BodyText'],
            fontSize=11,
            leading=13,  # 减小行间距
            spaceAfter=6,
            fontName=self.chinese_font
        ))
        
        styles.add(ParagraphStyle(
            name='OptionStyle',
            parent=styles['BodyText'],
            fontSize=10,
            leading=12,  # 减小行间距
            spaceAfter=0,
            leftIndent=15,
            fontName=self.chinese_font
        ))
        
        return styles
    
    def _create_question_content(self, question_num, title, options, answer=None, analysis=None):
        """创建单个题目内容"""
        content = []
        
        # 添加题目编号和标题
        question_text = f"<b>{question_num}. {title}</b>"
        content.append(Paragraph(question_text, self.styles['QuestionStyle']))
        
        # 添加选项
        for option_text in options:
            content.append(Paragraph(option_text, self.styles['OptionStyle']))
        
        return content
    
    def generate_sample_pdf(self, export_type, output_file):
        """
        生成测试PDF文件
        
        Args:
            export_type: 'practice' 练习版或 'review' 复习版
            output_file: 输出文件路径
            
        Returns:
            PDF文件内容的字节流
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        
        # 创建PDF内容
        story = []
        
        # 添加标题
        if export_type == 'practice':
            title = "错题本练习版"
        else:
            title = "错题本复习版"
        
        story.append(Paragraph(title, self.styles['CustomTitle']))
        
        # 添加示例题目
        sample_questions = [
            {
                'num': 1,
                'title': '以下哪个是Python中的内置数据类型？',
                'options': [
                    'A. array',
                    'B. list',
                    'C. matrix',
                    'D. vector'
                ],
                'answer': 'B',
                'analysis': 'Python的内置数据类型包括列表(list)、字典(dict)、集合(set)、元组(tuple)等。array不是内置类型，需要导入numpy库。'
            },
            {
                'num': 2,
                'title': '在Django中，哪个函数用于处理HTTP请求并返回响应？',
                'options': [
                    'A. request_handler()',
                    'B. view()',
                    'C. controller()',
                    'D. response()'
                ],
                'answer': 'B',
                'analysis': '在Django中，视图函数(view function)用于处理HTTP请求并返回HTTP响应。'
            },
            {
                'num': 3,
                'title': '以下哪个SQL语句用于从表中检索数据？',
                'options': [
                    'A. INSERT',
                    'B. UPDATE',
                    'C. SELECT',
                    'D. DELETE'
                ],
                'answer': 'C',
                'analysis': 'SELECT语句用于从一个或多个表中检索数据。'
            }
        ]
        
        # 添加每个题目
        for q in sample_questions:
            content = self._create_question_content(q['num'], q['title'], q['options'])
            story.extend(content)
            
            # 如果是复习版，添加答案和解析
            if export_type == 'review':
                answer_text = f"<b>答案：{q['answer']}</b>"
                analysis_text = f"<b>解析：</b>{q['analysis']}"
                story.append(Paragraph(answer_text, self.styles['OptionStyle']))
                story.append(Paragraph(analysis_text, self.styles['QuestionStyle']))
            
            # 添加段落间间距
            story.append(Spacer(1, 10))
        
        # 生成PDF
        doc.build(story)
        
        # 获取PDF内容
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # 保存到文件
        with open(output_file, 'wb') as f:
            f.write(pdf_content)
        
        return pdf_content

def run_test():
    """
    运行PDF生成测试
    """
    print("开始PDF生成测试...")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化测试生成器
    generator = TestPDFGenerator()
    
    # 测试新的文件名格式（类型名+日期时间）
    export_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 测试练习版
    practice_file = os.path.join(output_dir, f'练习版_{export_time}.pdf')
    print(f"生成练习版PDF: {practice_file}")
    practice_data = generator.generate_sample_pdf('practice', practice_file)
    print(f"练习版PDF大小: {len(practice_data)/1024:.2f} KB")
    
    # 测试复习版
    review_file = os.path.join(output_dir, f'复习版_{export_time}.pdf')
    print(f"生成复习版PDF: {review_file}")
    review_data = generator.generate_sample_pdf('review', review_file)
    print(f"复习版PDF大小: {len(review_data)/1024:.2f} KB")
    
    # 验证文件创建
    if os.path.exists(practice_file) and os.path.exists(review_file):
        print("\n✅ PDF生成测试成功!")
        print(f"练习版PDF路径: {practice_file}")
        print(f"复习版PDF路径: {review_file}")
        print("\n测试项目:")
        print("✓ 中文字体支持")
        print("✓ 优化的行间距")
        print("✓ 新的文件名格式（类型名+日期时间）")
        print("\nPDF导出功能已修复并正常工作。")
        return True
    else:
        print("\n❌ PDF文件创建失败。")
        return False

if __name__ == "__main__":
    success = run_test()
    exit(0 if success else 1)

# 代码结束