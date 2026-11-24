package com.aionemu.gameserver.model.base;

import com.aionemu.gameserver.model.siege.CampLocation;
import com.aionemu.gameserver.services.CampWarService;
import com.aionemu.gameserver.spawnengine.SpawnHandlerType;

/**
 * Base de uma torre de Tiamaranta Mesa. Quem manda nas fases e o {@link CampWarService}: aqui so ficam as duas
 * operacoes de spawn que a vulnerabilidade liga e desliga.
 * <p>
 * Diferencas para a {@link CasualBase} da 4.8, todas medidas nas capturas oficiais 5.0:
 * <ul>
 * <li>o boss (Watching Eye) e o MistOn nascem no instante em que a torre fica vulneravel, nao num atraso fixo;</li>
 * <li>nao existe assalto aleatorio nem outrider: a torre so troca de dono quando alguem mata o boss.</li>
 * </ul>
 *
 * @author Lost Academy Team & Durak
 */
public class CampBase extends Base<BaseLocation> implements CampWarService.CampBaseHolder {

	private final CampLocation camp;

	public CampBase(BaseLocation bLoc, CampLocation camp) {
		super(bLoc);
		this.camp = camp;
	}

	@Override
	protected int getAssaultDelay() {
		return 0;
	}

	@Override
	protected int getAssaultDespawnDelay() {
		return 0;
	}

	@Override
	protected int getBossSpawnDelay() {
		return 0;
	}

	@Override
	protected int getNpcSpawnDelay() {
		return 0; // sem outriders
	}

	/** O boss so existe enquanto a torre esta vulneravel; quem o acende e apaga e o CampWarService. */
	@Override
	protected void scheduleBossSpawn() {
		if (camp.isVulnerable())
			spawnVulnerableNpcs();
	}

	/** Camp war nao tem assalto aleatorio: a torre e tomada matando o boss. */
	@Override
	protected void scheduleAssault() {
	}

	@Override
	public void spawnVulnerableNpcs() {
		despawnVulnerableNpcs(); // idempotente: nunca deixa dois bosses na torre
		spawnBySpawnHandler(SpawnHandlerType.BOSS, getOccupier());
		spawnBySpawnHandler(SpawnHandlerType.GUARDIAN, getOccupier());
	}

	@Override
	public void despawnVulnerableNpcs() {
		despawnByHandlerType(SpawnHandlerType.BOSS);
		despawnByHandlerType(SpawnHandlerType.GUARDIAN);
	}
}
