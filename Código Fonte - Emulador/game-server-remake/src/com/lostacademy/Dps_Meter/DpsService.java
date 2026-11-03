package com.lostacademy.Dps_Meter;

import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.world.World;
import com.lostacademy.lostsocket.combat.ComboService;
import com.lostacademy.lostsocket.core.WebSocketServer;

/**
 * High-performance, zero CPU combat telemetry service.
 * Dispatches real-time combat damage, heal, combo events, target emblems, and 4-axis radar data
 * directly through WebSockets to BrService.dll.
 */
public final class DpsService {

	private static final DateTimeFormatter TIME_FORMATTER = DateTimeFormatter.ofPattern("HH:mm:ss");
	private static final DpsService instance = new DpsService();

	public static DpsService getInstance() {
		return instance;
	}

	private DpsService() {
	}

	public static void sendPlayerState(Player player, boolean inGame, boolean isLoading) {
		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers()) return;
		if (player == null) return;

		boolean isAdmin = player.isStaff();
		int onlineCount = World.getInstance().getAllPlayers().size();

		StringBuilder sb = new StringBuilder(192);
		sb.append("{\"type\":\"PLAYER_STATE\",")
		  .append("\"inGame\":").append(inGame).append(",")
		  .append("\"isLoading\":").append(isLoading).append(",")
		  .append("\"isAdmin\":").append(isAdmin).append(",")
		  .append("\"charId\":").append(player.getObjectId()).append(",")
		  .append("\"name\":\"").append(safeJsonString(player.getName())).append("\",")
		  .append("\"className\":\"").append(player.getPlayerClass() != null ? player.getPlayerClass().name() : "WARRIOR").append("\",")
		  .append("\"onlineCount\":").append(onlineCount)
		  .append("}");

