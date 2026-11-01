package dev.nodelift.companion

import org.junit.Assert.*
import org.junit.Test

class HomeActionTest {
    @Test fun guidesEnrollmentAndSessionWithoutImplicitConsent() {
        assertEquals(HomeAction.PAIR,HomeAction.choose(false,false,false,false,false,false))
        assertEquals(HomeAction.RESUME,HomeAction.choose(true,false,false,false,true,false))
        assertEquals(HomeAction.CONNECTING,HomeAction.choose(true,true,false,false,true,false))
        assertEquals(HomeAction.SETUP,HomeAction.choose(true,true,true,false,false,false))
        assertEquals(HomeAction.PAUSE,HomeAction.choose(true,true,true,false,true,false))
    }
    @Test fun diagnosticsKeepPauseAvailableEvenWithoutFreshContact() {
        val action=HomeAction.choose(true,true,false,true,false,false,diagnosticRunning=true)
        assertEquals(HomeAction.ASSESSING,action)
        assertTrue(action.enabled)
        assertEquals("Pause node",action.label)
        assertEquals(HomeAction.BUSY,HomeAction.choose(true,true,true,false,true,true,diagnosticRunning=true))
    }
    @Test fun cameraStartupBlocksAnotherHomeAction() {
        val action=HomeAction.choose(false,false,false,false,false,busy=true)
        assertEquals(HomeAction.BUSY,action)
        assertFalse(action.enabled)
    }
    @Test fun preventsDuplicateWorkDuringTransitions() {
        assertFalse(HomeAction.choose(true,true,true,true,false,false).enabled)
        assertEquals(HomeAction.LOADING,HomeAction.choose(true,true,true,true,true,false))
        assertEquals(HomeAction.BUSY,HomeAction.choose(false,false,false,false,false,true))
        assertFalse(HomeAction.BUSY.enabled)
        assertEquals(HomeAction.CONNECTING,HomeAction.choose(false,true,false,false,false,false))
    }
}
