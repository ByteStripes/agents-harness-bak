# 接口测试用例 — test-case / test-data

> 本模块覆盖接口测试用例和测试数据集管理。已从 SKILL.md 继承：写入标准流程、分支参数规则。

## 何时加载

- 创建/更新/删除/查看接口下的测试用例
- 管理测试步骤、断言、提取变量、前后置处理器
- 管理测试数据集（test-data）
- 排查"测试步骤无法展示""断言不生效""提取变量为空"
- 按 caseId、endpointId、categoryId 运行测试用例

## 不应使用

- 多接口流程编排 → 加载 `modules/test-scenario.md`
- 运行套件/CI → 加载 `modules/test-automation.md`
- 只改接口定义 → 加载 `modules/api-design.md`

## 核心概念

| 概念 | CLI 资源 | 说明 |
|------|----------|------|
| 接口测试用例 | `test-case` | 绑定接口 endpoint 的测试数据与步骤 |
| 测试分类 | `test-case category` | 创建 case 前用于获取有效 `categoryId` |
| 测试数据集 | `test-data` | 可供迭代运行的数据 |
| 接口定义 | `endpoint` | case 的依赖对象，不等同 case |

## 命令入口

```bash
apifox test-case --help
apifox test-data --help
```

具体参数以当前 CLI help 为准。

## 创建测试用例标准流程

1. 确认项目和分支
2. 定位 endpoint：`apifox endpoint list/get`
3. **必须执行** `apifox test-case category --project <projectId>` 获取有效 `categoryId`
4. 如有类似 case，先 `test-case list --endpoint <endpointId>` 再 `get` 一个作为模板
5. 获取 `test-case-create` schema 并校验
6. 构造完整 JSON（不要只写空壳 name/endpointId）
7. 创建后立即 `test-case get <caseId>` 确认后端保存结构
8. 运行一次确认 requestBody、处理器、断言和脚本在 runner 中生效

> `categoryId` 是前端展示测试用例的**关键必填字段**。无效 `categoryId` 可能导致 CLI 能看到但客户端不可见。

## 更新测试用例

更新时必须先 `get` 原结构并基于完整结构修改，`update` 不是 JSON Patch，会整体覆盖。`test-case-update` schema 已包含 processor/assertion/extractor 的枚举值说明，不要凭经验猜字段名。

## 处理器结构

```json
{
  "requestBody": {
    "type": "application/json",
    "data": "{\n  \"name\": \"Demo\"\n}"
  },
  "postProcessors": [
    {
      "id": "postProcessors.0.customScript",
      "type": "customScript",
      "data": "pm.test('返回 ID', function () {\n  var body = pm.response.json();\n  pm.expect(body.data.id).to.exist;\n});",
      "defaultEnable": true,
      "enable": true
    },
    {
      "id": "postProcessors.1.extractor",
      "type": "extractor",
      "data": {
        "variableName": "token",
        "variableType": "globals",
        "shareScope": "PROJECT",
        "subject": "responseJson",
        "expression": "$.data.token"
      },
      "defaultEnable": true,
      "enable": true
    }
  ]
}
```

规则：
- `requestBody.data` 必须是字符串，不要把 JSON Body 写成对象
- 处理器使用扁平结构 `{ id, type, data, defaultEnable, enable }`
- 处理器建议带稳定 `id`
- `shareScope` 优先 `PROJECT`，不要默认 `TEAM`
- 多行内容用 `\n` 预格式化

## 断言规则

常规校验优先用可视化 `assertion`，自定义脚本只做兜底：
- HTTP 状态码用 `httpCode`，不要用 `responseCode`
- JSON 字段用 `responseJson`，不要用 `responseBody`
- 全文包含用 `responseText` + `include`
- 比较符用 `equal`，不要用 `equals`

```json
{
  "type": "assertion",
  "data": {
    "name": "HTTP 状态码为 200",
    "subject": "httpCode",
    "comparison": "equal",
    "value": "200",
    "path": ""
  },
  "defaultEnable": true,
  "enable": true
}
```

## 字段风险提醒

- 不要把 `test-scenario` 的步骤结构写进 `test-case`
- 不要只写 case 名称和 endpointId（空壳）
- 不要使用未验证的 `categoryId`
- 不要凭经验猜 processor/assertion/extractor 的字段名
- test-case 不支持跨步骤数据传递，需要时加载 `test-scenario`

## 运行规则

- `test-case run <caseId>` — 单个 case
- `test-case run --endpoint <endpointId>` — 按接口运行
- `--category <categoryId>` 必须和 `--endpoint <endpointId>` 一起使用
- `apifox run --test-case <caseId>` 只支持 caseId
- 建议显式指定 `--environment`

## 常见恢复

| 现象 | 处理 |
|------|------|
| 测试步骤不展示 | `test-case get` 看真实保存结构 |
| 断言不生效 | 对比现有成功 case 模板，检查 assertion 字段 |
| 提取变量为空 | 检查 extractor 层级、变量名、响应路径和执行报告 |
| endpoint 下找不到 case | 检查 `--branch` 和 `--endpoint` |
