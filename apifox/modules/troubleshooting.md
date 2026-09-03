# 排查与版本确认 — 问题定位

> 本模块用于排查 Apifox CLI 常见问题。已从 SKILL.md 继承所有核心规则。

## 何时加载

- CLI 返回成功，但 Apifox 页面看不到资源或展示不完整
- 创建后 `list/get` 找不到资源
- 测试用例/场景/套件运行失败
- 本地报告或云端报告找不到、没有步骤详情
- `agentHints`、help、示例和实际行为互相矛盾
- 需要确认 CLI 版本或更新

## 排查 5 步法

1. **记录原始命令**：projectId、branch、resourceId、environmentId、文件路径、是否带 `--api-base-url`
2. **检查版本**：`apifox --version`
3. **查看 help**：`apifox <command> --help`，以当前公开 help 为准
4. **回读验证**：`list/get` 确认资源是否写入预期项目/分支/模块/目录/分类
5. **区分报告类型**：未带 `--upload-report` 时，不要去云端报告列表找结果

## 版本检查

```bash
apifox --version
```

参数不存在时先更新：

```bash
apifox update --yes
```

版本排查结论必须写清：当前版本、命令路径（`which apifox`）、缺失的参数名、建议更新方式。

## 页面看不到资源

优先检查：
- 是否写入正确 project
- 是否带正确 `--branch`
- 资源是否在 AI 分支中，页面当前是否查看同一分支
- 是否写入预期模块或目录
- 测试用例是否使用有效 `categoryId`

常用回读：
```bash
apifox endpoint list --project <projectId> --branch <branchName>
apifox test-case list --project <projectId> --endpoint <endpointId> --branch <branchName>
apifox test-scenario get <scenarioId> --project <projectId> --branch <branchName> --with-case-detail
```

## 测试用例排查

- 创建前必须 `apifox test-case category --project <projectId>` 获取有效 `categoryId`
- `test-case get` 能看到结构 ≠ 一定能运行
- 运行失败时检查 environment、变量、请求体、前后置脚本、断言和报告详情

## 测试场景排查

- `test-scenario create` 只创建元数据，步骤需要后续 `import-steps` / `add-ref` / `update --file`
- 创建/更新后先 `test-scenario get --with-case-detail`
- 步骤间变量为空 → 检查是否运行完整场景、步骤编号、响应路径、提取变量

## 运行与报告排查

- 未指定 `--environment` 时可能使用默认环境，建议显式指定
- 本地报告看 `--out-dir` / `--out-file`
- 只有带 `--upload-report` 时云端才有报告
- 有副作用的测试不要在生产环境执行

## help 与提示冲突

- 以当前 `apifox <command> --help` 和实测为准
- 不主动推荐 help 未公开的隐藏别名
- `success=false` 时以真实 `success` 字段和退出码为准

## 常见分流

| 现象 | 处理 |
|------|------|
| 新参数不识别 | `apifox --version`、`which apifox`，必要时 `apifox update --yes` |
| 创建成功但页面没看到 | 检查 project、branch、模块、目录、分类、页面筛选 |
| test-case 页面看不到 | 检查 `categoryId`、endpoint、branch |
| 场景步骤不展示 | `test-scenario get --with-case-detail`，确认 create 后写入 steps |
| run-config 或运行前失败 | 确认 case/scenario/endpoint/environment/branch 都存在 |
| 云端报告找不到 | 确认运行时是否带 `--upload-report` |
| agentHints 和 help 冲突 | 以当前 help 和实测为准 |
