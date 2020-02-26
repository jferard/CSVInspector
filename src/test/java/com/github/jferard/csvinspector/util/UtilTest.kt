package com.github.jferard.csvinspector.util

import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class UtilTest {
    @Test
    fun testToken() {
        assertEquals(14, generateToken(10L).length)
    }
}