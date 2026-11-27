# 关键技术地址（V4 补丁）

游戏版本：**2026-09-18 Steam 更新版（v1.6.9.96.3436）**。基址 0x140000000（无 ASLR，已验证）。

> **重定位历史**
> - 2026-09-12 版：相对上一版（1.6.9.91 / buildid 24132163）AMS2.exe 全体 +0x5780、AVX 全体 +0x56B0。
> - 2026-09-18 版（当前）：相对 09-12 版 AMS2.exe 全体 **+0x150**、AMS2AVX.exe 全体 **+0x140**。
>   校验方式：GetGlyph / E85C10 函数入口 48 字节窗口逐字节一致；glyph-fb / E85C4E / fb-store
>   三处特征字节唯一命中且差值一致；P4 两处 strcmp 调用点字节为 `E8` 且 call 目标同步平移同一差值。
>   全部由 `tools/relocate_v4.py` 自动完成（重定位时先跑它，再据此改补丁脚本常量）。
> - ⚠ **AMS2.exe 09-18 版与 09-12 版文件大小完全相同（43,185,224）**，只比大小会误判版本，
>   必须比 SHA256（见 `checksums.txt`）。旧版补丁脚本按大小命名备份，本次已改为「大小 + 哈希前 8 位」。

## AMS2.exe（非 AVX）

| 项目 | 2026-09-18 地址 | 说明 |
|---|---|---|
| GetGlyph | 0x140E8B010 | 字形查询主函数 |
| glyph-fb 钩子 | 0x140E8B091 | 原字节 `74 0A 0F B7 D7` → `E9` 共享例程 |
| GetGlyph 尾声 / ret0 | 0x140E8B09F / 0x140E8B09D | |
| E85C10（测量回退） | 0x140E8B4F0 | 返回可渲染该字形的字体对象 |
| E85C10 钩子 | 0x140E8B51E | 原字节 `48 85 C9 74 12` → `E9` 共享例程 |
| E85C10 递归 / ret0 | 0x140E8B523 / 0x140E8B535 | |
| fb-store 钩子 | 0x140F08B42 | 原字节 `49 89 85 58 03 00 00` → `E9` stub + 2 NOP |
| fb-store 续 | 0x140F08B49 | `lock inc [rax+0x10]` |
| P4 缓存 strcmp | 0x140F07B61 | → `E8` P4 helper |
| P4 槽位 strcmp | 0x140F08A4F | → `E8` P4 helper |
| .zh2 段 | RVA 0x2F13000（0x800 字节） | shared@+0、stub@+0x80、**P4@+0x100**、slots@+0x300 |
| 字体 size 字段 | obj+0x44 | 实测：12px=19、17px=25、31px=44（行高类指标） |
| 亚洲回退字段 | obj+0x358 | 游戏自己的关联；空时走共享例程 |

原始 43,185,224 → 补丁后 43,187,712 字节（SizeOfImage 0x2F13000 → 0x2F14000）。

## AMS2AVX.exe（AVX 版，Steam 实际启动的）

| 项目 | 2026-09-18 地址 |
|---|---|
| GetGlyph | 0x140E83020 |
| glyph-fb 钩子 | 0x140E830A1（`74 0A 0F B7 D7`）|
| GetGlyph 尾声 / ret0 | 0x140E830AF / 0x140E830AD |
| E85C10 | 0x140E834F0；钩子 0x140E8352E（`48 85 C9 74 12`）|
| E85C10 递归 / ret0 | 0x140E83533 / 0x140E83545 |
| fb-store 钩子 | 0x140F009C2（`49 89 85 58 03 00 00`）；续 0x140F009C9 |
| P4 缓存 strcmp | 0x140EFF9E1 |
| P4 槽位 strcmp | 0x140F008CF |
| .zh2 段 | RVA 0x2EE1000（0x800 字节），布局同上 |
| 启动引导器 | AMS2.exe 检测 CPU 支持 AVX 即转启 AMS2AVX.exe 并退出 |

原始 42,980,424 → 补丁后 42,982,912 字节（SizeOfImage 0x2EE1000 → 0x2EE2000）。

## 与旧版 V4 的一处实现差异（P4 helper 位置）

旧版（2026-08 以前）把 P4 helper（303 字节）放在 `.text` 尾部的零填充空洞，
并把 `.text` 的 VirtualSize 提升到 RawSize 以便该区域保持映射。

**2026-09 起 `.text` 尾部只剩 244 字节零填充，放不下 303 字节**，因此 P4 helper 改为放进
`.zh2` 段（段大小 0x400 → 0x800，slots 由 +0x0C0 移到 +0x300），不再需要 .text VSize 修补。
两个 exe 现在使用同一套 `.zh2` 布局。

## 共享例程逻辑（两个版本相同）

```
入口：rbx=字体, rcx=[rbx+0x358]（游戏自带关联）, rdi=字形码或字形记录
  test rcx,rcx ; jnz done            ; 有关联直接用
  tier = f([rbx+0x44]): ≤0x17→0, ≤0x20→1, else 2
  rcx = slots[tier] ; 为空则回退 slots[1] → slots[2]
done:
  cmp rcx,rbx ; je ret0              ; 防递归（中文字体自身查自身）
  test rcx,rcx ; jz ret0
  test edi,edi ; js 测量路径          ; 记录指针 bit31 置位 vs 字形码
  渲染路径: movzx edx,di; call GetGlyph; jmp GetGlyph尾声
  测量路径: jmp E85C10递归点
ret0: 按入口分别 jmp 到原版返回 0 路径
```

