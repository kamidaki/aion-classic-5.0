package com.aionemu.gameserver.skillengine.effect;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class BleedEffectTest {

	@Test void damageReductionUsesOfficialPermilleScale() {
		assertEquals(900, BleedEffect.applyDamageReduction(1000, 100));
		assertEquals(860, BleedEffect.applyDamageReduction(1000, 140));
		assertEquals(795, BleedEffect.applyDamageReduction(1000, 205));
		assertEquals(725, BleedEffect.applyDamageReduction(1000, 275));
	}

	@Test void damageReductionIsClampedAndNeverCreatesZeroDamage() {
		assertEquals(1000, BleedEffect.applyDamageReduction(1000, -1));
		assertEquals(1, BleedEffect.applyDamageReduction(1000, 1000));
		assertEquals(1, BleedEffect.applyDamageReduction(1000, 2000));
	}
}
