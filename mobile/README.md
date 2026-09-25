# 移动端（Flutter）

NAS API 服务的手机控制端：浏览目录 → 解析预览 → 一键重命名。

> **验证状态**：本机无 Flutter SDK，此代码为逻辑完整骨架，**尚未在本机编译验证**。
> 请在装有 Flutter SDK 的环境执行以下步骤构建。

## 构建步骤

```bash
cd mobile
flutter pub get
flutter analyze        # 应无 error
flutter run            # 连接真机/模拟器
```

## 页面流程

```
登录页（NAS 地址 + Token，本地保存）
  → 目录页（扫描媒体文件，展示解析建议，勾选）
    → 重命名页（预览建议名 → 确认执行，原文件自动备份）
```

## 目录结构

```
lib/
  main.dart                # 入口
  api/api_client.dart      # ApiClient：封装全部 NAS API（health/analyze/scan/rename）
  models/media_item.dart   # 媒体文件模型
  screens/
    login_screen.dart      # 连接页
    folder_screen.dart     # 目录扫描页
    rename_screen.dart     # 重命名预览/执行页
```

## 与后端联调

1. 先按 `server/README.md` 启动 NAS 服务（本机验证：`python3 server/app.py`）
2. 模拟器访问宿主机：Android 模拟器用 `http://10.0.2.2:8123`，真机用 NAS 局域网 IP
3. 登录页填写地址 + Token（启动时终端会打印自动生成的 Token，或自行设置 `API_TOKEN`）

## 依赖

- `http`：API 请求
- `shared_preferences`：本地保存服务器地址与 Token
- `provider`：预留状态管理（当前页面级 State 已够用，可后续迁移）
