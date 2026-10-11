# categories 模块设计

关联任务：[课程分类 #6](https://github.com/Bdemoy/RAG/issues/6)。产品与架构要求见 [#1](https://github.com/Bdemoy/RAG/issues/1)、[#2](https://github.com/Bdemoy/RAG/issues/2)。

本文说明分类模块的业务职责、数据归属、调用流程和事务责任。以下内容是设计约定，业务实现及验收进度由关联任务和 PR 记录。

## 功能
- 创建、查看、重命名、删除分类
- 一份资料最多属于一个分类，也可以未分类
- 删除分类时保留资料，资料变为未分类
- 给 usecases 提供分类有效性校验

## 业务职责与数据归属
categories 管理分类记录，并提供分类存在性检查。分类通过 ID 标识；名称用于展示，创建时间记录分类建立的时间。
- categories 维护分类的 ID、名称和创建时间。
- documents 维护资料所属的 `category_id`；一份资料最多关联一个分类，也可以未分类。
- 数据库通过分类名称唯一约束和外键维护数据关系。
- usecases 组织涉及分类与资料的完整操作，决定各模块的调用顺序及事务提交。

## 数据原型
```python
class Category:
    id: int
    name: str            # 唯一
    created_at: datetime

# documents.category_id → categories.id  ON DELETE SET NULL
```

## 对外接口
```text
POST   /categories        {name}  → Category，重名 409
GET    /categories        → list[Category]
PATCH  /categories/{id}   {name}  → Category，不存在 404，重名 409
DELETE /categories/{id}
```
```python
# categories/service.py：不提交事务，由 router 或 usecases 提交
def create(session, name: str) -> Category
def list_all(session) -> list[Category]
def rename(session, cat_id: int, name: str) -> Category
def delete(session, cat_id: int) -> None
def ensure_exists(session, cat_id: int | None) -> None   # None 直接通过；不存在 → 404
```

## 调用关系与业务流程

### 1. 用户管理分类
分类管理直接从 categories router 进入，由 router 调用自己的 service：
```text
用户管理分类
→ categories.router 接收请求并取得 session
→ categories.service 处理分类业务
→ 写操作由 categories.router 提交事务
→ 返回结果
```
- 创建：接收名称，检查名称是否可用，创建分类记录，提交成功后返回分类信息。
- 列表：读取已有分类并返回 ID、名称和创建时间，供展示与选择；没有分类时返回空列表。
- 重命名：按 ID 找到分类，检查新名称是否可用，修改名称并提交。ID 和创建时间保持原值，关联资料的归属保持不变。
- 删除：按 ID 定位并删除分类。数据库执行删除 SQL 时，按外键 `ON DELETE SET NULL` 清空关联资料的分类 ID；分类删除与归属清空在同一事务中提交，资料正文和文本块保留。
这四个分类管理接口直接调用分类 service。

### 2. 资料业务使用分类检查
导入资料或修改资料归属时，由 documents router 调用 usecases，usecases 再使用分类模块提供的能力：
```text
用户导入资料
→ documents.router
→ usecases.import_document
   → documents.parse：解析并规整完整正文
   → categories.ensure_exists：检查指定分类
   → indexing.prepare_chunks：写库前准备文本块和向量
   → documents.insert：保存资料及所属分类 ID
   → indexing.save_chunks：保存文本块
   → usecases 统一提交本次操作
```
修改资料分类时：documents router → usecases.update_meta → 提供非空分类 ID 时调用 categories.ensure_exists → documents 保存元数据 → usecases 提交。未传分类字段保留原归属，显式 null 清空分类；修改标题或分类不重建文本块与向量。
categories 为 usecases 提供能力，自身保持对分类数据的职责，不依赖 usecases。

### 3. 分类有效性检查的含义
`ensure_exists(session, cat_id)` 中的“有效”指指定分类 ID 存在。
- `cat_id=None`：表示未分类，直接通过。
- 分类 ID 存在：检查通过，usecases 继续后续业务。
- 分类 ID 不存在：报告 404，usecases 停止本次操作。
这是一项只读检查。检查通过后，资料归属仍由 documents 写入，整项操作由 usecases 编排。

### 4. 连续业务示例
创建“高等数学”分类，获得 ID 7 → 导入笔记并选择分类 7 → documents 保存资料的 `category_id=7` → 分类改名后 ID 仍为 7，资料归属不变 → 删除分类 7 后，资料变为未分类，正文和文本块继续保留。

## 示例
```text
POST /categories {"name": "高等数学"}
→ router 调 service.create → 提交 → 201 {"id": 1, "name": "高等数学"}

DELETE /categories/1
→ service.delete → 提交
→ 数据库按外键把 documents.category_id = 1 的资料置为 NULL
→ 这些资料在"全部资料"范围内仍能被问到
```

## 事务责任与失败处理
单模块分类写操作由 categories router 掌管事务；跨模块操作由 usecases 掌管事务。调用方提供 session，各参与步骤使用同一个 session。
- service 处理业务、读写数据并报告结果或错误；service 不提交，事务是否完成由调用方决定。
- 写入或必要的 `flush` 可以执行 SQL、获得新分类的 ID；此时修改仍处于当前事务中，尚未最终提交。
- 分类不存在、名称冲突等业务问题按接口约定报告；分类名称的唯一性由数据库约束兜底，包括并发创建同名分类的情况。
- 写入或提交失败时，由事务负责方回滚本次事务并返回错误，保留操作前已经提交的数据。
- 分类删除与关联资料归属清空一起提交，失败时一起回滚。
- 写操作只有提交成功后才对外返回成功；分类列表和存在性检查是只读操作。
正常路径：调用方 → service 处理业务 → 调用方提交 → 返回成功。
失败路径：service 或数据库报告错误 → 事务负责方回滚 → 返回错误。

## 边界
- 不依赖其他业务模块
- 不读写资料正文；"删分类保留资料"由外键 SET NULL 完成，本模块不直接改 documents 表
