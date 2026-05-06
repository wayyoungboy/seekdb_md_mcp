# SMM — seekdb Markdown MCP

[English README](README.md)

> 零配置，自动索引，语义搜索，无限进化。

将本地的 Markdown、TXT、RST 文档索引到 [seekdb](https://github.com/oceanbase/seekdb)，为 AI 工具提供 MCP 集成服务，支持实时文件监听和完整的 Web 管理面板。

## 特性

- **语义搜索** — 基于向量的语义搜索，支持混合、向量和全文三种模式
- **实时同步** — 监听目录文件变化，0.5 秒防抖，自动索引新增/修改/删除的文件
- **MCP 集成** — 通过 stdio 和 SSE 两种传输协议提供 MCP 服务，兼容 Claude Code、Cursor 及任何 MCP 工具
- **智能分块** — Markdown 按标题分块，TXT 按段落分块，RST 按章节分块，自动处理超长文本
- **多集合** — 每个监听目录映射为独立集合，支持按集合搜索或跨集合合并搜索
- **Web 面板** — 基于 React 的完整 Web 界面，支持搜索、文档管理、配置编辑和实时日志流

## 快速开始

```bash
# 安装
pip install -e ".[dev]"

# 初始化配置
smm init

# 导入文档
smm import ~/my-notes

# 启动 Web UI + 文件监听守护进程
smm serve --daemon

# 或者启动 MCP 服务
smm mcp

# CLI 搜索
smm search "如何部署" --mode hybrid

# 查看守护进程状态
smm status
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `smm init` | 创建配置目录并初始化数据库 |
| `smm import <path>` | 从目录导入文档进行索引 |
| `smm search <query>` | 搜索已索引的文档（向量/全文/混合模式） |
| `smm serve` | 启动 Web UI + 文件监听守护进程 |
| `smm serve --daemon` | 后台运行 |
| `smm mcp` | 启动 MCP 服务（stdio 模式） |
| `smm status` | 查看守护进程状态 |
| `smm stop` | 停止守护进程 |
| `smm skill` | 显示 Claude Code 技能配置 |

## 架构

```
CLI                           守护进程
 smm init ──────────────────> FastAPI Web UI + 文件监听 + SSE MCP
 smm import ────────────────> seekdb (HNSW 向量索引 + 全文索引)
 smm search ────────────────> MCP: 搜索 / 导入 / 获取文档 / ...
 smm serve ─────────────────> Web 仪表板 (React + Vite + Tailwind)
```

## 配置

配置文件位于 `~/.smm/config.yaml`：

```yaml
database:
  path: ~/.smm/seekdb.db
  mode: embedded  # embedded 或 server
embedding:
  model: text-embedding-3-small
  dimension: 1536
chunking:
  max_tokens: 512
  overlap: 50
search:
  top_k: 10
  mode: hybrid
web:
  host: 127.0.0.1
  port: 8080
mcp:
  sse_port: 8081
watch_dirs:
  - path: ~/my-notes
    collection: notes
```

## 技术栈

- **后端**: Python 3.11+, FastAPI, Uvicorn, click, watchfiles
- **数据库**: seekdb (pyseekdb) — HNSW 向量索引 + 全文索引
- **前端**: React 18, Vite, Tailwind CSS
- **MCP**: MCP SDK，支持 stdio + SSE 两种协议
- **配置**: YAML，支持环境变量覆盖

## 开发

```bash
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

Apache 2.0
