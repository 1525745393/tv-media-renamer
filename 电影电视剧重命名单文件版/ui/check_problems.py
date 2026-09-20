#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题检查脚本
"""

import sys
import os

def check_imports():
    """检查导入问题"""
    print("🔍 检查模块导入...")
    
    modules_to_check = [
        'main_window',
        'workers',
        'constants',
        'control_panel',
        'file_table',
        'settings_dialog',
        'help_dialog',
        'batch_preview_dialog',
        'operation_history',
        'file_protector',
        'enhanced_analyzer',
        'batch_manager',
        'file_classifier',
        'smart_analysis_dialog',
        'tv_rename_cache_optimized'
    ]
    
    failed_imports = []
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append((module, str(e)))
        except Exception as e:
            print(f"❌ {module}: {e}")
            failed_imports.append((module, str(e)))
    
    return failed_imports

def check_syntax():
    """检查语法错误"""
    print("\n🔍 检查语法错误...")
    
    python_files = [
        'main_window.py',
        'workers.py',
        'constants.py',
        'control_panel.py',
        'file_table.py',
        'settings_dialog.py',
        'help_dialog.py',
        'batch_preview_dialog.py',
        'operation_history.py',
        'file_protector.py',
        'enhanced_analyzer.py',
        'batch_manager.py',
        'file_classifier.py',
        'smart_analysis_dialog.py',
        'tv_rename_cache_optimized.py'
    ]
    
    syntax_errors = []
    
    for file in python_files:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    compile(f.read(), file, 'exec')
                print(f"✅ {file}")
            except SyntaxError as e:
                print(f"❌ {file}: {e}")
                syntax_errors.append((file, str(e)))
            except Exception as e:
                print(f"❌ {file}: {e}")
                syntax_errors.append((file, str(e)))
        else:
            print(f"⚠️ {file}: 文件不存在")
    
    return syntax_errors

def check_dependencies():
    """检查依赖"""
    print("\n🔍 检查依赖...")
    
    dependencies = [
        'PyQt5',
        'psutil',
        'colorama',
        'guessit'
    ]
    
    missing_deps = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}: 未安装")
            missing_deps.append(dep)
    
    return missing_deps

def check_files():
    """检查必要文件"""
    print("\n🔍 检查必要文件...")
    
    required_files = [
        'constants.py',
        'custom_rules.json',
        'classification_rules.json',
        'requirements.txt'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}: 文件不存在")
            missing_files.append(file)
    
    return missing_files

def main():
    """主函数"""
    print("🚀 开始问题检查...\n")
    
    # 检查导入
    import_errors = check_imports()
    
    # 检查语法
    syntax_errors = check_syntax()
    
    # 检查依赖
    missing_deps = check_dependencies()
    
    # 检查文件
    missing_files = check_files()
    
    # 总结
    print("\n" + "="*50)
    print("📊 检查结果总结:")
    
    if import_errors:
        print(f"❌ 导入错误: {len(import_errors)} 个")
        for module, error in import_errors:
            print(f"   - {module}: {error}")
    else:
        print("✅ 导入检查通过")
    
    if syntax_errors:
        print(f"❌ 语法错误: {len(syntax_errors)} 个")
        for file, error in syntax_errors:
            print(f"   - {file}: {error}")
    else:
        print("✅ 语法检查通过")
    
    if missing_deps:
        print(f"❌ 缺失依赖: {len(missing_deps)} 个")
        for dep in missing_deps:
            print(f"   - {dep}")
    else:
        print("✅ 依赖检查通过")
    
    if missing_files:
        print(f"❌ 缺失文件: {len(missing_files)} 个")
        for file in missing_files:
            print(f"   - {file}")
    else:
        print("✅ 文件检查通过")
    
    total_errors = len(import_errors) + len(syntax_errors) + len(missing_deps) + len(missing_files)
    
    if total_errors == 0:
        print("\n🎉 所有检查通过！项目状态良好")
        return 0
    else:
        print(f"\n⚠️ 发现 {total_errors} 个问题需要修复")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 