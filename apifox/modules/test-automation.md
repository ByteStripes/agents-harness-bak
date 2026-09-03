# 自动化测试与 CI — test-suite / scheduled-task / runner / run / test-report

> 本模块覆盖测试套件、定时任务、Runner 管理、测试运行和报告。已从 SKILL.md 继承：写入标准流程、分支参数规则。

## 何时加载

- 创建/更新/运行测试套件（test-suite）
- 运行测试场景（test-scenario）
- 配置定时任务（scheduled-task）或 CI 回归
- 管理 Runner 或检查 Runner 状态
- 配置 `apifox run` 的执行参数（reporters、迭代、变量覆盖、SSL、超时）
- 查看/下载测试报告

## 资源边界

| 用户诉求 | 优先资源 | 如需细节 |
|----------|----------|----------|
| 单接口下的测试用例 | `test-case` | 加载 `modules/test-case.md` |
| 多步骤业务流程建模 | `test-scenario` | 加载 `modules/test-scenario.md` |
| 多场景集合回归 | `test-suite` | 本模块 |
| 定时执行 | `scheduled-task` | 本模块 |
| 私有执行机 | `runner` | 本模块 |
| 查看执行结果 | `test-report` | 本模块 |

## 命令入口

```bash
apifox test-suite --help
apifox scheduled-task --help
apifox runner --help
apifox run --help
apifox test-report --help
```

具体参数以当前 CLI help 为准。

## 测试套件

`test-suite create --name` 创建空套件（`items: []`），客户端可展示但无内容。除非用户明确要占位套件，否则创建回归套件必须通过 `--file` 或后续 update 加入 items。

非空套件使用 `cli-schema get test-suite-create` 中的前端兼容结构，如 `STATIC_TEST_CASE` + `testCases[].id` 引用已有测试用例。不要使用 legacy shorthand（如 `{ testScenarioId }`）。

## Runner

Runner 是团队级执行资源，创建前必须确认团队和用途。常用组合：`runnerType=GENERAL`、`serverType=SELF_HOSTED`。

## 定时任务

创建时不要给空壳示例。真实可用任务通常需要有效 runner、`TEST_SUITE` entityId 等上下文。`runOn` 仅限当前 CLI help/schema 支持值（如 `APP/TSHGR/OSHGR`），不要写未支持的 `CLOUD`。

## 运行参数

以 `apifox run --help` 为准。CI 场景重点确认：environment、reporters、out-dir、upload-report、iteration、变量覆盖、超时。

CI 最小命令形态：

```bash
apifox test-suite run <suiteId> --project <projectId> --environment <environmentId> --reporters cli,json,junit --upload-report
```

## 执行后动作

- 本地报告：检查 `--out-dir` 和 `--out-file`
- 云端报告：仅在带 `--upload-report` 后，按 CLI help 执行 `test-report list/get/download`
- 不带 `--upload-report` 时，云端 `test-report list` 不会出现本次本地执行结果
- CI 中建议显式 `--environment`，token 使用 CI secret 注入

## 创建/更新规则

- 复杂测试场景创建/更新 → 加载 `modules/test-scenario.md`
- 更新前必须先 `get` 原始结构，避免覆盖步骤、变量、场景引用

## 常见恢复

| 现象 | 处理 |
|------|------|
| 创建场景后步骤不对 | 加载 test-scenario；确认 create 后是否 update steps |
| 套件运行为空 | `test-suite get` 确认包含的场景/用例 |
| 套件 `items: []` | 空占位套件，不是有效回归套件 |
| CI 找不到环境 | `environment list/get` 确认 environmentId |
| runner 不可用 | `runner check`，再看 runner get/list |
| 报告没有步骤详情 | 区分本地 JSON vs 云端上传，必要时加载 troubleshooting |
