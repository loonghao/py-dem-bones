#!/usr/bin/env python
"""
测试py_dem_bones模块是否正确安装和加载
"""
import sys


def main():
    """主函数，测试模块导入和基本功能"""
    print(f"Python版本: {sys.version}")
    print(f"Python解释器路径: {sys.executable}")
    
    try:
        import py_dem_bones
        print(f"成功导入py_dem_bones模块，版本: {py_dem_bones.__version__}")
        
        # 测试基本功能 - 仅检查模块是否正确加载
        print("模块属性:")
        for attr in dir(py_dem_bones):
            if not attr.startswith('__'):
                print(f"  - {attr}")
        
        # 尝试创建一个DemBones对象
        if hasattr(py_dem_bones, 'DemBones'):
            db = py_dem_bones.DemBones()
            print("成功创建DemBones对象")
            
            # 打印对象的方法
            print("DemBones对象方法:")
            for method in dir(db):
                if not method.startswith('__'):
                    print(f"  - {method}")
        
        print("测试完成，模块工作正常！")
        
    except ImportError as e:
        print(f"导入py_dem_bones模块失败: {e}")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()
