# Ultimate 3.5.0 x86 实测

版本来自用户，DIE 识别 VMProtect 3.2.0–3.5.0。输入 6,095,872 字节，I386/PE32，基址 `0x400000`，壳入口 RVA `0x4E16F4`，22 个磁盘导入。

常规模式在 GetProcessWindowStation 停止。添加 x86 窗口站模型后，MessageBoxW 报调试器检测；只提取文本并停止，没有吞错。补充匹配 catalog 的 32 位 ntdll 版本资源后模拟成功，资源目录偏移为 `0x108`（不是 x64 的 `0x118`），896 字节版本载荷与 catalog 一致。x86 栈参数/stdcall 清栈和 x64 原资源路径均有回归检查。

选择性回调成功轮约 32 秒，恢复 1,191 页。445 是回调计数，不是基本块总数。自动 stop `0x569A02` 在 `.vmp0`。重新确认 CRT 入口 RVA `0xA7B60`；ASLR 候选在 `0x930000` 装载时读取旧地址 `0x54D180` 崩溃，交付使用固定基址。

## 包装改写失败

工具生成 175 个 IAT 项、31 个静态引用补丁及 261 个包装改写，共 292 处；459 个包装候选中 261 个报告 resolved、198 个拒绝。但首个固定基址候选五组对比全部失败，在 `0x4F9B54` 崩溃。该地址位于新 GetProcAddress 调用的末字节：RVA `0xF9B4F` 原 `E8 11 F0 16 00 C3` 被改成 `FF 15 98 B1 E7 00`。这提示旧返回位置可能仍被引用，但未独立证明只有这一处是全部根因。

验证补丁原值后，回退全部 261 个包装改写，保留 175 项 IAT、32 个普通槽、215 个编码槽及 31 个静态引用修复。最终五组输入与原版一致、退出 0，WOW64 调试通过。回退项不能继续算作最终展开成功项。

资源一致；Load Config 目录 RVA `0xA780C0`，目录大小 `0x40`，内部 Size `0xC0`；SafeSEH 表地址 `0xE78180`、415 项，已排序且 RVA 在映像内。最终扫描仍有 469 处保护区直接引用。有效密钥、真实虚拟机、全部 SEH/SDK 路径及完整重定位未验证；不是完整去保护。

输入 SHA-256：`9BE621DBA5BBFF1BE3F89520A4146F6BB93B81D847D8F0E9469B7AA3A3D12E1D`。

中间 SHA-256：`EFA157B7F7CA9D1466C4ADB8644C28D4FEB0AAEBB7AFDFD4007A37C2C14FECB1`。

首次失败候选 SHA-256：`8DF793AD4AEA4F7B59A6786D9BE5B1717541F0EC9A2889524A286A58F4D76E1A`。

最终 SHA-256：`3778BD6E411FBD42F18334250C9E40301FFAD49EDB5E0DA65D6879DB2E20804F`。

结论：本样本需要旧版 x86 环境适配及有证据的包装回退；API 名解析成功不能自动证明改写后的调用、返回及栈行为正确。

## 后续 Win10 兼容修正（取代上方旧交付统计）

用户反馈旧版在 Win11 正常，但 Win10 缺少 ZwSetInformationCpuPartition 入口。追溯发现四个 final_scan_only 数值碰撞误报，既不来自 bootstrap/编码导入，也没有相应指令补丁或对槽地址的绝对引用。其中 NtAllocateVirtualMemoryEx 的所谓指针实际跨越正常指令字节。

恢复 RVA `0x16A414`、`0x1F105C`、`0x471DB4`、`0x473468` 的原值，并移除误加的 NtAllocateVirtualMemoryEx、Heap32ListNext、GetUserDefaultGeoName、ZwSetInformationCpuPartition。保留 IAT 地址不变，必要时拆分 KERNEL32 描述符；不替换 API、不复制系统 DLL。修正版实际导入为 171 项，已无 NTDLL 导入描述符。

兼容修正版 SHA-256：`DD243320E846EE32B41F82CE9FCE479787BAFD7DB531D90EAEF555CA857B83F1`。本机五组对比与 WOW64 调试通过；真实 Win10 仍待用户复测。旧 175 项/3778BD6E…版本只保留作证据，不应继续作为推荐产物。详见 [导入来源审计](import-provenance.md)。
