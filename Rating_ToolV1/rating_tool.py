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

def find_matching_files(main_folder, basenames_to_match):
    """在主文件夹中查找所有与指定基本名称匹配的文件（不区分大小写，不限扩展名）"""
    matching_files = []
    basenames_lower = {b.lower() for b in basenames_to_match} # Use a set for faster lookups

    try:
        for item in Path(main_folder).iterdir():
            if item.is_file():
                if item.stem.lower() in basenames_lower:
                    matching_files.append(item)
    except Exception as e:
        print(f"查找匹配文件时出错: {e}")

    return matching_files

def set_rating_with_exiftool(files, rating=4):
    """使用ExifTool为文件设置星级评级"""
    success_files = []
    failed_files = []

    # Get the likely console encoding, default to utf-8 if unsure
    console_encoding = sys.stdout.encoding or sys.getfilesystemencoding() or 'utf-8'

    for file in files:
        try:
            file_path_raw_str = str(file)
            file_path_str = file_path_raw_str.replace('\u200e', '')
            cmd = ['exiftool', f'-XMP:Rating={rating}', '-overwrite_original', file_path_str]

            # Run exiftool, capturing raw bytes for stdout/stderr
            result = subprocess.run(cmd, capture_output=True, check=False) # Removed text=True, encoding='utf-8'

            if result.returncode == 0:
                success_files.append(file_path_str)
                # Decode stdout for success message (optional, using detected encoding with fallback)
                # stdout_msg = result.stdout.decode(console_encoding, errors='replace').strip()
                # print(f"成功: {file_path_str} ({stdout_msg})")
                print(f"成功: {file_path_str}") # Simpler success message
            else:
                failed_files.append(file_path_str)
                # Decode stderr using detected encoding (or fallback) only on error
                stderr_output = result.stderr.decode(console_encoding, errors='replace').strip()
                original_vs_sanitized = f"{file_path_raw_str}" if file_path_raw_str == file_path_str else f"{file_path_raw_str} (Sanitized: {file_path_str})"
                print(f"失败: {original_vs_sanitized} - {stderr_output}")
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
    
    # --- REVISED Path Input Logic ---
    jpeg_folder_raw = input("请输入低质量JPEG文件夹路径: ").strip()
    jpeg_folder = jpeg_folder_raw.replace('\u200e', '') # Attempt to sanitize

    # Check if the sanitized path exists
    if not os.path.isdir(jpeg_folder):
        # If sanitized failed, check if the raw path (with bad char) exists
        if os.path.isdir(jpeg_folder_raw):
             # If the raw path exists, the folder name *on disk* is the problem
             print(f"\n错误: 检测到文件夹名称包含特殊（可能隐藏）的字符 (U+200E):")
             print(f"  '{jpeg_folder_raw}'")
             print(f"虽然脚本可能找到此文件夹，但 ExifTool 无法处理带有此字符的路径。")
             print(f"请在文件浏览器中重命名此文件夹，确保名称开头没有隐藏字符，然后重试脚本。")
             input("\n按Enter键退出...") # Keep window open
             return # Exit script
        else:
            # Neither path exists
            print(f"错误: 文件夹 '{jpeg_folder_raw}' 不存在或不是一个有效的目录")
            return
    elif jpeg_folder != jpeg_folder_raw:
        # Sanitized path exists, but was different from raw input (warn user)
        print(f"警告: 输入的路径包含特殊字符，已清理为 '{jpeg_folder}'。将使用此清理后的路径。")
        print(f"     原始输入: '{jpeg_folder_raw}'")

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
    
    # --- REVISED Path Input Logic ---
    main_folder_raw = input("\n请输入包含要评级文件的主文件夹路径: ").strip()
    main_folder = main_folder_raw.replace('\u200e', '') # Attempt to sanitize

    # Check if the sanitized path exists
    if not os.path.isdir(main_folder):
        # If sanitized failed, check if the raw path (with bad char) exists
        if os.path.isdir(main_folder_raw):
             # If the raw path exists, the folder name *on disk* is the problem
             print(f"\n错误: 检测到文件夹名称包含特殊（可能隐藏）的字符 (U+200E):")
             print(f"  '{main_folder_raw}'")
             print(f"虽然脚本可能找到此文件夹，但 ExifTool 无法处理带有此字符的路径。")
             print(f"请在文件浏览器中重命名此文件夹，确保名称开头没有隐藏字符，然后重试脚本。")
             input("\n按Enter键退出...") # Keep window open
             return # Exit script
        else:
            # Neither path exists
            print(f"错误: 文件夹 '{main_folder_raw}' 不存在或不是一个有效的目录")
            return
    elif main_folder != main_folder_raw:
         # Sanitized path exists, but was different from raw input (warn user)
        print(f"警告: 输入的路径包含特殊字符，已清理为 '{main_folder}'。将使用此清理后的路径。")
        print(f"     原始输入: '{main_folder_raw}'")

    # 查找匹配的文件
    print(f"\n正在 '{main_folder}' 中查找匹配的文件...")
    matching_files = find_matching_files(main_folder, jpeg_basenames)
    
    if not matching_files:
        print(f"未找到任何匹配的文件")
        return
    
    print(f"\n找到 {len(matching_files)} 个匹配的文件:")
    for file in matching_files[:10]:  # 只显示前10个文件
        print(f"- {file}")
    if len(matching_files) > 10:
        print(f"... 以及其他 {len(matching_files) - 10} 个文件")
    
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
    confirm = input(f"\n确认为这 {len(matching_files)} 个文件设置 {rating} 星级评级? (y/n): ").strip().lower()
    if confirm != 'y':
        print("操作已取消")
        return
    
    # 设置星级评级
    print("\n正在设置星级评级...")
    success_files, failed_files = set_rating_with_exiftool(matching_files, rating)
    
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