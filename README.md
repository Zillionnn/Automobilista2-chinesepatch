# AMS2 简体中文汉化包

Automobilista 2 简体中文本地化补丁，包含字体渲染修复和完整文本汉化。
**已验证：中文正常渲染、无 `*`，静态持久（重启不丢），支持 AMS2（非 AVX）与 AMS2AVX 双版本。**

## 适用版本

- 游戏版本：**2026-09-12 Steam 更新版**
  （原始文件大小：AMS2.exe 43,185,224、AMS2AVX.exe 42,979,912、Pakfiles\BOOTFLOW.bff 32,258,449）
- AMS2.exe（非 AVX）与 AMS2AVX.exe（Steam 实际启动的，CPU 支持 AVX 时由 AMS2.exe 转启）
- Steam 启动参数：`-novr -lang Chinese-Simple`
- 地址表与"游戏更新后重新定位"方法：`deliverables/docs/addresses.md`

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
5. 备份自动生成：`AMS2.exe.bak-v4-orig-<原始大小>`（按文件大小区分版本，仅首次创建，游戏更新后不会覆盖旧备份）。

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

包内 BOOTFLOW.bff 的 11 个文本表（共 18,253 键）Chinese-Simple 全部为中文：

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

本次更新后清零的原版 `UNTRANSLATED` 缺口：**1,489 条**
（Game 1094、RAC 220、General 138、Platform 32、Pit 4、Presence 1）。

其余表（Credits 305、SetupEngineer 161、Splash 14）游戏原版自带完整中文：
Credits 位于 `MenuSetup.bff`，无缺口，不需要替换。

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
| `find_translation.py` | 查找翻译条目（`--all` 可搜游戏内置翻译 all_entries.json 查键名） |
| `check_missing.py` | **游戏更新后**：对比新版未翻译条目与现有译文，列出需要补翻的键 |
| `deploy.py` | 一键端到端部署（extract 缺失时自动对已翻译 .tdb 重新应用译文） |
| `verify_deploy.py` | 部署验证 |
| `verify_v4.py` | 运行时验证（游戏运行中检查字体槽位/钩子；支持 ams2 / avx 两个进程） |

历史实验脚本已删除（tools/ 仅保留核心工具）。

## 修改翻译

**只需改一个文件**：`work/translations/translations.json`（结构：`{"表名": {"键名": "中文译文"}}`），
然后一条命令重新打包并部署到游戏。

```cmd
chcp 65001          rem 防止 cmd 中文乱码（PowerShell 可跳过）
rem 1. 查找要改的条目（按中文/键名关键词）
python tools\find_translation.py 光头胎                 rem 搜补丁翻译
python tools\find_translation.py 煞车死区 --all        rem 连游戏内置翻译一起搜（查键名）
python tools\find_translation.py TestDay Game          rem 限定表名

rem 2. 用编辑器打开 work\translations\translations.json，按键名搜索并修改中文值
rem    （游戏内置翻译的条目也能改：把查到"表名/键名/新中文"加进 JSON 即可覆盖内置值）

rem 3. 重新生成 .tdb → 回包 BOOTFLOW.bff → 备份原版并覆盖到游戏目录
python tools\deploy.py --deploy
```

要点：

- **`all_entries.json` 是只读参考文件**（全量导出：表/键/英文/中文，共 10.7 万行），
  用来**查键名**（比如游戏里看到"煞车死区"，搜它得到 `Game_UI_Bra6`），
  deploy.py 不读它，改它没有任何效果——修改永远只写 `translations.json`。
- **游戏内置中文**：游戏文件自带一个不完整的 Chinese-Simple 语言块（约 1.7 万条，
  台湾用词风格如"煞车/设定"），缺失的条目原样是 `UNTRANSLATED_xxx` 占位。
  汉化包补全了缺失条目；对内置条目不满意时，把键加进 translations.json 即可覆盖。
- `deploy.py` 会对 `work/translated/` 中已有的 .tdb **重新应用**当前 translations.json
  （幂等：未改动的条目保持原样，只更新你改过的键），无需重新解包 18GB 的 extract。
