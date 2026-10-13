package io.github.xgl34222220.ziyu.ui.design

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.DropdownMenu as MaterialDropdownMenu
import androidx.compose.material3.DropdownMenuItem as MaterialDropdownMenuItem
import androidx.compose.material3.LocalContentColor
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.DpOffset
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntRect
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.PopupProperties
import io.github.suqi8.coui.kmp.basic.BasicComponent as CouiBasicComponent
import io.github.suqi8.coui.kmp.basic.ListPopupDefaults as CouiListPopupDefaults
import io.github.suqi8.coui.kmp.basic.ListPopupColumn as CouiListPopupColumn
import io.github.suqi8.coui.kmp.basic.PopupPositionProvider as CouiPopupPositionProvider
import io.github.suqi8.coui.kmp.overlay.OverlayListPopup as CouiOverlayListPopup
import io.github.suqi8.coui.kmp.theme.COUITheme
import io.github.suqi8.coui.kmp.theme.LocalContentColor as CouiLocalContentColor
import io.github.xgl34222220.ziyu.ui.appearance.UiStyle
import io.github.xgl34222220.ziyu.ui.theme.LocalUiStyle
import top.yukonga.miuix.kmp.basic.BasicComponent as MiuixBasicComponent
import top.yukonga.miuix.kmp.basic.ListPopupDefaults as MiuixListPopupDefaults
import top.yukonga.miuix.kmp.basic.ListPopupColumn as MiuixListPopupColumn
import top.yukonga.miuix.kmp.basic.PopupPositionProvider as MiuixPopupPositionProvider
import top.yukonga.miuix.kmp.overlay.OverlayListPopup as MiuixOverlayListPopup
import top.yukonga.miuix.kmp.theme.LocalContentColor as MiuixLocalContentColor
import top.yukonga.miuix.kmp.theme.MiuixTheme

@Composable
fun ZiyuDropdownMenu(
    expanded: Boolean,
    onDismissRequest: () -> Unit,
    modifier: Modifier = Modifier,
    offset: DpOffset = DpOffset.Zero,
    properties: PopupProperties = PopupProperties(focusable = true),
    scrollState: androidx.compose.foundation.ScrollState = rememberScrollState(),
    content: @Composable ColumnScope.() -> Unit,
) {
    when (LocalUiStyle.current) {
        UiStyle.MATERIAL -> MaterialDropdownMenu(
            expanded = expanded,
            onDismissRequest = onDismissRequest,
            modifier = modifier,
            offset = offset,
            properties = properties,
            scrollState = scrollState,
            content = content,
        )

        UiStyle.MIUIX -> {
            BackHandler(enabled = expanded && properties.dismissOnBackPress) {
                onDismissRequest()
            }
            MiuixOverlayListPopup(
                show = expanded,
                popupModifier = modifier,
                popupPositionProvider = MiuixOffsetProvider(offset, androidx.compose.ui.platform.LocalDensity.current),
                enableWindowDim = false,
                onDismissRequest = { if (properties.dismissOnClickOutside) onDismissRequest() },
                maxHeight = 320.dp,
            ) {
                MiuixListPopupColumn {
                    CompositionLocalProvider(
                        LocalContentColor provides MiuixTheme.colorScheme.onSurface,
                        LocalZiyuContentColor provides MiuixTheme.colorScheme.onSurface,
                        MiuixLocalContentColor provides MiuixTheme.colorScheme.onSurface,
                    ) {
                        Column(Modifier.defaultMinSize(minWidth = 200.dp)) { content() }
                    }
                }
            }
        }

        UiStyle.COUI -> {
            BackHandler(enabled = expanded && properties.dismissOnBackPress) {
                onDismissRequest()
            }
            CouiOverlayListPopup(
                show = expanded,
                popupModifier = modifier,
                popupPositionProvider = CouiOffsetProvider(offset, androidx.compose.ui.platform.LocalDensity.current),
                enableWindowDim = false,
                onDismissRequest = { if (properties.dismissOnClickOutside) onDismissRequest() },
                maxHeight = 320.dp,
            ) {
                CouiListPopupColumn {
                    CompositionLocalProvider(
                        LocalContentColor provides COUITheme.colorScheme.onSurface,
                        LocalZiyuContentColor provides COUITheme.colorScheme.onSurface,
                        CouiLocalContentColor provides COUITheme.colorScheme.onSurface,
                    ) {
                        Column(Modifier.defaultMinSize(minWidth = 200.dp)) { content() }
                    }
                }
            }
        }
    }
}

