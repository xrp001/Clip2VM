# Clip2VM — Cross-Host Clipboard Delivery Tool

Ctrl+Shift+Q 将控制机剪贴板内容直接键入到虚拟机窗口，也支持一次投递到多个窗口。**VM 内部无需安装任何东西。**

## 原理

VM 窗口是控制机上的普通 GUI 窗口。Clip2VM 监听全局热键，触发时读剪贴板，通过 xdotool 将文本逐字模拟键盘输入到焦点窗口。对 VM 来说等同于人类敲键盘。

```
Ctrl+C 复制 → 点 VM 窗口 → Ctrl+Shift+Q → 文本逐字键入 VM 终端
```

## 系统要求

| 项目 | 要求 |
|------|------|
| **操作系统** | Linux（控制机） |
| **显示协议** | X11（完整支持） / Wayland（仅多窗口模式，热键不可用） |
| **系统依赖** | `xdotool` `xclip`（X11）或 `ydotool` `wl-clipboard`（Wayland） |
| **Python** | 源码运行需 Python 3.8+；二进制运行无需 Python |
| **VM 软件** | VirtualBox / QEMU-KVM / VMware — 任何有 GUI 窗口的虚拟机 |
| **VM 侧** | **无需安装任何东西**（ASCII 内容）；非 ASCII 内容需 Guest Additions / SPICE agent |

## 快速开始

### 方式一：源码运行

```bash
pip install pyperclip pynput
sudo apt install xdotool xclip

# 守护进程模式（Ctrl+Shift+Q 投递到焦点窗口）
python3 clip2vm-daemon.py

# 多窗口模式（按标题关键字投递到多个窗口）
python3 clip2vm-daemon.py m
```

### 方式二：打包为独立二进制（无需 Python 环境）

```bash
# 构建（需要 PyInstaller，自动安装）
python3 build.py

# 产出 dist/clip2vm，复制到任意同架构 Linux 机器
./clip2vm
```

目标机器只需 `sudo apt install xdotool xclip`，无需 Python 或任何 pip 包。

## 多窗口模式

`python3 clip2vm-daemon.py m` 将剪贴板内容一次投递到多个窗口：

```
$ python3 clip2vm-daemon.py m
Clipboard (16c): "sudo apt update"

    1. [289406986] user@host: ~
    2. [290496789] Ubuntu 22.04 - VirtualBox
    3. [98566151] Ubuntu 20.04 - QEMU/KVM
  ...
Windows (keywords, or Enter to confirm)> Ubuntu

  (2 windows)
    1. [290496789] Ubuntu 22.04 - VirtualBox
    2. [98566151] Ubuntu 20.04 - QEMU/KVM
Windows (keywords, or Enter to confirm)>

Sending to 2 windows ...
  [OK] 290496789 Ubuntu 22.04 - VirtualBox (keyboard-type)
  [OK] 98566151 Ubuntu 20.04 - QEMU/KVM (keyboard-type)
```

- 输入关键字（空格分隔 = AND 匹配，忽略大小写）筛选窗口
- 回车确认，投递到所有匹配窗口
- 通过 `xdotool type --window <wid>` 直接写入，无需切换焦点

## 输入方式

| 内容 | 方式 | 说明 |
|------|------|------|
| 英文/数字/符号 | 逐字模拟键盘输入 | 不依赖 VM 剪贴板共享 |
| 中文/emoji 等非 ASCII | Ctrl+Shift+V 粘贴 | 需 VM 启用剪贴板共享（Guest Additions / SPICE） |

## 日志格式

```
[14:32:07] keyboard-type 16c → Ubuntu 22.04 - VirtualBox
  "sudo apt update"
[14:32:15] ctrl+shift+v 42c → win10-2 - QEMU/KVM
  "echo 你好世界"
```

## 限制

- **Wayland**：pynput 全局热键不支持，需改用桌面环境快捷键绑定
- **非 ASCII**：需要 VM 内安装 Guest Additions / SPICE agent / VMware Tools 并启用剪贴板共享
- **X11**：xdotool 仅操作当前用户有权限的窗口，无需 root

## 项目结构

```
Clip2VM/
├── clip2vm-daemon.py    # 唯一入口
├── build.py             # 打包为独立二进制
├── clip2vm/
│   ├── backends.py      # xdotool / ydotool / wtype / pyautogui
│   ├── client.py        # 剪贴板读取 + 注入 + 热键守护 + 多窗口模式
│   └── window.py        # 焦点窗口查询 + 所有可见窗口枚举
├── requirements.txt
├── README.md
└── CLAUDE.md
```
