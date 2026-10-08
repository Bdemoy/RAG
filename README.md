# MyDocAgent

个人学习资料知识库。把课程笔记放进来，按课程分类，然后用自然语言提问；回答附带原文出处，资料里没有依据时明确说明，不编造。

> 当前阶段：文档设计。代码按 Issue 逐步提交。

## 功能

- 导入资料：上传 TXT / Markdown / 可提取文字的 PDF，或直接粘贴文本
- 管理资料：查看、修改标题和正文、调整分类、删除；修改后问答立即使用新内容
- 课程分类：一份资料最多属于一个分类；删除分类时保留资料
- 知识问答：在某门课程或全部资料中提问，必要时自动补查
- 来源核对：展示引用的资料标题、章节和原文，可跳转到原文位置
- 证据不足提示：说明已找到什么、缺少什么

详见 [#1 产品需求](https://github.com/Bdemoy/MyDocAgent/issues/1)。

## 技术栈

| 层 | 选型 |
|---|---|
| 前端 | HTML、CSS、JavaScript，Vite 构建 |
| 后端 | Python 3.12+、FastAPI、SQLModel |
| 数据库 | PostgreSQL + pgvector |
| 模型 | Embedding 模型生成向量，对话模型完成问答（具体型号待定） |
| Agent | 拟采用 Agents SDK，接入前验证工具调用兼容性 |

## 架构

后端分为四个业务模块：

| 模块 | 职责 |
|---|---|
| documents 资料管理 | 解析导入内容，资料增删改查，协调正文与文本块同步更新 |
| categories 课程分类 | 分类增删改查，校验分类有效性 |
| indexing 分块与检索 | 切分正文、生成向量，在指定范围内检索证据 |
| qa 知识问答 | 组织检索与 Agent 补查，根据证据回答或说明不足 |

知识问答通过自己定义的知识访问接口（SPI）获取检索能力，不直接依赖检索模块，由适配器在应用入口注入。

详见 [#2 架构设计](https://github.com/Bdemoy/MyDocAgent/issues/2)。

## 目录结构

```text
backend/app/
├── main.py             # 应用入口与依赖组装
├── documents/          # 资料管理
├── categories/         # 课程分类
├── indexing/           # 分块与检索
├── qa/                 # 知识问答、Agent、知识访问接口
├── adapters/           # 知识访问接口到检索模块的适配
└── infrastructure/     # 数据库、模型客户端、配置

frontend/src/
├── documents/
├── categories/
├── qa/
└── api/
```

## 本地运行

> 骨架搭好后补充完整命令。

依赖：

- Python 3.12+，[uv](https://docs.astral.sh/uv/)
- Node.js 20+
- PostgreSQL 16+，并安装 [pgvector](https://github.com/pgvector/pgvector) 扩展
- Embedding 与对话模型的 API Key

配置：复制 `.env.example` 为 `.env`，填写数据库连接和模型配置。

## 开发流程

- 每个功能一个分支、一个 PR，PR 关联对应 Issue
- 采用 squash merge，PR 标题遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/)
