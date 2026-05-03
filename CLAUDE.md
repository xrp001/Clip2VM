# CLAUDE.md

Clip2VM — 将剪贴板内容模拟键盘输入到 VM 窗口。守护进程模式 Ctrl+Shift+Q 热键，多窗口模式按标题关键字投递。控制机运行，VM 侧零安装。

## 入口

```bash
python3 clip2vm-daemon.py       # 守护进程模式，Ctrl+Shift+Q 热键
python3 clip2vm-daemon.py m     # 多窗口模式，交互式关键字搜索
```

## 模块

| 文件 | 职责 |
|------|------|
| `clip2vm-daemon.py` | 入口脚本，`sys.argv` 分发到 `run_daemon()` 或 `run_multi()` |
| `backends.py` | XdotoolBackend / YdotoolBackend / WtypeBackend / PyAutoGUIBackend + 自动检测 `detect_backend()` |
| `client.py` | `read_clipboard()` → `inject()` → 日志输出；`run_daemon()` pynput 热键循环；`run_multi()` 多窗口交互模式 |
| `window.py` | `get_active_window()` 当前焦点窗口；`get_all_visible_windows()` 枚举所有可见窗口 |

## 注入策略

- `text.isascii()` → `xdotool type --delay 3` 逐字键入（最可靠）
- 非 ASCII → `xdotool key --clearmodifiers ctrl+shift+v` 剪贴板粘贴

## 设计约定

- Python 3.8+，依赖 pyperclip + pynput
- 无网络、无配置文件，最小 CLI（仅 `m` 子命令），最小化代码路径
- 后端运行时自动检测 `$XDG_SESSION_TYPE` + 可执行文件
- 键入前调用 `backend.release_modifiers()` 清除热键残留的 Ctrl/Shift
