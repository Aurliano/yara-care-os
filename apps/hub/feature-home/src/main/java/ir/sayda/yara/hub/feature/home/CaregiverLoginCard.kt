package ir.sayda.yara.hub.feature.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import ir.sayda.yara.hub.ui.theme.Error
import ir.sayda.yara.hub.ui.theme.TextPrimary
import ir.sayda.yara.hub.ui.theme.TextSecondary
import ir.sayda.yara.hub.ui.theme.WarmWhite
import ir.sayda.yara.hub.ui.theme.YaraGreen

@Composable
fun CaregiverLoginCard(
    phone: String,
    password: String,
    isSubmitting: Boolean,
    errorMessage: String?,
    onPhoneChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onSubmit: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        color = WarmWhite,
        shadowElevation = 4.dp,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = "ورود مراقب",
                color = TextPrimary,
            )
            Text(
                text = "با همان شماره و رمزی که در اپ مراقب وارد می‌کنید، دستگاه را به پرونده سالمند وصل کنید.",
                color = TextSecondary,
            )
            OutlinedTextField(
                value = phone,
                onValueChange = onPhoneChange,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 64.dp),
                label = { Text("شماره موبایل") },
                singleLine = true,
                enabled = !isSubmitting,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                shape = RoundedCornerShape(16.dp),
            )
            OutlinedTextField(
                value = password,
                onValueChange = onPasswordChange,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 64.dp),
                label = { Text("رمز عبور") },
                singleLine = true,
                enabled = !isSubmitting,
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                shape = RoundedCornerShape(16.dp),
            )
            if (!errorMessage.isNullOrBlank()) {
                Text(text = errorMessage, color = Error)
            }
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = onSubmit,
                enabled = !isSubmitting,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 64.dp),
                colors = ButtonDefaults.buttonColors(containerColor = YaraGreen),
                shape = RoundedCornerShape(20.dp),
            ) {
                if (isSubmitting) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(28.dp),
                        color = WarmWhite,
                    )
                } else {
                    Text("ورود")
                }
            }
        }
    }
}
