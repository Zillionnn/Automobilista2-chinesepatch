# AMS2 简体中文汉化包

Automobilista 2 简体中文本地化补丁，包含字体渲染修复和完整文本汉化。
**已验证：中文正常渲染、无 `*`，静态持久（重启不丢），支持 AMS2（非 AVX）与 AMS2AVX 双版本。**

## 适用版本

- 游戏版本：1.6.9.91（buildid 24132163）
- AMS2.exe（非 AVX）与 AMS2AVX.exe（Steam 实际启动的，CPU 支持 AVX 时由 AMS2.exe 转启）
- Steam 启动参数：`-novr -lang Chinese-Simple`

## 安装（直接覆盖文件）

游戏目录为 `<Steam 库>\steamapps\common\Automobilista 2`（本机 `F:\SteamLibrary\steamapps\common\Automobilista 2`），
详细步骤见 `deliverables/README.md`。无需任何脚本：

1. 复制 `deliverables\patched_exe\AMS2.exe`、`AMS2AVX.exe` → 游戏目录覆盖
2. 复制 `deliverables\translated_pak\BOOTFLOW.bff` → 游戏目录 `Pakfiles\` 覆盖
3. Steam 启动选项填入：`-novr -lang Chinese-Simple`

> 覆盖前建议备份原文件；Steam"验证文件完整性"可随时还原。
> 游戏更新后会覆盖被修改的文件，需重新覆盖。



## 技术细节

### 字体补丁（V4）

AMS2 的字体系统在渲染中文字符时显示为 `*`/方块，原因是多数字体没有中文字体回退机制。V4 补丁：

1. **P4 变体容错比较器**（303 字节）— 布局变体字体名（如 `font_phoenix_body_regular_light`）
   与注册对象名（`.bfont`）比较时忽略 `_light`/`_dark`/`.bfont` 后缀，使字体正确解析。
2. **共享回退例程**（87 字节，挂在 GetGlyph 与测量函数 E85C10 的回退路径）— 字体自身
   无中文字体关联（+0x358）时，按字号分层（size≤0x17→12px 档、≤0x20→17px 档、其余→31px 档）
   从全局槽位取中文字体，带回退链与防递归自检。
3. **槽位捕获 stub**（49 字节，挂在游戏自动关联处）— 游戏为 5 个槽位字体加载中文字体时，
   按字号把中文字体指针存入 3 个全局槽位。
4. **独立 `.zh2` PE 段** — 全部新代码放入追加段（RWX），杜绝旧版补丁代码重叠崩溃问题。
5. 备份自动生成：`AMS2.exe.bak-v4-orig` / `AMS2AVX.exe.bak-v4-orig`（仅首次）。

补丁脚本可重复运行（已打补丁自动跳过）；若游戏更新导致地址失效会**自动中止**而非写坏文件。

### 文本汉化

通过完整管线提取游戏文本、翻译、回包：

```
.bff 解包 (kap_all.py)
    → .tdb 解析 (tdb_dump.py) → TSV 导出
    → 未翻译提取 (tdb_extract.py)
    → 翻译 (translations.json + 术语表)
    → 回填 (tdb_repack.py)
    → .bff 回包 (kap_repack.py)
    → 部署 (deploy.py)
