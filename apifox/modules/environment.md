# 环境与 Mock — environment / variables / mock / database-connection

> 本模块覆盖环境配置、变量管理、Mock 规则及数据库连接。已从 SKILL.md 继承：写入标准流程、分支参数规则。

## 何时加载

- 创建/更新/查询/删除环境
- 管理环境变量、全局变量
- 配置 Mock 规则/期望/智能 Mock
- 配置数据库连接

## 命令入口

```bash
apifox environment --help
apifox variables --help
apifox mock --help
apifox database-connection --help
```

具体参数以当前 CLI help 为准。

## 环境管理

```bash
# 列出项目环境
apifox environment list --project <projectId>

# 获取环境详情
apifox environment get <environmentId> --project <projectId>
```

- 创建/更新前先通过 `cli-schema get` 获取结构定义
- 敏感变量（token、密码等）不要在回复中展示

## Mock 配置

Mock 是独立于环境的功能，需要在接口层级配置 Mock 规则或期望。

- 先确认接口已有响应定义，再配置 Mock
- Mock 未配置可能导致接口测试返回 404 或异常响应
- 区分：接口测试失败 ≠ 接口定义未保存，也可能是 Mock/环境未配置

## 运行环境建议

- 运行测试时建议显式带 `--environment`
- CI 场景 token 通过 secret 注入，不要写入仓库

## 不可违反规则

1. 敏感变量不要出现在最终回复中
2. 运行测试建议显式指定 `--environment`，避免默认环境变化
3. 不要在未确认环境的情况下执行有副作用的操作
