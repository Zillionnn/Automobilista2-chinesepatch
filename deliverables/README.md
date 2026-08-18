# AMS2 简体中文渲染修复包（V4）

Automobilista 2 简中字体渲染修复 —— 解决中文显示为 `*` / 方块的问题。
**已验证：AMS2 与 AMS2AVX 双版本中文正常渲染，无 `*`，静态持久（重启不丢）。**

## 交付内容

```
deliverables/
├── README.md              本说明
├── patch/
│   ├── patch_v4.py        AMS2.exe（非 AVX）静态补丁脚本
│   └── patch_v4_avx.py    AMS2AVX.exe 静态补丁脚本
├── patched_exe/
│   ├── AMS2.exe           已打补丁的可执行文件（SHA256 见 checksums.txt）
│   └── AMS2AVX.exe        已打补丁的可执行文件
├── docs/
│   ├── verify_v4.py       运行时验证脚本（游戏运行中检查槽位/钩子）
│   ├── apply_patch.ps1    一键应用补丁
│   ├── restore_original.ps1  一键还原官方原版
│   └── checksums.txt      补丁后 exe 的 SHA256
```

## 背景：为什么中文显示 `*`

1. 游戏通过 `-lang Chinese-Simple` 激活简体中文，但**只有 5 个"槽位字体"**（
   `font_phoenix_body_footnote/large/regular/page_title/tab_title`）会被游戏自动
   关联到中文字体（`font_phoenix_asian_12/17/31_zh-cn`）。其余字体（
   `ams2_font_*`、`font_*_light/_dark` 变体等）查询 CJK 字符时找不到字形 → 返回 0
   → 游戏渲染 `*`。
2. 布局中的变体字体名（如 `font_phoenix_body_regular_light`）与注册表中的
   `.bfont` 对象名严格比较不相等 → 字体解析失败 → 回退默认字体（无 CJK）。

## 修复方案（V4 静态补丁）

- **P4 变体容错字符串比较器**：比较字体名时忽略 `_light` / `_dark` / `.bfont`
  后缀差异，使变体名正确解析到已注册字体对象。
- **共享回退例程**（挂在 GetGlyph 回退路径 + 测量函数 E85C10 回退路径）：
  字体自身无 +0x358 关联时，按字号分层（size≤0x17→12px 档、≤0x20→17px 档、
  其余→31px 档）从全局槽位取中文字体，并带**回退链**（首选槽为空时依次尝试
  其他槽）和**防递归自检**。
- **槽位捕获 stub**（挂在游戏自动关联处）：游戏为槽位字体加载中文字体时，按
  槽位字体 size 字段把中文字体指针存入 3 个全局槽位。
- 全部新代码放入**追加的独立 `.zh2` 段**（RWX），杜绝旧版补丁"代码重叠导致
  跳转到堆内存崩溃"的问题。

## 使用方法

### 应用补丁（游戏已更新/被 Steam 校验还原后）

1. **完全退出游戏**（AMS2/AMS2AVX 进程不运行）。
2. 双击运行 `docs\apply_patch.ps1`（或在 PowerShell 中执行），或手动：
   ```powershell
   python patch\patch_v4.py       # 打 AMS2.exe
   python patch\patch_v4_avx.py   # 打 AMS2AVX.exe
   ```
3. 通过 Steam 启动游戏（默认即 AMS2AVX，若 CPU 支持 AVX）。

### 直接替换 exe（给好友分享用）

把 `patched_exe\` 下对应文件复制到
`<Steam 库>\steamapps\common\Automobilista 2\` 覆盖即可（替换前建议先备份
原文件）。

### 还原官方原版

1. 运行 `docs\restore_original.ps1`（使用脚本自动生成的原版备份），或
2. Steam 库 → 右键游戏 → 属性 → 已安装文件 → **验证游戏文件完整性**
   （会还原所有被修改的文件）。

### 运行时验证（可选）

游戏运行中执行 `python docs\verify_v4.py`，可查看：
- 内存中的钩子字节是否生效
- 3 个中文字体槽位是否填充（s12/s17/s31）
- 字体注册表状态（名称/字号/+0x358 关联）

## 注意事项

- **Steam 启动参数需含 `-lang Chinese-Simple`**，否则中文 provider 不激活。
- 游戏本体更新后补丁会被覆盖，重新运行 apply 脚本即可。
- `UNTRANSLATED_*` 字符串（如 `UNTRANSLATED_game_UI_testday`）是**游戏自带
  中文本地化的内容缺口**（新内容未翻译），不是渲染问题，需后续文本 pak
  提取/翻译/回包管线解决。
- 备份文件 `AMS2.exe.bak-v4-orig` / `AMS2AVX.exe.bak-v4-orig` 由补丁脚本自动
  生成在游戏目录，勿删除。

## 版本记录

- **V4.1（当前）**：修正字号分层阈值（按实测 size 字段 19/25/44 对应
  12/17/31px），共享例程增加回退链，消除小字号字体 `*`。
- **V4**：修复 V2/V3 崩溃根因（stub 与 ext 重叠 2 字节导致跳转位移被改写、
  启动即 NX 崩溃）；新代码全部移入独立 .zh2 段；支持 AMS2 与 AMS2AVX。