## 重新定位（游戏更新后）

```cmd
rem 0. 先用 Steam「验证游戏文件完整性」还原被覆盖的文件（拿到新原版 exe）
rem 1. 自动重定位：扫描特征字节、校验统一差值、算出新常量与 .zh2 RVA
python tools\relocate_v4.py
rem 2. 按输出的常量块更新 tools\patch_v4.py / tools\patch_v4_avx.py
rem 3. 打补丁（钩子字节不符会打印 ABORT 且完全不写盘，安全）
python tools\patch_v4.py
python tools\patch_v4_avx.py
```

特征字节（在 exe 中唯一）：
- glyph-fb：`74 0A 0F B7 D7`（唯一命中）
- E85C4E：`48 8B 8B 58 03 00 00 48 85 C9 74 12`
- fb-store：`49 89 85 58 03 00 00`（唯一命中）
- 定位新地址后，比较新旧差值是否为**统一常量**——若是（本次 AMS2 +0x150 / AVX +0x140），
  其余站点直接加同一差值即可，风险极低。
- `.zh2` RVA 取新版 SizeOfImage（页对齐；AMS2 0x2F13000 / AVX 0x2EE1000），
  段表紧接原最后一个段头写入，SizeOfImage 同步更新。

补丁脚本自带校验：钩子点的原始字节不符时打印 ABORT 并**完全不写盘**，
因此版本不匹配时不会损坏 exe。

## 版本不匹配的症状（本次故障复盘）

游戏更新后仍覆盖旧版 exe，启动会**静默退出（exit code 0）**，没有崩溃弹窗、
WER 里也查不到 APPCRASH。判定方法看游戏日志
`%USERPROFILE%\Documents\Automobilista 2\log\online.log`：

```
[Session][Exe Built]      Sat Sep 12 21:45:56 2026     <-- 旧版 exe
[Session][BuildVerSimple] v1.6.9.96.3436               <-- 新内容
[Session][BuildVerInject] SMSPHX.20260912.3432...      <-- exe 自带版本，与内容不一致 → 退出
```

`BuildVerInject` 与 `BuildVer` 不一致即代表 exe 版本落后，必须重新打补丁。

## 崩溃历史（避免重蹈覆辙）

- **V2/V3 崩溃根因**：stub 写在 ext 尾跳指令之后 2 字节处，`49 89` 覆盖了
  `jmp 0x140E857CF` 的位移 → 变成 `jmp 0xCB2E57CF`（堆地址）→ 每次 CJK
  查询 NX 崩溃（WER 转储 `c0000005 @ cb2e57cf`）。
- **尾调用陷阱**：对 GetGlyph 用 `jmp` 尾调用时，GetGlyph 的 `ret` 会弹出
  未压栈的垃圾返回地址（堆指针）→ 必须 `call GetGlyph; jmp 尾声`。
- **跨字体字形语义**：GetGlyph 返回字形记录、E85C10 返回字体对象，两者
  契约不同，不可混用；E85C10 返回 0 会让调用方 `[rax+0xDC]` 解引用崩溃。
- **校验比较陷阱**：钩子校验必须把两侧都规范成"小写无空格"再比较，
  否则 `bytes.hex(" ")`（小写带空格）与字面量（大写）永不相等 → 永远 ABORT。

## 文本汉化（BOOTFLOW.bff）

- BOOTFLOW.bff 目录密钥：`5RHFHER9G72eQGlkxhFMln`（kap_all.py 自动扫描）
- 含 11 个 .tdb 文本表（file_0035~0045），Chinese-Simple 语言块条目值格式：
  - 正常译文：UTF-16LE 文本
  - 未翻译占位：`UNTRANSLATED (hash): KeyName`
- 2026-09-18 版与 09-12 版文本表**键集合完全一致**（Game 7407 / Drivers 4209 / Pit 2604 /
  Career 1131 / General 972 / Platform 874 / RAC 664 / Online 160 / ChatFilter 103 /
  VehicleDetails 82 / Presence 47），原版缺口同为 1,489 条；仅 Game 表内 4 字节元数据有差异。
  因此本次汉化只需「重新解包 → 复用既有译文 → 回包」，无需新翻译。
- 汉化管线：kap_all.py 解包 → tdb_dump/tdb_extract 提取 → 补 translations.json
  → deploy.py 回填/回包/部署
- deploy.py 在 work/extract 存在时按新版 tdb 重建；extract 缺失时对
  work/translated 中的已翻译 .tdb **重新应用**当前 translations.json（幂等）
- 部署前自动把游戏原版 pak 备份到 `work/deploy/backup/BOOTFLOW.bff.bak-<哈希前8位>`
- 游戏更新后的标准流程：
  1. `python tools\kap_all.py BOOTFLOW`（重新解包新版 pak）
  2. `python tools\tdb_dump.py` → `python tools\tdb_extract.py`
  3. `python tools\check_missing.py`（列出需要新翻译的键，写入 need_translation.json）
  4. 补键到 `work/translations/translations.json`
  5. `python tools\deploy.py --deploy`
