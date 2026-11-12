# 参考案例：VMProtect Ultimate 3.5.0

用户提供文件名 `ConsoleApp2Cpp_VMP_Ultimate.3.5.0.vmp.exe`，说明相同参数。DIE 识别范围为 VMProtect 3.2.0–3.5.0，精确版本来自用户。输入 6,000,640 字节，AMD64 EXE，壳入口 RVA `0x54A03C`，ImageBase `0x140000000`，22 个磁盘导入。

## 原流程不能直接完成

1. 原模拟器在 user32!GetProcessWindowStation 停止（unknown_import）。
2. 添加窗口站/UOI_FLAGS 模型后，在 MessageBoxW 处读到“A debugger has been found running in your system.”。诊断显示样本读取模拟 ntdll 的空资源目录。
3. 从随工具提供的 ntdll 复制 896 字节真实版本资源载荷，重建 984 字节资源目录；不改变版本载荷。此后不再进入此前错误路径，继续到缺失的 CheckRemoteDebuggerPresent。
4. 按当前进程无调试器的模型补充该 API，必须返回成功并写出 FALSE。运行约 147 秒后又遇到 EnumSystemFirmwareTables('FIRM') 缺失。
5. 按上游已有固件模型的 UEFI 场景补充固件 API，FIRM 返回不支持；最终运行成功。

具体实现与官方语义链接见 [legacy-compat.md](legacy-compat.md)。成功轮实际调用了新增 CheckRemoteDebuggerPresent 和 FIRM 枚举模型；窗口站模型用于失败路径调查，RSMB 读写通过单元检查但未在成功轮观察到调用。不要把“兼容层里存在”写成“目标实际调用过”。没有吞掉 MessageBox 或统一跳过未知 API。

## 成功轮与验证

约 239 秒，90,797,689 个基本块，恢复 1,299 页；170 个 IAT 项；303 处调用、41 处跳转、5 处加载共 349 个引用；22 个普通槽和 230 个编码槽。239 秒不含此前失败与重跑时间。

自动 stop `0x1401C1B5C` 位于 `.vmp0`。重新发现 CRT 候选 `0xB45E0`/`0xB48B0`，反汇编并测试选用前者。仅改入口的版本在实际基址 `0x7FF7B1AC0000` 下执行旧地址 `0x140AD1BB8` 而崩溃；固定基址后正常运行。保留 Load Config（RVA `0xABFE10`、大小 `0x140`）；自动重建到最终版仅 8 个 PE 头字节变化。

五组空/无效输入与原文件一致、均退出 0；真实附加调试只有系统初始断点并正常退出。资源载荷一致。异常表 4,959 项且已排序，但保护区三组相邻区间重叠；`.text` 扫描有 137 处指向保护区的直接引用，不能删除全部壳段。仍未验证有效密钥、所有异常/SDK 路径、真实虚拟机或完整重定位。

输入 SHA-256：`DC82B66BD32A20A16AB96D62933013C2948EE06DD3CDC0A75409F5B8D466EF95`。

中间 SHA-256：`92B4B13B554F37A1AE8D98073D6DF12E51A3D511C5BAEA3BA86B48114F4495B3`。

最终 SHA-256：`E48A4887F7E33E083EF5D387F3BDA864686F7D9A3EF8B2B104026F1C791E8399`。

结论：旧技能原样运行失败；加入有明确语义、可测试的模拟兼容层后，可获得已验证路径的可运行恢复版。此结论不能外推为所有 3.5.0 配置或全部旧版本均支持。

后续用户确认此恢复版“可以正常工作”。这是用户侧成功复测；未提供具体输入、虚拟机和调试环境，不能自行扩展测试覆盖范围。
