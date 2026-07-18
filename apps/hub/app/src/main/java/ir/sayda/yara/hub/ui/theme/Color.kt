package ir.sayda.yara.hub.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * Yara Premium Palette (Sprint X - Visual Polish)
 * Defined in DESIGN_LANGUAGE.md and UI Redesign Spec.
 */

val YaraGreen = Color(0xFF4CAF70)       // Soft green for identity and success
val YaraLightGreen = Color(0xFFE7F6EE)  // For secondary backgrounds and borders
val WarmWhite = Color(0xFFFDFCFB)       // Main background (Calm)
val SurfaceGray = Color(0xFFF6F7F9)     // Very light gray for neutral elements

val SoftBlue = Color(0xFF7DBBFF)        // Subtle blue for info/messages
val SoftOrange = Color(0xFFFFB96B)      // Warm accent (Overdue/Warning)
val SoftRed = Color(0xFFE57373)         // Soft red for critical alerts

// Typography Colors
val TextPrimary = Color(0xFF3D3D3D)     // Calm dark gray for readability
val TextSecondary = Color(0xFF757575)   // For less important information
val TextTertiary = Color(0xFF9E9E9E)    // For very subtle hints

// Functional Aliases
val Success = YaraGreen
val Warning = SoftOrange
val Error = SoftRed
val Info = SoftBlue
