# 发布指南（tv-media-renamer）

本仓库发布流程：**Semantic Release 全自动发版** —— 提交遵循 Conventional Commits，合并到 `main` 后自动计算版本、更新 `core/version.py` 与 `CHANGELOG.md`、打 `v*` 标签，再由三个发布工作流自动构建分发。

## 1. 发布总览

`semantic-release` 工作流（监听 `main` push）根据提交类型自动升版并打标签：

| 提交类型 | 版本增量 | 示例 |
|---|---|---|
| `feat:` | MINOR（1.4.0 → 1.5.0） | `feat: 新增批量导出` |
| `fix:` / `perf:` | PATCH（1.4.0 → 1.4.1） | `fix: 修复路径解析崩溃` |
| 其余（docs/chore/ci/test/refactor…） | 不升版 | `docs: 更新 README` |

打标签后自动触发三个发布工作流：

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

- 版本号：`core/version.py`（桌面/服务端，`__version__` 由 Semantic Release 自动更新）
- 变更记录：`CHANGELOG.md`（Keep a Changelog 格式，由 Semantic Release 按提交自动生成中文分类：新增/改进/废弃/移除/修复/安全）
- 提交信息规范（必须，否则不升版）：
  - 格式：`<type>(<scope>): <描述>`，如 `fix(server): 修复鉴权失效`
  - type 必须为 `feat` / `fix` / `perf` / `docs` / `chore` / `ci` / `test` / `refactor` / `style` / `build` 之一
  - 破坏性变更：`feat!: ...` 或提交正文含 `BREAKING CHANGE:`（将触发 MAJOR 升版）
- 发布前校验：`scripts/check_release.py --release`（CI `python-test` 会校验版本与 Changelog 一致性）

## 4. 发布步骤（全自动，无需手动操作）

```bash
# 只需让 main 分支包含规范提交（feat/fix/perf）
git commit -m "feat: 新功能说明"
git push origin main
# Semantic Release 自动：升版 → 更新 version.py/CHANGELOG → 打标签
# 三个发布工作流自动：桌面版 Release + Docker 镜像 + Android APK
```

- **不升版**：提交用 `docs:`/`chore:` 等前缀，仅触发 CI 不发布
- **立即发布**：想要未发布内容立即出版，合并一个 `fix:`/`feat:` 提交即可
- **手动补发**：如需强制发版，可运行 `semantic-release version --patch`（CI 内），或走 §5 手动重打标签

## 5. 发布失败处理

- **某个工作流失败**：修正代码后推送新提交，或删除标签重打（见下），或直接在 Actions 手动重跑
- **需要重打标签**：

```bash
git tag -d v0.1.0 && git push origin :refs/tags/v0.1.0
git tag v0.1.0 && git push origin v0.1.0
```

- **版本回滚**：旧版本镜像/APK 仍保留在 GHCR 与 Release 资产中，按需重新发布旧标签即可
- **镜像覆盖策略**：docker-release 同时推送 `latest` 与版本标签；GHCR 设为 public 后他人可直接 `docker pull ghcr.io/1525745393/tv-renamer-server:latest`
