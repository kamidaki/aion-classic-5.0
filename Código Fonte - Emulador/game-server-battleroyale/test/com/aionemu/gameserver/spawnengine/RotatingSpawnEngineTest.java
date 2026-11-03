package com.aionemu.gameserver.spawnengine;

import static org.junit.jupiter.api.Assertions.*;

import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import org.junit.jupiter.api.Test;

class RotatingSpawnEngineTest {

	@Test
	void rotatesWithoutOverlappingOrRepeatingTheCurrentSpot() {
		Set<Integer> live = new HashSet<>();
		AtomicInteger previous = new AtomicInteger(-1);
		AtomicInteger spawned = new AtomicInteger();
		var cycle = new RotatingSpawnEngine.Cycle<Integer>(20, bound -> spawned.get() % bound, spot -> {
			assertTrue(live.isEmpty(), "O NPC anterior deve ser removido antes do novo spawn");
			assertNotEquals(previous.get(), spot);
			assertTrue(spot >= 0 && spot < 20);
			live.add(spot);
			previous.set(spot);
			spawned.incrementAndGet();
			return spot;
		}, live::remove);
		for (int i = 0; i < 100; i++) {
			cycle.rotate();
			assertEquals(1, live.size());
		}
		cycle.close();
		assertTrue(live.isEmpty());
		cycle.rotate();
		assertEquals(100, spawned.get(), "Uma instância encerrada não pode voltar a criar NPCs");
	}

	@Test
	void recoversOnTheNextTickAfterSpawnFailure() {
		AtomicBoolean fail = new AtomicBoolean(true);
		Set<Integer> live = new HashSet<>();
		var cycle = new RotatingSpawnEngine.Cycle<Integer>(2, _ -> 0, spot -> {
			if (fail.getAndSet(false))
				throw new IllegalStateException("Falha de spawn");
			live.add(spot);
			return spot;
		}, live::remove);
		assertThrows(IllegalStateException.class, cycle::rotate);
		cycle.rotate();
		assertEquals(Set.of(0), live);
		cycle.rotate();
		assertEquals(Set.of(1), live);
		cycle.close();
		cycle.close();
		assertTrue(live.isEmpty());
	}
}
