#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
删除数据库中所有表的脚本
"""

import os
import sys
from django.db import connection

# 添加Django项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'need_to_do.settings')

# 导入Django设置并初始化
import django
django.setup()


def drop_all_tables():
    """删除数据库中所有表"""
    with connection.cursor() as cursor:
        # 获取数据库类型
        db_engine = connection.vendor
        
        print(f"连接到数据库引擎: {db_engine}")
        print("开始删除所有表...")
        
        if db_engine == 'sqlite':
            # SQLite数据库删除所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
            tables = cursor.fetchall()
            
            # 先删除所有外键约束
            cursor.execute("PRAGMA foreign_keys = OFF;")
            
            # 删除所有表
            for table_name in tables:
                print(f"删除表: {table_name[0]}")
                cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]} CASCADE;")
            
            # 重新启用外键约束
            cursor.execute("PRAGMA foreign_keys = ON;")
            
        elif db_engine == 'mysql':
            # MySQL数据库删除所有表
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            
            for table_name in tables:
                print(f"删除表: {table_name[0]}")
                cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]} CASCADE;")
            
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            
        elif db_engine == 'postgresql' or db_engine == 'postgresql_psycopg2':
            # PostgreSQL数据库删除所有表
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = cursor.fetchall()
            
            # 关闭外键约束检查
            cursor.execute("ALTER TABLE IF EXISTS django_migrations DISABLE TRIGGER ALL;")
            
            for table_name in tables:
                print(f"删除表: {table_name[0]}")
                cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]} CASCADE;")
            
            # 重新启用触发器
            cursor.execute("ALTER TABLE IF EXISTS django_migrations ENABLE TRIGGER ALL;")
        
        else:
            # 通用方法：删除所有表
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            tables = cursor.fetchall()
            
            for table_name in tables:
                print(f"删除表: {table_name[0]}")
                cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]} CASCADE;")
        
        # 删除Django迁移记录（如果使用Django的迁移系统）
        print("数据库表已全部删除!")


if __name__ == "__main__":
    print("开始执行删除所有表操作...")
    drop_all_tables()
    print("所有表删除操作完成！")