		ws.sendToPlayer(player.getObjectId(), sb.toString());
	}

	public static void onTargetSelected(Player player, VisibleObject newTarget) {
		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers()) return;
		if (player == null) return;

		// Never show self as combat target
		if (newTarget == null || newTarget.equals(player)) {
			ws.sendToPlayer(player.getObjectId(), "{\"type\":\"TARGET_INFO\",\"hasTarget\":false}");
			return;
		}

		if (newTarget instanceof Creature creature) {
			String name = safeJsonString(creature.getName());
			int targetId = creature.getObjectId();
			int level = creature.getLevel();
			int curHp = (creature.getLifeStats() != null && !creature.isDead()) 
				? creature.getLifeStats().getCurrentHp() : 0;
			int maxHp = creature.getLifeStats() != null ? creature.getLifeStats().getMaxHp() : 100;
			boolean isNpc = creature instanceof Npc;
			int modelId = 0;
			String aiName = "general";
			String rating = "NORMAL";
			String race = "NPC";
			int pAttack = 0;
			int pDef = 0;
			int mRes = 0;

			if (creature instanceof Npc npc) {
				modelId = npc.getNpcId();
				if (npc.getObjectTemplate() != null) {
					if (npc.getObjectTemplate().getAiName() != null) {
						aiName = npc.getObjectTemplate().getAiName();
					}
					if (npc.getObjectTemplate().getRating() != null) {
						rating = npc.getObjectTemplate().getRating().name();
					}
				}
				if (npc.getRace() != null) {
					race = npc.getRace().name();
				}
			} else if (creature instanceof Player pTarget) {
				rating = "PLAYER";
				if (pTarget.getRace() != null) {
					race = pTarget.getRace().name();
				}
			}

			if (creature.getGameStats() != null) {
				if (creature.getGameStats().getMainHandPAttack() != null) {
					pAttack = creature.getGameStats().getMainHandPAttack().getCurrent();
				}
				if (creature.getGameStats().getPDef() != null) {
					pDef = creature.getGameStats().getPDef().getCurrent();
				}
				try {
					var mresStat = creature.getGameStats().getStat(StatEnum.MAGICAL_RESIST, 0);
					if (mresStat != null) {
						mRes = mresStat.getCurrent();
					}
				} catch (Exception ignored) {
				}
			}

			StringBuilder sb = new StringBuilder(320);
			sb.append("{\"type\":\"TARGET_INFO\",")
			  .append("\"hasTarget\":true,")
			  .append("\"targetId\":").append(targetId).append(",")
			  .append("\"name\":\"").append(name).append("\",")
			  .append("\"level\":").append(level).append(",")
			  .append("\"currentHp\":").append(curHp).append(",")
			  .append("\"maxHp\":").append(maxHp).append(",")
			  .append("\"isNpc\":").append(isNpc).append(",")
			  .append("\"rating\":\"").append(rating).append("\",")
			  .append("\"race\":\"").append(race).append("\",")
			  .append("\"modelId\":").append(modelId).append(",")
			  .append("\"aiName\":\"").append(safeJsonString(aiName)).append("\",")
			  .append("\"attack\":").append(pAttack).append(",")
			  .append("\"pdef\":").append(pDef).append(",")
			  .append("\"mres\":").append(mRes)
			  .append("}");

			ws.sendToPlayer(player.getObjectId(), sb.toString());
		}
	}

	public static void recordPlayerDamage(Player player, Creature target, long damage, int skillId, String skillName, boolean isCrit) {
		if (player == null || target == null || damage <= 0) return;
		if (target.equals(player)) return; // Exclude self target

		// Trigger Combo chaining unconditionally for valid hits
		ComboService.getInstance().onPlayerHit(player, target, (int) damage);

		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers()) return;

		String attackerName = safeJsonString(player.getName());
		String targetName = safeJsonString(target.getName());
		String safeSkill = safeJsonString(skillName != null ? skillName : "Auto Attack");
		String timeStr = LocalTime.now().format(TIME_FORMATTER);

		int targetHp = (target.getLifeStats() != null && !target.isDead()) 
			? target.getLifeStats().getCurrentHp() : 0;
		if (targetHp < 0) targetHp = 0;
		int targetMaxHp = target.getLifeStats() != null ? target.getLifeStats().getMaxHp() : 100;
		int targetLevel = target.getLevel();

		// Calculate 4-axis Combat Radar stats (Crítico, Bloqueio, Esquiva, Resistência)
		int pCrit = 45;
		int pBlock = 30;
		int pDodge = 25;
		int pResist = 35;
		if (player.getGameStats() != null) {
			try {
				var cStat = player.getGameStats().getStat(StatEnum.PHYSICAL_CRITICAL, 0);
				if (cStat != null) pCrit = Math.min(100, Math.max(10, cStat.getCurrent() / 10));
				var bStat = player.getGameStats().getStat(StatEnum.BLOCK, 0);
				if (bStat != null) pBlock = Math.min(100, Math.max(10, bStat.getCurrent() / 25));
				var eStat = player.getGameStats().getStat(StatEnum.EVASION, 0);
				if (eStat != null) pDodge = Math.min(100, Math.max(10, eStat.getCurrent() / 20));
				var rStat = player.getGameStats().getStat(StatEnum.MAGICAL_RESIST, 0);
				if (rStat != null) pResist = Math.min(100, Math.max(10, rStat.getCurrent() / 20));
			} catch (Exception ignored) {
			}
		}

		int targetId = target.getObjectId();
		int modelId = (target instanceof Npc npc) ? npc.getNpcId() : 0;
		boolean isNpc = target instanceof Npc;
		String rating = "NORMAL";
		String race = "NPC";
		if (target instanceof Npc npc) {
			if (npc.getObjectTemplate() != null && npc.getObjectTemplate().getRating() != null) {
				rating = npc.getObjectTemplate().getRating().name();
			}
			if (npc.getRace() != null) {
				race = npc.getRace().name();
			}
		} else if (target instanceof Player pTarget) {
			rating = "PLAYER";
			if (pTarget.getRace() != null) {
				race = pTarget.getRace().name();
			}
		}

		StringBuilder sb = new StringBuilder(410);
		sb.append("{\"type\":\"COMBAT_EVENT\",")
		  .append("\"time\":\"").append(timeStr).append("\",")
		  .append("\"actionType\":\"DAMAGE\",")
		  .append("\"attacker\":\"").append(attackerName).append("\",")
		  .append("\"attackerClass\":\"").append(player.getPlayerClass() != null ? player.getPlayerClass().name() : "WARRIOR").append("\",")
		  .append("\"target\":\"").append(targetName).append("\",")
		  .append("\"targetId\":").append(targetId).append(",")
		  .append("\"modelId\":").append(modelId).append(",")
		  .append("\"isNpc\":").append(isNpc).append(",")
		  .append("\"rating\":\"").append(rating).append("\",")
		  .append("\"race\":\"").append(race).append("\",")
		  .append("\"skillId\":").append(skillId).append(",")
		  .append("\"skillName\":\"").append(safeSkill).append("\",")
		  .append("\"damage\":").append(damage).append(",")
		  .append("\"isCrit\":").append(isCrit).append(",")
		  .append("\"isHeal\":false,")
		  .append("\"targetHp\":").append(targetHp).append(",")
		  .append("\"targetMaxHp\":").append(targetMaxHp).append(",")
		  .append("\"targetLevel\":").append(targetLevel).append(",")
		  .append("\"radar\":{")
		  .append("\"crit\":").append(pCrit).append(",")
		  .append("\"block\":").append(pBlock).append(",")
		  .append("\"dodge\":").append(pDodge).append(",")
		  .append("\"resist\":").append(pResist)
		  .append("}}");

		ws.sendToGroupOrAlliance(player, sb.toString());
	}

	public static void recordNpcDamage(Creature attacker, Player player, long damage, int skillId, String skillName, boolean isCrit) {
		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers()) return;
		if (attacker == null || player == null || damage <= 0) return;

		String attackerName = safeJsonString(attacker.getName());
		String targetName = safeJsonString(player.getName());
		String safeSkill = safeJsonString(skillName != null ? skillName : "Auto Attack");
		String timeStr = LocalTime.now().format(TIME_FORMATTER);

		int targetHp = (player.getLifeStats() != null && !player.isDead()) 
			? player.getLifeStats().getCurrentHp() : 0;
		if (targetHp < 0) targetHp = 0;
		int targetMaxHp = player.getLifeStats() != null ? player.getLifeStats().getMaxHp() : 100;
		int targetLevel = player.getLevel();

		StringBuilder sb = new StringBuilder(256);
		sb.append("{\"type\":\"COMBAT_EVENT\",")
		  .append("\"time\":\"").append(timeStr).append("\",")
		  .append("\"actionType\":\"DAMAGE\",")
		  .append("\"attacker\":\"").append(attackerName).append("\",")
		  .append("\"target\":\"").append(targetName).append("\",")
		  .append("\"skillId\":").append(skillId).append(",")
		  .append("\"skillName\":\"").append(safeSkill).append("\",")
		  .append("\"damage\":").append(damage).append(",")
		  .append("\"isCrit\":").append(isCrit).append(",")
		  .append("\"isHeal\":false,")
		  .append("\"targetHp\":").append(targetHp).append(",")
		  .append("\"targetMaxHp\":").append(targetMaxHp).append(",")
		  .append("\"targetLevel\":").append(targetLevel)
		  .append("}");

		ws.sendToPlayer(player.getObjectId(), sb.toString());
	}

	public static void recordPlayerHeal(Player healer, Creature target, long healAmount, int skillId, String skillName) {
		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers()) return;
		if (healer == null || target == null || healAmount <= 0) return;

		String attackerName = safeJsonString(healer.getName());
		String targetName = safeJsonString(target.getName());
		String safeSkill = safeJsonString(skillName != null ? skillName : "Heal");
		String timeStr = LocalTime.now().format(TIME_FORMATTER);

		int targetHp = (target.getLifeStats() != null && !target.isDead()) 
			? target.getLifeStats().getCurrentHp() : 0;
		if (targetHp < 0) targetHp = 0;
		int targetMaxHp = target.getLifeStats() != null ? target.getLifeStats().getMaxHp() : 100;
		int targetLevel = target.getLevel();

		StringBuilder sb = new StringBuilder(256);
		sb.append("{\"type\":\"COMBAT_EVENT\",")
		  .append("\"time\":\"").append(timeStr).append("\",")
		  .append("\"actionType\":\"HEAL\",")
		  .append("\"attacker\":\"").append(attackerName).append("\",")
		  .append("\"target\":\"").append(targetName).append("\",")
		  .append("\"skillId\":").append(skillId).append(",")
		  .append("\"skillName\":\"").append(safeSkill).append("\",")
		  .append("\"damage\":").append(healAmount).append(",")
		  .append("\"isCrit\":false,")
		  .append("\"isHeal\":true,")
		  .append("\"targetHp\":").append(targetHp).append(",")
		  .append("\"targetMaxHp\":").append(targetMaxHp).append(",")
		  .append("\"targetLevel\":").append(targetLevel)
		  .append("}");

		ws.sendToGroupOrAlliance(healer, sb.toString());
	}

	public static void sendComboEvent(Player player, String event, int hits, int hitDamage, int totalDamage, int timeoutMs, String title) {
		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers() || player == null) return;
		StringBuilder sb = new StringBuilder(192);
		sb.append("{\"type\":\"COMBO_EVENT\",")
		  .append("\"event\":\"").append(event).append("\",")
		  .append("\"hits\":").append(hits).append(",")
		  .append("\"hitDamage\":").append(hitDamage).append(",")
		  .append("\"totalDamage\":").append(totalDamage).append(",")
		  .append("\"timeoutMs\":").append(timeoutMs).append(",")
		  .append("\"title\":\"").append(safeJsonString(title)).append("\"")
		  .append("}");
		ws.sendToPlayer(player.getObjectId(), sb.toString());
	}

	public static void sendParticipationGained(Player player, int pointsEarned, long totalPoints) {
		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers() || player == null) return;
		StringBuilder sb = new StringBuilder(128);
		sb.append("{\"type\":\"ACTION_POINT_GAINED\",")
		  .append("\"pointsEarned\":").append(pointsEarned).append(",")
		  .append("\"totalPoints\":").append(totalPoints)
		  .append("}");
		ws.sendToPlayer(player.getObjectId(), sb.toString());
	}

	public static void sendNewRecord(Player player, int recordHits) {
		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers() || player == null) return;
		StringBuilder sb = new StringBuilder(96);
		sb.append("{\"type\":\"ACTION_NEW_RECORD\",")
		  .append("\"recordHits\":").append(recordHits)
		  .append("}");
		ws.sendToPlayer(player.getObjectId(), sb.toString());
	}

	public static void sendAbnormalState(Player player, int detailId, String stateName) {
		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers() || player == null) return;
		StringBuilder sb = new StringBuilder(128);
		sb.append("{\"type\":\"ACTION_ABNORMAL_STATE\",")
		  .append("\"detail\":").append(detailId).append(",")
		  .append("\"name\":\"").append(safeJsonString(stateName)).append("\"")
		  .append("}");
		ws.sendToPlayer(player.getObjectId(), sb.toString());
	}

	public static void sendParticipationNotification(Player player, long delta, long total) {
		sendParticipationGained(player, (int) delta, total);
	}

	private static String safeJsonString(String str) {
		if (str == null) return "";
		return str.replace("\\", "\\\\")
				  .replace("\"", "\\\"")
				  .replace("\r", "")
				  .replace("\n", " ");
	}
}
