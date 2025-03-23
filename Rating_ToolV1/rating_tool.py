#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图片批量星级标记工具
根据低质量图片文件夹中的文件名，在主文件夹中匹配同名RAW文件并自动添加星级评级
"""

import os
import re
import subprocess
from pathlib import Path
import sys

def get_file_basenames(folder_path, extensions=None):
    """获取指定文件夹中所有文件的基本名称（不含扩展名）"""
    files = []
    basenames = []
    
    try:
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                if extensions:
                    if any(file.lower().endswith(ext.lower()) for ext in extensions):
                        files.append(file)
                        basenames.append(os.path.splitext(file)[0])
                else:
                    files.append(file)
                    basenames.append(os.path.splitext(file)[0])
    except Exception as e:
        print(f"读取文件夹时出错: {e}")
        return [], []
        
    return files, basenames

def find_matching_raw_files(raw_folder, basenames):
    """在RAW文件夹中查找匹配的RAW文件"""
    matching_files = []
    raw_extensions = ['.arw', '.raw', '.ARW', '.RAW']
    
    all_raw_files = []
    for ext in raw_extensions:
        all_raw_files.extend(list(Path(raw_folder).glob(f"*{ext}")))
    
    for basename in basenames:
        for raw_file in all_raw_files:
            if raw_file.stem.lower() == basename.lower():
                matching_files.append(raw_file)
                break
    
    return matching_files

def set_rating_with_exiftool(files, rating=4):
    """使用ExifTool为文件设置星级评级"""
    success_files = []
    failed_files = []
    
    for file in files:
        try:
            cmd = ['exiftool', f'-XMP:Rating={rating}', '-overwrite_original', str(file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                success_files.append(str(file))
                print(f"成功: {file}")
            else:
                failed_files.append(str(file))
                print(f"失败: {file} - {result.stderr}")
        except Exception as e:
            failed_files.append(str(file))
            print(f"处理文件时出错: {file} - {e}")
    
    return success_files, failed_files

def write_log(success_files, failed_files):
    """将处理结果写入日志文件"""
    with open("rating_log.txt", "w", encoding="utf-8") as log:
        log.write("=== 成功处理的文件 ===\n")
        for file in success_files:
            log.write(f"{file}\n")
        
        log.write("\n=== 处理失败的文件 ===\n")
        for file in failed_files:
            log.write(f"{file}\n")
    
    print(f"日志已保存至 rating_log.txt")

def check_exiftool():
    """检查ExifTool是否已安装"""
    try:
        subprocess.run(['exiftool', '-ver'], capture_output=True, text=True)
        return True
    except FileNotFoundError:
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("图片批量星级标记工具")
    print("=" * 50)
    
    # 检查ExifTool是否已安装
    if not check_exiftool():
        print("错误: 未找到ExifTool。请先安装ExifTool后再运行此脚本。")
        print("安装说明: https://exiftool.org/install.html")
        return
    
    # 获取低质量JPEG文件夹路径
    jpeg_folder = input("请输入低质量JPEG文件夹路径: ").strip()
    if not os.path.isdir(jpeg_folder):
        print(f"错误: 文件夹 '{jpeg_folder}' 不存在或不是一个有效的目录")
        return
    
    # 获取JPEG文件列表
    jpeg_extensions = ['.jpg', '.jpeg', '.JPG', '.JPEG']
    jpeg_files, jpeg_basenames = get_file_basenames(jpeg_folder, jpeg_extensions)
    
    if not jpeg_files:
        print(f"在 '{jpeg_folder}' 中未找到任何JPEG文件")
        return
    
    print(f"\n在 '{jpeg_folder}' 中找到 {len(jpeg_files)} 个JPEG文件:")
    for file in jpeg_files[:10]:  # 只显示前10个文件
        print(f"- {file}")
    if len(jpeg_files) > 10:
        print(f"... 以及其他 {len(jpeg_files) - 10} 个文件")
    
    # 获取主RAW文件夹路径
    raw_folder = input("\n请输入主RAW文件夹路径: ").strip()
    if not os.path.isdir(raw_folder):
        print(f"错误: 文件夹 '{raw_folder}' 不存在或不是一个有效的目录")
        return
    
    # 查找匹配的RAW文件
    print(f"\n正在 '{raw_folder}' 中查找匹配的RAW文件...")
    matching_raw_files = find_matching_raw_files(raw_folder, jpeg_basenames)
    
    if not matching_raw_files:
        print(f"未找到任何匹配的RAW文件")
        return
    
    print(f"\n找到 {len(matching_raw_files)} 个匹配的RAW文件:")
    for file in matching_raw_files[:10]:  # 只显示前10个文件
        print(f"- {file}")
    if len(matching_raw_files) > 10:
        print(f"... 以及其他 {len(matching_raw_files) - 10} 个文件")
    
    # 询问星级评级
    try:
        rating = int(input("\n请输入要设置的星级评级 (1-5，默认为4): ") or "4")
        if rating < 1 or rating > 5:
            print("星级评级必须在1-5之间，将使用默认值4")
            rating = 4
    except ValueError:
        print("无效的输入，将使用默认值4")
        rating = 4
    
    # 用户确认
    confirm = input(f"\n确认为这 {len(matching_raw_files)} 个RAW文件设置 {rating} 星级评级? (y/n): ").strip().lower()
    if confirm != 'y':
        print("操作已取消")
        return
    
    # 设置星级评级
    print("\n正在设置星级评级...")
    success_files, failed_files = set_rating_with_exiftool(matching_raw_files, rating)
    
    # 输出结果
    print(f"\n处理完成:")
    print(f"- 成功: {len(success_files)} 个文件")
    print(f"- 失败: {len(failed_files)} 个文件")
    
    # 写入日志
    write_log(success_files, failed_files)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已被用户中断")
    except Exception as e:
        print(f"\n发生错误: {e}")
    
    input("\n按Enter键退出...") 