#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图片批量星级标记工具 (GUI版本)
根据低质量图片文件夹中的文件名，在主文件夹中匹配同名RAW文件并自动添加星级评级
"""

import os
import re
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, font
from pathlib import Path
import threading

class RatingToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片批量星级标记工具")
        self.root.geometry("900x650")
        
        # 设置更好的字体
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=11)
        text_font = font.Font(family="Microsoft YaHei UI", size=11)
        
        # 设置全局字体样式
        style = ttk.Style()
        style.configure("TLabel", font=("Microsoft YaHei UI", 11))
        style.configure("TButton", font=("Microsoft YaHei UI", 11))
        style.configure("TLabelframe.Label", font=("Microsoft YaHei UI", 11, "bold"))
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="12")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件夹选择部分
        folder_frame = ttk.LabelFrame(main_frame, text="文件夹选择", padding="12")
        folder_frame.pack(fill=tk.X, pady=8)
        
        # JPEG文件夹选择
        ttk.Label(folder_frame, text="低质量JPEG文件夹:").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.jpeg_folder_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.jpeg_folder_var, width=50, font=text_font).grid(row=0, column=1, sticky=tk.W)
        ttk.Button(folder_frame, text="浏览...", command=self.browse_jpeg_folder).grid(row=0, column=2, padx=8)
        
        # 主文件夹选择
        ttk.Label(folder_frame, text="RAW文件主文件夹:").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.main_folder_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.main_folder_var, width=50, font=text_font).grid(row=1, column=1, sticky=tk.W)
        ttk.Button(folder_frame, text="浏览...", command=self.browse_main_folder).grid(row=1, column=2, padx=8)
        
        # 星级选择
        rating_frame = ttk.LabelFrame(main_frame, text="星级设置", padding="12")
        rating_frame.pack(fill=tk.X, pady=8)
        
        ttk.Label(rating_frame, text="星级评级 (1-5):").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.rating_var = tk.IntVar(value=4)
        rating_scale = ttk.Scale(rating_frame, from_=1, to=5, variable=self.rating_var, orient=tk.HORIZONTAL)
        rating_scale.grid(row=0, column=1, sticky=tk.EW, padx=8)
        self.rating_spinbox = ttk.Spinbox(rating_frame, from_=1, to=5, textvariable=self.rating_var, width=5, font=text_font)
        self.rating_spinbox.grid(row=0, column=2, padx=8)
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=12)
        
        ttk.Button(button_frame, text="扫描文件", command=self.scan_files, width=15).pack(side=tk.LEFT, padx=8)
        ttk.Button(button_frame, text="设置星级", command=self.set_rating, width=15).pack(side=tk.LEFT, padx=8)
        ttk.Button(button_frame, text="清除日志", command=self.clear_log, width=15).pack(side=tk.RIGHT, padx=8)
        
        # 文件列表框架
        files_frame = ttk.LabelFrame(main_frame, text="匹配的文件", padding="12")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=8)
        
        # 创建带滚动条的列表框
        self.file_list = tk.Listbox(files_frame, font=text_font)
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="12")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=8)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=text_font)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, font=text_font)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 存储匹配文件
        self.matching_files = []
        
        # 检查ExifTool
        self.check_exiftool()
        
        # 设置高DPI感知（减少模糊）
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

    def log(self, message):
        """向日志区域添加消息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # 自动滚动到最新内容
        
    def clear_log(self):
        """清除日志区域"""
        self.log_text.delete(1.0, tk.END)
        
    def check_exiftool(self):
        """检查ExifTool是否已安装"""
        try:
            subprocess.run(['exiftool', '-ver'], capture_output=True, text=True)
            self.log("ExifTool 已安装 ✓")
        except FileNotFoundError:
            self.log("错误: 未找到ExifTool。请先安装ExifTool后再运行此脚本。")
            self.log("安装说明: https://exiftool.org/install.html")
            messagebox.showerror("错误", "未找到ExifTool\n请先安装ExifTool后再运行此脚本。")
            
    def browse_jpeg_folder(self):
        """浏览选择JPEG文件夹"""
        folder = filedialog.askdirectory(title="选择低质量JPEG文件夹")
        if folder:
            self.jpeg_folder_var.set(folder)
            
    def browse_main_folder(self):
        """浏览选择主文件夹"""
        folder = filedialog.askdirectory(title="选择RAW文件主文件夹")
        if folder:
            self.main_folder_var.set(folder)
    
    def get_file_basenames(self, folder_path, extensions=None):
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
            self.log(f"读取文件夹时出错: {e}")
            return [], []
            
        return files, basenames
    
    def find_matching_files(self, main_folder, basenames_to_match):
        """在主文件夹中查找所有与指定基本名称匹配的文件（不区分大小写，不限扩展名）"""
        matching_files = []
        basenames_lower = {b.lower() for b in basenames_to_match}  # Use a set for faster lookups

        try:
            for item in Path(main_folder).iterdir():
                if item.is_file():
                    if item.stem.lower() in basenames_lower:
                        matching_files.append(item)
        except Exception as e:
            self.log(f"查找匹配文件时出错: {e}")

        return matching_files
    
    def set_rating_with_exiftool(self, files, rating=4):
        """使用ExifTool为文件设置星级评级"""
        success_files = []
        failed_files = []

        # 获取控制台编码
        console_encoding = sys.stdout.encoding or sys.getfilesystemencoding() or 'utf-8'
        
        # 更新状态
        total = len(files)
        self.status_var.set(f"正在处理文件... (0/{total})")

        for i, file in enumerate(files):
            try:
                file_path_raw_str = str(file)
                file_path_str = file_path_raw_str.replace('\u200e', '')
                cmd = ['exiftool', f'-XMP:Rating={rating}', '-overwrite_original', file_path_str]

                # 运行ExifTool
                result = subprocess.run(cmd, capture_output=True, check=False)

                if result.returncode == 0:
                    success_files.append(file_path_str)
                    self.log(f"成功: {file_path_str}")
                else:
                    failed_files.append(file_path_str)
                    stderr_output = result.stderr.decode(console_encoding, errors='replace').strip()
                    self.log(f"失败: {file_path_str} - {stderr_output}")
                
                # 更新状态
                self.status_var.set(f"正在处理文件... ({i+1}/{total})")
                self.root.update()
            except Exception as e:
                failed_files.append(str(file))
                self.log(f"处理文件时出错: {file} - {e}")

        return success_files, failed_files
    
    def write_log(self, success_files, failed_files):
        """将处理结果写入日志文件"""
        try:
            with open("rating_log.txt", "w", encoding="utf-8") as log:
                log.write("=== 成功处理的文件 ===\n")
                for file in success_files:
                    log.write(f"{file}\n")
                
                log.write("\n=== 处理失败的文件 ===\n")
                for file in failed_files:
                    log.write(f"{file}\n")
            
            self.log(f"日志已保存至 rating_log.txt")
        except Exception as e:
            self.log(f"写入日志文件时出错: {e}")
    
    def scan_files(self):
        """扫描文件并更新UI"""
        # 清空列表
        self.file_list.delete(0, tk.END)
        self.matching_files = []
        
        # 获取文件夹路径
        jpeg_folder = self.jpeg_folder_var.get()
        main_folder = self.main_folder_var.get()
        
        if not jpeg_folder or not os.path.isdir(jpeg_folder):
            messagebox.showerror("错误", "请选择有效的JPEG文件夹")
            return
            
        if not main_folder or not os.path.isdir(main_folder):
            messagebox.showerror("错误", "请选择有效的主文件夹")
            return
        
        # 更新状态
        self.status_var.set("正在扫描文件...")
        self.root.update()
        
        # 获取JPEG文件列表
        jpeg_extensions = ['.jpg', '.jpeg', '.JPG', '.JPEG']
        jpeg_files, jpeg_basenames = self.get_file_basenames(jpeg_folder, jpeg_extensions)
        
        if not jpeg_files:
            messagebox.showinfo("提示", f"在 '{jpeg_folder}' 中未找到任何JPEG文件")
            self.status_var.set("就绪")
            return
        
        self.log(f"在 '{jpeg_folder}' 中找到 {len(jpeg_files)} 个JPEG文件")
        
        # 查找匹配的文件
        self.log(f"正在 '{main_folder}' 中查找匹配的文件...")
        self.matching_files = self.find_matching_files(main_folder, jpeg_basenames)
        
        if not self.matching_files:
            messagebox.showinfo("提示", "未找到任何匹配的文件")
            self.status_var.set("就绪")
            return
        
        # 更新列表
        for file in self.matching_files:
            self.file_list.insert(tk.END, str(file))
        
        self.log(f"找到 {len(self.matching_files)} 个匹配的文件")
        self.status_var.set(f"找到 {len(self.matching_files)} 个匹配文件")
    
    def set_rating(self):
        """设置星级评级"""
        if not self.matching_files:
            messagebox.showinfo("提示", "请先扫描文件")
            return
        
        # 获取星级
        rating = self.rating_var.get()
        
        # 确认
        if not messagebox.askyesno("确认", f"确认为这 {len(self.matching_files)} 个文件设置 {rating} 星级评级?"):
            return
        
        # 创建线程执行评级任务
        thread = threading.Thread(target=self.run_rating_task, args=(rating,))
        thread.daemon = True
        thread.start()
    
    def run_rating_task(self, rating):
        """在线程中执行评级任务"""
        self.log(f"正在设置 {rating} 星级评级...")
        
        # 设置星级评级
        success_files, failed_files = self.set_rating_with_exiftool(self.matching_files, rating)
        
        # 输出结果
        self.log(f"处理完成:")
        self.log(f"- 成功: {len(success_files)} 个文件")
        self.log(f"- 失败: {len(failed_files)} 个文件")
        
        # 写入日志
        self.write_log(success_files, failed_files)
        
        # 更新状态
        self.status_var.set(f"完成 - 成功: {len(success_files)}, 失败: {len(failed_files)}")
        
        # 显示结果对话框
        self.root.after(0, lambda: messagebox.showinfo("处理完成", 
                                               f"星级评级设置完成\n成功: {len(success_files)} 个文件\n失败: {len(failed_files)} 个文件"))

def main():
    root = tk.Tk()
    app = RatingToolApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 