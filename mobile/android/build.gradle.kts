// 根构建文件：flutter 工具以 android/build.gradle(.kts) 的存在性
// 判定 Gradle 工程并定位 Manifest；此文件同时统一各模块仓库与构建目录。
allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.buildDir = "../build"
subprojects {
    project.buildDir = "${rootProject.buildDir}/${project.name}"
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register("clean", Delete) {
    delete(rootProject.buildDir)
}
