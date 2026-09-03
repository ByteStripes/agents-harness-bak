---
name: apifox
description: Apifox CLI 全功能入口。覆盖登录/项目管理、API 设计、环境/Mock、分支协作、测试用例、测试场景、自动化测试/CI、导入导出、API 生命周期工作流及问题排查。按需加载命令模块。
metadata:
  requires:
    bins: ["apifox"]
  cliHelp: "apifox --help"
agent_created: true
---

# Apifox CLI

用 Apifox CLI 完成用户请求。不要凭记忆拼 payload，优先让 `--help`、`cli-schema`、`agentHints.nextSteps` 驱动下一步。

## 安装

如果 `apifox` 不可用：

```bash
npm install -g apifox-cli@latest
```

如果下载较慢或安装异常，可切换国内镜像源：

```bash
npm install -g apifox-cli@latest --registry=https://registry.npmmirror.com/
```

安装后执行 `apifox login --with-token <TOKEN>` 登录。API 访问令牌在 Apifox 客户端「用户头像 → 账号设置 → API 访问令牌」创建。

> 不要每次默认升级；只有命令返回版本过低/unknown command/参数缺失疑似旧版导致，或用户任务依赖新能力时，才建议升级。

## 模块按需加载

本 skill 按命令类别拆分为以下模块。**读到本文件后，根据用户任务匹配模块，立即读取对应 `modules/<name>.md`：**

| 用户任务关键词 | 加载模块 | 覆盖命令 |
|---|---|---|
| 安装、登录、项目、初次使用、help | `modules/quick-start.md` | login, project, 基础用法 |
| 接口、endpoint、Schema、目录/文件夹、安全方案 | `modules/api-design.md` | endpoint, schema, response-component, security-scheme, folder |
| 环境、变量、Mock、数据库连接 | `modules/environment.md` | environment, variables, mock, database-connection |
| 分支、合并、merge request、AI 分支、pick-to | `modules/branch.md` | branch, merge-request |
| 测试用例、test case、测试数据 | `modules/test-case.md` | test-case, test-data |
| 测试场景、多步骤、场景编排 | `modules/test-scenario.md` | test-scenario |
| 测试套件、定时任务、runner、CI、报告 | `modules/test-automation.md` | test-suite, scheduled-task, runner, run, test-report |
| 导入、导出、OpenAPI、Postman、质量门禁 | `modules/import-export.md` | import, export |
| 创建一组接口、全流程、API 生命周期 | `modules/workflow.md` | 端到端工作流 |
| 命令成功但页面没有、404、找不到资源、版本问题 | `modules/troubleshooting.md` | 排查与版本确认 |

> 用户任务可能匹配多个模块（如"创建接口并写测试用例"→ 先读 api-design.md，再读 test-case.md）。按需依次加载。

## 核心共享规则

以下规则适用于**所有模块**，模块文件中不再重复。

### 基础用法

```bash
apifox --help
apifox <command> --help
apifox <command> <subcommand> --help
```

全局参数：

```text
--project <projectId>     项目 ID
--branch <branchName>     分支名；纯数字值兼容旧 branchId
--access-token <token>    覆盖当前登录 token
--api-base-url <url>      私有部署地址
```

### 登录与项目

- 未登录时让用户提供 API 访问令牌：`apifox login --with-token <TOKEN>`
- 凭证存在 `~/.apifox/config.toml`；不要把 token 打印到日志、提交到仓库或写进普通聊天摘要
- 项目未指定时，先查 `.apifox/settings.json` 中是否有默认 `projectId`
- 项目 ID 可从「项目设置 - 基本设置 - 项目 ID」获取，或 `apifox project list`
- 写入任何本地配置文件前先询问用户

### 写入标准流程

执行 `create` 或 `update` 前必须：

1. `apifox cli-schema get <schemaKey>` — 获取 JSON schema
2. 生成资源的 JSON 数据文件
3. `apifox cli-schema validate <schemaKey> --file <path>` — 校验
4. 只有 `validate` 无误后才执行 `create` 或 `update`
5. 命令完成后读取 `agentHints.nextSteps` 继续执行或恢复

### CLI 事实优先

- 具体命令、参数、schema key 以当前 CLI 输出为准
- 如本 skill 与当前 CLI 输出不一致，以 CLI 输出执行，并同步修正本 skill

### AI 写入权限

- 写入被 AI 权限限制时，不要替用户选择，优先询问：开启目标分支直接编辑权限，或在 AI 分支上编辑
- 直接编辑主分支/迭代分支/通用分支 → 需在 Apifox 客户端 2.8.32+ 「项目设置 - 功能设置 - AI 功能设置 - 外部 AI 编辑权限」开启
- 选择 AI 分支流程：创建 AI 分支 → pick-to 导入资源 → 编辑 → 完成后提醒用户合并
- 目标主分支受保护时（isProtected），优先 `merge-request`，不要直接 `merge`

### AI 分支说明

- AI 分支是给 AI/自动化修改项目资源的隔离分支
- 24 小时内与来源分支无差异将自动归档
- AI 分支初始为空，修改源分支已有资源前必须先 `pick-to`
- AI 分支新建资源无需先导入
- AI 分支修改不会自动写回源分支；完成后必须让用户确认是否合并

### 必须询问用户

- 登录 token、本地配置写入、私有部署地址
- 创建/切换 AI 分支、导入源分支资源到 AI 分支
- 删除、归档、覆盖导入、批量更新等破坏性操作
- AI 分支改动 merge / merge-request 回源分支
- 是否升级 CLI

### 分支参数规则（全局）

- 优先使用分支名：`--branch <branchName>`
- 同一任务内查询、创建、更新、运行测试必须带同一个分支上下文
- 不要在分支任务中省略 `--branch`

### 命令输出处理

- 命令输出结果后，优先读取 JSON 里的 `agentHints.nextSteps`
- `success=false` 时以真实 `success` 字段和退出码为准，不要相信 summary 里的成功语义
