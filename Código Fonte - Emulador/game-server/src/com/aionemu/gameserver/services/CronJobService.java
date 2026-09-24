package com.aionemu.gameserver.services;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.configs.main.SiegeConfig;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.templates.spawns.SpawnTemplate;
import com.aionemu.gameserver.services.cron.CronService;
import com.aionemu.gameserver.services.player.BattlePassService;
import com.aionemu.gameserver.spawnengine.SpawnEngine;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * @author Lost Academy Team & Durak
 */
public class CronJobService {

	private static final CronJobService INSTANCE = new CronJobService();

	private CronJobService() {
		scheduleMoltenusSpawn();
		scheduleLegionDominionCalculation();
		scheduleBattlePassReset();
	}

	public static CronJobService getInstance() {
		return INSTANCE;
	}

	private void scheduleMoltenusSpawn() {
		CronService.getInstance().schedule(new Runnable() {

			private Npc moltenus;

			@Override
			public void run() {
				if (moltenus != null && moltenus.isSpawned())
					return;

				SpawnTemplate template = switch (Rnd.get(1, 3)) {
					case 1 -> SpawnEngine.newSingleTimeSpawn(400010000, 251045, 2464.9199f, 1689f, 2882.221f, (byte) 0);
					case 2 -> SpawnEngine.newSingleTimeSpawn(400010000, 251045, 2263.4812f, 2587.1633f, 2879.5447f, (byte) 0);
					default -> SpawnEngine.newSingleTimeSpawn(400010000, 251045, 1692.96f, 1809.04f, 2886.027f, (byte) 0);
				};
				moltenus = (Npc) SpawnEngine.spawnObject(template, 1);
				// Despawn task
				ThreadPoolManager.getInstance().schedule(() -> {
					if (moltenus != null && !moltenus.isDead()) {
						moltenus.getController().delete();
						moltenus = null;
					}
				}, 3600 * 1000);
			}
		}, SiegeConfig.MOLTENUS_SPAWN_SCHEDULE);
	}

	private void scheduleLegionDominionCalculation() {
		CronService.getInstance().schedule(() -> LegionDominionService.getInstance().startWeeklyCalculation(), "0 0 9 ? * WED *");
	}

	private void scheduleBattlePassReset() {
		CronService.getInstance().schedule(() -> BattlePassService.getInstance().onRestart(), "0 0 9 ? * * *");
	}
}
