# AMS2 简体中文汉化包

Automobilista 2 简体中文本地化补丁：**字体渲染修复（中文不再显示 `*`/方块）+ 全量文本汉化（14 个文本表 100% 覆盖）**。
已验证：中文正常渲染、无 `*`、无 `UNTRANSLATED_`（专有名词按策略保留英文）。

## 适用版本

- 游戏版本：**1.6.9.91**（buildid 24132163）
- AMS2.exe（非 AVX）与 AMS2AVX.exe（Steam 实际启动的版本）
- Steam 启动参数：`-novr -lang Chinese-Simple`（必填，否则中文不激活）

## 交付内容

```
deliverables/
├── README.md              本说明
├── patch/
│   ├── patch_v4.py        AMS2.exe 字体补丁脚本（可重复运行）
│   └── patch_v4_avx.py    AMS2AVX.exe 字体补丁脚本
├── patched_exe/
│   ├── AMS2.exe           已打补丁可执行文件
│   └── AMS2AVX.exe        已打补丁可执行文件
├── translated_pak/
│   └── BOOTFLOW.bff       汉化文本包（14 表 100% 中文）
└── docs/
    ├── addresses.md       技术地址表 + 重新定位方法
    ├── apply_patch.ps1    一键应用补丁（需游戏退出）
    ├── restore_original.ps1  一键还原官方原版
    ├── verify_v4.py       运行时验证工具
    └── checksums.txt      全部文件 SHA256
```

## 安装（三选一）

**方式 A：一键安装**（本机，需已具备 python 环境）
双击 `docs\apply_patch.ps1`，或项目根目录 `install.bat`（含文本部署）。

**方式 B：直接覆盖文件**（推荐给朋友）
1. 复制 `patched_exe\AMS2.exe` 和 `patched_exe\AMS2AVX.exe` 到
   `<Steam 库>\steamapps\common\Automobilista 2\` 覆盖
2. 复制 `translated_pak\BOOTFLOW.bff` 到同目录 `Pakfiles\` 覆盖
   （覆盖前建议备份原文件）
3. Steam 启动参数加 `-novr -lang Chinese-Simple`

**方式 C：脚本重打**（游戏更新后）
```
python patch\patch_v4.py
python patch\patch_v4_avx.py
```
脚本自动校验版本：已打补丁自动跳过；游戏版本不匹配自动中止（不会写坏）。

## 翻译覆盖

| 表名 | 总键数 | 覆盖率 | 说明 |
|------|--------|--------|------|
| Game | 7400 | 100% | 1114 条汉化补丁 + 6286 条游戏内置 |
| Drivers | 4201 | 100% | 游戏内置翻译 |
| Pit | 2604 | 100% | 17 条汉化补丁 + 2587 条游戏内置 |
| Career | 1131 | 100% | 游戏内置翻译 |
| General | 972 | 100% | 138 条汉化补丁 + 834 条游戏内置 |
| Platform | 874 | 100% | 33 条汉化补丁 + 841 条游戏内置 |
| RAC | 661 | 100% | 228 条汉化补丁 + 433 条游戏内置 |
| Credits | 305 | 100% | 游戏内置翻译 |
| SetupEngineer | 161 | 100% | 游戏内置翻译 |
| Online | 160 | 100% | 游戏内置翻译 |
| ChatFilter | 103 | 100% | 游戏内置翻译 |
| VehicleDetails | 82 | 100% | 游戏内置翻译 |
| Presence | 47 | 100% | 1 条汉化补丁 + 46 条游戏内置 |
| Splash | 14 | 100% | 游戏内置翻译 |
| **合计** | **18859** | **100%** | **1531 条汉化补丁 + 17328 条游戏内置** |

覆盖了游戏原版中全部 **1480 条 UNTRANSLATED 缺口**（Game 1088、RAC 217、General 138、Platform 32、Pit 4、Presence 1）。

## 专有名词策略（术语表）

- **赛道名**：中文惯用译名（银石、蒙扎、纽博格林）
- **品牌/车型名**：列表界面保留英文原名，描述文本可用中文品牌名
- **车队/车手名**：保留英文
- 术语表详见工程 `work/translations/glossary.txt`

## 已知限制

- 游戏**更新后新增的键**会显示 `UNTRANSLATED_xxx`：需重新解包 → 提取新键 →
  翻译 → 回包（工程内 `tools\kap_all.py` + `tdb_extract.py` + `deploy.py` 管线）。
- 游戏本体更新会覆盖 exe 与 BOOTFLOW.bff，需重新应用本包。

## 还原官方原版

1. 运行 `docs\restore_original.ps1`，或
2. 用安装前备份覆盖回原文件，或
3. Steam 库 → 属性 → 已安装文件 → **验证游戏文件完整性**

## 版本记录

- **V4.1（当前）**：修正字号分层阈值 + 回退链；文本汉化全量部署（1480 条缺口清零）。
- **V4**：修复旧版补丁崩溃根因（代码重叠 → 跳转堆内存）；新代码独立 `.zh2` 段；
  支持 AMS2 与 AMS2AVX 双版本。

## 分发提示

修改版 exe 请仅在**自己和信任的朋友间**使用，勿公开传播（涉及 Steam 条款）。
如需打包分发，请用 7-Zip 压缩本 deliverables 目录（旧的
`patched_exe2026-08-18 090943.7z` 不含文本包，已过时）。
