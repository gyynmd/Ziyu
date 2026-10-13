package io.github.xgl34222220.ziyu.ui.design

import androidx.compose.foundation.Image
import androidx.compose.material3.Icon as MaterialIcon
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.LocalTextStyle
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text as MaterialText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.foundation.text.InlineTextContent
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.TextUnit
import io.github.xgl34222220.ziyu.ui.appearance.UiStyle
import io.github.xgl34222220.ziyu.ui.theme.LocalUiStyle
import io.github.suqi8.coui.kmp.theme.COUITheme
import io.github.suqi8.coui.kmp.basic.Icon as CouiIcon
import io.github.suqi8.coui.kmp.basic.Text as CouiText
import top.yukonga.miuix.kmp.theme.MiuixTheme
import top.yukonga.miuix.kmp.basic.Icon as MiuixIcon
import top.yukonga.miuix.kmp.basic.Text as MiuixText
import androidx.compose.foundation.text.TextAutoSize
import androidx.compose.ui.text.TextLayoutResult

/** Explicit inherited content color for the active design system. Null means use that system's local. */
val LocalZiyuContentColor = staticCompositionLocalOf<Color?> { null }

/** Optional neutral text-style override used to carry typography through native wrapper slots. */
val LocalZiyuTextStyle = staticCompositionLocalOf<TextStyle?> { null }

@Composable
private fun requestedContentColor(color: Color): Color =
    if (color != Color.Unspecified) color else LocalZiyuContentColor.current ?: Color.Unspecified

@Composable
fun ZiyuText(
    text: String,
    modifier: Modifier = Modifier,
    color: Color = Color.Unspecified,
    fontSize: TextUnit = TextUnit.Unspecified,
    fontStyle: FontStyle? = null,
    fontWeight: FontWeight? = null,
    fontFamily: FontFamily? = null,
    letterSpacing: TextUnit = TextUnit.Unspecified,
    textDecoration: TextDecoration? = null,
    textAlign: TextAlign? = null,
    lineHeight: TextUnit = TextUnit.Unspecified,
    overflow: TextOverflow = TextOverflow.Clip,
    softWrap: Boolean = true,
    maxLines: Int = Int.MAX_VALUE,
    minLines: Int = 1,
    onTextLayout: (TextLayoutResult) -> Unit = {},
    style: TextStyle? = null,
    autoSize: TextAutoSize? = null,
) {
    val resolvedColor = requestedContentColor(color)
    when (LocalUiStyle.current) {
        UiStyle.MATERIAL -> MaterialText(
            text = text,
            modifier = modifier,
            color = if (resolvedColor == Color.Unspecified) LocalContentColor.current else resolvedColor,
            fontSize = fontSize,
            fontStyle = fontStyle,
            fontWeight = fontWeight,
            fontFamily = fontFamily,
            letterSpacing = letterSpacing,
            textDecoration = textDecoration,
            textAlign = textAlign,
            lineHeight = lineHeight,
            overflow = overflow,
            softWrap = softWrap,
            maxLines = maxLines,
            minLines = minLines,
            onTextLayout = onTextLayout,
            style = style ?: LocalZiyuTextStyle.current ?: LocalTextStyle.current,
            autoSize = autoSize,
        )
        UiStyle.MIUIX -> MiuixText(
            text = text,
            modifier = modifier,
            color = resolvedColor,
            fontSize = fontSize,
            fontStyle = fontStyle,
            fontWeight = fontWeight,
            fontFamily = fontFamily,
            letterSpacing = letterSpacing,
            textDecoration = textDecoration,
            textAlign = textAlign,
            lineHeight = lineHeight,
            overflow = overflow,
            softWrap = softWrap,
            maxLines = maxLines,
            minLines = minLines,
            onTextLayout = onTextLayout,
            style = style ?: LocalZiyuTextStyle.current ?: MiuixTheme.textStyles.main,
            autoSize = autoSize,
        )
        UiStyle.COUI -> CouiText(
            text = text,
            modifier = modifier,
            color = resolvedColor,
            fontSize = fontSize,
            fontStyle = fontStyle,
            fontWeight = fontWeight,
            fontFamily = fontFamily,
            letterSpacing = letterSpacing,
            textDecoration = textDecoration,
            textAlign = textAlign,
            lineHeight = lineHeight,
            overflow = overflow,
            softWrap = softWrap,
            maxLines = maxLines,
            minLines = minLines,
            onTextLayout = onTextLayout,
            style = style ?: LocalZiyuTextStyle.current ?: COUITheme.textStyles.main,
            autoSize = autoSize,
        )
    }
}

