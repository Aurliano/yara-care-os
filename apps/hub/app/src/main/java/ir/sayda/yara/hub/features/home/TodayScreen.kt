package ir.sayda.yara.hub.features.home

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import ir.sayda.yara.hub.domain.model.Medication
import ir.sayda.yara.hub.domain.repository.MedicationRepository
import ir.sayda.yara.hub.ui.components.*
import ir.sayda.yara.hub.ui.theme.HubTheme
import ir.sayda.yara.hub.ui.theme.WarmWhite

@Composable
fun TodayScreen(
    repository: MedicationRepository,
    onMedicationClick: (Medication) -> Unit,
    onSettingsClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val medications by repository.getMedications().collectAsState(initial = emptyList())

    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
        Scaffold(
            modifier = modifier.fillMaxSize(),
            containerColor = WarmWhite
        ) { innerPadding ->
            Box(modifier = Modifier.fillMaxSize()) {
                TodayBackground(modifier = Modifier.fillMaxSize())

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(innerPadding)
                ) {
                    BrandHeader(
                        time = "10:30",
                        date = "چهارشنبه، ۲۰ خرداد ۱۴۰۴"
                    )

                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(
                            start = 24.dp,
                            end = 24.dp,
                            top = 32.dp,
                            bottom = 120.dp
                        ),
                        verticalArrangement = Arrangement.spacedBy(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        item {
                            GreetingSection(name = "مریم عزیز")
                            Spacer(modifier = Modifier.height(32.dp))
                        }

                        items(medications.filter { it.isEnabled }) { medication ->
                            MedicationCard(
                                medicationName = medication.name,
                                time = medication.dosageTime,
                                isCompleted = medication.isCompleted,
                                onClick = { onMedicationClick(medication) }
                            )
                        }

                        item {
                            VoiceMessageCard(
                                from = "سارا",
                                onClick = { /* TODO */ }
                            )
                        }

                        item {
                            ContactCard(
                                name = "تماس با سارا",
                                onClick = { /* TODO */ }
                            )
                        }
                    }
                }

                Box(
                    modifier = Modifier
                        .align(Alignment.BottomStart)
                        .padding(24.dp)
                ) {
                    SettingsButton(onLongClick = onSettingsClick)
                }
            }
        }
    }
}
