package com.aionemu.gameserver.services.teleport;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.TaskId;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.hotspot.HotspotTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_BIND_POINT_TELEPORT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService;
import com.aionemu.gameserver.services.trade.PricesService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.utils.audit.AuditLogger;

/**
 * @author Lost Academy Team & Durak
 */
public class BindPointTeleportService {

	// Captura oficial 5.0 (21/10, hotspot 21 de Inggison): C 0x143 -> S 0x1AF [C 1]; 3,0 s depois o kinah e S 0x1AF [C 3][D 21][D 15];
	// o jogador reaparece no destino ~0,4 s depois, pelo S_PUT_USER (sem S_REQUEST_TELEPORT).
	private static final int CAST_TIME_IN_MS = 3000;
	private static final int ARRIVAL_DELAY_IN_MS = 400;
	private static final int COOLDOWN_IN_SECONDS = 15;
	/**
	 * player id - cooldown
	 */
	private static final Map<Integer, Cooldown> cooldowns = new ConcurrentHashMap<>();

	public static void onLogin(Player player) {
		Cooldown cooldown = getCooldown(player);
		if (cooldown != null && cooldown.getTimeLeft() > 0)
			PacketSendUtility.broadcastPacketAndReceive(player,
				new SM_BIND_POINT_TELEPORT(3, player.getObjectId(), cooldown.getLocId(), cooldown.getTimeLeft()));
	}

	public static void teleport(Player player, int locId, long kinah) {
		HotspotTemplate hotspot = DataManager.HOTSPOT_DATA.getHotspotTemplateById(locId);
		if (hotspot == null) {
			AuditLogger.log(player, "Tried to use invalid hotspot teleport to locId " + locId);
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_CANNOT_MOVE_TO_AIRPORT_NO_ROUTE());
			return;
		}
		long price = calculateTeleportationPrice(player, hotspot, kinah);

		if (!checkRequirements(player, hotspot, price))
			return;

		PacketSendUtility.broadcastPacket(player, new SM_BIND_POINT_TELEPORT(1, player.getObjectId(), locId, 0), true);

		player.getController().addTask(TaskId.SKILL_USE, ThreadPoolManager.getInstance().schedule(new Runnable() {

			@Override
			public void run() {
				if (!player.getInventory().tryDecreaseKinah(price, ItemPacketService.ItemUpdateType.DEC_KINAH_FLY)) {
					PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_CANNOT_MOVE_TO_AIRPORT_NOT_ENOUGH_FEE());
					return;
				}
				addCooldown(player, locId);
				PacketSendUtility.broadcastPacket(player, new SM_BIND_POINT_TELEPORT(3, player.getObjectId(), locId, COOLDOWN_IN_SECONDS), true);
				ThreadPoolManager.getInstance().schedule(new Runnable() {
					@Override
					public void run() {
						if (!player.getLifeStats().isAboutToDie() && !player.isDead())
							TeleportService.teleportTo(player, hotspot.getWorldId(), hotspot.getX(), hotspot.getY(), hotspot.getZ(), hotspot.getHeading());
					}
				}, ARRIVAL_DELAY_IN_MS);
			}
		}, CAST_TIME_IN_MS));
	}

	public static void cancelTeleport(Player player, int locId) {
		if (player.getController().hasTask(TaskId.SKILL_USE)) {
			player.getController().cancelTask(TaskId.SKILL_USE);
			PacketSendUtility.broadcastPacket(player, new SM_BIND_POINT_TELEPORT(2, player.getObjectId(), locId, 0), true);
		}
	}

	private static long calculateTeleportationPrice(Player player, HotspotTemplate hotspot, long priceSentByGameClient) {
		// client_zonemap_hotspot: required_base_gold + required_distance_gold por metro. O cliente manda esse valor (300 no hotspot 21,
		// longe do destino e com distance 0) e o oficial cobrou 355, ou seja, com a taxa de serviço por cima.
		double distance = PositionUtil.getDistance(player, hotspot.getX(), hotspot.getY(), hotspot.getZ());
		long price = Math.max(1, hotspot.getPrice() + (long) (distance * hotspot.getDistancePrice()));
		if (Math.abs(price - priceSentByGameClient) > 1) // diferença mínima é arredondamento da distância
			LoggerFactory.getLogger(BindPointTeleportService.class).warn("Hotspot teleport {} prices don't match: {} vs. {}", hotspot.getId(), price, priceSentByGameClient);
		return PricesService.getPriceForService(Math.max(price, priceSentByGameClient), player.getRace());
	}

	private static boolean checkRequirements(Player player, HotspotTemplate hotspot, long price) {
		if (player.getWorldId() != hotspot.getWorldId()) {
			AuditLogger.log(player, "tried to use hotspot teleport " + hotspot.getId() + " from invalid start world " + player.getWorldId() + ", expected "
				+ hotspot.getWorldId());
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_CANNOT_MOVE_TO_AIRPORT_NO_ROUTE());
			return false;
		}
		if (hotspot.getRace() != Race.PC_ALL && player.getRace() != hotspot.getRace()) {
			AuditLogger.log(player, "tried to use hotspot teleport " + hotspot.getId() + " for invalid race " + player.getRace() + ", expected " + hotspot.getRace());
			return false;
		}
		if (player.getLevel() < hotspot.getMinLevel()) {
			AuditLogger.log(player, "tried to use hotspot teleport " + hotspot.getId() + " below the required level " + hotspot.getMinLevel());
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_CANNOT_MOVE_TO_AIRPORT_NO_ROUTE());
			return false;
		}
		if (player.getInventory().getKinah() < price) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_CANNOT_MOVE_TO_AIRPORT_NOT_ENOUGH_FEE());
			return false;
		}
		Cooldown cooldown = getCooldown(player);
		if (cooldown != null && cooldown.getTimeLeft() > 0) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_FLYING_TIME_NOT_READY());
			return false;
		}

		return true;
	}

	private static void addCooldown(Player player, int locId) {
		long cooldown = System.currentTimeMillis() + COOLDOWN_IN_SECONDS * 1000;
		cooldowns.put(player.getObjectId(), new Cooldown(locId, cooldown));
	}

	private static Cooldown getCooldown(Player player) {
		Cooldown cooldown = cooldowns.get(player.getObjectId());
		if (cooldown != null && cooldown.getTimeLeft() <= 0) {
			cooldowns.remove(player.getObjectId(), cooldown);
			return null;
		}
		return cooldown;
	}

	private static class Cooldown {

		int locId;
		long cdEnd;

		protected Cooldown(int locId, long cdEnd) {
			this.locId = locId;
			this.cdEnd = cdEnd;
		}

		protected int getLocId() {
			return locId;
		}

		protected int getTimeLeft() {
			int estimated = (int) ((cdEnd - System.currentTimeMillis()) / 1000);
			if (estimated > 0)
				return estimated;
			else
				return 0;
		}
	}

}
