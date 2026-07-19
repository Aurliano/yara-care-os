package ir.sayda.yara.hub.features.medication

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import ir.sayda.yara.hub.domain.model.Medication
import ir.sayda.yara.hub.ui.theme.WarmWhite
import ir.sayda.yara.hub.ui.theme.YaraGreen

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MedicationEditScreen(
    medication: Medication?,
    onSave: (name: String, time: String) -> Unit,
    onDelete: (() -> Unit)?,
    onBack: () -> Unit
) {
    var name by remember { mutableStateOf(medication?.name ?: "") }
    var time by remember { mutableStateOf(medication?.dosageTime ?: "") }

    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text(if (medication == null) "افزودن دارو" else "ویرایش دارو") },
                    navigationIcon = {
                        IconButton(onClick = onBack) {
                            Icon(Icons.Rounded.ArrowBack, contentDescription = "بازگشت")
                        }
                    },
                    actions = {
                        if (onDelete != null) {
                            IconButton(onClick = onDelete) {
                                Icon(Icons.Rounded.Delete, contentDescription = "حذف", tint = MaterialTheme.colorScheme.error)
                            }
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.White)
                )
            },
            containerColor = WarmWhite
        ) { innerPadding ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .padding(32.dp),
                verticalArrangement = Arrangement.spacedBy(24.dp)
            ) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("نام دارو") },
                    modifier = Modifier.fillMaxWidth(),
                    textStyle = MaterialTheme.typography.bodyLarge
                )

                OutlinedTextField(
                    value = time,
                    onValueChange = { time = it },
                    label = { Text("زمان مصرف (مثال: ۱۱:۰۰)") },
                    modifier = Modifier.fillMaxWidth(),
                    textStyle = MaterialTheme.typography.bodyLarge
                )

                Spacer(modifier = Modifier.weight(1f))

                Button(
                    onClick = { if (name.isNotBlank() && time.isNotBlank()) onSave(name, time) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(80.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = YaraGreen),
                    shape = MaterialTheme.shapes.large
                ) {
                    Text("ذخیره", style = MaterialTheme.typography.headlineSmall)
                }
            }
        }
    }
}
