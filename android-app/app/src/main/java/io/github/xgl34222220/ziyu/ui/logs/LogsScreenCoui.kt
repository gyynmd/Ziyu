package io.github.xgl34222220.ziyu.ui.logs

import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.Dp
import io.github.xgl34222220.ziyu.ui.appearance.UiStyle

@Composable
internal fun LogsScreenCoui(
    state: LogsUiState,
    actions: LogsActions,
    diagnosticState: DiagnosticExportState,
    onDiagnostic: () -> Unit,
    onBack: () -> Unit,
    controlsBottomPadding: Dp,
) {
    LogsPageContent(UiStyle.COUI, state, actions, diagnosticState, onDiagnostic, onBack, controlsBottomPadding)
}
