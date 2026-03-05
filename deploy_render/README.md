# 部署说明（最短上线版）

你当前代码已保留不动，部署版入口在 `deploy_render/app.py`。

## 是否适合直接放 GitHub

已检查本地 `Transition_matrix`：

- 文件数：`19`
- 总大小：约 `0.93 MB`

结论：体量很小，适合直接随仓库提交并部署。

## 一次性准备

1. 把整个项目推送到 GitHub。
2. 确认仓库中包含：
   - `deploy_render/app.py`
   - `deploy_render/requirements.txt`
   - `deploy_render/Procfile`
   - `Transition_matrix/`

## 本地验证（可选）

在项目根目录执行：

```bash
pip install -r deploy_render/requirements.txt
python deploy_render/app.py
```

打开 `http://127.0.0.1:5000`，确认年份/领域可正常切换并生成表格。

## Render 上线步骤（推荐）

1. 登录 Render，新建 **Web Service**，选择你的 GitHub 仓库。
2. 配置命令：
   - Build Command: `pip install -r deploy_render/requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT deploy_render.app:app`
3. 环境变量（可选）：
   - `DATA_DIR=/opt/render/project/src/Transition_matrix`
   - 不填也可，默认就是仓库根目录 `Transition_matrix`。
4. 点击部署，等待成功后获得公网 URL。

## 给他人访问

把 Render 提供的公网 URL 发给对方即可。  
多人可同时访问并独立选择年份与领域，互不影响。
# 部署说明（Render/Railway）

此目录是部署专用版本，不会改动你当前根目录下的现有代码。

## 目录用途

- `app.py`: 部署入口，复用根目录的 `index.html` 和 `algorithm.py`
- `requirements.txt`: Python 依赖
- `Procfile`: 云平台启动命令（Gunicorn）

## 关键行为

- 页面地址 `/` 可直接访问网站
- API 地址为同源 `/api/...`，不再写死 `127.0.0.1`
- 支持多人同时访问（请求独立）
- 通过环境变量 `DATA_DIR` 指定数据目录

## 本地测试

在仓库根目录执行：

```bash
python deploy_render/app.py
```

默认使用：

- 端口：`5000`
- 数据目录：`./Transition_matrix`

## Render 部署建议

1. 把整个项目推送到 GitHub
2. 在 Render 新建 `Web Service`
3. 选择该仓库
4. 设置：
   - Build Command: `pip install -r deploy_render/requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT deploy_render.app:app`
5. 如需自定义数据目录，设置环境变量：
   - `DATA_DIR=/opt/render/project/src/Transition_matrix`

> 注意：确保线上环境能读取 `Transition_matrix` 数据文件。
# Deploy Version (Render)

This folder contains a deployment-ready backend without changing your current files.

## What this version does

- Keeps your existing `app.py`, `algorithm.py`, and `index.html` untouched.
- Uses `deploy_render/app.py` as the online service entry.
- Reuses root `algorithm.py` but overrides `DATA_DIR` via environment variable.
- Serves root `index.html` and rewrites `API_BASE` from localhost to relative path (`""`) at runtime.

## Deploy on Render

1. Push this repository to GitHub.
2. In Render, create a **Web Service** from this repository.
3. Set:
   - Build Command: `pip install -r deploy_render/requirements.txt`
   - Start Command: `gunicorn deploy_render.app:app`
4. Ensure your data folder exists in repo root as `Transition_matrix`.
5. (Optional) Set env var `DATA_DIR` if you store data elsewhere.

## Local run (deployment version)

```bash
pip install -r deploy_render/requirements.txt
python deploy_render/app.py
```
