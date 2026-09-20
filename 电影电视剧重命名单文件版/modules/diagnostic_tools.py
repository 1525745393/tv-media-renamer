#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影视文件重命名工具 - 诊断工具集
集成所有诊断和测试功能
"""

import sys
import os
import logging
from datetime import datetime

def setup_logging():
    """设置日志系统"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    log_file = f'logs/diagnostic_{datetime.now().strftime("%Y%m%d")}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def run_problem_check():
    """运行问题检查"""
    print("\n🔍 运行问题检查...")
    try:
        from check_problems import main as check_main
        return check_main()
    except ImportError as e:
        print(f"❌ 无法导入check_problems模块: {e}")
        return 1
    except Exception as e:
        print(f"❌ 问题检查失败: {e}")
        return 1

def run_gui_test():
    """运行GUI完整性测试"""
    print("\n🔍 运行GUI完整性测试...")
    try:
        from test_gui import main as test_main
        return test_main()
    except ImportError as e:
        print(f"❌ 无法导入test_gui模块: {e}")
        return 1
    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        return 1

def run_media_renamer_test():
    """运行媒体重命名测试"""
    print("\n🔍 运行媒体重命名测试...")
    try:
        from test_media_renamer import main as media_test_main
        return media_test_main()
    except ImportError as e:
        print(f"❌ 无法导入test_media_renamer模块: {e}")
        return 1
    except Exception as e:
        print(f"❌ 媒体重命名测试失败: {e}")
        return 1

def run_workers_test():
    """运行工作线程测试"""
    print("\n🔍 运行工作线程测试...")
    try:
        from test_workers import main as workers_test_main
        return workers_test_main()
    except ImportError as e:
        print(f"❌ 无法导入test_workers模块: {e}")
        return 1
    except Exception as e:
        print(f"❌ 工作线程测试失败: {e}")
        return 1

def show_menu():
    """显示诊断工具菜单"""
    print("\n" + "="*60)
    print("🔧 影视文件重命名工具 - 诊断工具集")
    print("="*60)
    print("请选择要运行的诊断工具:")
    print("1. 问题检查 (check_problems.py)")
    print("2. GUI完整性测试 (test_gui.py)")
    print("3. 媒体重命名测试 (test_media_renamer.py)")
    print("4. 工作线程测试 (test_workers.py)")
    print("5. 运行所有测试")
    print("0. 退出")
    print("-"*60)

def main():
    """主函数"""
    setup_logging()
    
    while True:
        show_menu()
        
        try:
            choice = input("请输入选择 (0-5): ").strip()
            
            if choice == '0':
                print("👋 退出诊断工具")
                break
            elif choice == '1':
                result = run_problem_check()
                print(f"\n📊 问题检查结果: {'✅ 通过' if result == 0 else '❌ 失败'}")
            elif choice == '2':
                result = run_gui_test()
                print(f"\n📊 GUI测试结果: {'✅ 通过' if result == 0 else '❌ 失败'}")
            elif choice == '3':
                result = run_media_renamer_test()
                print(f"\n📊 媒体重命名测试结果: {'✅ 通过' if result == 0 else '❌ 失败'}")
            elif choice == '4':
                result = run_workers_test()
                print(f"\n📊 工作线程测试结果: {'✅ 通过' if result == 0 else '❌ 失败'}")
            elif choice == '5':
                print("\n🚀 运行所有测试...")
                results = []
                
                results.append(("问题检查", run_problem_check()))
                results.append(("GUI完整性测试", run_gui_test()))
                results.append(("媒体重命名测试", run_media_renamer_test()))
                results.append(("工作线程测试", run_workers_test()))
                
                print("\n" + "="*60)
                print("📊 所有测试结果汇总:")
                passed = 0
                for test_name, result in results:
                    status = "✅ 通过" if result == 0 else "❌ 失败"
                    print(f"  {test_name}: {status}")
                    if result == 0:
                        passed += 1
                
                print(f"\n📈 总体结果: {passed}/{len(results)} 测试通过")
                if passed == len(results):
                    print("🎉 所有测试通过！系统状态良好！")
                else:
                    print("⚠️ 部分测试失败，请检查相关模块")
            else:
                print("❌ 无效选择，请输入 0-5")
                
        except KeyboardInterrupt:
            print("\n👋 用户中断，退出诊断工具")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
        
        if choice != '5':  # 如果不是运行所有测试，等待用户确认
            input("\n按回车键继续...")

if __name__ == "__main__":
    sys.exit(main()) 