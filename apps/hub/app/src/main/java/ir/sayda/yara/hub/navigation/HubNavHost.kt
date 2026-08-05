package ir.sayda.yara.hub.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import ir.sayda.yara.hub.feature.home.HomeRoute

object HubRoutes {
    const val HOME = "home"
    const val SETTINGS = "settings"
}

@Composable
fun HubNavHost(modifier: Modifier = Modifier) {
    val navController = rememberNavController()
    NavHost(
        navController = navController,
        startDestination = HubRoutes.HOME,
        modifier = modifier,
    ) {
        composable(HubRoutes.HOME) {
            HomeRoute(
                onSettingsLongPress = {
                    navController.navigate(HubRoutes.SETTINGS)
                },
            )
        }
        composable(HubRoutes.SETTINGS) {
            SettingsPlaceholder(onBack = { navController.popBackStack() })
        }
    }
}
