package io.github.xgl34222220.ziyu.ui.theme

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.disabled
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.Role
import io.github.xgl34222220.ziyu.ui.design.ZiyuCircularProgressIndicator as CircularProgressIndicator
import io.github.xgl34222220.ziyu.ui.design.ZiyuIcon as Icon
import io.github.xgl34222220.ziyu.ui.design.LocalZiyuContentColor
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import io.github.xgl34222220.ziyu.ui.appearance.UiStyle
import top.yukonga.miuix.kmp.basic.IconButton as MiuixIconButton
import io.github.suqi8.coui.kmp.basic.IconButton as CouiIconButton
import io.github.suqi8.coui.kmp.theme.COUITheme
import top.yukonga.miuix.kmp.theme.MiuixTheme

/**
 * One visual scale for the active App UI. The slot stays fixed while opticalScale
 * compensates only the vector path, so selected/disabled/loading states never jump.
 */
internal object ZiyuIconTokens {
    // Keep the native button surface and its interactive target at the standard 48 dp size.
    val HeaderTouchTarget = 48.dp
    val HeaderContainer = 48.dp
    val HeaderGlyph = 21.dp
    val DockGlyph = 22.dp
    val SectionGlyph = 18.dp
    val ToolGlyph = 20.dp
    val LeadingGlyph = 20.dp
    val StatusGlyph = 22.dp
    val TrailingGlyph = 18.dp
    val ProgressGlyph = 22.dp
    val CompactProgress = 20.dp
}

@Composable
internal fun ZiyuGlyph(
    imageVector: ImageVector,
    contentDescription: String?,
    size: Dp,
    modifier: Modifier = Modifier,
    opticalScale: Float = 1f,
    tint: Color = Color.Unspecified,
) {
    val resolvedTint = when {
        tint != Color.Unspecified -> tint
        LocalZiyuContentColor.current != null -> LocalZiyuContentColor.current!!
        LocalUiStyle.current == UiStyle.MATERIAL -> LocalContentColor.current
        else -> Color.Unspecified
    }
    Box(modifier = modifier.size(size), contentAlignment = Alignment.Center) {
        Icon(
            imageVector = imageVector,
            contentDescription = contentDescription,
            modifier = Modifier.fillMaxSize().scale(opticalScale),
            tint = resolvedTint,
        )
    }
}

@Composable
internal fun ZiyuHeaderAction(
    icon: ImageVector,
    contentDescription: String,
    onClick: () -> Unit,
    containerColor: Color,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    loading: Boolean = false,
    opticalScale: Float = 1f,
    contentColor: Color = Color.Unspecified,
) {
    val style = LocalUiStyle.current
    val nativeContentColor = if (contentColor != Color.Unspecified) contentColor else when (style) {
        UiStyle.MATERIAL -> MaterialTheme.colorScheme.primary
        UiStyle.MIUIX -> MiuixTheme.colorScheme.primary
        UiStyle.COUI -> COUITheme.colorScheme.primary
    }
    val disabledContentColor = when (style) {
        UiStyle.MATERIAL -> MaterialTheme.colorScheme.onSurface.copy(alpha = .38f)
        UiStyle.MIUIX -> MiuixTheme.colorScheme.disabledOnSecondaryVariant
        UiStyle.COUI -> COUITheme.colorScheme.disabledOnSecondaryVariant
    }
    val actionContentColor = if (!enabled && !loading) disabledContentColor else nativeContentColor
    val buttonEnabled = enabled && !loading
    val buttonSemantics = Modifier.semantics(mergeDescendants = true) {
        this.contentDescription = contentDescription
        role = Role.Button
        if (!buttonEnabled) disabled()
    }
    Box(
        modifier = modifier.size(ZiyuIconTokens.HeaderTouchTarget),
        contentAlignment = Alignment.Center,
    ) {
        when (style) {
            UiStyle.MIUIX -> MiuixIconButton(
                onClick = onClick,
                enabled = buttonEnabled,
                modifier = Modifier.size(ZiyuIconTokens.HeaderContainer).then(buttonSemantics),
                backgroundColor = containerColor,
                cornerRadius = 22.dp,
            ) {
                CompositionLocalProvider(LocalZiyuContentColor provides actionContentColor) {
                    HeaderActionContent(icon, loading, opticalScale)
                }
            }
            UiStyle.COUI -> CouiIconButton(
                onClick = onClick,
                enabled = buttonEnabled,
                modifier = Modifier.size(ZiyuIconTokens.HeaderContainer).then(buttonSemantics),
                backgroundColor = containerColor,
                cornerRadius = 22.dp,
            ) {
                CompositionLocalProvider(LocalZiyuContentColor provides actionContentColor) {
                    HeaderActionContent(icon, loading, opticalScale)
                }
            }
            UiStyle.MATERIAL -> IconButton(
                onClick = onClick,
                enabled = buttonEnabled,
                modifier = Modifier.fillMaxSize().then(buttonSemantics),
                colors = IconButtonDefaults.iconButtonColors(
                    containerColor = Color.Transparent,
                    contentColor = nativeContentColor,
                    disabledContainerColor = Color.Transparent,
                    disabledContentColor = disabledContentColor,
                ),
            ) {
                CompositionLocalProvider(LocalZiyuContentColor provides actionContentColor) {
                    HeaderActionContent(icon, loading, opticalScale)
                }
            }
        }
    }
}

@Composable
private fun HeaderActionContent(icon: ImageVector, loading: Boolean, scale: Float) {
    val color = LocalZiyuContentColor.current ?: LocalContentColor.current
    if (loading) {
        CircularProgressIndicator(Modifier.size(ZiyuIconTokens.HeaderGlyph), strokeWidth = 2.dp, color = color)
    } else {
        ZiyuGlyph(
            imageVector = icon,
            contentDescription = null,
            size = ZiyuIconTokens.HeaderGlyph,
            opticalScale = scale,
            tint = Color.Unspecified,
        )
    }
}
