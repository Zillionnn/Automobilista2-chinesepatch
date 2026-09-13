# AMS2 简体中文汉化包

Automobilista 2 简体中文本地化补丁：**字体渲染修复（中文不再显示 `*`/方块）+ 全量文本汉化**。
已验证：中文正常渲染、无 `*`、无 `UNTRANSLATED_`（专有名词按策略保留英文）。

## 适用版本

- 游戏版本：**2026-09-12 Steam 更新版**
- 原始（未打补丁）文件大小 —— 装之前请确认一致，不一致说明游戏又更新了，请不要覆盖：
  - `AMS2.exe` 43,185,224 字节
  - `AMS2AVX.exe` 42,979,912 字节
  - `Pakfiles\BOOTFLOW.bff` 32,258,449 字节
- AMS2.exe（非 AVX）与 AMS2AVX.exe（Steam 实际启动的版本）
- Steam 启动参数：`-novr -lang Chinese-Simple`（必填，否则中文不激活）

## 交付内容

```
deliverables/
├── README.md              本说明
├── patched_exe/
│   ├── AMS2.exe           已打补丁可执行文件（字体渲染修复）
│   └── AMS2AVX.exe        已打补丁可执行文件
├── translated_pak/
│   └── BOOTFLOW.bff       汉化文本包（11 个文本表 100% 中文）
└── docs/
    ├── addresses.md       技术地址表 + 重新定位方法
    ├── checksums.txt      全部文件 SHA256 + 原始文件大小
    └── verify_v4.py       运行时验证工具（可选，游戏运行中执行）
```

## 安装（直接覆盖文件，无需任何脚本）

1. 复制 `patched_exe\AMS2.exe` 和 `patched_exe\AMS2AVX.exe` 到
   `<Steam 库>\steamapps\common\Automobilista 2\` 覆盖
   （Steam 库位置可在 Steam → 设置 → 存储 中查看，或右键游戏 → 管理 → 浏览本地文件）
2. 复制 `translated_pak\BOOTFLOW.bff` 到同目录 `Pakfiles\` 覆盖
3. Steam 库 → 右键游戏 → 属性 → 启动选项填入：`-novr -lang Chinese-Simple`

覆盖前建议先备份原文件（或记住可用 Steam"验证文件完整性"还原）。

## 翻译覆盖

包内 BOOTFLOW.bff 的 11 个文本表（共 18,253 键）**全部为中文**：

| 表名 | 总键数 | 覆盖率 |
|------|--------|--------|
| Game | 7407 | 100% |
| Drivers | 4209 | 100% |
| Pit | 2604 | 100% |
| Career | 1131 | 100% |
| General | 972 | 100% |
| Platform | 874 | 100% |
| RAC | 664 | 100% |
| Online | 160 | 100% |
| ChatFilter | 103 | 100% |
| VehicleDetails | 82 | 100% |
| Presence | 47 | 100% |
| **合计** | **18,253** | **100%** |

- 本次更新后清零的原版缺口：**1,489 条**（Game 1094、RAC 220、General 138、Platform 32、Pit 4、Presence 1）。
- 其余表（Credits 305、SetupEngineer 161、Splash 14）游戏原版自带完整中文，本包不含
  （Credits 位于 `MenuSetup.bff`，无缺口，无需替换）。

## 专有名词策略（术语表）

- **赛道名**：保留英文原名（如 `Velopark STT`、`Spielberg Historic 1974`）
- **品牌/车型名**：列表界面保留英文原名，描述文本可用中文品牌名
- **车队/车手名**：保留英文
- **术语统一**：brake→刹车（非"煞车"）、stint→出场次数、lap limit→圈数限制

## 已知限制

- 游戏**每次更新**都会还原 `AMS2.exe`、`AMS2AVX.exe` 与 `Pakfiles\BOOTFLOW.bff`，
  需要重新覆盖本包——但**若游戏版本变了，本包的 exe 不能再用**（地址失效），
  必须按 `docs/addresses.md` 的"重新定位"流程更新补丁。
  本包 exe 的钩子校验会在版本不符时安全中止（不会损坏文件）。
- 修改版 exe 请仅在**自己和信任的朋友间**使用，勿公开传播（涉及 Steam 条款）。

## 还原官方原版

用安装前备份覆盖回原文件，或：
Steam 库 → 右键游戏 → 属性 → 已安装文件 → **验证游戏文件完整性**（一键还原全部文件）。

## 版本记录

- **V4.2（当前，2026-09-12 游戏更新后）**：地址整体重定位（AMS2 +0x5780、AVX +0x56B0）；
  P4 helper 移入 `.zh2` 段（新版 .text 尾部零填充不足）；修复钩子校验的大小写比较 bug；
  文本重新解包并补翻 11 条新增键（Stint/Lap Limit 等），1,489 条原版缺口清零。
- **V4.1**：修正字号分层阈值 + 回退链；文本汉化全量部署。
- **V4**：修复旧版补丁崩溃根因（代码重叠 → 跳转堆内存）；新代码独立 `.zh2` 段；
  支持 AMS2 与 AMS2AVX 双版本。