@Composable
fun ZiyuText(
    text: AnnotatedString,
    modifier: Modifier = Modifier,
    color: Color = Color.Unspecified,
    fontSize: TextUnit = TextUnit.Unspecified,
    fontStyle: FontStyle? = null,
    fontWeight: FontWeight? = null,
    fontFamily: FontFamily? = null,
    letterSpacing: TextUnit = TextUnit.Unspecified,
    textDecoration: TextDecoration? = null,
    textAlign: TextAlign? = null,
    lineHeight: TextUnit = TextUnit.Unspecified,
    overflow: TextOverflow = TextOverflow.Clip,
    softWrap: Boolean = true,
    maxLines: Int = Int.MAX_VALUE,
    minLines: Int = 1,
    inlineContent: Map<String, InlineTextContent> = mapOf(),
    onTextLayout: (TextLayoutResult) -> Unit = {},
    style: TextStyle? = null,
    autoSize: TextAutoSize? = null,
) {
    val resolvedColor = requestedContentColor(color)
    when (LocalUiStyle.current) {
        UiStyle.MATERIAL -> MaterialText(
            text = text,
            modifier = modifier,
            color = if (resolvedColor == Color.Unspecified) LocalContentColor.current else resolvedColor,
            fontSize = fontSize,
            fontStyle = fontStyle,
            fontWeight = fontWeight,
            fontFamily = fontFamily,
            letterSpacing = letterSpacing,
            textDecoration = textDecoration,
            textAlign = textAlign,
            lineHeight = lineHeight,
            overflow = overflow,
            softWrap = softWrap,
            maxLines = maxLines,
            minLines = minLines,
            inlineContent = inlineContent,
            onTextLayout = onTextLayout,
            style = style ?: LocalZiyuTextStyle.current ?: LocalTextStyle.current,
            autoSize = autoSize,
        )
        UiStyle.MIUIX -> MiuixText(
            text = text,
            modifier = modifier,
            color = resolvedColor,
            fontSize = fontSize,
            fontStyle = fontStyle,
            fontWeight = fontWeight,
            fontFamily = fontFamily,
            letterSpacing = letterSpacing,
            textDecoration = textDecoration,
            textAlign = textAlign,
            lineHeight = lineHeight,
            overflow = overflow,
            softWrap = softWrap,
            maxLines = maxLines,
            minLines = minLines,
            inlineContent = inlineContent,
            onTextLayout = onTextLayout,
            style = style ?: LocalZiyuTextStyle.current ?: MiuixTheme.textStyles.main,
            autoSize = autoSize,
        )
        UiStyle.COUI -> CouiText(
            text = text,
            modifier = modifier,
            color = resolvedColor,
            fontSize = fontSize,
            fontStyle = fontStyle,
            fontWeight = fontWeight,
            fontFamily = fontFamily,
            letterSpacing = letterSpacing,
            textDecoration = textDecoration,
            textAlign = textAlign,
            lineHeight = lineHeight,
            overflow = overflow,
            softWrap = softWrap,
            maxLines = maxLines,
            minLines = minLines,
            inlineContent = inlineContent,
            onTextLayout = onTextLayout,
            style = style ?: LocalZiyuTextStyle.current ?: COUITheme.textStyles.main,
            autoSize = autoSize,
        )
    }
}

@Composable
fun ZiyuIcon(
    imageVector: ImageVector,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    tint: Color = Color.Unspecified,
) {
    val resolvedTint = requestedContentColor(tint)
    when (LocalUiStyle.current) {
        UiStyle.MATERIAL -> MaterialIcon(
            imageVector = imageVector,
            contentDescription = contentDescription,
            modifier = modifier,
            tint = if (resolvedTint == Color.Unspecified) LocalContentColor.current else resolvedTint,
        )
        UiStyle.MIUIX -> MiuixIcon(imageVector, contentDescription, modifier, resolvedTint)
        UiStyle.COUI -> CouiIcon(imageVector, contentDescription, modifier, resolvedTint)
    }
}

@Composable
fun ZiyuIcon(
    painter: Painter,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    tint: Color = Color.Unspecified,
) {
    val resolvedTint = requestedContentColor(tint)
    when (LocalUiStyle.current) {
        UiStyle.MATERIAL -> MaterialIcon(
            painter = painter,
            contentDescription = contentDescription,
            modifier = modifier,
            tint = if (resolvedTint == Color.Unspecified) LocalContentColor.current else resolvedTint,
        )
        else -> Image(
            painter = painter,
            contentDescription = contentDescription,
            modifier = modifier,
            colorFilter = if (resolvedTint == Color.Unspecified) null else ColorFilter.tint(resolvedTint),
        )
    }
}

@Composable
fun ZiyuIcon(
    bitmap: ImageBitmap,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    tint: Color = Color.Unspecified,
) {
    val resolvedTint = requestedContentColor(tint)
    when (LocalUiStyle.current) {
        UiStyle.MATERIAL -> MaterialIcon(
            bitmap = bitmap,
            contentDescription = contentDescription,
            modifier = modifier,
            tint = if (resolvedTint == Color.Unspecified) LocalContentColor.current else resolvedTint,
        )
        UiStyle.MIUIX -> MiuixIcon(bitmap, contentDescription, modifier, resolvedTint)
        UiStyle.COUI -> CouiIcon(bitmap, contentDescription, modifier, resolvedTint)
    }
}
