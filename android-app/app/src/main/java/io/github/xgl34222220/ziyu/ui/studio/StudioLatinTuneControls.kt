package io.github.xgl34222220.ziyu.ui.studio

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import io.github.xgl34222220.ziyu.MIX_LATIN_OFFSET_LIMIT
import io.github.xgl34222220.ziyu.MIX_LATIN_SIZE_LIMIT
import io.github.xgl34222220.ziyu.ui.theme.ZiyuCard
import kotlin.math.roundToInt

@Composable
internal fun StudioLatinTuneControls(state: FontStudioUiState, actions: FontStudioActions) {
    val idle = !state.loading && !state.busy && !state.operationBusy
    val enabled = idle && state.manualTuneSupported
    ZiyuCard(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("英数微调", modifier = Modifier.weight(1f), fontWeight = FontWeight.SemiBold)
                TextButton(
                    onClick = { actions.updateTune(0, 0) },
                    enabled = idle && (state.latinSize != 0 || state.latinOffset != 0),
                ) { Text("恢复默认") }
            }
            Text("在自动对齐结果上调整英文和数字，重新生成组合后生效。",
                style = MaterialTheme.typography.bodySmall)
            if (!state.loading && !state.manualTuneSupported) {
                Text("请更新配套模块以使用英数微调。", style = MaterialTheme.typography.bodySmall)
            }
            LatinTuneSlider("英数大小", state.latinSize, MIX_LATIN_SIZE_LIMIT,
                "负值缩小，正值放大", enabled) { actions.updateTune(it, state.latinOffset) }
            LatinTuneSlider("英数上下位置", state.latinOffset, MIX_LATIN_OFFSET_LIMIT,
                "负值下移，正值上移", enabled) { actions.updateTune(state.latinSize, it) }
        }
    }
}

@Composable
private fun LatinTuneSlider(
    label: String,
    value: Int,
    limit: Int,
    hint: String,
    enabled: Boolean,
    onValue: (Int) -> Unit,
) {
    Text("$label：${if (value > 0) "+" else ""}$value%", modifier = Modifier.padding(top = 12.dp))
    Slider(
        value = value.toFloat(),
        onValueChange = { onValue(it.roundToInt().coerceIn(-limit, limit)) },
        valueRange = -limit.toFloat()..limit.toFloat(),
        steps = limit * 2 - 1,
        enabled = enabled,
    )
    Text(hint, style = MaterialTheme.typography.bodySmall)
}
