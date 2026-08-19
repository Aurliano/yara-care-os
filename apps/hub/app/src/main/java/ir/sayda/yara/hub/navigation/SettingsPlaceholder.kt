package ir.sayda.yara.hub.navigation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ir.sayda.yara.hub.feature.home.CaregiverLoginCard
import ir.sayda.yara.hub.feature.home.HomeViewModel

@Composable
fun SettingsPlaceholder(
    onBack: () -> Unit,
    viewModel: HomeViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = "تنظیمات",
            style = MaterialTheme.typography.headlineMedium,
        )
        Text(
            text = "تنظیمات دستگاه از طریق اپلیکیشن مراقب انجام می‌شود.",
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.padding(top = 16.dp, bottom = 24.dp),
        )
        CaregiverLoginCard(
            phone = uiState.phone,
            password = uiState.password,
            isSubmitting = uiState.isSubmittingLogin,
            errorMessage = uiState.loginError,
            onPhoneChange = viewModel::onPhoneChange,
            onPasswordChange = viewModel::onPasswordChange,
            onSubmit = viewModel::submitCaregiverLogin,
        )
        Button(
            onClick = onBack,
            modifier = Modifier.padding(top = 24.dp),
        ) {
            Text("بازگشت")
        }
    }
}