- 部署前自动备份游戏目录当前 BOOTFLOW.bff 到 `work/deploy/backup/`（仅首次）。
- 进游戏验证：Steam 启动参数 `-novr -lang Chinese-Simple`。
- 分享给别人：把 `work\deploy\BOOTFLOW.bff` 复制到 `deliverables\translated_pak\BOOTFLOW.bff`
  覆盖旧包（并更新 `deliverables\docs\checksums.txt` 中的 SHA256），重新压缩 deliverables 即可；
  两个 exe 无需重打（字体补丁与文本无关）。
- 游戏更新后出现新的 `UNTRANSLATED_xxx` 键（当前包没有该键）时，走完整管线：
  `kap_all.py` 解包 → `tdb_dump.py` → `tdb_extract.py` → `check_missing.py` 列出新键
  → 补进 translations.json → `deploy.py --deploy`。详见"游戏更新后如何恢复"。

## 游戏更新后如何恢复（本次已验证流程）

**第 1 步：先判断是不是新版本**——对比原始文件大小（`deliverables/docs/checksums.txt` 有记录）：

- 大小一致 → 只是被还原，重新覆盖 `deliverables/` 里的文件即可。
- 大小不一致 → 新版本，**旧 exe 不能再用**（补丁地址失效），必须重新定位。

**第 2 步：重定位地址 + 重新汉化**

```cmd
rem ① 用旧版原 exe 的特征字节在新 exe 里搜索新地址（方法见 deliverables/docs/addresses.md）
rem    本次实测结果：AMS2.exe 全体 +0x5780、AMS2AVX.exe 全体 +0x56B0（GetGlyph/E85C10
rem    函数入口 48 字节逐字节一致，glyph-fb 与 fb-store 特征唯一命中）
rem ② 更新 tools\patch_v4.py / patch_v4_avx.py 的地址常量 + ZH2_RVA 等
rem ③ 重新打补丁（钩子字节不符会打印 ABORT 且完全不写盘，安全）
python tools\patch_v4.py
python tools\patch_v4_avx.py

rem ④ 重新解包新版 pak → 导出 TSV → 提取未翻译 → 看还缺哪些键
python tools\kap_all.py BOOTFLOW
python tools\tdb_dump.py
python tools\tdb_extract.py
python tools\check_missing.py

rem ⑤ 把 need_translation.json 里的新键翻译后补进 translations.json
rem ⑥ 重新打包并部署（自动备份新版原版 pak）
python tools\deploy.py --deploy
```

**第 3 步：更新交付物**——把游戏目录的 `AMS2.exe`、`AMS2AVX.exe`、`Pakfiles\BOOTFLOW.bff`
复制到 `deliverables/` 对应目录，并更新 `deliverables/docs/checksums.txt` 的哈希与原始大小。

> 排查提示：`tdb_dump.py` 的 TSV 导出必须把 `\r`/`\n`/`\t` 全部替换为空格，
> 且 `tdb_extract.py` 读 TSV 要用 `csv.QUOTE_NONE`——否则值里的回车/引号会拆断行，
> 导致未翻译条目被少数（本次曾少数约 45 条，已修复）。

## 恢复原版

Steam 库 → 右键游戏 → 属性 → 已安装文件 → **验证游戏文件完整性**（一键还原），
或手动用备份覆盖回原文件（exe 备份 `AMS2.exe.bak-v4-orig` 等位于游戏目录）。

## 术语表

详见 `work/translations/glossary.txt`，涵盖轮胎配方、车辆设置、控制输入、赛事规则、赛道状态、旗语、故障、力反馈、游戏模式、图形设置等分类。

## 已知限制

- `UNTRANSLATED_*` 字符串（如 `UNTRANSLATED_game_UI_testday`）是游戏更新后新增键、
  中文表缺失条目的表现；**当前包内已 0 条**。游戏再次更新后按"游戏更新后如何恢复"流程补翻。
- 每次游戏更新都会还原 exe 与 pak；版本变化时旧 exe 的补丁地址失效
  （补丁脚本会校验并安全中止，不会写坏文件）。
