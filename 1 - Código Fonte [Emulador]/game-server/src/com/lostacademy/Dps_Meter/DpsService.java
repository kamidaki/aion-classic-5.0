package com.lostacademy.Dps_Meter;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.lostacademy.lostsocket.core.WebSocketServer;

/**
 * High-performance, zero CPU combat telemetry service.
 * Dispatches real-time combat damage and heal events directly through WebSockets to BrService.dll.
 * Does not store events in emulator database, delegating indexing to client SQLite DB.
 */
public final class DpsService {

	private DpsService() {
	}

	public static void recordPlayerDamage(Player player, Creature target, long damage, int skillId, String skillName, boolean isCrit) {
		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers()) return;
		if (player == null || target == null || damage <= 0) return;

		String attackerName = safeJsonString(player.getName());
		String targetName = safeJsonString(target.getName());
		String safeSkill = safeJsonString(skillName != null ? skillName : "Auto Attack");

		int targetHp = target.getLifeStats() != null ? target.getLifeStats().getCurrentHp() : 0;
		int targetMaxHp = target.getLifeStats() != null ? target.getLifeStats().getMaxHp() : 100;
		int targetLevel = target.getLevel();

		StringBuilder sb = new StringBuilder(256);
		sb.append("{\"type\":\"COMBAT_EVENT\",")
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

		ws.broadcast(sb.toString());
	}

	public static void recordNpcDamage(Creature attacker, Player player, long damage, int skillId, String skillName, boolean isCrit) {
		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers()) return;
		if (attacker == null || player == null || damage <= 0) return;

		String attackerName = safeJsonString(attacker.getName());
		String targetName = safeJsonString(player.getName());
		String safeSkill = safeJsonString(skillName != null ? skillName : "Auto Attack");

		int targetHp = player.getLifeStats() != null ? player.getLifeStats().getCurrentHp() : 0;
		int targetMaxHp = player.getLifeStats() != null ? player.getLifeStats().getMaxHp() : 100;
		int targetLevel = player.getLevel();

		StringBuilder sb = new StringBuilder(256);
		sb.append("{\"type\":\"COMBAT_EVENT\",")
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

		ws.broadcast(sb.toString());
	}

	public static void recordPlayerHeal(Player healer, Creature target, long healAmount, int skillId, String skillName) {
		WebSocketServer ws = WebSocketServer.getInstance();
		if (!ws.hasActiveSubscribers()) return;
		if (healer == null || target == null || healAmount <= 0) return;

		String attackerName = safeJsonString(healer.getName());
		String targetName = safeJsonString(target.getName());
		String safeSkill = safeJsonString(skillName != null ? skillName : "Heal");

		int targetHp = target.getLifeStats() != null ? target.getLifeStats().getCurrentHp() : 0;
		int targetMaxHp = target.getLifeStats() != null ? target.getLifeStats().getMaxHp() : 100;
		int targetLevel = target.getLevel();

		StringBuilder sb = new StringBuilder(256);
		sb.append("{\"type\":\"COMBAT_EVENT\",")
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

		ws.broadcast(sb.toString());
	}

	private static String safeJsonString(String str) {
		if (str == null) return "";
		return str.replace("\\", "\\\\")
				  .replace("\"", "\\\"")
				  .replace("\r", "")
				  .replace("\n", " ");
	}
}
