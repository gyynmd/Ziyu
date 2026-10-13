package io.github.xgl34222220.ziyu.ui.theme

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.PrimaryTabRow
import androidx.compose.material3.PrimaryScrollableTabRow
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import top.yukonga.miuix.kmp.basic.TabRowDefaults as MiuixTabRowDefaults
import top.yukonga.miuix.kmp.theme.MiuixTheme
import io.github.xgl34222220.ziyu.ui.appearance.UiStyle

/** A tab contract whose indicator and touch feedback remain native to the selected UI system. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun ZiyuSegmentedTabs(
    labels: List<String>,
    selectedIndex: Int,
    onSelected: (Int) -> Unit,
    modifier: Modifier = Modifier,
    height: Dp = Dp.Unspecified,
) {
    if (labels.isEmpty()) return
    val selected = selectedIndex.coerceIn(labels.indices)
    when (LocalUiStyle.current) {
        UiStyle.MATERIAL -> {
            val tabs: @Composable () -> Unit = {
                labels.forEachIndexed { index, label ->
                    Tab(
                        selected = index == selected,
                        onClick = { if (index != selected) onSelected(index) },
                        text = { Text(label, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                        modifier = Modifier,
                    )
                }
            }
            if (labels.size > 4) {
                PrimaryScrollableTabRow(
                    selectedTabIndex = selected,
                    modifier = modifier.fillMaxWidth(),
                    containerColor = Color.Transparent,
                    contentColor = MaterialTheme.colorScheme.onSurface,
                    tabs = tabs,
                )
            } else {
                PrimaryTabRow(
                    selectedTabIndex = selected,
                    modifier = modifier.fillMaxWidth(),
                    containerColor = Color.Transparent,
                    contentColor = MaterialTheme.colorScheme.onSurface,
                    tabs = tabs,
                )
            }
        }
        UiStyle.MIUIX -> top.yukonga.miuix.kmp.basic.TabRow(
            tabs = labels,
            selectedTabIndex = selected,
            onTabSelected = { if (it != selected) onSelected(it) },
            modifier = modifier.fillMaxWidth(),
            colors = MiuixTabRowDefaults.tabRowColors(
                backgroundColor = Color.Transparent,
                contentColor = MiuixTheme.colorScheme.onSurfaceVariantSummary,
                selectedBackgroundColor = MiuixTheme.colorScheme.primaryContainer,
                selectedContentColor = MiuixTheme.colorScheme.onPrimaryContainer,
            ),
            height = if (height.value.isNaN()) MiuixTabRowDefaults.TabRowHeight else height,
        )
        UiStyle.COUI -> io.github.suqi8.coui.kmp.basic.TabRowWithContour(
            tabs = labels,
            selectedTabIndex = selected,
            onTabSelected = { if (it != selected) onSelected(it) },
            modifier = modifier.fillMaxWidth(),
            height = if (height.value.isNaN()) {
                io.github.suqi8.coui.kmp.basic.TabRowDefaults.TabRowWithContourHeight
            } else {
                height
            },
        )
    }
}
