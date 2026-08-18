# 关键技术地址（V4 补丁）

游戏版本：1.6.9.91（buildid 24132163）。基址 0x140000000（无 ASLR，已验证）。
若游戏更新后地址失效，用 `tools/` 中的特征扫描重新定位（见下文"重新定位"）。

## AMS2.exe（非 AVX）

| 项目 | 地址 | 说明 |
|---|---|---|
| GetGlyph | 0x140E85740 | 字形查询主函数 |
| glyph-fb 钩子 | 0x140E857C1 | 原字节 `74 0A 0F B7 D7` → `E9` 共享例程 |
| GetGlyph 尾声 | 0x140E857CF / ret0 0x140E857CD | |
| E85C10（测量回退） | 0x140E85C10 | 返回可渲染该字形的字体对象 |
| E85C10 钩子 | 0x140E85C4E | 原字节 `48 85 C9 74 12` → `E9` 共享例程 |
| E85C10 递归/ret0 | 0x140E85C53 / 0x140E85C65 | |
| fb-store 钩子 | 0x140F03272 | 原字节 `49 89 85 58 03 00 00` → `E9` stub |
| fb-store 续 | 0x140F03279 | `lock inc [rax+0x10]` |
| P4 缓存 strcmp | 0x140F02291 | → `E8` P4 helper |
| P4 槽位 strcmp | 0x140F0317F | → `E8` P4 helper |
| .zh2 段 | RVA 0x2F09000 | shared@+0, stub@+0x80, P4@+0x100, slots@+0x300 |
| 字体 size 字段 | obj+0x44 | 实测：12px=19、17px=25、31px=44（行高类指标） |
| 亚洲回退字段 | obj+0x358 | 游戏自己的关联；空时走共享例程 |

## AMS2AVX.exe（AVX 版，Steam 实际启动的）

| 项目 | 地址 |
|---|---|
| GetGlyph | 0x140E7D830 |
| glyph-fb 钩子 | 0x140E7D8B1（`74 0A 0F B7 D7`）|
| GetGlyph 尾声 | 0x140E7D8BF / ret0 0x140E7D8BD |
| E85C10 | 0x140E7DD00；钩子 0x140E7DD3E（`48 85 C9 74 12`）|
| E85C10 递归/ret0 | 0x140E7DD43 / 0x140E7DD55 |
| fb-store 钩子 | 0x140EFB1D2（`49 89 85 58 03 00 00`）；续 0x140EFB1D9 |
| P4 缓存 strcmp | 0x140EFA1F1 |
| P4 槽位 strcmp | 0x140EFB0DF |
| .zh2 段 | RVA 0x2ED7000（0x800 字节）|
| 启动引导器 | AMS2.exe 检测 CPU 支持 AVX 即转启 AMS2AVX.exe 并退出 |

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

特征字节（在 exe 中唯一）：
- glyph-fb：`74 0A 0F B7 D7`（唯一命中）
- E85C4E：`48 85 C9 74 12`（配合前 7 字节 `48 8B 8B 58 03 00 00` 确认）
- fb-store：`49 89 85 58 03 00 00`（唯一命中）
- 段表：`.text` 尾部 VSize/RawSize 之间的零洞可放 P4 helper；或直接追加
  `.zh2` 段（RWX，特征 0xE0000020），与 V4 相同做法。

## 崩溃历史（避免重蹈覆辙）

- **V2/V3 崩溃根因**：stub 写在 ext 尾跳指令之后 2 字节处，`49 89` 覆盖了
  `jmp 0x140E857CF` 的位移 → 变成 `jmp 0xCB2E57CF`（堆地址）→ 每次 CJK
  查询 NX 崩溃（WER 转储 `c0000005 @ cb2e57cf`）。
- **尾调用陷阱**：对 GetGlyph 用 `jmp` 尾调用时，GetGlyph 的 `ret` 会弹出
  未压栈的垃圾返回地址（堆指针）→ 必须 `call GetGlyph; jmp 尾声`。
- **跨字体字形语义**：GetGlyph 返回字形记录、E85C10 返回字体对象，两者
  契约不同，不可混用；E85C10 返回 0 会让调用方 `[rax+0xDC]` 解引用崩溃。
