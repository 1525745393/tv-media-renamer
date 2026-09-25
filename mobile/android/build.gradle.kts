// 本文件用于让 flutter 工具识别 android 工程为 Gradle 工程并
// 正确定位 app/src/main/AndroidManifest.xml（无此文件会被误判为
// 已删除的 v1 embedding）。
// 依赖仓库按 flutter 官方模板在此声明（allprojects，兼容 flutter
// gradle 插件注入的 download.flutter.io 仓库；不要改用 settings 的
// dependencyResolutionManagement，实测会与插件仓库注入冲突）。
allprojects {
    repositories {
        google()
        mavenCentral()
    }
}
