package io.github.xgl34222220.ziyu.ui.design

import androidx.compose.foundation.clickable
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.disabled
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.ListItem as MaterialListItem
import androidx.compose.material3.ListItemColors
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import io.github.xgl34222220.ziyu.ui.appearance.UiStyle
import io.github.xgl34222220.ziyu.ui.theme.LocalUiStyle
import io.github.suqi8.coui.kmp.basic.BasicComponent as CouiBasicComponent
import io.github.suqi8.coui.kmp.basic.BasicComponentDefaults as CouiBasicComponentDefaults
import io.github.suqi8.coui.kmp.theme.COUITheme
import top.yukonga.miuix.kmp.basic.BasicComponent as MiuixBasicComponent
import top.yukonga.miuix.kmp.basic.BasicComponentDefaults as MiuixBasicComponentDefaults
import top.yukonga.miuix.kmp.theme.MiuixTheme

/** Shared ListItem call shape; non-Material layouts use the active surface, text and spacing tokens. */
@Composable
fun ZiyuListItem(
    headlineContent: @Composable () -> Unit,
    modifier: Modifier = Modifier,
    overlineContent: (@Composable () -> Unit)? = null,
    supportingContent: (@Composable () -> Unit)? = null,
    leadingContent: (@Composable () -> Unit)? = null,
    trailingContent: (@Composable () -> Unit)? = null,
    colors: ListItemColors? = null,
    tonalElevation: Dp = 0.dp,
    shadowElevation: Dp = 0.dp,
    shape: Shape? = null,
    contentPadding: PaddingValues? = null,
    onClick: (() -> Unit)? = null,
    enabled: Boolean = true,
    onClickLabel: String? = null,
) {
    when (LocalUiStyle.current) {
        UiStyle.MATERIAL -> {
            val resolvedColors = colors ?: ListItemDefaults.colors()
            val materialColors = if (enabled) resolvedColors else resolvedColors.copy(
                headlineColor = resolvedColors.disabledHeadlineColor,
                overlineColor = resolvedColors.overlineColor.copy(alpha = .38f),
                supportingTextColor = resolvedColors.supportingTextColor.copy(alpha = .38f),
                leadingIconColor = resolvedColors.disabledLeadingIconColor,
                trailingIconColor = resolvedColors.disabledTrailingIconColor,
            )
            MaterialListItem(
                headlineContent = {
                    CompositionLocalProvider(LocalZiyuContentColor provides materialColors.headlineColor) { headlineContent() }
                },
                modifier = if (onClick == null) modifier else modifier.clickable(
                    enabled = enabled, role = Role.Button,
                    onClickLabel = onClickLabel, onClick = onClick,
                ),
                overlineContent = coloredListSlot(materialColors.overlineColor, overlineContent),
                supportingContent = coloredListSlot(materialColors.supportingTextColor, supportingContent),
                leadingContent = coloredListSlot(materialColors.leadingIconColor, leadingContent),
                trailingContent = coloredListSlot(materialColors.trailingIconColor, trailingContent),
                colors = materialColors,
                tonalElevation = tonalElevation,
                shadowElevation = shadowElevation,
            )
        }
        UiStyle.MIUIX -> NativeListItem(
            style = UiStyle.MIUIX,
            headlineContent = headlineContent,
            modifier = modifier,
            overlineContent = overlineContent,
            supportingContent = supportingContent,
            leadingContent = leadingContent,
            trailingContent = trailingContent,
            colors = colors,
            tonalElevation = tonalElevation,
            shadowElevation = shadowElevation,
            shape = shape,
            contentPadding = contentPadding,
            onClick = onClick,
            enabled = enabled,
            onClickLabel = onClickLabel,
        )
        UiStyle.COUI -> NativeListItem(
            style = UiStyle.COUI,
            headlineContent = headlineContent,
            modifier = modifier,
            overlineContent = overlineContent,
            supportingContent = supportingContent,
            leadingContent = leadingContent,
            trailingContent = trailingContent,
            colors = colors,
            tonalElevation = tonalElevation,
            shadowElevation = shadowElevation,
            shape = shape,
            contentPadding = contentPadding,
            onClick = onClick,
            enabled = enabled,
            onClickLabel = onClickLabel,
        )
    }
}

private fun coloredListSlot(color: Color, slot: (@Composable () -> Unit)?): (@Composable () -> Unit)? =
    slot?.let { content -> { CompositionLocalProvider(LocalZiyuContentColor provides color) { content() } } }

