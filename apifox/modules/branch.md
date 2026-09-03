# 分支协作 — branch / merge-request

> 本模块覆盖分支管理、AI 分支、pick-to、合并与合并请求。已从 SKILL.md 继承：AI 权限规则、AI 分支说明、分支参数规则、必须询问用户。

## 何时加载

- 创建/查看/归档/删除分支
- 创建 AI 分支并在分支上修改资源
- 将源分支资源 pick-to 到目标分支
- 合并分支或创建/审批 merge request
- 遇到 AI 写入权限限制

## 命令入口

```bash
apifox branch --help
apifox merge-request --help
```

具体参数以当前 CLI help 为准。

## 先判断怎么改

分支写入前先问清楚用户：

- 直接编辑目标分支：用户明确允许直接修改，且目标分支没有保护或权限限制
- 通过 AI 分支编辑：目标分支受保护、未开启外部 AI 直接写入，或用户希望先隔离验证再合并

开始写入前必须确认：项目 ID、源分支和目标分支、修改的资源范围、是否允许后续 merge/merge-request。

## AI 分支完整流程

```text
确认源分支和目标变更
  → 创建 AI 分支（命名：ai/年月日-from-来源分支名-功能模块名）
  → pick-to 已有资源（新建资源不需要）
  → 在 AI 分支修改（所有命令带 --branch <aiBranchName>）
  → 验证 get/run/report
  → merge-request preview 让用户确认
  → 用户确认后 create merge-request 或 merge
```

## AI 分支注意点

- AI 分支初始为空，不会自动复制源分支全部资源
- `branch get` 可能返回 `type: SPRINT` 且 `isAiBranch: true`；AI 分支操作仍使用 `--type ai`
- 修改源分支已有资源前必须先 `pick-to`
- 写入 AI 分支可能因"允许 AI 修改 AI 分支内容"关闭而失败

## pick-to 规则

- 必须带 `--type ai`
- 只支持从主分支或普通迭代分支导入到 AI 分支
- 不能导入到主分支，不能以 AI 分支作为来源
- 使用 `--include-endpoint-cases` 可在导入接口时同时导入接口用例

## 分支参数规则

- 同一任务内查询、创建、更新、运行测试必须带同一个分支上下文
- `get` 不带 branch 找不到资源 → 带 `--branch <branchName>` 重试
- AI 分支里找不到源资源 → 先 `branch pick-to` 导入

## 合并规则

- 目标主分支受保护时（isProtected），优先 `merge-request preview/create`，不要直接 `branch merge`
- 从 CLI 直接执行合并/合并请求时，要求来源和目标分支的直接编辑权限均已开启
- 否则提醒用户在客户端手动触发合并

## 不可违反规则

1. 不要在用户未确认时创建 AI 分支
2. 不要在 AI 分支里修改源分支已有资源而不先 pick-to
3. 不要在分支任务中省略 `--branch`
4. 不要在用户未确认时 merge、create merge-request 或审批 merge request
5. 不要删除/归档分支，除非用户明确要求
6. 遇到 `Automation caller branch required` 时必须停下来问用户选择权限策略