```

> 注：`work/extract/` 为可再生解包产物，已从工程目录清理；
> `deploy.py` 在 extract 缺失时会自动对 `work/translated/` 中的已翻译 .tdb
> 重新应用当前 translations.json 后回包（修改译文无需重新解包）。

.tdb 格式关键点：
- offset 4：field4（meta[0] 的副本，引擎内部字段，必须原样保留）
- 表名：ASCII 字符串（扫描到非打印字符为止）
- 语言块：每个条目为 12 字节头（h1/h2 哈希 + cc 字符数）+ UTF-16LE 文本

## 翻译覆盖

所有 14 个 .tdb 表的 Chinese-Simple 条目均已实现 100% 翻译覆盖率：

| 表名 | 总键数 | 覆盖率 | 说明 |
|------|--------|--------|------|
| Career | 1131 | 100% | 游戏内置翻译 |
| ChatFilter | 103 | 100% | 游戏内置翻译 |
| Drivers | 4201 | 100% | 游戏内置翻译 |
| Game | 7400 | 100% | 1114 条汉化补丁 + 6286 条游戏内置 |
| General | 972 | 100% | 138 条汉化补丁 + 834 条游戏内置 |
| Online | 160 | 100% | 游戏内置翻译 |
| Pit | 2604 | 100% | 17 条汉化补丁 + 2587 条游戏内置 |
| Platform | 874 | 100% | 33 条汉化补丁 + 841 条游戏内置 |
| Presence | 47 | 100% | 1 条汉化补丁 + 46 条游戏内置 |
| RAC | 661 | 100% | 228 条汉化补丁 + 433 条游戏内置 |
| VehicleDetails | 82 | 100% | 游戏内置翻译 |
| Splash | 14 | 100% | 游戏内置翻译 |
| SetupEngineer | 161 | 100% | 游戏内置翻译 |
| Credits | 305 | 100% | 游戏内置翻译 |
| **合计** | **18859** | **100%** | **1531 条汉化补丁 + 17328 条游戏内置** |

## 工具链

| 工具 | 用途 |
|------|------|
| `patch_v4.py` / `patch_v4_avx.py` | 字体补丁（AMS2 / AMS2AVX，可重复运行） |
| `kap_all.py` | .bff 解包（RC4 解密 + zlib/Oodle 解压） |
| `kap_repack.py` | .bff 回包（目录重加密 + zlib 压缩） |
| `tdb_dump.py` | .tdb 解析导出多语言 TSV |
| `tdb_extract.py` | 提取未翻译条目到 JSON |
| `build_translations.py` | 翻译字典引擎（含术语表） |
| `tdb_repack.py` | 翻译回填到 .tdb 二进制 |
| `find_translation.py` | 在 translations.json 中按关键词查找翻译条目 |
| `deploy.py` | 一键端到端部署（extract 缺失时自动对已翻译 .tdb 重新应用译文） |
| `verify_deploy.py` | 部署验证 |
| `verify_v4.py` | 运行时验证（游戏运行中检查字体槽位/钩子） |

历史实验脚本已删除（tools/ 仅保留核心工具）。

## 修改翻译

**只需改一个文件**：`work/translations/translations.json`（结构：`{"表名": {"键名": "中文译文"}}`），
然后一条命令重新打包并部署到游戏。

```cmd
chcp 65001          rem 防止 cmd 中文乱码（PowerShell 可跳过）
rem 1. 查找要改的条目（按中文/键名关键词）
python tools\find_translation.py 光头胎
python tools\find_translation.py TestDay Game

rem 2. 用编辑器打开 work\translations\translations.json，按键名搜索并修改中文值

rem 3. 重新生成 .tdb → 回包 BOOTFLOW.bff → 备份原版并覆盖到游戏目录
python tools\deploy.py --deploy
```

要点：

- `deploy.py` 会对 `work/translated/` 中已有的 .tdb **重新应用**当前 translations.json
  （幂等：未改动的条目保持原样，只更新你改过的键），无需重新解包 18GB 的 extract。
- 部署前自动备份游戏目录当前 BOOTFLOW.bff 到 `work/deploy/backup/`（仅首次）。
- 进游戏验证：Steam 启动参数 `-novr -lang Chinese-Simple`。
- 分享给别人：把 `work\deploy\BOOTFLOW.bff` 复制到 `deliverables\translated_pak\BOOTFLOW.bff`
  覆盖旧包（并更新 `deliverables\docs\checksums.txt` 中的 SHA256），重新压缩 deliverables 即可；
  两个 exe 无需重打（字体补丁与文本无关）。
- 游戏更新后出现新的 `UNTRANSLATED_xxx` 键（当前包没有该键）时，才需要走完整管线：
  `kap_all.py` 解包 → `tdb_extract.py` 提取 → 补键到 translations.json → `deploy.py --deploy`。

## 恢复原版

Steam 库 → 右键游戏 → 属性 → 已安装文件 → **验证游戏文件完整性**（一键还原），
或手动用备份覆盖回原文件（exe 备份 `AMS2.exe.bak-v4-orig` 等位于游戏目录）。

## 术语表

详见 `work/translations/glossary.txt`，涵盖轮胎配方、车辆设置、控制输入、赛事规则、赛道状态、旗语、故障、力反馈、游戏模式、图形设置等分类。

## 已知限制

- `UNTRANSLATED_*` 字符串（如 `UNTRANSLATED_game_UI_testday`）是游戏更新后新增键、
  中文表缺失条目的表现；部署汉化包可覆盖已知键，全新键需走"重新解包 → 翻译 → 回包"管线补齐。
