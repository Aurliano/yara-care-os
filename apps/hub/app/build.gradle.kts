import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.hilt)
    alias(libs.plugins.ksp)
}

val localProperties = Properties()
val localPropertiesFile = rootProject.file("local.properties")
if (localPropertiesFile.exists()) {
    localPropertiesFile.inputStream().use { localProperties.load(it) }
}
val hubBackendUrl = localProperties.getProperty("hub.backend.url")?.trim()?.let { url ->
    if (url.endsWith("/")) url else "$url/"
} ?: "http://10.0.2.2:8000/api/v1/"
val hubProvisionPhone = localProperties.getProperty("hub.provision.phone")?.trim()
    ?: "+989136666666"
val hubProvisionPassword = localProperties.getProperty("hub.provision.password")?.trim()
    ?: "securepass123"

android {
    namespace = "ir.sayda.yara.hub"
    compileSdk = 36

    defaultConfig {
        applicationId = "ir.sayda.yara.hub"
        minSdk = 24
        targetSdk = 36
        versionCode = 2
        versionName = "2.0.0-foundation"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "HUB_DEVICE_MODEL_CODE", "\"YARA-HUB-TABLET\"")
        buildConfigField("String", "HUB_BACKEND_URL", "\"$hubBackendUrl\"")
        buildConfigField("String", "PROVISION_PHONE", "\"$hubProvisionPhone\"")
        buildConfigField("String", "PROVISION_PASSWORD", "\"$hubProvisionPassword\"")
    }

    buildTypes {
        debug {
            buildConfigField("boolean", "DEBUG", "true")
        }
        release {
            isMinifyEnabled = false
            buildConfigField("boolean", "DEBUG", "false")
            buildConfigField("String", "PROVISION_PHONE", "\"\"")
            buildConfigField("String", "PROVISION_PASSWORD", "\"\"")
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    implementation(project(":core"))
    implementation(project(":database"))
    implementation(project(":network"))
    implementation(project(":data"))
    implementation(project(":sync"))
    implementation(project(":runtime"))
    implementation(project(":ui"))
    implementation(project(":feature-home"))
    implementation(project(":feature-reminder"))
    implementation(project(":feature-communication"))

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.work.runtime.ktx)
    implementation(libs.androidx.hilt.work)
    ksp(libs.hilt.compiler)

    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3)
    implementation(libs.hilt.android)
    implementation(libs.hilt.navigation.compose)

    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(platform(libs.androidx.compose.bom))
}
