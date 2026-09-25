# 发布指南（tv-media-renamer）

本仓库发布流程：**打 `v*` 标签 → GitHub Actions 自动构建并分发**。

## 1. 发布总览

打标签 `git tag v0.1.0 && git push origin v0.1.0` 后自动触发三个工作流：

| 工作流 | 产物 | 说明 |
|---|---|---|
| `android-release` | `tv-renamer-mobile-<tag>.apk`（release 签名） | 移动端 APK，见 §2 签名配置 |
| `docker-release` | `ghcr.io/1525745393/tv-renamer-server:<tag>`（amd64 + arm64） | NAS 服务镜像，群晖 arm64 可直接拉取 |
| `release` | Linux / Windows 桌面版安装包 | PyInstaller 打包发布 |

各工作流也可在 Actions 页面手动触发（`workflow_dispatch`）。

## 2. Android 签名 Secrets 配置（一次性）

未配置 Secrets 时 APK 自动回退 debug 签名；配置后为正式 release 签名。

### 2.1 生成密钥（JDK 自带 keytool）

```bash
keytool -genkey -v -keystore tv-renamer.jks -keyalg RSA -keysize 2048 -validity 10000 -alias release
```

按提示填写密码与组织信息，**记住 storePassword 和 keyPassword**（建议一致）。

### 2.2 转 base64（上传到 GitHub 用）

Linux / macOS：

```bash
base64 -w0 tv-renamer.jks
```

Windows PowerShell：

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("$PWD\tv-renamer.jks"))
```

### 2.3 配置仓库 Secrets

仓库 → **Settings → Secrets and variables → Actions → New repository secret**：

| Secret 名 | 值 |
|---|---|
| `ANDROID_KEYSTORE` | §2.2 得到的 base64 长串 |
| `ANDROID_KEYSTORE_PWD` | storePassword |
| `ANDROID_KEY_ALIAS` | `release`（与 keytool `-alias` 一致） |
| `ANDROID_KEY_PWD` | keyPassword |

> `tv-renamer.jks` 与 `key.properties` 均已被 `.gitignore` 排除，密钥只存于 GitHub Secrets，**不要提交仓库、不要发到聊天/邮件**。

### 2.4 验证签名

本地校验 release APK：

```bash
jarsigner -verify -verbose -certs tv-renamer-mobile-<tag>.apk
```

## 3. 版本号与 Changelog

- 版本号：`core/version.py`（桌面/服务端）+ `mobile/pubspec.yaml`（移动端，`x.y.z+build`）
- 变更记录：`CHANGELOG.md`（Keep a Changelog 格式），每次发布前补充条目
- CI 的 `python-test` job 会校验版本与 Changelog 一致性（有 `version` 标签时）

## 4. 发布步骤（标准流程）

```bash
# 1. 确认 main 分支 CI 全绿
# 2. 更新 CHANGELOG.md 与版本号
git add -A && git commit -m "chore: prepare release v0.1.0"
# 3. 打标签并推送（触发三个发布工作流）
git tag v0.1.0
git push origin v0.1.0
# 4. Actions 页确认三个工作流全绿，下载产物
```

## 5. 发布失败处理

- **某个工作流失败**：修正代码后，可删除标签重新打（见下），或直接在 Actions 手动重跑
- **需要重打标签**：

```bash
git tag -d v0.1.0 && git push origin :refs/tags/v0.1.0
git tag v0.1.0 && git push origin v0.1.0
```

- **版本回滚**：旧版本镜像/APK 仍保留在 GHCR 与 Release 资产中，按需重新发布旧标签即可
- **镜像覆盖策略**：docker-release 同时推送 `latest` 与版本标签；GHCR 设为 public 后他人可直接 `docker pull ghcr.io/1525745393/tv-renamer-server:latest`
