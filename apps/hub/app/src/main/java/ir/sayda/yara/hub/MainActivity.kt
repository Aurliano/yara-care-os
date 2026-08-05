package ir.sayda.yara.hub

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import dagger.hilt.android.AndroidEntryPoint
import ir.sayda.yara.hub.navigation.HubNavHost
import ir.sayda.yara.hub.ui.theme.HubTheme

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            HubTheme {
                HubNavHost(modifier = Modifier.fillMaxSize())
            }
        }
    }
}
