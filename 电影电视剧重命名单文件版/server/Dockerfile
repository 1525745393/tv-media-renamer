# 影视文件智能重命名工具 - NAS API 服务镜像
# 构建：docker build -f server/Dockerfile -t tv-renamer-api .
# 运行：docker run -d -p 8123:8123 \
#         -e API_TOKEN=<你的token> \
#         -e ALLOWED_ROOT=/media \
#         -v /volume1/media:/media:rw \
#         --name tv-renamer-api tv-renamer-api
FROM python:3.12-slim

WORKDIR /app

# 后端依赖
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# 应用代码（解析引擎 + API 服务）
COPY core /app/core
COPY modules /app/modules
COPY server /app/server
COPY main /app/main

EXPOSE 8123

ENV PYTHONPATH=/app
ENV PORT=8123

CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8123"]
