# API 生命周期工作流

> 本模块覆盖从需求到 API 交付的端到端流程。执行前先阅读各具体模块。已从 SKILL.md 继承所有核心规则。

## 适用场景

- 根据需求创建或更新一组接口
- 导入 OpenAPI/Postman 后整理接口、Schema、目录和测试
- 从代码库、PRD、需求文档生成 API spec 后导入
- 给接口补 Mock、测试用例、文档和发布设置
- 在 AI 分支完成 API 变更并准备合并

## 工作流

```text
确认项目/分支
  → 如需从代码/文档导入，先做 spec 生成和质量门禁（modules/import-export.md）
  → 设计接口和 Schema（modules/api-design.md）
  → 配置环境和变量（modules/environment.md）
  → 配置 Mock（modules/environment.md）
  → 创建接口测试用例（modules/test-case.md）
  → 运行测试并查看报告（modules/test-automation.md）
  → 导出/发布文档（modules/import-export.md）
  → 合并或创建 MR（modules/branch.md）
```

## Step 1: 确认上下文

- 确认身份、项目、目标分支
- 直接改主分支/迭代分支时确认权限，或走 AI 分支
- AI 分支改已有资源先用 `branch pick-to` 导入

## Step 2: 设计 API 资源

加载 `modules/api-design.md`。先创建 schema、response-component、security-scheme 等可复用资源，再引用到 endpoint。创建后 `endpoint get` 验证。

## Step 3: 配置环境

加载 `modules/environment.md`。没有合适环境时创建或更新。

## Step 4: 补测试用例

加载 `modules/test-case.md`。不要创建空壳 case，创建后 `test-case get` 验证。

## Step 5: 验证和交付

- 测试报告异常 → 区分本地/云端报告；必要时加载 `modules/troubleshooting.md`
- 前端展示异常 → 加载 `modules/troubleshooting.md`
- 需要合并 → 加载 `modules/branch.md`
- 新建 API 测试返回 404 → 先检查 Mock/环境是否配置，不等同于接口创建失败

## 不可违反规则

1. 不要跳过 project/branch 确认
2. 不要直接在受保护主分支写入
3. 不要只创建接口不验证保存结构
4. 不要只创建空测试用例
5. 不要把测试失败当作接口创建失败
