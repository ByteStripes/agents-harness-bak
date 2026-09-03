# API 设计 — endpoint / schema / folder / response-component / security-scheme

> 本模块覆盖 Apifox API 设计相关命令。已从 SKILL.md 继承：写入标准流程、分支参数规则。

## 何时加载

- 创建/更新/查询/删除接口（endpoint）
- 管理 Schema 数据模型
- 管理目录/文件夹结构
- 创建/管理响应组件、安全方案

## 命令入口

```bash
apifox endpoint --help
apifox schema --help
apifox response-component --help
apifox security-scheme --help
apifox folder --help
```

具体参数以当前 CLI help 为准。

## 核心边界

| 资源 | 用途 | 注意 |
|------|------|------|
| endpoint | 接口定义（method + path + params + body + response） | 不等同 test-case |
| schema | 可复用的数据模型 | 先创建再由 endpoint 引用 |
| response-component | 可复用的响应结构 | 减少重复定义 |
| security-scheme | 认证方案（Bearer/JWT/Basic 等） | 全局引用 |
| folder | 接口目录/分组 | 组织接口层级 |

## 创建接口标准流程

1. 确认 project 和 branch
2. 先创建可复用资源（schema、response-component、security-scheme）
3. 获取 `endpoint-create` schema：`apifox cli-schema get endpoint-create`
4. 生成 JSON，通过 `cli-schema validate` 校验
5. 执行 `apifox endpoint create ...`
6. `apifox endpoint get <id>` 验证保存结构

## 不可违反规则

1. 不要把 endpoint 和 test-case 混写
2. 先建可复用资源，再引用到 endpoint
3. 创建后必须 `get` 验证
4. 环境变量不要写进 common-parameter
