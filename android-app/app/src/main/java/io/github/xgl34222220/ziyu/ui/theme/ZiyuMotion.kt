package io.github.xgl34222220.ziyu.ui.theme

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.LinearOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.Shape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.unit.dp
import io.github.suqi8.coui.kmp.theme.COUITheme
import io.github.xgl34222220.ziyu.ui.appearance.UiStyle
import io.github.xgl34222220.ziyu.ui.theme.LocalUiStyle
import top.yukonga.miuix.kmp.theme.MiuixTheme
import kotlinx.coroutines.delay

internal object ZiyuMotionTokens {
    const val Micro = 120
    const val Fast = 180
    const val Normal = 220
    const val Emphasized = 260
    const val LoadingRevealDelay = 160L
}

@Composable
internal fun ZiyuLoadingSkeleton(
    modifier: Modifier = Modifier,
    active: Boolean = true,
    shape: Shape = RoundedCornerShape(12.dp),
    revealDelayMs: Long = ZiyuMotionTokens.LoadingRevealDelay,
) {
    val style = LocalUiStyle.current
    var revealed by remember(active) { mutableStateOf(false) }
    LaunchedEffect(active, revealDelayMs, style) {
        revealed = false
        if (active) {
            delay(revealDelayMs)
            revealed = true
        }
    }

    val motion = when (style) {
        UiStyle.MATERIAL -> SkeletonMotion(durationMs = ZiyuMotionTokens.Fast, alpha = .075f, easing = FastOutSlowInEasing)
        UiStyle.MIUIX -> SkeletonMotion(durationMs = ZiyuMotionTokens.Micro, alpha = .055f, easing = LinearOutSlowInEasing)
        UiStyle.COUI -> SkeletonMotion(durationMs = ZiyuMotionTokens.Normal, alpha = .07f, easing = LinearOutSlowInEasing)
    }
    val revealAlpha by animateFloatAsState(
        targetValue = if (active && revealed) 1f else 0f,
        animationSpec = tween(motion.durationMs, easing = motion.easing),
        label = "ziyuSkeletonAlpha",
    )
    val base = when (style) {
        UiStyle.MATERIAL -> MaterialTheme.colorScheme.onSurface
        UiStyle.MIUIX -> MiuixTheme.colorScheme.onSurface
        UiStyle.COUI -> COUITheme.colorScheme.onSurface
    }.copy(alpha = motion.alpha)
    Box(
        modifier = modifier
            .clip(shape)
            .graphicsLayer { alpha = revealAlpha }
            .background(base),
    )
}

private data class SkeletonMotion(
    val durationMs: Int,
    val alpha: Float,
    val easing: androidx.compose.animation.core.Easing,
)
