package io.github.xgl34222220.ziyu

internal fun filterFonts(fonts: List<FontItem>, rawQuery: String): List<FontItem> {
    val query = rawQuery.trim()
    if (query.isEmpty()) return fonts
    return fonts.filter { item ->
        item.name.contains(query, ignoreCase = true) ||
            item.id.contains(query, ignoreCase = true) ||
            item.format.contains(query, ignoreCase = true)
    }
}

/** Reuses the last result while the immutable font-list reference and query stay unchanged. */
internal class FontFilterMemo(
    private val filter: (List<FontItem>, String) -> List<FontItem> = ::filterFonts,
) {
    private var lastFonts: List<FontItem>? = null
    private var lastQuery: String? = null
    private var lastResult: List<FontItem> = emptyList()

    @Synchronized
    fun filter(fonts: List<FontItem>, query: String): List<FontItem> {
        if (fonts === lastFonts && query == lastQuery) return lastResult
        val result = filter.invoke(fonts, query)
        lastFonts = fonts
        lastQuery = query
        lastResult = result
        return result
    }
}
