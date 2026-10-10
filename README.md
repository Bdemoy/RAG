# MyDocAgent

个人学习资料知识库。计划支持课程笔记导入与分类、基于资料的问答，以及原文引用核对。

> 当前阶段：后端骨架。已提供应用入口、数据模型、函数签名、路由和启动测试；业务函数仍为 `raise NotImplementedError`。资料管理、分类和问答功能待后续 PR 实现，前端尚未开始。

## 本阶段可验证的内容

- FastAPI 应用启动时通过 `init_db()` 创建 categories、documents、chunks 三张表。
- `/health` 返回 `{"status":"ok"}`，`/docs` 提供接口文档。
- pytest 检查健康接口、业务表存在和文档页面可访问。
- GitHub Actions 在 PR 和 main 更新时，使用临时 PostgreSQL 运行锁定依赖安装和 pytest。

## 计划功能

- 导入 TXT、Markdown、可提取文字的 PDF，或粘贴文本。
- 查看、修改、分类和删除资料；正文修改与文本块同步更新。
- 在指定课程或全部资料中提问，根据证据回答，并展示引用来源。
- 证据不足时最多补查 2 次，再给出回答、部分回答或资料不足说明。

详见 [#1 产品需求](https://github.com/Bdemoy/RAG/issues/1)。

## 技术栈

| 部分 | 选型 |
|---|---|
| 后端 | Python ≥3.13、FastAPI、SQLModel |
| 数据库 | PostgreSQL ≥16；向量检索实现阶段接入 pgvector |
| 模型 | Embedding 模型生成向量，对话模型完成问答 |
| 前端（待实现） | HTML、CSS、JavaScript，Vite |

本阶段的启动和测试只需 PostgreSQL，不需要模型 API Key、向量扩展或 Node.js。

## 架构

| 模块 | 职责 |
|---|---|
| documents | 解析和保存完整正文，管理资料信息 |
| categories | 管理分类，校验分类存在 |
| indexing | 生成文本块和向量，检索证据与相邻片段 |
| qa | 执行固定的检索、判断、有限补查和回答流程 |
| usecases | 编排跨模块调用，决定顺序和事务提交 |

service 不互相调用，也不提交事务。跨模块操作由 usecases 提交；单模块写操作由 router 提交。

`Document.content` 是解析并规整后的完整正文，也是索引输入和 offset 基准；`Chunk.content` 是其中一段。索引完成后仍保留完整正文。

元数据 PATCH 仅传递明确提供的字段：分类未传时保留，传 `null` 时清空，传 ID 时校验分类存在。正文更新先确认资料存在，再规整编辑文本，生成新分块与向量，最后在同一事务中替换正文和旧块。这些业务流程当前仅定义了接口与说明。

qa 通过 `KnowledgeAccess` 接口取得检索能力，由 adapters 连接 indexing，并在 main 中注入。

详见 [#2 架构设计](https://github.com/Bdemoy/RAG/issues/2)。

## 目录

```text
backend/
├── app/
│   ├── main.py
│   ├── usecases.py
│   ├── documents/
│   ├── categories/
│   ├── indexing/
│   ├── qa/
│   ├── adapters/
│   └── infrastructure/
├── tests/test_health.py
├── .env.example
├── pyproject.toml
└── uv.lock
.github/workflows/ci.yml
```

## 本地运行

先安装 Python ≥3.13、[uv](https://docs.astral.sh/uv/) 和 PostgreSQL，并启动数据库服务。创建供应用使用的数据库，按本机实际情况调整连接参数：

```bash
createdb -h 127.0.0.1 -p 5432 -U postgres mydocagent
```

从仓库根目录进入 backend，安装锁定依赖并准备配置：

```bash
cd backend
uv sync --frozen
cp -n .env.example .env
```

在 `.env` 中填写实际的 `DATABASE_URL`。默认示例连接本机 5432 端口的 mydocagent 库；`.env` 不提交。

```bash
uv run --frozen uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开 [健康接口](http://127.0.0.1:8000/health) 和 [接口文档](http://127.0.0.1:8000/docs)。业务接口仍为占位实现。

## 测试与 CI

测试会执行应用启动和建表流程。先在 PostgreSQL 中创建独立的测试库：

```bash
createdb -h 127.0.0.1 -p 5432 -U postgres mydocagent_test
```

在 backend 目录运行，按实际端口和认证方式调整 URL；下面使用默认示例账号：

```bash
DATABASE_URL='postgresql+psycopg://postgres:postgres@127.0.0.1:5432/mydocagent_test' \
  uv run --frozen pytest -v
```

CI 使用 Python 3.13 和临时 PostgreSQL 16，执行 `uv sync --frozen`、`uv run --frozen pytest -v`。

## 开发流程

- 每个 PR 关联对应 issue，公开需求和验收说明可独立阅读。
- PR1 验收后，业务功能通过后续 PR 逐项实现。
- 完成本地和 CI 验证，经过代码审查及项目负责人最终确认后 squash 合入 main。
- PR 标题采用 `类型(范围): 描述`。
