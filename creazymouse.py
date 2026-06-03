# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import LabelFrame, Radiobutton, Entry, Label, messagebox
from pynput.mouse import Button, Controller
import keyboard
import winsound
import ctypes
import sys
import random
import threading
import math
import configparser
import os
import subprocess


def is_admin():
    """检测是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(f'"{arg}"' for arg in sys.argv), None,
                                        1)
    sys.exit(0)


if not is_admin():
    run_as_admin()

# 默认参数配置
CFG_HIGH_BASE = 0.02
CFG_HIGH_RAND = 0.01
CFG_LOW_BASE = 1.0
CFG_LOW_RAND = 0.1
CFG_CUST_BASE_DEFAULT = 0.08
CFG_CUST_RAND_DEFAULT = 0.02
CFG_OFFSET_PX_DEFAULT = 7
MAX_OFFSET_PX = 30
MIN_BASE_INTERVAL = 0.01
MIN_RAND_FLOAT = 0
GAUSSIAN_SIGMA_FACTOR = 0.5

DEFAULT_START_HOT_KEY = 'alt+1'
DEFAULT_STOP_HOT_KEY = 'alt+2'
CONFIG_FILE = "hotkey_config.ini"


def resource_path(relative_path):
    """获取资源文件的绝对路径（支持PyInstaller打包）"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class SimpleHotkeySettings:
    """快捷键设置窗口"""

    def __init__(self, parent=None, on_close_callback=None):
        self.parent = parent
        self.on_close_callback = on_close_callback
        if self.parent and not self.parent.winfo_exists():
            self.parent = None
        self.config_file = resource_path(CONFIG_FILE)
        self.setting_window = None
        self.DEFAULT_HOTKEYS = {
            'start': DEFAULT_START_HOT_KEY,
            'stop': DEFAULT_STOP_HOT_KEY
        }
        self.hotkeys = self.DEFAULT_HOTKEYS.copy()
        self.modify_buttons = []
        self.load_config()
        self.create_window()

        try:
            self.window.iconbitmap(resource_path("creazymouse.ico"))
        except Exception:
            pass

    def is_open(self):
        try:
            return self.window.winfo_exists()
        except:
            return False

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                config = configparser.ConfigParser()
                config.read(self.config_file, encoding='utf-8')
                if 'Hotkeys' in config:
                    start_hotkey = config['Hotkeys'].get('start', self.DEFAULT_HOTKEYS['start']).strip()
                    stop_hotkey = config['Hotkeys'].get('stop', self.DEFAULT_HOTKEYS['stop']).strip()
                    self.hotkeys['start'] = start_hotkey if start_hotkey else self.DEFAULT_HOTKEYS['start']
                    self.hotkeys['stop'] = stop_hotkey if stop_hotkey else self.DEFAULT_HOTKEYS['stop']
            except Exception as e:
                messagebox.showwarning("警告", f"加载配置失败，使用默认值：{str(e)}")
                self.save_config()
        else:
            self.save_config()

    def save_config(self):
        if not self.hotkeys['start'] or not self.hotkeys['stop']:
            messagebox.showwarning("警告", "快捷键不能为空，保存失败！")
            return False
        try:
            config = configparser.ConfigParser()
            config['Hotkeys'] = self.hotkeys
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")
            return False

    def create_window(self):
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.window.transient(self.parent)
        self.window.title("快捷键设置")
        window_width = 300
        window_height = 200
        self.window.geometry(f"{window_width}x{window_height}")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
        # 居中显示
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        tk.Label(self.window, text="快捷键设置", font=("", 12, "bold")).pack(pady=10)

        start_frame = tk.Frame(self.window)
        start_frame.pack(pady=5)
        tk.Label(start_frame, text="启动:", width=6).pack(side=tk.LEFT)
        self.start_var = tk.StringVar(value=self.hotkeys['start'])
        tk.Label(start_frame, textvariable=self.start_var, width=15, relief="sunken", padx=5, pady=2).pack(side=tk.LEFT,
                                                                                                           padx=5)
        start_btn = tk.Button(start_frame, text="修改", width=6, command=lambda: self.set_hotkey('start'))
        start_btn.pack(side=tk.LEFT)
        self.modify_buttons.append(start_btn)

        stop_frame = tk.Frame(self.window)
        stop_frame.pack(pady=5)
        tk.Label(stop_frame, text="停止:", width=6).pack(side=tk.LEFT)
        self.stop_var = tk.StringVar(value=self.hotkeys['stop'])
        tk.Label(stop_frame, textvariable=self.stop_var, width=15, relief="sunken", padx=5, pady=2).pack(side=tk.LEFT,
                                                                                                         padx=5)
        stop_btn = tk.Button(stop_frame, text="修改", width=6, command=lambda: self.set_hotkey('stop'))
        stop_btn.pack(side=tk.LEFT)
        self.modify_buttons.append(stop_btn)

        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="重置", width=8, command=self.reset_hotkeys).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="保存", width=8, command=self.save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="关闭", width=8, command=self.on_window_close).pack(side=tk.LEFT, padx=5)

    def reset_hotkeys(self):
        if self.setting_window and self.setting_window.winfo_exists():
            self.setting_window.grab_release()
            self.setting_window.destroy()
            self.setting_window = None
        self.hotkeys = self.DEFAULT_HOTKEYS.copy()
        self.start_var.set(self.DEFAULT_HOTKEYS['start'])
        self.stop_var.set(self.DEFAULT_HOTKEYS['stop'])
        messagebox.showinfo("重置成功", "所有快捷键已恢复默认！\n请点击【保存】生效")

    def normalize_key(self, keysym):
        """标准化按键名称"""
        key_map = {
            'return': 'enter', 'escape': 'esc', 'delete': 'del', 'backspace': 'backspace',
            'tab': 'tab', 'space': 'space', 'kp_0': '0', 'kp_1': '1', 'kp_2': '2', 'kp_3': '3',
            'kp_4': '4', 'kp_5': '5', 'kp_6': '6', 'kp_7': '7', 'kp_8': '8', 'kp_9': '9',
            'kp_add': '+', 'kp_subtract': '-', 'kp_multiply': '*', 'kp_divide': '/',
            'kp_decimal': '.', 'kp_enter': 'enter'
        }
        if keysym.startswith('f') and keysym[1:].isdigit():
            return keysym.upper()
        if len(keysym) == 1 and keysym.isalpha():
            return keysym.lower()
        return key_map.get(keysym.lower(), keysym.lower())

    def set_hotkey(self, hotkey_type):
        if self.setting_window and self.setting_window.winfo_exists():
            self.setting_window.lift()
            self.setting_window.focus_force()
            return

        self.setting_window = tk.Toplevel(self.window)
        self.setting_window.title(f"设置{'启动' if hotkey_type == 'start' else '停止'}快捷键")
        setting_window_width = 300
        setting_window_height = 150
        self.setting_window.geometry(f"{setting_window_width}x{setting_window_height}")
        self.setting_window.resizable(False, False)
        self.setting_window.grab_set()
        self.setting_window.focus_force()
        self.disable_modify_buttons(True)

        try:
            self.setting_window.iconbitmap(resource_path("creazymouse.ico"))
        except Exception:
            pass

        self.setting_window.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - setting_window_width) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - setting_window_height) // 2
        self.setting_window.geometry(f"{setting_window_width}x{setting_window_height}+{x}+{y}")

        tip_label = tk.Label(self.setting_window, text="请按下新的快捷键组合\n（按ESC取消，按Enter确认）", pady=5)
        tip_label.pack()
        key_label = tk.Label(self.setting_window, text="等待按键...", font=("Arial", 10, "bold"))
        key_label.pack(pady=5)

        pressed_modifiers = set()
        pressed_key = None
        is_capturing = True
        modifier_mapping = {
            'control_l': 'ctrl', 'control_r': 'ctrl',
            'shift_l': 'shift', 'shift_r': 'shift',
            'alt_l': 'alt', 'alt_r': 'alt',
            'win_l': 'win', 'win_r': 'win'
        }

        def key_event_record(event):
            if not is_capturing or not key_label.winfo_exists():
                return
            nonlocal pressed_key
            keysym = event.keysym.lower()

            if keysym == 'escape':
                close_setting_window()
                return
            elif keysym == 'return':
                if pressed_modifiers or pressed_key:
                    finish_capture()
                return

            if keysym in modifier_mapping:
                pressed_modifiers.add(modifier_mapping[keysym])
            else:
                normalized_key = self.normalize_key(keysym)
                if (normalized_key not in ['??', 'caps_lock', 'num_lock', 'scroll_lock']
                        and not normalized_key.startswith('iso_')):
                    pressed_key = normalized_key
            update_display()

        def update_display():
            if not is_capturing or not key_label.winfo_exists():
                return
            modifier_order = ['ctrl', 'alt', 'shift', 'win']
            hotkey_parts = [mod for mod in modifier_order if mod in pressed_modifiers]
            if pressed_key:
                hotkey_parts.append(pressed_key)
            display_text = '+'.join(hotkey_parts) if hotkey_parts else "等待按键..."
            if hotkey_parts and not pressed_key:
                display_text += "（无效：需包含主键）"
            current_hotkey = '+'.join(hotkey_parts) if (hotkey_parts and pressed_key) else ""
            if current_hotkey and current_hotkey == self.hotkeys['stop' if hotkey_type == 'start' else 'start']:
                display_text += "（重复：已被占用）"
            key_label.config(text=display_text)

        def finish_capture():
            nonlocal is_capturing
            is_capturing = False
            modifier_order = ['ctrl', 'alt', 'shift', 'win']
            hotkey_parts = [mod for mod in modifier_order if mod in pressed_modifiers]
            if pressed_key:
                hotkey_parts.append(pressed_key)
            hotkey = '+'.join(hotkey_parts)

            if not hotkey:
                messagebox.showwarning("提示", "快捷键不能为空！")
                is_capturing = True
                return
            if pressed_key is None:
                messagebox.showwarning("提示", "快捷键必须包含一个非修饰键（如A/1/F5等）！")
                is_capturing = True
                return

            other_type = 'stop' if hotkey_type == 'start' else 'start'
            if hotkey == self.hotkeys[other_type]:
                messagebox.showwarning("提示", f"该快捷键已被{('停止' if other_type == 'stop' else '启动')}功能占用！")
                is_capturing = True
                return

            if hotkey_type == 'start':
                self.start_var.set(hotkey)
                self.hotkeys['start'] = hotkey
            else:
                self.stop_var.set(hotkey)
                self.hotkeys['stop'] = hotkey

            messagebox.showinfo("成功", f"快捷键已设置为: {hotkey}")
            close_setting_window()

        def close_setting_window():
            nonlocal is_capturing
            is_capturing = False
            try:
                self.setting_window.unbind('<KeyPress>')
                self.setting_window.unbind('<KeyRelease>')
                self.setting_window.grab_release()
                self.setting_window.destroy()
            except:
                pass
            self.setting_window = None
            self.disable_modify_buttons(False)
            if self.window and self.window.winfo_exists():
                self.window.focus_force()

        self.setting_window.bind('<KeyPress>', key_event_record)
        self.setting_window.bind('<KeyRelease>', key_event_record)
        self.setting_window.protocol("WM_DELETE_WINDOW", close_setting_window)

        btn_frame = tk.Frame(self.setting_window)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="确认", command=finish_capture, width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=close_setting_window, width=8).pack(side=tk.LEFT, padx=5)

    def disable_modify_buttons(self, disable=True):
        state = "disabled" if disable else "normal"
        for btn in self.modify_buttons:
            if btn.winfo_exists():
                btn.config(state=state)

    def on_window_close(self):
        if self.on_close_callback:
            self.on_close_callback()
        try:
            if self.setting_window and self.setting_window.winfo_exists():
                self.setting_window.grab_release()
                self.setting_window.destroy()
        except:
            pass
        try:
            if self.parent:
                self.window.destroy()
            else:
                self.window.quit()
                self.window.destroy()
        except:
            pass

    def save(self):
        if self.save_config():
            messagebox.showinfo("成功", "设置已保存，程序将重启生效！")
            self.restart_app()

    def restart_app(self):
        keyboard.unhook_all()
        if self.parent:
            self.parent.destroy()
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit()


