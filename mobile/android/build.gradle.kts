// 根 build 文件（Flutter 3.44.8 官方模板原文）。
// 作用：① 依赖仓库 google/mavenCentral（flutter gradle 插件在
// 项目级注入 download.flutter.io，allprojects 声明与之兼容）；
// ② build 目录指到 mobile/build，flutter 工具按该路径查找 APK；
// ③ 让 flutter 工具识别为 Gradle 工程并正确定位
//    app/src/main/AndroidManifest.xml（缺失会被误判为 v1 embedding）。
allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
