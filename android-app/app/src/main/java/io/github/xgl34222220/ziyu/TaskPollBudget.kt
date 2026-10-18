package io.github.xgl34222220.ziyu

/** Counts elapsed wall time; only explicitly reported user pauses may be excluded. */
internal class TaskPollBudget(
    timeoutMs: Long,
    private val nowMs: () -> Long = { System.nanoTime() / 1_000_000L },
) {
    private val startedAt = nowMs()
    private var pausedMs = 0L
    private var deadlineMs = timeoutMs

    val elapsedMs: Long
        get() {
            val now = nowMs()
            return (now - startedAt - pausedMs).coerceAtLeast(0L)
        }
    val remainingMs: Long get() = (deadlineMs - elapsedMs).coerceAtLeast(0L)

    fun excludePause(durationMs: Long) {
        pausedMs += durationMs.coerceAtLeast(0L)
    }

    fun extendTo(timeoutMs: Long) {
        deadlineMs = maxOf(deadlineMs, timeoutMs)
    }
}

/** Background checks stay bounded while foreground resumption can interrupt the wait. */
internal const val BACKGROUND_TASK_POLL_INTERVAL_MS = 15_000L

/** Status cadence stays responsive initially and backs off only while the task is unchanged. */
internal fun taskPollIntervalMs(elapsedMs: Long, unchangedPolls: Int): Long {
    val base = if (elapsedMs < 30_000L) 1_000L else 2_000L
    return when {
        unchangedPolls >= 6 -> 4_000L
        unchangedPolls >= 3 -> maxOf(base, 2_000L)
        else -> base
    }
}
