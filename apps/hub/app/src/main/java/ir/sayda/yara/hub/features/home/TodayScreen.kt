package ir.sayda.yara.hub.features.home

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import ir.sayda.yara.hub.ui.components.*
import ir.sayda.yara.hub.ui.theme.HubTheme
import ir.sayda.yara.hub.ui.theme.WarmWhite

@Composable
fun TodayScreen(modifier: Modifier = Modifier) {
    // Enforce RTL for Persian-first experience
    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
        Scaffold(
            modifier = modifier.fillMaxSize(),
            containerColor = WarmWhite
        ) { innerPadding ->
            Box(modifier = Modifier.fillMaxSize()) {
                // Organic Background Elements
                TodayBackground(modifier = Modifier.fillMaxSize())

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(innerPadding)
                ) {
                    // Header: Time, Date (Left) | Logo, Slogan (Right)
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
                            bottom = 120.dp // Spacing for bottom wave and settings
                        ),
                        verticalArrangement = Arrangement.spacedBy(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        // Emotional Greeting
                        item {
                            GreetingSection(name = "مریم عزیز")
                            Spacer(modifier = Modifier.height(32.dp))
                        }

                        // Medication Card (High Priority - Green Border)
                        item {
                            MedicationCard(
                                medicationName = "قرص فشار خون",
                                time = "ساعت ۱۱:۰۰",
                                onClick = { /* TODO */ }
                            )
                        }

                        // Voice Message Card
                        item {
                            VoiceMessageCard(
                                from = "سارا",
                                onClick = { /* TODO */ }
                            )
                        }

                        // Family Contact Card
                        item {
                            ContactCard(
                                name = "تماس با سارا",
                                onClick = { /* TODO */ }
                            )
                        }
                    }
                }

                // Settings Button positioned in the bottom organic wave
                Box(
                    modifier = Modifier
                        .align(Alignment.BottomStart)
                        .padding(24.dp)
                ) {
                    SettingsButton(onLongClick = { /* TODO */ })
                }
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
