package io.github.xgl34222220.ziyu.ui.theme

import android.os.Build
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.shape.CornerBasedShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.compositeOver
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.unit.dp
import io.github.xgl34222220.ziyu.ui.appearance.AppearanceSettings
import io.github.xgl34222220.ziyu.ui.design.ZiyuSurface
import io.github.xgl34222220.ziyu.ui.design.LocalZiyuContentColor
import io.github.xgl34222220.ziyu.ui.navigation.kernelsu.liquid.lens
import io.github.xgl34222220.ziyu.ui.navigation.kernelsu.liquid.vibrancy
import top.yukonga.miuix.kmp.blur.Backdrop
import top.yukonga.miuix.kmp.blur.blur
import top.yukonga.miuix.kmp.blur.drawBackdrop
import top.yukonga.miuix.kmp.blur.isRuntimeShaderSupported

/** Shared backdrop rendering; navigation content remains native to its own theme. */
@Composable
internal fun ZiyuGlassDockSurface(
    appearance: AppearanceSettings,
    backdrop: Backdrop,
    shape: CornerBasedShape,
    color: Color,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    val palette = LocalZiyuPaletteTokens.current
    val dark = palette.pageBackground.luminance() < .5f
    val surfaceColor = color.compositeOver(palette.pageBackground)
    val renderGlass = appearance.glassEnabled && Build.VERSION.SDK_INT >= 33 && isRuntimeShaderSupported()
    val surfaceTintAlpha = when {
        appearance.blurEnabled -> if (dark) .38f else .50f
        dark -> .82f
        else -> .86f
    }
    if (renderGlass) {
        val borderColor = lerp(surfaceColor, palette.textPrimary, if (dark) .20f else .14f)
        Box(
            modifier = modifier
                .shadow(LocalZiyuThemeTokens.current.layout.cardElevation, shape, clip = false)
                // drawBackdrop's surface callback paints a rectangle. Clip the complete
                // glass layer so it cannot leave a second rectangular fill inside the dock.
                .clip(shape)
                .drawBackdrop(
                    backdrop = backdrop,
                    shape = { shape },
                    effects = {
                        vibrancy()
                        if (appearance.blurEnabled) {
                            blur(ZiyuGlassTokens.BlurRadius.toPx(), ZiyuGlassTokens.BlurRadius.toPx())
                        }
                        lens(
                            refractionHeight = ZiyuGlassTokens.RefractionHeightDp.dp.toPx(),
                            refractionAmount = ZiyuGlassTokens.RefractionAmountDp.dp.toPx(),
                            chromaticAberration = ZiyuGlassTokens.ChromaticAberration,
                        )
                    },
                    onDrawSurface = { drawRect(surfaceColor.copy(alpha = surfaceTintAlpha)) },
                )
                .border(.75.dp, borderColor, shape),
            contentAlignment = androidx.compose.ui.Alignment.Center,
        ) {
            androidx.compose.runtime.CompositionLocalProvider(
                LocalZiyuContentColor provides palette.textPrimary,
                androidx.compose.material3.LocalContentColor provides palette.textPrimary,
            ) {
                content()
            }
        }
    } else {
        ZiyuSurface(
            modifier = modifier,
            shape = shape,
            color = surfaceColor,
            contentColor = palette.textPrimary,
            border = BorderStroke(.75.dp, lerp(surfaceColor, palette.textPrimary, if (dark) .20f else .14f)),
            shadowElevation = LocalZiyuThemeTokens.current.layout.cardElevation,
            content = content,
        )
    }
}