@Composable
fun ZiyuDropdownMenuItem(
    text: @Composable () -> Unit,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    leadingIcon: (@Composable () -> Unit)? = null,
    trailingIcon: (@Composable () -> Unit)? = null,
    enabled: Boolean = true,
) {
    when (LocalUiStyle.current) {
        UiStyle.MATERIAL -> MaterialDropdownMenuItem(
            text = text,
            onClick = onClick,
            modifier = modifier,
            leadingIcon = leadingIcon,
            trailingIcon = trailingIcon,
            enabled = enabled,
        )

        UiStyle.MIUIX -> MiuixDropdownMenuItem(
            text = text,
            onClick = onClick,
            modifier = modifier,
            leadingIcon = leadingIcon,
            trailingIcon = trailingIcon,
            enabled = enabled,
        )

        UiStyle.COUI -> CouiDropdownMenuItem(
            text = text,
            onClick = onClick,
            modifier = modifier,
            leadingIcon = leadingIcon,
            trailingIcon = trailingIcon,
            enabled = enabled,
        )
    }
}

@Composable
private fun MiuixDropdownMenuItem(
    text: @Composable () -> Unit,
    onClick: () -> Unit,
    modifier: Modifier,
    leadingIcon: (@Composable () -> Unit)?,
    trailingIcon: (@Composable () -> Unit)?,
    enabled: Boolean,
) {
    CompositionLocalProvider(
        LocalContentColor provides if (enabled) MiuixTheme.colorScheme.onSurface else MiuixTheme.colorScheme.disabledOnSecondaryVariant,
        LocalZiyuContentColor provides if (enabled) MiuixTheme.colorScheme.onSurface else MiuixTheme.colorScheme.disabledOnSecondaryVariant,
        MiuixLocalContentColor provides if (enabled) MiuixTheme.colorScheme.onSurface else MiuixTheme.colorScheme.disabledOnSecondaryVariant,
    ) {
        MiuixBasicComponent(
            modifier = modifier.fillMaxWidth(),
            insideMargin = PaddingValues(0.dp),
            onClick = onClick,
            role = Role.Button,
            enabled = enabled,
        ) {
            NativeMenuRowContent(text, leadingIcon, trailingIcon)
        }
    }
}

@Composable
private fun CouiDropdownMenuItem(
    text: @Composable () -> Unit,
    onClick: () -> Unit,
    modifier: Modifier,
    leadingIcon: (@Composable () -> Unit)?,
    trailingIcon: (@Composable () -> Unit)?,
    enabled: Boolean,
) {
    CompositionLocalProvider(
        LocalContentColor provides if (enabled) COUITheme.colorScheme.onSurface else COUITheme.colorScheme.disabledOnSecondaryVariant,
        LocalZiyuContentColor provides if (enabled) COUITheme.colorScheme.onSurface else COUITheme.colorScheme.disabledOnSecondaryVariant,
        CouiLocalContentColor provides if (enabled) COUITheme.colorScheme.onSurface else COUITheme.colorScheme.disabledOnSecondaryVariant,
    ) {
        CouiBasicComponent(
            modifier = modifier.fillMaxWidth(),
            insideMargin = PaddingValues(0.dp),
            onClick = onClick,
            role = Role.Button,
            enabled = enabled,
        ) {
            NativeMenuRowContent(text, leadingIcon, trailingIcon)
        }
    }
}

@Composable
private fun NativeMenuRowContent(
    text: @Composable () -> Unit,
    leadingIcon: (@Composable () -> Unit)?,
    trailingIcon: (@Composable () -> Unit)?,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .defaultMinSize(minHeight = 48.dp)
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (leadingIcon != null) Box { leadingIcon() }
        Box(Modifier.weight(1f)) { text() }
        if (trailingIcon != null) {
            Spacer(Modifier.width(4.dp))
            Box { trailingIcon() }
        }
    }
}

private fun MiuixOffsetProvider(offset: DpOffset, density: Density): MiuixPopupPositionProvider {
    val delegate = MiuixListPopupDefaults.dropdownPositionProvider()
    return object : MiuixPopupPositionProvider {
        override fun calculatePosition(
            anchorBounds: IntRect,
            windowBounds: IntRect,
            layoutDirection: LayoutDirection,
            popupContentSize: IntSize,
            popupMargin: IntRect,
            alignment: MiuixPopupPositionProvider.Align,
        ): IntOffset = delegate.calculatePosition(
            anchorBounds,
            windowBounds,
            layoutDirection,
            popupContentSize,
            popupMargin,
            alignment,
        ) + with(density) { IntOffset(offset.x.roundToPx(), offset.y.roundToPx()) }

        override fun getMargins() = delegate.getMargins()
    }
}

private fun CouiOffsetProvider(offset: DpOffset, density: Density): CouiPopupPositionProvider {
    val delegate = CouiListPopupDefaults.dropdownPositionProvider()
    return object : CouiPopupPositionProvider {
        override fun calculatePosition(
            anchorBounds: IntRect,
            windowBounds: IntRect,
            layoutDirection: LayoutDirection,
            popupContentSize: IntSize,
            popupMargin: IntRect,
            alignment: CouiPopupPositionProvider.Align,
        ): IntOffset = delegate.calculatePosition(
            anchorBounds,
            windowBounds,
            layoutDirection,
            popupContentSize,
            popupMargin,
            alignment,
        ) + with(density) { IntOffset(offset.x.roundToPx(), offset.y.roundToPx()) }

        override fun getMargins() = delegate.getMargins()
    }
}
