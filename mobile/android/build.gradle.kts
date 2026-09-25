// Flutter 官方模板根 build 文件。
// ① 依赖仓库：google() + mavenCentral()（flutter gradle 插件会在
//    项目级注入 download.flutter.io，allprojects 声明与之兼容；
//    不要改用 settings 的 dependencyResolutionManagement，实测冲突）
// ② buildDir="../build"：flutter 工具按 mobile/build/... 查找 APK，
//    缺失会导致 "Gradle build failed to produce an .apk file"
// ③ 本文件同时让 flutter 工具识别 android 工程为 Gradle 工程并
//    正确定位 app/src/main/AndroidManifest.xml（无此文件会被误判
//    为已删除的 v1 embedding）
allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.buildDir = File("../build")
subprojects {
    project.buildDir = File("${rootProject.buildDir}/${project.name}")
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register("clean", Delete) {
    delete rootProject.buildDir
}
