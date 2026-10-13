package io.github.xgl34222220.ziyu.ui.library

import androidx.compose.runtime.Composable
import io.github.xgl34222220.ziyu.ui.appearance.UiStyle

@Composable
internal fun FontLibraryScreenMaterial(
    state: FontLibraryUiState,
    actions: FontLibraryActions,
    topActions: @Composable () -> Unit = {},
) {
    FontLibraryPageContent(UiStyle.MATERIAL, state, actions, topActions)
}
