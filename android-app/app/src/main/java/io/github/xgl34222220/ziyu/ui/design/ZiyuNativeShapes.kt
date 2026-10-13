package io.github.xgl34222220.ziyu.ui.design

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.border
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Outline
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import io.github.xgl34222220.ziyu.ui.appearance.UiStyle
import io.github.suqi8.coui.kmp.squircle.SquircleDefaults as CouiSquircleDefaults
import io.github.suqi8.coui.kmp.squircle.addSquircleRect as addCouiSquircleRect
import io.github.suqi8.coui.kmp.squircle.isSquircleEnabled as isCouiSquircleEnabled
import io.github.suqi8.coui.kmp.squircle.squircleBorder as couiSquircleBorder
import top.yukonga.miuix.kmp.squircle.SquircleDefaults as MiuixSquircleDefaults
import top.yukonga.miuix.kmp.squircle.addSquircleRect as addMiuixSquircleRect
import top.yukonga.miuix.kmp.squircle.isSquircleEnabled as isMiuixSquircleEnabled
import top.yukonga.miuix.kmp.squircle.squircleBorder as miuixSquircleBorder

/** Returns a Shape with the same path and fallback behavior as the active native squircle APIs. */
@Composable
internal fun rememberNativeSquircleShape(style: UiStyle, cornerRadius: Dp): Shape {
    val enabled = when (style) {
        UiStyle.MIUIX -> isMiuixSquircleEnabled()
        UiStyle.COUI -> isCouiSquircleEnabled()
        UiStyle.MATERIAL -> false
    }
    val extension = when (style) {
        UiStyle.MIUIX -> MiuixSquircleDefaults.Extension
        UiStyle.COUI -> CouiSquircleDefaults.Extension
        UiStyle.MATERIAL -> 1f
    }
    return remember(style, cornerRadius, enabled, extension) {
        NativeSquircleShape(style, cornerRadius, extension, enabled)
    }
}

/** Draws a caller border along the exact squircle path used by the native component. */
@Composable
internal fun Modifier.nativeSquircleBorder(
    border: BorderStroke,
    style: UiStyle,
    cornerRadius: Dp,
): Modifier {
    val solidColor = (border.brush as? SolidColor)?.value
    if (solidColor != null) {
        return when (style) {
            UiStyle.MIUIX -> this.miuixSquircleBorder(border.width, solidColor, cornerRadius)
            UiStyle.COUI -> this.couiSquircleBorder(border.width, solidColor, cornerRadius)
            UiStyle.MATERIAL -> this.border(border, rememberNativeSquircleShape(style, cornerRadius))
        }
    }
    return this.border(border, rememberNativeSquircleShape(style, cornerRadius))
}

private data class NativeSquircleShape(
    private val style: UiStyle,
    private val cornerRadius: Dp,
    private val extension: Float,
    private val squircleEnabled: Boolean,
) : Shape {
    override fun createOutline(size: Size, layoutDirection: LayoutDirection, density: Density): Outline {
        val path = Path()
        val radiusPx = with(density) { cornerRadius.toPx() }
        when (style) {
            UiStyle.MIUIX -> path.addMiuixSquircleRect(
                width = size.width,
                height = size.height,
                cornerRadius = radiusPx,
                extension = extension,
                squircleEnabled = squircleEnabled,
            )
            UiStyle.COUI -> path.addCouiSquircleRect(
                width = size.width,
                height = size.height,
                cornerRadius = radiusPx,
                extension = extension,
                squircleEnabled = squircleEnabled,
            )
            UiStyle.MATERIAL -> path.addRoundRect(
                androidx.compose.ui.geometry.RoundRect(
                    left = 0f,
                    top = 0f,
                    right = size.width,
                    bottom = size.height,
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(radiusPx),
                ),
            )
        }
        return Outline.Generic(path)
    }
}
