# 旧版 x64 模拟兼容层

仅在普通流程出现对应缺口时启用 `scripts/run_with_winstation.py`；该命令行入口仅用于 x64，不是所有版本的默认选项，也不是宿主 API hook 或原 EXE 的永久补丁。x86 通过专用 `run_x86_compat.py` 的显式选项复用经验证的辅助模型，不直接给此入口传 `--32bit`。脚本通过当前进程内的适配器扩展已下载的 vmp-lazy-unpack，不修改上游源码。上游已经实现的 API 不被覆盖。

```powershell
$env:PYTHONPATH = "$PWD\tools\pylibs"
python -u "$skillDir\scripts\run_with_winstation.py" --tool-root .\tools\vmp-lazy-unpack-main --ntdll-resources -- .\sample.exe sample.stage1.exe --diagnostics
```

脚本依赖上游 ApiHandlers、catalog 和 synthetic PE 布局。变更工具版本后须重新检查接口与测试，不能保证自动兼容。命令行入口仍拒绝 `--32bit`；共享资源函数已按架构核对 catalog/Magic，并选择 PE32/PE32+ 的资源目录偏移，分别经过回归验证。工具根必须含 unpack/tracer.py，依赖安装在任务环境中。

## 已实现的有限模型

- GetProcessWindowStation：返回稳定的模拟窗口站句柄。GetUserObjectInformationA/W 仅支持此句柄的 UOI_FLAGS，返回 12 字节 USEROBJECTFLAGS，处理短缓冲区、输出长度和无效地址；其他信息类停止。
- CheckRemoteDebuggerPresent：仅支持当前进程伪句柄；成功返回非零，并写入 FALSE，表示所建模的进程没有被调试。不能把返回值零当作“没有调试器”。
- EnumSystemFirmwareTables / GetSystemFirmwareTable：采用与上游固件模型一致的 UEFI 场景，FIRM 返回不支持；RSMB 枚举表 ID 0，内容复用上游 smbios_table()，支持查询长度、短缓冲区和实际复制。未知 provider 停止，不能伪造任意 ACPI 表。
- `--ntdll-resources`：从随工具提供的 ntdll.dll **原样复制版本资源载荷**，重建其三级资源目录到 synthetic ntdll 中。不是伪造任意 Windows 版本，也不读取宿主系统 DLL。仅支持当前观察到的单个数字 ID、单语言版本资源，校验 PE64 头、空间和目标区为空；不匹配就停止。

窗口站模型在本次失败路径调查中调用过；成功流程的关键差异是补充 ntdll 版本资源和缺失的调试/固件 API。脚本没有吞掉 MessageBox，也没有“所有未知 API 一律成功”的兜底。

参考官方语义：[GetProcessWindowStation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getprocesswindowstation)、[GetUserObjectInformationW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getuserobjectinformationw)、[CheckRemoteDebuggerPresent](https://learn.microsoft.com/en-us/windows/win32/api/debugapi/nf-debugapi-checkremotedebuggerpresent)、[EnumSystemFirmwareTables](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-enumsystemfirmwaretables)、[GetSystemFirmwareTable](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getsystemfirmwaretable)。

## 验证要求

验证 API 的成功/失败返回值、输出缓冲区、所需长度、未知信息类停止，以及版本资源载荷与 catalog 原始数据一致。记录新增模型确实执行过的事件；某个方法经过单元检查不代表已被目标调用。之后仍需真实原生运行、调试及功能对比；模拟通过不能替代真实虚拟机验证。
