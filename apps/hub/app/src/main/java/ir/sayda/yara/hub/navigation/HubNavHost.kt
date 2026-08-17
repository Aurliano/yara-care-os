package ir.sayda.yara.hub.navigation

import android.net.Uri
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import ir.sayda.yara.hub.BuildConfig
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Alignment
import ir.sayda.yara.hub.communication.CallMediaSurface
import ir.sayda.yara.hub.feature.communication.CallRoute
import ir.sayda.yara.hub.feature.communication.CallViewArgs
import ir.sayda.yara.hub.feature.home.HomeRoute
import ir.sayda.yara.hub.feature.reminder.ReminderRoute

object HubRoutes {
    const val HOME = "home"
    const val SETTINGS = "settings"
    const val DEVELOPER = "developer"
    const val REMINDER = "reminder"
    const val CALL = "call"
    const val CALL_ROUTE =
        "call?contactId={contactId}&elderId={elderId}&channel={channel}&contactName={contactName}"

    fun outgoingCall(
        contactId: String,
        elderId: String,
        channel: String,
        contactName: String,
    ): String {
        return "call?contactId=${Uri.encode(contactId)}" +
            "&elderId=${Uri.encode(elderId)}" +
            "&channel=${Uri.encode(channel)}" +
            "&contactName=${Uri.encode(contactName)}"
    }
}

@Composable
fun HubNavHost(
    modifier: Modifier = Modifier,
    navigationCoordinator: HubNavigationCoordinator = hiltViewModel(),
) {
    val navController = rememberNavController()
    val openRequest by navigationCoordinator.openRequests.collectAsState()
    val activeCall by navigationCoordinator.activeCall.collectAsState()

    LaunchedEffect(openRequest) {
        val request = openRequest ?: return@LaunchedEffect
        navController.navigate("${HubRoutes.REMINDER}/${request.executionId}")
    }

    LaunchedEffect(activeCall?.sessionId, activeCall?.runtimeState) {
        if (activeCall == null) return@LaunchedEffect
        val current = navController.currentDestination?.route.orEmpty()
        if (current.startsWith(HubRoutes.CALL)) return@LaunchedEffect
        navController.navigate(HubRoutes.outgoingCall("", "", "", "")) {
            launchSingleTop = true
        }
    }

    NavHost(
        navController = navController,
        startDestination = HubRoutes.HOME,
        modifier = modifier,
    ) {
        composable(HubRoutes.HOME) {
            HomeRoute(
                isDebugBuild = BuildConfig.DEBUG,
                onOpenDeveloperSettings = {
                    navController.navigate(HubRoutes.DEVELOPER)
                },
                onSettingsLongPress = {
                    navController.navigate(HubRoutes.SETTINGS)
                },
                onCallContact = { contactId, elderId, channel, displayName ->
                    navController.navigate(
                        HubRoutes.outgoingCall(contactId, elderId, channel, displayName),
                    )
                },
            )
        }
        composable(HubRoutes.SETTINGS) {
            SettingsPlaceholder(onBack = { navController.popBackStack() })
        }
        composable(HubRoutes.DEVELOPER) {
            if (BuildConfig.DEBUG) {
                DeveloperSettingsScreen(onBack = { navController.popBackStack() })
            } else {
                SettingsPlaceholder(onBack = { navController.popBackStack() })
            }
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
        composable(
            route = HubRoutes.CALL_ROUTE,
            arguments = listOf(
                navArgument("contactId") {
                    type = NavType.StringType
                    defaultValue = ""
                },
                navArgument("elderId") {
                    type = NavType.StringType
                    defaultValue = ""
                },
                navArgument("channel") {
                    type = NavType.StringType
                    defaultValue = ""
                },
                navArgument("contactName") {
                    type = NavType.StringType
                    defaultValue = ""
                },
            ),
        ) { backStackEntry ->
            Box(modifier = Modifier.fillMaxSize()) {
                CallRoute(
                    args = CallViewArgs(
                        contactId = backStackEntry.arguments?.getString("contactId").orEmpty(),
                        elderId = backStackEntry.arguments?.getString("elderId").orEmpty(),
                        channel = backStackEntry.arguments?.getString("channel").orEmpty(),
                        contactName = backStackEntry.arguments?.getString("contactName").orEmpty(),
                    ),
                    onReturnHome = {
                        navController.popBackStack(HubRoutes.HOME, inclusive = false)
                    },
                )
                CallMediaSurface(modifier = Modifier.align(Alignment.TopCenter))
            }
        }
    }
}
