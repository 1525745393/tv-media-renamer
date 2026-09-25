# NAS API 服务（移动端后端）

把桌面版解析引擎包装为轻量 HTTP 服务，供手机端（Flutter App）远程控制：
**浏览 NAS 媒体目录 → 解析预览 → 一键重命名**（自动备份，可回滚）。

## 快速启动（本机验证）

```bash
cd 电影电视剧重命名单文件版
pip install -r server/requirements.txt
export API_TOKEN=你的随机token        # 必填，所有请求鉴权
export ALLOWED_ROOT=/home/user/media   # 允许操作的根目录（防越权）
python3 server/app.py                  # 默认 8123 端口
```

启动后访问 `http://127.0.0.1:8123/docs` 查看交互式 API 文档。

## 群晖 NAS 部署（推荐：Docker Compose 一键）

```bash
cd 电影电视剧重命名单文件版
cp server/.env.example .env   # 编辑填写 API_TOKEN（生成：python3 -c "import secrets; print(secrets.token_urlsafe(32))"）
./deploy.sh                   # 或手动：docker compose up -d --build
```

`.env` 配置项：`API_TOKEN`（必填）、`MEDIA_DIR`（媒体目录，默认 `/volume1/media`）、`PORT`、`ALLOWED_ROOT`。服务含健康检查与开机自启（restart: unless-stopped）。

### 备选：直接 Docker 构建运行

```bash
cd 电影电视剧重命名单文件版
docker build -f server/Dockerfile -t tv-renamer-api .
docker run -d -p 8123:8123 \
  -e API_TOKEN=你的随机token \
  -e ALLOWED_ROOT=/media \
  -v /volume1/media:/media:rw \
  --restart unless-stopped \
  --name tv-renamer-api tv-renamer-api
```

手机与 NAS 需同一局域网；外网访问建议经反向代理 + HTTPS。

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查（返回应用名与版本） |
| GET | `/api/analyze?filename=&folder=` | 解析单个文件名 |
| POST | `/api/analyze-batch` | 批量解析（`{filenames: [...]}`，≤500） |
| GET | `/api/scan?path=&recursive=` | 扫描目录媒体文件（含解析建议） |
| POST | `/api/rename-preview` | 生成重命名预览（不执行） |
| POST | `/api/rename` | 执行重命名（`dry_run` 默认 `true`；`false` 时先自动备份到 `.tv_renamer_backup/`） |

**鉴权**：所有请求携带 `Authorization: Bearer <API_TOKEN>`。

## 网页控制台（PWA，无需安装 App）

服务启动后直接访问 **`http://<NAS-IP>:8123/`** 即打开手机/电脑均可用的网页控制台：

- **登录**：输入 API Token（同源访问可留空服务器地址）
- **扫描**：输入媒体目录，列出文件与解析建议（类型徽章 + 需改名高亮）
- **重命名**：勾选/全选/仅需改名筛选 → 预览 → 确认执行（原文件自动备份）
- **PWA**：支持添加到主屏幕（manifest + Service Worker），可离线打开外壳

对应文件：`server/static/index.html`（单页应用）、`manifest.webmanifest`、`sw.js`、`icons/`。
手机浏览器打开后选择"添加到主屏幕"即可像原生 App 一样使用，无需 Flutter 编译环境。

**安全设计**：
- 路径校验：任何目录操作都被限制在 `ALLOWED_ROOT` 内（防目录穿越）
- 重命名默认预览模式（dry_run），实际执行才落盘
- 执行前自动备份原文件到 `.tv_renamer_backup/`，可手动恢复
- 单次批量上限 500 文件，防滥用

## 返回示例（/api/analyze）

```json
{
  "type": "tv", "title": "Game of Thrones",
  "season": 8, "episode": 3, "year": null,
  "confidence": 0.95,
  "suggested_name": "Game of Thrones.S08.E03.mkv"
}
```

## 移动端对接

配套 Flutter 客户端代码见仓库 `mobile/` 目录（`ApiClient` 封装全部接口）。
