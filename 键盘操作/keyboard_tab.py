# 需要安装 keyboard 库：pip install keyboard
# 注意：该脚本需要管理员权限运行，Windows 下请以管理员身份运行命令提示符或 PowerShell
# 间隔特定时间，按下某个按键

import keyboard
import time
def keyboard_tab():
    # key = input('请设置暂停/恢复的按键（如 tab、space、a、b、1、2 等）：')
    # interval = float(input('请输入按键间隔时间（秒）：'))

    key = 'space'
    interval = 0.8

    print(f'每{interval}秒按一次tab键，按{key}暂停/恢复，按 Ctrl+x 结束程序')
    state = { # 使用字典共享状态，避免变量问题
        'paused' : True, # 初始状态为暂停  
        'running' : True
    }
    
    def toggle_pause():
        state['paused'] = not state['paused']
        print("已暂停" if state['paused'] else "已恢复")

    def end():
        state['running'] = False
        print("Ctrl+x 被触发，程序结束。")

    keyboard.add_hotkey('ctrl+x', end)
    keyboard.add_hotkey(key, toggle_pause)

    while state['running']:
        if  not state['paused']:
            keyboard.press_and_release('tab')
            print(f'按下了tab键')
            time.sleep(interval)
        else:
            time.sleep(0.1)

keyboard_tab()  