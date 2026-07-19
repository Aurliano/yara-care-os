package ir.sayda.yara.hub.features.medication

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Edit
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import ir.sayda.yara.hub.domain.model.Medication
import ir.sayda.yara.hub.domain.repository.MedicationRepository
import ir.sayda.yara.hub.ui.theme.WarmWhite
import ir.sayda.yara.hub.ui.theme.YaraGreen
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MedicationManagementScreen(
    repository: MedicationRepository,
    onAddMedication: () -> Unit,
    onEditMedication: (Medication) -> Unit,
    onBack: () -> Unit
) {
    val medications by repository.getMedications().collectAsState(initial = emptyList())
    val scope = rememberCoroutineScope()

    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("مدیریت داروها", style = MaterialTheme.typography.headlineMedium) },
                    navigationIcon = {
                        IconButton(onClick = onBack) {
                            Icon(Icons.Rounded.ArrowBack, contentDescription = "بازگشت")
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = Color.White
                    )
                )
            },
            floatingActionButton = {
                FloatingActionButton(
                    onClick = onAddMedication,
                    containerColor = YaraGreen,
                    contentColor = Color.White,
                    shape = MaterialTheme.shapes.large,
                    modifier = Modifier.size(80.dp)
                ) {
                    Icon(Icons.Rounded.Add, contentDescription = "افزودن دارو", modifier = Modifier.size(40.dp))
                }
            },
            containerColor = WarmWhite
        ) { innerPadding ->
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
                contentPadding = PaddingValues(24.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                items(medications) { medication ->
                    MedicationManageItem(
                        medication = medication,
                        onEdit = { onEditMedication(medication) },
                        onToggle = { enabled ->
                            scope.launch {
                                repository.toggleMedication(medication.id, enabled)
                            }
                        }
                    )
                }
            }
        }
    }
}

@Composable
fun MedicationManageItem(
    medication: Medication,
    onEdit: () -> Unit,
    onToggle: (Boolean) -> Unit
) {
    Surface(
        onClick = onEdit,
        shape = MaterialTheme.shapes.large,
        color = Color.White,
        shadowElevation = 2.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(24.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = medication.name,
                    style = MaterialTheme.typography.titleLarge,
                    color = if (medication.isEnabled) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f),
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = medication.dosageTime,
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            Switch(
                checked = medication.isEnabled,
                onCheckedChange = onToggle,
                colors = SwitchDefaults.colors(
                    checkedThumbColor = YaraGreen,
                    checkedTrackColor = YaraGreen.copy(alpha = 0.5f)
                )
            )
            
            Spacer(modifier = Modifier.width(16.dp))
            
            Icon(
                imageVector = Icons.Rounded.Edit,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
