package ir.sayda.yara.hub.features.home

import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import ir.sayda.yara.hub.ui.theme.HubTheme

@Composable
fun HomeScreen(modifier: Modifier = Modifier) {
    Greeting(
        name = "Android",
        modifier = modifier
    )
}

@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}

@Preview(showBackground = true)
@Composable
fun GreetingPreview() {
    HubTheme {
        HomeScreen()
    }
}
