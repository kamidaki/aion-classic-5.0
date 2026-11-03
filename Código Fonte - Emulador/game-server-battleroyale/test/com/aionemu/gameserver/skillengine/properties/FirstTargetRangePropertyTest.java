package com.aionemu.gameserver.skillengine.properties;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class FirstTargetRangePropertyTest {

	@Test
	void addsWeaponRangeToOfficialBaseRange() {
		assertEquals(3f, FirstTargetRangeProperty.calculateRange(1, true, 2_000));
		assertEquals(25f, FirstTargetRangeProperty.calculateRange(0, true, 25_000));
		assertEquals(17f, FirstTargetRangeProperty.calculateRange(15, true, 2_000));
	}

	@Test
	void keepsOfficialRangeWhenWeaponRangeDoesNotApply() {
		assertEquals(25f, FirstTargetRangeProperty.calculateRange(25, false, 2_000));
	}
}
