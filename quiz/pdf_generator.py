from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.utils import timezone
import io
import os
import glob

class WrongQuestionPDFGenerator:
    """
    错题本PDF生成器
    支持两种导出格式：
    1. 练习版：不带参考答案和解析
    2. 复习版：带参考答案和解析
    """
    
    def __init__(self):
        # 设置页面大小和边距
        self.page_width, self.page_height = A4
        self.margin_left = 1.5 * cm
        self.margin_right = 1.5 * cm
        self.margin_top = 2 * cm
        self.margin_bottom = 2 * cm
        self.content_width = self.page_width - self.margin_left - self.margin_right
        self.content_height = self.page_height - self.margin_top - self.margin_bottom
        
        # 注册中文字体
        self._register_chinese_fonts()
        
        # 设置字体样式
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
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
                                pass
            if font_name in registered_fonts:
                break
        
        # 如果成功注册了中文字体，使用它
        if registered_fonts:
            self.chinese_font = registered_fonts[0]
        else:
            # 如果没有找到中文字体，使用默认字体（可能会有显示问题）
            self.chinese_font = 'Helvetica'  # 默认英文字体
    
    def _setup_custom_styles(self):
        """设置自定义段落样式"""
        # 标题样式
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#333333'),
            spaceAfter=15,
            alignment=TA_CENTER,
            fontName=self.chinese_font  # 使用中文字体
        )
        
        # 副标题样式（日期）
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=10,  # 减小副标题间距
            alignment=TA_CENTER,
            fontName=self.chinese_font,
            leading=14  # 减小行间距
        )
        
        # 题目序号样式
        self.question_number_style = ParagraphStyle(
            'QuestionNumber',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#000000'),
            spaceAfter=5,
            alignment=TA_LEFT,
            fontName=self.chinese_font,
            leading=14  # 减小行间距
        )
        
        # 题目内容样式
        self.question_content_style = ParagraphStyle(
            'QuestionContent',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,  # 减小内容间距
            alignment=TA_LEFT,
            leading=13,  # 减小行间距（从16改为13）
            fontName=self.chinese_font
        )
        
        # 选项样式
        self.option_style = ParagraphStyle(
            'Option',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=0,
            alignment=TA_LEFT,
            leftIndent=15,
            leading=12,  # 减小行间距
            fontName=self.chinese_font
        )
        
        # 答案标题样式
        self.answer_title_style = ParagraphStyle(
            'AnswerTitle',
            parent=self.styles['Heading4'],
            fontSize=11,
            textColor=colors.HexColor('#FF6B00'),
            spaceAfter=3,  # 减小间距
            alignment=TA_LEFT,
            leading=13,
            fontName=self.chinese_font
        )
        
        # 答案内容样式
        self.answer_content_style = ParagraphStyle(
            'AnswerContent',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,  # 减小间距
            alignment=TA_LEFT,
            leading=12,
            fontName=self.chinese_font
        )
        
        # 解析样式
        self.explanation_style = ParagraphStyle(
            'Explanation',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=15,  # 减小间距（从20改为15）
            alignment=TA_LEFT,
            leftIndent=10,
            leading=12,
            fontName=self.chinese_font
        )
    
    def generate_pdf(self, wrong_questions, user, export_type='practice'):
        """
        生成错题本PDF
        
        Args:
            wrong_questions: 错题对象列表
            user: 用户对象
            export_type: 导出类型 ('practice' - 练习版, 'review' - 复习版)
            
        Returns:
            io.BytesIO: PDF文件流
        """
        # 创建内存中的PDF文件
        buffer = io.BytesIO()
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=self.margin_left,
            rightMargin=self.margin_right,
            topMargin=self.margin_top,
            bottomMargin=self.margin_bottom
        )
        
        # 构建PDF内容
        elements = []
        
        # 添加标题和副标题
        title = Paragraph(f"错题本 - {user.username}", self.title_style)
        subtitle = Paragraph(f"导出时间: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", self.subtitle_style)
        subtitle2 = Paragraph(f"总题数: {len(wrong_questions)} 题", self.subtitle_style)
        export_type_text = "练习版" if export_type == 'practice' else "复习版"
        subtitle3 = Paragraph(f"导出类型: {export_type_text}", self.subtitle_style)
        
        elements.append(title)
        elements.append(subtitle)
        elements.append(subtitle2)
        elements.append(subtitle3)
        elements.append(Spacer(1, 20))
        
        # 添加错题内容
        for index, wrong_question in enumerate(wrong_questions, 1):
            question = wrong_question.question
            
            # 题目序号
            question_number_text = f"{index}. 题目 ({'选择题' if question.type == 1 else '判断题'})"
            elements.append(Paragraph(question_number_text, self.question_number_style))
            
            # 题目内容
            question_content = question.content.replace('\n', '<br/>')
            elements.append(Paragraph(question_content, self.question_content_style))
            
            # 选项内容
            if question.options and isinstance(question.options, dict):
                for key, value in question.options.items():
                    option_text = f"{key}. {value}"
                    elements.append(Paragraph(option_text, self.option_style))
            
            # 复习版：添加正确答案和解析
            if export_type == 'review':
                # 用户错误答案
                if wrong_question.user_answer:
                    elements.append(Paragraph(f"<b>您的答案:</b> {wrong_question.user_answer}", self.answer_title_style))
                
                # 正确答案
                elements.append(Paragraph(f"<b>正确答案:</b> {question.correct_answer}", self.answer_title_style))
                
                # 解析内容
                if question.explanation:
                    elements.append(Paragraph(f"<b>解析:</b>", self.answer_title_style))
                    explanation_text = question.explanation.replace('\n', '<br/>')
                    elements.append(Paragraph(explanation_text, self.explanation_style))
            
            # 题目之间的间距
            elements.append(Spacer(1, 10))  # 减小题目间间距（从15改为10）
        
        # 构建PDF
        doc.build(elements)
        
        # 将文件指针移到开始位置
        buffer.seek(0)
        
        return buffer
    
    def generate_practice_pdf(self, wrong_questions, user):
        """生成练习版PDF（不带答案和解析）"""
        return self.generate_pdf(wrong_questions, user, export_type='practice')
    
    def generate_review_pdf(self, wrong_questions, user):
        """生成复习版PDF（带答案和解析）"""
        return self.generate_pdf(wrong_questions, user, export_type='review')