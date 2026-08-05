package ir.sayda.yara.hub.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import ir.sayda.yara.hub.feature.home.HomeRoute
import ir.sayda.yara.hub.feature.reminder.ReminderRoute

object HubRoutes {
    const val HOME = "home"
    const val SETTINGS = "settings"
    const val REMINDER = "reminder"
}

@Composable
fun HubNavHost(
    modifier: Modifier = Modifier,
    navigationCoordinator: HubNavigationCoordinator = hiltViewModel(),
) {
    val navController = rememberNavController()
    val openRequest by navigationCoordinator.openRequests.collectAsState()

    LaunchedEffect(openRequest) {
        val request = openRequest ?: return@LaunchedEffect
        navController.navigate("${HubRoutes.REMINDER}/${request.executionId}")
    }

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
        composable(
            route = "${HubRoutes.REMINDER}/{executionId}",
            arguments = listOf(navArgument("executionId") { type = NavType.StringType }),
        ) { backStackEntry ->
            val executionId = backStackEntry.arguments?.getString("executionId").orEmpty()
            ReminderRoute(
                executionId = executionId,
                onFinished = {
                    navController.popBackStack(HubRoutes.HOME, inclusive = false)
                },
            )
        }
    }
}
