# 间隔特定时间，按下某个按键
# 需要安装 keyboard 库：pip install keyboard
import keyboard
import time

key = input('请输入要按的键（如 tab、space、a、b、1、2 等）：')

interval = float(input('请输入按键间隔时间（秒）：'))
print(f'每{interval}秒按一次tab键，按{key}暂停/恢复，按 Ctrl+c 结束程序')
paused = True # 初始状态为暂停      
s_end = True
def toggle_pause():
    global paused
    paused = not paused
    print("已暂停" if paused else "已恢复")

def end():
    global s_end
    s_end = False
    print("Ctrl+c 被触发，程序结束。")

keyboard.add_hotkey('ctrl+c', end)
keyboard.add_hotkey(key, toggle_pause)

while s_end:
    if paused:
        event = keyboard.read_event()
    else:
        keyboard.press_and_release('tab')
        print(f'按下了tab键')
        time.sleep(interval)