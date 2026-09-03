# 导入导出与质量门禁 — import / export

> 本模块覆盖 Apifox 项目数据导入导出及质量门禁。已从 SKILL.md 继承：写入标准流程。

## 何时加载

- 从代码库、PRD、文档生成 API spec 并导入 Apifox
- 导入 OpenAPI、Postman、HAR、Apifox 原生格式
- 配置自动导入
- 导出 OpenAPI、Markdown、HTML、Postman 或 Apifox 原生格式
- 迁移、备份或复制 Apifox 项目

## 命令入口

```bash
apifox import --help
apifox export --help
```

## 核心原则

1. 优先查项目内已有生成器，不要先手写路由提取脚本
2. 不要把"路径完整"误判为"接口 spec 完整"
3. 导入前必须输出质量指标
4. 导入策略不确定时，优先新建临时项目验证，不要污染已有项目
5. 导入结果里的大量 `ignoreCount` 是风险信号
6. Apifox 目录分组依赖 OpenAPI operation tags

## 导入标准流程

### Step 1: 搜索已有生成器

从源码/文档生成 spec 时，先搜项目内：
```
openapi / swagger / routegen / docs generator / api docs / schema generator
```
- 优先使用能抽取 handler request/response struct、DTO、schema 的工具
- 不要先手写脚本从 router 提取路径

### Step 2: 生成 spec 并确认格式

- 保存原始产物
- 不根据扩展名判断格式，读文件开头或用 parser 判断 JSON/YAML

### Step 3: 统计导入前质量指标

必须实际解析文件并报告真实统计值：

| 指标 | 含义 | 用途 |
|------|------|------|
| `paths` | OpenAPI paths 数量 | 接口规模 |
| `operations` | 实际 operation 数量 | 导入规模 |
| `schemas` | `components.schemas` 数量 | 模型完整度 |
| `writes` | POST/PUT/PATCH 写接口数量 | body 覆盖目标 |
| `withBody` | 写接口中有 requestBody 的数量 | requestBody 覆盖率 |
| `emptyObjectBodies` | requestBody schema 是空对象的数量 | 路由骨架风险 |

### Step 4: 判断 spec 完整性

| 现象 | 判断 | 处理 |
|------|------|------|
| 接口/写接口多，schemas 极少 | 疑似路由骨架 | 继续找 DTO、生成器 |
| 写接口多，withBody 覆盖不足 | requestBody 不完整 | 补充 request DTO |
| emptyObjectBodies 很多 | 强风险 | 不作为最终 spec 导入 |
| 纯 GET/健康检查/webhook 项目 | schemas 少可能合理 | 结合业务判断 |

### Step 5: 校验 tags 和可读性

- operation 必须有业务化 tags（不要按 URL path 机械分组）
- tags 按产品模块/业务域/功能域分组
- 不推荐 `api / v1 / <resource>` 这类技术路径展开

### Step 6: 执行导入并检查结果

导入后检查 `ignoreCount`。大量 ignore 意味着接口匹配策略不对或污染了已有项目。

### Apifox 原生格式导入

```bash
apifox import --project <projectId> --format apifox --file ./project.apifox.json
```

默认模块策略 `match-name`：源模块名与目标唯一匹配时导入已有模块，否则新建。策略选项：
- `match-name`：默认，二次导入同一项目推荐
- `new`：每次都创建全新模块
- `--module-map "源模块名=目标模块ID"`：精确控制

导入后必须验证：模块数量、API/Schema/测试用例/场景数量、单接口用例分类可见性。

### Apifox 原生格式导出

```bash
# 全量
apifox export --project <projectId> --format apifox --output ./project.apifox.json

# 指定接口
apifox export --project <projectId> --format apifox --scope apis --api-ids 1001,1002

# 按目录
apifox export --project <projectId> --format apifox --scope folders --folder-ids 2001

# 按标签
apifox export --project <projectId> --format apifox --scope tags --include-tags pet,store
```

## 不可违反规则

1. 不要先手写路由提取脚本，先查项目内生成器
2. 不要把接口数量多等同于 spec 完整
3. 不要跳过导入前质量指标
4. 不要在已有项目反复试错导入
5. 不要忽略大量 `ignoreCount`
6. 不要导入 tags 混乱、无法按业务导航的 spec
