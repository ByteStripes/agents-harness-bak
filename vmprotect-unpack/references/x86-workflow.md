# 原生 x86 / PE32 路线

先检查 Machine=0x14C、OptionalHeader.Magic=0x10B，再选择 x86；不要按文件名猜位数。工具使用 `--32bit` 和随附 catalog_32.json/ntdll_32.dll，不需要把 Python 宿主也换成 32 位。不要启用仅验证过 x64 的 run_with_winstation.py。

```powershell
$env:PYTHONPATH = "$PWD\tools\pylibs;$PWD\tools\vmp-lazy-unpack-main"
python -u -m unpack .\sample-x86.exe sample-x86.stage1.exe --32bit
```

CRC/LZMA 候选数量为零表示这轮没有匹配到加速例程，不等同于没有压缩或不支持 x86。若缺少状态输出，可使用观测包装器：

```powershell
python "$skillDir\scripts\run_with_progress.py" --tool-root .\tools\vmp-lazy-unpack-main --progress-log .\analysis\heartbeat.jsonl -- .\sample-x86.exe sample-x86.stage1.exe --32bit
```

包装器在原 on_block 完成后只读寄存器和计数，追加 JSONL，不修改目标寄存器/内存；不启用旧版环境兼容层。记录页数、扫描指针、调用事件和计数的变化来判断进度。首次没有可观测状态的运行如果被手工终止，应明确标注“人工终止、未完成”，不能写成工具自报失败或版本不支持。

## 按需 x86 兼容层

本例常规模式在解压后因 VirtualQuery 缺失停止。若日志出现相同缺口，可使用 `run_x86_compat.py`：

```powershell
$env:PYTHONPATH = "$PWD\tools\pylibs"
python "$skillDir\scripts\run_x86_compat.py" --tool-root .\tools\vmp-lazy-unpack-main -- .\sample-x86.exe sample-x86.stage1.exe --32bit
```

VirtualQuery 模型复用模拟器内存映射，输出 28 字节 MEMORY_BASIC_INFORMATION32，按模拟地址上限、长度和写入权限处理失败。kernel32!RtlUnwind 别名仅在现有异常分派处于活动状态时委托给上游 x86 展开器，不是简单返回成功；其他未知 API 仍停止。参考：[VirtualQuery](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualquery)。

对于 Python 全局基本块回调成为瓶颈的情况，可以显式加 `--selective-hooks`（放在 `--` 前）。此选项只在本 x86 样本实测：按上游 native filter 的观测范围思路，保留映像外、恢复区、入口/已知加速点/栈复制点的 block 回调，其他内存写入、系统调用、异常及独立 SEH 监视钩子保持。它不跳过目标指令，但日志的 blocks/instruction_count 此时是**回调计数**，不是基本块总数；上游模拟 QueryPerformanceCounter 也引用该计数，时间敏感样本可能受影响。需要完整指令诊断或怀疑计数影响时关闭该选项。不要将其视为所有样本均可靠的通用加速器。

`--dump-on-failure` 可指定一个不存在的文件，停止时保留内存 PE 供分析；该转储不自动恢复完整导入或启动状态，不能直接命名为成功脱壳产物。适配器依赖当前工具的内部接口，升级工具后须重新验证。

## 入口与 PE 修复

旧版环境检查缺口可以按需添加 `--legacy-user32` 和 `--ntdll-resources`（均在 `--` 前，默认关闭）。前者提供窗口站/UOI_FLAGS/当前进程调试查询模型，MessageBoxW 只提取文本后停止；后者复制匹配 x86 catalog 的版本资源，使用 PE32 目录偏移。不要套用 x64 偏移或绕过错误消息。

模拟成功和 wrapper resolved 不保证原生改写正确。若崩溃位于新导入指令内部、返回地址或邻接栈操作，应核对精确补丁及控制流。未跟踪证实时，不把推测当作已定位的唯一根因。

有证据时可保守回退 encoded_wrapper/api_wrapper 改写，保留原包装代码和恢复的 IAT/编码槽。随附 `restore_wrapper_calls.py` 要求输入 SHA-256，按对应报告验证所有新字节、长度、边界、不重叠后输出新文件：

```powershell
python "$skillDir\scripts\restore_wrapper_calls.py" .\candidate.exe --report .\analysis.imports.json --sha256 EXPECTED_SHA256 --out .\candidate-preserved.exe
```

回退不是默认操作，也不是完整去保护；原包装仍可能依赖保护区。回退后重跑原生功能/调试测试，并区分“工具曾生成的包装补丁数”和“最终保留的改写数”。

使用 Capstone CS_MODE_32 或 x86 调试器重新分析，不照搬 x64 CRT 指令序列、入口 RVA 或安全 cookie 初始化地址。IAT/指针为 4 字节，导入调用通常使用绝对内存操作数；恢复 x86 重定位时检查 HIGHLOW 等实际类型，不能套用 x64 DIR64 的 8 字节修复。

x86 的 SEH/SafeSEH/Load Config 与 x64 的 .pdata/unwind 不同：没有 .pdata 不能直接判定异常信息丢失；不得无条件清除 Load Config 或 SafeSEH。保留 ASLR 测试优先，只有实际换址失败证据才能说明当前候选需要受限固定基址方案。

## 真实调试验证

调试事件结构布局取决于**调试器宿主**位数，而目标寄存器上下文取决于**目标**位数。64 位 Python 的 Win32 DEBUG_EVENT/EXCEPTION_RECORD 不能因为目标 x86 就改成 32 位布局；读取或设置 WOW64 寄存器时才应使用对应上下文 API。

WOW64 进程可能先后出现原生系统断点 `0x80000003` 和 WOW64 断点 `0x4000001F`。记录并区分加载器启动事件、后续断点、访问异常和应用退出，不能把 WOW64 启动断点误判为反调试失败，也不能无条件吞掉后续所有断点。原始测试和候选测试必须使用相同处理方式。

首选现有 x32dbg/WinDbg；自写验证器应核对宿主结构大小、参数/指针类型、EOF、超时和退出事件。参考：[Microsoft WOW64 调试](https://learn.microsoft.com/en-us/windows/win32/winprog64/debugging-wow64)、[调试器异常处理](https://learn.microsoft.com/en-us/windows/win32/debug/debugger-exception-handling)、[LLVM Windows 调试事件实现](https://lldb.llvm.org/cpp_reference/DebuggerThread_8cpp_source.html)。