class AutoClickerApp(tk.Tk):
    """主应用程序"""

    def __init__(self):
        super().__init__()
        self.title("疯狂的老鼠")

        try:
            self.iconbitmap(resource_path("creazymouse.ico"))
        except Exception as e:
            pass

        window_width = 520
        window_height = 360
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        self.mouse_ctrl = Controller()

        self.running = False
        self.click_thread = None
        self.stop_event = None
        self.start_lock = threading.Lock()
        self.hotkey_settings_win = None

        # 界面变量
        self.act_var = tk.IntVar(value=0)
        self.gear_var = tk.IntVar(value=2)
        self.offset_var = tk.IntVar(value=1)
        self.base_interval = tk.DoubleVar(value=CFG_CUST_BASE_DEFAULT)
        self.rand_float = tk.DoubleVar(value=CFG_CUST_RAND_DEFAULT)
        self.offset_px = tk.IntVar(value=CFG_OFFSET_PX_DEFAULT)

        self.all_entries = []
        self.create_widgets()
        self.gear_var.trace_add("write", self.on_gear_switch)
        self.offset_var.trace_add("write", self.on_offset_switch)
        self.bind("<Button-1>", self.on_global_click)

        # 加载并注册快捷键
        self.start_hotkey, self.stop_hotkey = self.load_hotkey_config()
        self.update_hotkey_label()
        self.register_hotkeys()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_hotkey_config(self):
        config_file = resource_path(CONFIG_FILE)
        start = DEFAULT_START_HOT_KEY
        stop = DEFAULT_STOP_HOT_KEY
        if os.path.exists(config_file):
            try:
                config = configparser.ConfigParser()
                config.read(config_file, encoding='utf-8')
                if 'Hotkeys' in config:
                    start = config['Hotkeys'].get('start', start).strip()
                    stop = config['Hotkeys'].get('stop', stop).strip()
                    if not start: start = DEFAULT_START_HOT_KEY
                    if not stop: stop = DEFAULT_STOP_HOT_KEY
            except Exception:
                pass
        return start, stop

    def register_hotkeys(self):
        try:
            keyboard.unhook_all()
        except:
            pass
        keyboard.add_hotkey(self.start_hotkey, self.start_click)
        keyboard.add_hotkey(self.stop_hotkey, self.stop_click)

    def update_hotkey_label(self):
        try:
            self.hotkey_label.config(text=f"启动: {self.start_hotkey} | 停止: {self.stop_hotkey}")
        except:
            pass

    def blur_all_entries(self, event=None):
        self.focus()
        self.check_all_input()

    def on_global_click(self, event):
        if event.widget not in self.all_entries:
            self.blur_all_entries()

    def create_widgets(self):
        top_frame = tk.Frame(self)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        self.setting_btn = tk.Button(top_frame, text="⚙ 快捷键设置", font=("", 10), command=self.open_hotkey_settings)
        self.setting_btn.pack(side=tk.LEFT, padx=(0, 15))
        self.state_label = tk.Label(top_frame, text="状态：已停止", fg="red", font=("", 16, "bold"))
        self.state_label.pack(side=tk.LEFT, expand=True)
        self.hotkey_label = tk.Label(top_frame, text="", font=("", 9), fg="gray")
        self.hotkey_label.pack(side=tk.RIGHT)

        row_idx = 1
        info_label = tk.Label(self, text="提示：启动/停止快捷键可点击左上角按钮修改", font=("", 9), fg="gray")
        info_label.grid(row=row_idx, column=0, columnspan=2, pady=(0, 10))
        row_idx += 1

        # 动作选择
        frame_act = LabelFrame(self, text="点击/滚动动作", font=("", 10, "bold"))
        frame_act.grid(row=row_idx, column=0, columnspan=2, padx=15, pady=8, sticky="ew")
        self.act_rbs = [
            Radiobutton(frame_act, text="鼠标左键", variable=self.act_var, value=0),
            Radiobutton(frame_act, text="鼠标右键", variable=self.act_var, value=1),
            Radiobutton(frame_act, text="滚轮上滚", variable=self.act_var, value=2),
            Radiobutton(frame_act, text="滚轮下滚", variable=self.act_var, value=3)
        ]
        for i, rb in enumerate(self.act_rbs):
            rb.grid(row=0, column=i, padx=12, pady=5)
        row_idx += 1

        # 速度档位
        frame_gear = LabelFrame(self, text="点击档位", font=("", 10, "bold"))
        frame_gear.grid(row=row_idx, column=0, columnspan=2, padx=15, pady=8, sticky="ew")
        self.rb_high = Radiobutton(frame_gear, text=f"高速({CFG_HIGH_BASE}±{CFG_HIGH_RAND}s)", variable=self.gear_var,
                                   value=0)
        self.rb_low = Radiobutton(frame_gear, text=f"慢速({CFG_LOW_BASE}±{CFG_LOW_RAND}s)", variable=self.gear_var,
                                  value=1)
        self.rb_cust = Radiobutton(frame_gear, text="自定义参数", variable=self.gear_var, value=2)
        self.gear_rbs = [self.rb_high, self.rb_low, self.rb_cust]
        for i, rb in enumerate(self.gear_rbs):
            rb.grid(row=0, column=i, padx=12, pady=5)
        row_idx += 1

        # 间隔参数
        frame_interval = LabelFrame(self, text="点击间隔参数 (秒)", font=("", 10, "bold"))
        frame_interval.grid(row=row_idx, column=0, columnspan=2, padx=15, pady=8, sticky="ew")
        Label(frame_interval, text="基础间隔:", font=("", 9)).grid(row=0, column=0, padx=10, pady=8, sticky="e")
        self.ent_base = Entry(frame_interval, textvariable=self.base_interval, width=12)
        self.ent_base.grid(row=0, column=1, padx=5, pady=8, sticky="w")
        Label(frame_interval, text="随机浮动:", font=("", 9)).grid(row=0, column=2, padx=10, pady=8, sticky="e")
        self.ent_rand = Entry(frame_interval, textvariable=self.rand_float, width=12)
        self.ent_rand.grid(row=0, column=3, padx=5, pady=8, sticky="w")
        for entry in [self.ent_base, self.ent_rand]:
            entry.bind("<Return>", self.blur_all_entries)
            entry.bind("<Escape>", self.blur_all_entries)
            self.all_entries.append(entry)
        row_idx += 1

        # 随机偏移
        frame_offset = LabelFrame(self, text="坐标随机偏移 (防检测)", font=("", 10, "bold"))
        frame_offset.grid(row=row_idx, column=0, columnspan=2, padx=15, pady=8, sticky="ew")
        self.rb_no_off = Radiobutton(frame_offset, text="无偏移", variable=self.offset_var, value=0)
        self.rb_rand_off = Radiobutton(frame_offset, text=f"随机偏移(±{self.offset_px.get()}像素)",
                                       variable=self.offset_var, value=1)
        self.offset_rbs = [self.rb_no_off, self.rb_rand_off]
        Label(frame_offset, text="偏移像素:", font=("", 9)).grid(row=0, column=2, padx=10, pady=8)
        self.ent_px = Entry(frame_offset, textvariable=self.offset_px, width=8)
        self.ent_px.grid(row=0, column=3, padx=5, pady=8)
        self.ent_px.bind("<Return>", self.blur_all_entries)
        self.ent_px.bind("<Escape>", self.blur_all_entries)
        self.all_entries.append(self.ent_px)
        for i, rb in enumerate(self.offset_rbs):
            rb.grid(row=0, column=i, padx=12, pady=5)
        row_idx += 1

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.on_gear_switch()
        self.on_offset_switch()

    def open_hotkey_settings(self):
        if self.hotkey_settings_win and self.hotkey_settings_win.is_open():
            self.hotkey_settings_win.window.lift()
            self.hotkey_settings_win.window.focus_force()
            return

        keyboard.unhook_all()

        def on_settings_close():
            self.register_hotkeys()
            self.hotkey_settings_win = None

        self.hotkey_settings_win = SimpleHotkeySettings(self, on_close_callback=on_settings_close)

    def on_gear_switch(self, *args):
        gear = self.gear_var.get()
        if gear == 0:
            self.base_interval.set(CFG_HIGH_BASE)
            self.rand_float.set(CFG_HIGH_RAND)
            self.ent_base.config(state="disabled")
            self.ent_rand.config(state="disabled")
        elif gear == 1:
            self.base_interval.set(CFG_LOW_BASE)
            self.rand_float.set(CFG_LOW_RAND)
            self.ent_base.config(state="disabled")
            self.ent_rand.config(state="disabled")
        else:
            self.base_interval.set(CFG_CUST_BASE_DEFAULT)
            self.rand_float.set(CFG_CUST_RAND_DEFAULT)
            self.ent_base.config(state="normal")
            self.ent_rand.config(state="normal")

    def on_offset_switch(self, *args):
        if self.offset_var.get() == 0:
            self.ent_px.config(state="disabled")
        else:
            self.ent_px.config(state="normal")

    def check_all_input(self):
        try:
            base_val = float(self.base_interval.get())
            if base_val < MIN_BASE_INTERVAL:
                base_val = MIN_BASE_INTERVAL
        except:
            base_val = CFG_CUST_BASE_DEFAULT
        self.base_interval.set(base_val)

        try:
            rand_val = float(self.rand_float.get())
            if rand_val < MIN_RAND_FLOAT:
                rand_val = MIN_RAND_FLOAT
        except:
            rand_val = CFG_CUST_RAND_DEFAULT
        self.rand_float.set(rand_val)

        try:
            px_val = int(self.offset_px.get())
            if px_val < 0:
                px_val = 0
            elif px_val > MAX_OFFSET_PX:
                px_val = MAX_OFFSET_PX
        except:
            px_val = CFG_OFFSET_PX_DEFAULT
        self.offset_px.set(px_val)

        self.rb_rand_off.config(text=f"随机偏移(±{px_val}像素)")

    def play_start_sound(self):
        winsound.Beep(900, 120)

    def play_stop_sound(self):
        winsound.Beep(350, 180)

    def set_widget_lock(self, is_lock: bool):
        state = "disabled" if is_lock else "normal"
        for rb in self.act_rbs + self.gear_rbs + self.offset_rbs:
            rb.config(state=state)
        self.ent_base.config(state=state if is_lock else ("normal" if self.gear_var.get() == 2 else "disabled"))
        self.ent_rand.config(state=state if is_lock else ("normal" if self.gear_var.get() == 2 else "disabled"))
        self.ent_px.config(state=state if is_lock else ("normal" if self.offset_var.get() == 1 else "disabled"))
        self.setting_btn.config(state=state)

    def get_gaussian_offset(self, max_px):
        """使用Box-Muller变换生成高斯分布的随机偏移，避免超出边界"""
        MAX_RETRIES = 3
        sigma = max_px * GAUSSIAN_SIGMA_FACTOR

        for _ in range(MAX_RETRIES):
            u1 = max(random.random(), 0.001)
            u2 = random.random()
            z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
            radius = abs(z) * sigma

            if radius <= max_px:
                angle = random.uniform(0, 2 * math.pi)
                return round(radius * math.cos(angle)), round(radius * math.sin(angle))

        # 兜底：均匀分布
        radius = random.uniform(0, max_px)
        angle = random.uniform(0, 2 * math.pi)
        return round(radius * math.cos(angle)), round(radius * math.sin(angle))

    def click_loop(self, stop_event: threading.Event):
        act_type = self.act_var.get()
        use_offset = self.offset_var.get() == 1
        off_px = self.offset_px.get()
        base_t = self.base_interval.get()
        rand_t = self.rand_float.get()

        while not stop_event.is_set():
            org_x, org_y = self.mouse_ctrl.position
            if use_offset:
                dx, dy = self.get_gaussian_offset(off_px)
                self.mouse_ctrl.position = (org_x + dx, org_y + dy)

            if act_type == 0:
                self.mouse_ctrl.click(Button.left)
            elif act_type == 1:
                self.mouse_ctrl.click(Button.right)
            elif act_type == 2:
                self.mouse_ctrl.scroll(0, 1)
            elif act_type == 3:
                self.mouse_ctrl.scroll(0, -1)

            if use_offset:
                self.mouse_ctrl.position = (org_x, org_y)

            sleep_t = base_t + random.uniform(0, rand_t)
            if stop_event.wait(timeout=sleep_t):
                break

    def start_click(self):
        with self.start_lock:
            if self.running and self.click_thread and self.click_thread.is_alive():
                self._stop_click_internal()
                if self.click_thread.is_alive():
                    self.click_thread.join()
                self.click_thread = None

            self.stop_event = threading.Event()
            self.running = True
            self.set_widget_lock(True)
            self.state_label.config(text="状态：运行中", fg="green")
            self.play_start_sound()

            self.click_thread = threading.Thread(target=self.click_loop, args=(self.stop_event,), daemon=True)
            self.click_thread.start()

    def _stop_click_internal(self):
        if not self.running:
            return
        self.play_stop_sound()
        self.running = False
        if self.stop_event:
            self.stop_event.set()

    def stop_click(self):
        with self.start_lock:
            if not self.running:
                return
            self._stop_click_internal()
            if self.click_thread and self.click_thread.is_alive():
                self.click_thread.join()
            self.click_thread = None
            self.set_widget_lock(False)
            self.state_label.config(text="状态：已停止", fg="red")

    def on_closing(self):
        if self.hotkey_settings_win and self.hotkey_settings_win.is_open():
            self.hotkey_settings_win.on_window_close()
        self.stop_click()
        keyboard.unhook_all()
        self.destroy()


if __name__ == "__main__":
    app = AutoClickerApp()
    app.mainloop()