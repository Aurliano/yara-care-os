package ir.sayda.yara.hub.features.medication

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.Medication
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ir.sayda.yara.hub.domain.model.Medication
import ir.sayda.yara.hub.ui.components.TodayBackground
import ir.sayda.yara.hub.ui.theme.YaraGreen
import ir.sayda.yara.hub.ui.theme.YaraLightGreen
import kotlinx.coroutines.delay

@Composable
fun MedicationReminderScreen(
    medication: Medication,
    onTaken: () -> Unit,
    onBack: () -> Unit
) {
    var showSuccess by remember { mutableStateOf(false) }

    LaunchedEffect(showSuccess) {
        if (showSuccess) {
            delay(2000) // Success feedback duration
            onTaken()
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        TodayBackground(modifier = Modifier.fillMaxSize())

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            if (!showSuccess) {
                // Medication Icon
                Box(
                    modifier = Modifier
                        .size(120.dp)
                        .clip(CircleShape)
                        .background(YaraLightGreen),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Rounded.Medication,
                        contentDescription = null,
                        tint = YaraGreen,
                        modifier = Modifier.size(80.dp)
                    )
                }

                Spacer(modifier = Modifier.height(48.dp))

                Text(
                    text = "وقت مصرف دارو",
                    style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.onBackground
                )

                Text(
                    text = medication.name,
                    style = MaterialTheme.typography.displayMedium,
                    color = YaraGreen,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center
                )

                Text(
                    text = medication.dosageTime,
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                Spacer(modifier = Modifier.height(64.dp))

                // Action Button
                Button(
                    onClick = { showSuccess = true },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(100.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = YaraGreen),
                    shape = MaterialTheme.shapes.large
                ) {
                    Text(
                        text = "خوردم",
                        style = MaterialTheme.typography.headlineMedium,
                        color = Color.White,
                        fontWeight = FontWeight.Bold
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                TextButton(
                    onClick = onBack,
                    modifier = Modifier.height(64.dp)
                ) {
                    Text(
                        text = "بعداً مصرف می‌کنم",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            } else {
                // Success Feedback
                Box(
                    modifier = Modifier
                        .size(160.dp)
                        .clip(CircleShape)
                        .background(YaraGreen),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Rounded.Check,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(100.dp)
                    )
                }
                
                Spacer(modifier = Modifier.height(32.dp))
                
                Text(
                    text = "آفرین!",
                    style = MaterialTheme.typography.displayMedium,
                    color = YaraGreen,
                    fontWeight = FontWeight.Bold
                )
                
                Text(
                    text = "داروی شما با موفقیت ثبت شد.",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onBackground,
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}
