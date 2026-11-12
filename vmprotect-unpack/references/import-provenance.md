# 导入来源与跨 Windows 版本审计

在较新 Windows/catalog 下运行通过，不证明旧版 Windows 能装载。新增静态导入会在程序入口执行前就要求目标系统提供对应导出；不能把 Entry Point Not Found 一律归因于用户 DLL 缺失，也不建议用户复制新版系统 DLL。

## 保留来源

x86 适配器支持 `--import-evidence path.json`（在 `--` 前，要求新文件），在重建前保存 bootstrap、解析写入、编码元数据及最终扫描来源。例如：

```powershell
python "$skillDir\scripts\run_x86_compat.py" --tool-root .\tools\vmp-lazy-unpack-main --import-evidence .\analysis\imports-evidence.json -- .\sample.exe sample.stage1.exe --32bit
python "$skillDir\scripts\audit_import_evidence.py" .\sample.stage1.exe --evidence .\analysis\imports-evidence.json --reconstruction .\analysis.imports.json --out .\analysis\imports-audit.json
```

审计工具只列出需要复核的 final_scan_only 候选，不自动删除。单独检查这些候选是否存在原导入描述符、编码元数据、真实 API 解析写入、调用点或可信数据引用。重建器自己生成的 thunk/IAT 不能反过来当作原始程序调用证据。

## 数值碰撞的实测错误

模拟模块的 API 地址只是人工布局中的整数。原代码/位移/字节码里相同的 4 字节并不一定是函数指针。旧版 x86 分类器曾把恢复区中的每个非 bootstrap 扫描匹配都加入额外导入。

Ultimate 3.5.0 x86 的四项误报仅有 final_scan_only 来源，无 bootstrap、编码表或指令补丁证据，也没有对槽地址的绝对引用。其中 RVA `0x16A414` 的 `00 0F 84 70` 跨越比较指令尾部与条件跳转，却匹配模拟 NtAllocateVirtualMemoryEx 地址。另三个匹配 Heap32ListNext、GetUserDefaultGeoName、ZwSetInformationCpuPartition。误报不仅增加不必要依赖，还会改坏原字节；Windows 11 可解析导出，掩盖了问题，用户的 Windows 10 在入口前报错。

缺少绝对引用本身不构成删除证明，编码/间接引用可能存在；需要结合来源、上下文及原值证据。此案例经过联合复核后恢复四处原字节并移除对应导入，而非将它们重命名成旧系统 API 或提供虚假成功桩。

## 修复与验证约束

- 修改导入表时保持所有保留 IAT 单元地址不变。不能删除中间元素后整体平移 IAT，代码仍可能引用旧地址。可按经过审核的布局拆分同 DLL 描述符，并在被移除的 INT/IAT 单元终止原连续段。
- 同时撤回误识别槽对应的字节改写，保留精确前后值与输入哈希。
- 重新解析完整导入表，确认误报身份消失、保留项数量/地址正确，检查资源与装载元数据，再重跑原生功能及调试测试。
- 如果有目标系统的可信导出目录，可做静态依赖审计；不要使用分析机的 Win11 导出存在性代替 Win10 验证。
- 没有真实目标系统实测时，结论写成“已移除该缺失依赖，本机回归通过，目标系统待复测”，不要宣称所有 Windows 10 版本已兼容。
