# 移动端（Flutter）

NAS API 服务的手机控制端：浏览目录 → 解析预览 → 一键重命名。

> **验证状态**：本机无 Flutter SDK，代码与工程文件为完整骨架，**尚未在本机编译验证**。
> Android / iOS 工程已按 Flutter stable 官方模板生成（Gradle 9.3.1 / AGP 9.1.0 / Kotlin 2.4.0），
> 请在装有 Flutter SDK 的环境执行下方步骤构建。

## 环境要求

- Flutter SDK ≥ 3.0（Dart 3）
- Android：JDK 17、Android SDK（含 Gradle 9.3.1 自动下载）
- iOS：macOS + Xcode（仅打包 iOS 时需要）

## 构建步骤

```bash
cd mobile
flutter pub get
flutter analyze        # 应无 error
flutter run            # 真机/模拟器运行
```

### Android 打包（APK / AAB）

```bash
flutter build apk --release          # 生成 build/app/outputs/flutter-apk/app-release.apk
flutter build appbundle --release    # 上架 Google Play 用 AAB
```

**发布签名**：`build.gradle.kts` 已内置自动检测——检测到 `android/key.properties` 即用正式签名，否则回退 debug 签名（自用分发可直接打包）。首次上架前：

```bash
# 1. 生成签名（只需一次）
keytool -genkey -v -keystore android/key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias release

# 2. 创建 android/key.properties（勿提交，已 gitignore）
#    storeFile=key.jks
#    storePassword=<密码>
#    keyAlias=release
#    keyPassword=<密码>

# 3. 重新打包即使用正式签名
flutter build appbundle --release
```

### iOS 打包

```bash
flutter build ios --release    # 需 macOS + Xcode
```

- 开发团队：`ios/Runner.xcodeproj` 中 `Signing & Capabilities` 选择你的 Team，
  并把 `DEVELOPMENT_TEAM` 写入工程的 Build Settings
- 包名（Bundle ID）：`com.example.tvMediaRenamerMobile`（可在 Xcode 中修改）

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
android/                   # Android 工程（Kotlin DSL + AGP 9.1.0，已含图标与启动图）
ios/                       # iOS 工程（Runner，已含 AppIcon 全套图标与启动屏）
```

## App 图标

设计：深蓝灰渐变底 + 白色电影胶片 + 橙色重命名箭头（无文字，小尺寸清晰）。
已按官方规范生成：

- Android：`android/app/src/main/res/mipmap-*/ic_launcher.png`（48~192px 五档）
- iOS：`ios/Runner/Assets.xcassets/AppIcon.appiconset/`（20~1024px 全套）

更换图标：替换主图后重新缩放，或直接覆盖上述 PNG。

## 与后端联调

1. 先按 `server/README.md` 启动 NAS 服务（本机验证：`python3 server/app.py`）
2. 模拟器访问宿主机：Android 模拟器用 `http://10.0.2.2:8123`，真机用 NAS 局域网 IP
3. 登录页填写地址 + Token（启动时终端会打印自动生成的 Token，或自行设置 `API_TOKEN`）

## 依赖

- `http`：API 请求
- `shared_preferences`：本地保存服务器地址与 Token
- `provider`：预留状态管理（当前页面级 State 已够用，可后续迁移）