@Composable
private fun NativeListItem(
    style: UiStyle,
    headlineContent: @Composable () -> Unit,
    modifier: Modifier,
    overlineContent: (@Composable () -> Unit)?,
    supportingContent: (@Composable () -> Unit)?,
    leadingContent: (@Composable () -> Unit)?,
    trailingContent: (@Composable () -> Unit)?,
    colors: ListItemColors?,
    tonalElevation: Dp,
    shadowElevation: Dp,
    shape: Shape?,
    contentPadding: PaddingValues?,
    onClick: (() -> Unit)?,
    enabled: Boolean,
    onClickLabel: String?,
) {
    val nativeSurface = when (style) {
        UiStyle.MIUIX -> MiuixTheme.colorScheme.surface
        UiStyle.COUI -> COUITheme.colorScheme.surface
        UiStyle.MATERIAL -> MaterialTheme.colorScheme.surface
    }
    val nativeOnSurface = when (style) {
        UiStyle.MIUIX -> MiuixTheme.colorScheme.onSurface
        UiStyle.COUI -> COUITheme.colorScheme.onSurface
        UiStyle.MATERIAL -> MaterialTheme.colorScheme.onSurface
    }
    val containerColor = colors?.containerColor ?: nativeSurface
    val headlineColor = if (enabled) colors?.headlineColor ?: nativeOnSurface
        else colors?.disabledHeadlineColor ?: nativeOnSurface.copy(alpha = .38f)
    val overlineColor = (colors?.overlineColor ?: when (style) {
        UiStyle.MIUIX -> MiuixTheme.colorScheme.onSurfaceVariantSummary
        UiStyle.COUI -> COUITheme.colorScheme.onSurfaceSecondary
        UiStyle.MATERIAL -> MaterialTheme.colorScheme.onSurfaceVariant
    }).let { if (enabled) it else it.copy(alpha = .38f) }
    val supportingColor = colors?.supportingTextColor?.let { if (enabled) it else it.copy(alpha = .38f) } ?: overlineColor
    val leadingColor = if (enabled) colors?.leadingIconColor ?: headlineColor
        else colors?.disabledLeadingIconColor ?: headlineColor
    val trailingColor = if (enabled) colors?.trailingIconColor ?: headlineColor
        else colors?.disabledTrailingIconColor ?: headlineColor
    // Native BasicComponent omits clickable semantics when disabled. Keep the
    // control role and disabled state on its outer surface in that case.
    val rowModifier = if (!enabled && onClick != null) modifier.semantics(mergeDescendants = true) {
        role = Role.Button
        disabled()
    } else modifier
    ZiyuSurface(
        modifier = rowModifier,
        shape = shape,
        color = containerColor,
        contentColor = headlineColor,
        tonalElevation = tonalElevation,
        shadowElevation = shadowElevation,
    ) {
        val nativeLeadingContent: (@Composable () -> Unit)? = leadingContent?.let { slot ->
            { CompositionLocalProvider(LocalZiyuContentColor provides leadingColor) { slot() } }
        }
        val nativeTrailingContent: (@Composable RowScope.() -> Unit)? =
            trailingContent?.let { slot ->
                { CompositionLocalProvider(LocalZiyuContentColor provides trailingColor) { slot() } }
            }
        val nativeTextSlots: @Composable ColumnScope.() -> Unit = {
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                if (overlineContent != null) {
                    CompositionLocalProvider(LocalZiyuContentColor provides overlineColor) { overlineContent() }
                }
                CompositionLocalProvider(LocalZiyuContentColor provides headlineColor) { headlineContent() }
                if (supportingContent != null) {
                    CompositionLocalProvider(LocalZiyuContentColor provides supportingColor) { supportingContent() }
                }
            }
        }
        when (style) {
            UiStyle.MIUIX -> MiuixBasicComponent(
                modifier = Modifier.fillMaxWidth(),
                startAction = nativeLeadingContent,
                endActions = nativeTrailingContent,
                insideMargin = contentPadding ?: MiuixBasicComponentDefaults.InsideMargin,
                onClick = onClick,
                enabled = enabled,
                onClickLabel = onClickLabel,
                role = if (onClick != null) Role.Button else null,
                content = nativeTextSlots,
            )
            UiStyle.COUI -> CouiBasicComponent(
                modifier = Modifier.fillMaxWidth(),
                startAction = nativeLeadingContent,
                endActions = nativeTrailingContent,
                insideMargin = contentPadding ?: CouiBasicComponentDefaults.InsideMargin,
                onClick = onClick,
                enabled = enabled,
                onClickLabel = onClickLabel,
                role = if (onClick != null) Role.Button else null,
                content = nativeTextSlots,
            )
            UiStyle.MATERIAL -> Unit
        }
    }
}
