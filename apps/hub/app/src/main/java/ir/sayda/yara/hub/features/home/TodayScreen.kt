package ir.sayda.yara.hub.features.home

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import ir.sayda.yara.hub.ui.components.*
import ir.sayda.yara.hub.ui.theme.HubTheme

@Composable
fun TodayScreen(modifier: Modifier = Modifier) {
    Scaffold(
        modifier = modifier.fillMaxSize(),
        bottomBar = {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                horizontalArrangement = Arrangement.End
            ) {
                SettingsButton(onLongClick = { /* TODO: Open Settings */ })
            }
        }
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding),
            contentPadding = PaddingValues(32.dp), // XL Spacing
            verticalArrangement = Arrangement.spacedBy(32.dp) // XL Spacing
        ) {
            item {
                ClockCard(time = "10:30")
            }
            item {
                GreetingCard(greeting = "Good morning, Mary")
            }
            item {
                MedicationCard(
                    medicationName = "Blood Pressure Pill",
                    time = "at 11:00 AM",
                    onClick = { /* TODO */ }
                )
            }
            item {
                VoiceMessageCard(
                    from = "Daughter Sarah",
                    onClick = { /* TODO */ }
                )
            }
            item {
                ContactCard(
                    name = "Call Sarah",
                    onClick = { /* TODO */ }
                )
            }
        }
    }
}

@Preview(showBackground = true, widthDp = 800, heightDp = 1280)
@Composable
fun TodayScreenPreview() {
    HubTheme {
        TodayScreen()
    }
}
