package io.github.xgl34222220.ziyu

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotSame
import org.junit.Assert.assertSame
import org.junit.Test

class FontFilterMemoTest {
    @Test
    fun reusesTheLastResultOnlyForTheSameListReferenceAndQuery() {
        val fonts = listOf(
            font(id = "noto-sans", name = "Noto Sans", format = "OTF"),
            font(id = "source-han", name = "Source Han", format = "TTF"),
        )
        val memo = FontFilterMemo()

        val all = memo.filter(fonts, " ")
        assertSame(fonts, all)
        assertSame(all, memo.filter(fonts, " "))

        val filtered = memo.filter(fonts, " Noto ")
        assertEquals(listOf(fonts.first()), filtered)
        assertSame(filtered, memo.filter(fonts, " Noto "))
        assertEquals(listOf(fonts.last()), memo.filter(fonts, "source-han"))

        val replacement = fonts.toList()
        assertNotSame(fonts, replacement)
        assertNotSame(filtered, memo.filter(replacement, " Noto "))
    }

    private fun font(id: String, name: String, format: String) = FontItem(
        id = id,
        name = name,
        format = format,
        size = "",
        date = "",
        variable = false,
        valid = true,
        error = "",
        weights = emptyList(),
    )
}
