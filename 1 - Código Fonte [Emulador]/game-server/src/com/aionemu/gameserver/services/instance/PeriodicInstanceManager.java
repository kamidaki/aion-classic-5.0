package com.aionemu.gameserver.services.instance;

import static com.aionemu.gameserver.configs.main.AutoGroupConfig.*;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.Future;

import org.quartz.CronExpression;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.configs.main.AutoGroupConfig;
import com.aionemu.gameserver.model.autogroup.AutoGroup;
import com.aionemu.gameserver.model.autogroup.AutoGroupType;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_AUTO_GROUP;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.AutoGroupService;
import com.aionemu.gameserver.services.cron.CronService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.World;

/**
 * @author Lost Academy Team & Durak
 */
public class PeriodicInstanceManager {

	private static final Logger log = LoggerFactory.getLogger(PeriodicInstanceManager.class);
	private static final PeriodicInstanceManager INSTANCE = new PeriodicInstanceManager();
	private final Set<Integer> openedRegistrations = new HashSet<>();
	private final Map<Integer, Future<?>> registrationCloseTasksByMaskId = new HashMap<>();

	public static PeriodicInstanceManager getInstance() {
		return INSTANCE;
	}

	private PeriodicInstanceManager() {
		if (AutoGroupConfig.AUTO_GROUP_ENABLE) {
			scheduleRegistration(DREDGION_TIMES, SM_SYSTEM_MESSAGE.STR_MSG_INSTANCE_OPEN_IDAB1_DREADGION(), 1, DREDGION_REGISTRATION_PERIOD);
			scheduleRegistration(CHANTRA_TIMES, SM_SYSTEM_MESSAGE.STR_MSG_INSTANCE_OPEN_IDDREADGION_02(), 2, CHANTRA_REGISTRATION_PERIOD);
		}
	}

	private void scheduleRegistration(CronExpression[] startExpressions, SM_SYSTEM_MESSAGE openingMsg, int maskId, long registrationPeriod) {
		AutoGroupType agt = AutoGroupType.getAGTByMaskId(maskId);
		if (agt == null || agt.getTemplate() == null) {
			log.warn("AutoGroup registration skipped: no template found for maskId {}", maskId);
			return;
		}
		if (startExpressions == null) {
			return;
		}
		for (CronExpression startExpression : startExpressions) {
			CronService.getInstance().schedule(() -> openRegistration(openingMsg, maskId, registrationPeriod), startExpression);
			log.info("Scheduled registration opening for {} based on cron expression: {}", agt, startExpression);
			log.info("Scheduled " + agt + ": based on cron expression: " + startExpression + " Duration: "
				+ registrationPeriod + " in minutes");
		}
	}

	public synchronized boolean openRegistration(SM_SYSTEM_MESSAGE openingMsg, int maskId, long registrationPeriod) {
		if (openedRegistrations.contains(maskId))
			return false;

		openedRegistrations.add(maskId);
		broadcastRegistrationUpdate(openingMsg, maskId, false);

		registrationCloseTasksByMaskId.put(maskId, ThreadPoolManager.getInstance().schedule(() -> closeRegistration(maskId), registrationPeriod * 60000));
		log.info("Scheduled registration closing for {} in {} minutes", AutoGroupType.getAGTByMaskId(maskId), registrationPeriod);
		return true;
	}

	public synchronized boolean closeRegistration(int maskId) {
		if (!openedRegistrations.contains(maskId))
			return false;
		openedRegistrations.remove(maskId);
		broadcastRegistrationUpdate(null, maskId, true);
		AutoGroupService.getInstance().stopRegistrationsByMaskId(maskId);

		if (registrationCloseTasksByMaskId.containsKey(maskId)) {
			Future<?> closeTask = registrationCloseTasksByMaskId.remove(maskId);
			if (closeTask != null && !closeTask.isDone())
				closeTask.cancel(false);
		}
		return true;
	}

	private void broadcastRegistrationUpdate(SM_SYSTEM_MESSAGE msg, int maskId, boolean isClosed) {
		AutoGroupType type = AutoGroupType.getAGTByMaskId(maskId);
		if (type != null && type.getTemplate() != null) {
			World.getInstance().forEachPlayer(player -> {
				if (isInLvlRange(player.getLevel(), type.getTemplate().getMinLvl(), type.getTemplate().getMaxLvl())) {
					PacketSendUtility.sendPacket(player, new SM_AUTO_GROUP(maskId, SM_AUTO_GROUP.WND_ENTRY_ICON, isClosed));
					if (msg != null)
						PacketSendUtility.sendPacket(player, msg);
				}
			});
		}
	}

	public void checkAndSendOpenRegistrations(int objectId) {
		Player player = World.getInstance().getPlayer(objectId);
		if (player != null)
			checkAndSendOpenRegistrations(player);
	}

	public void checkAndSendOpenRegistrations(Player player) {
		for (int maskId : openedRegistrations) {
			AutoGroupType agt = AutoGroupType.getAGTByMaskId(maskId);
			if (agt != null) {
				AutoGroup data = agt.getTemplate();
				if (isInLvlRange(player.getLevel(), data.getMinLvl(), data.getMaxLvl())
					&& !player.getPortalCooldownList().isPortalUseDisabled(data.getInstanceMapId()))
					PacketSendUtility.sendPacket(player, new SM_AUTO_GROUP(maskId, SM_AUTO_GROUP.WND_ENTRY_ICON, false));
			}
		}
	}

	public boolean isRegistrationOpen(int maskId) {
		return openedRegistrations.contains(maskId);
	}

	private boolean isInLvlRange(int playerLvl, int minLvl, int maxLvl) {
		return playerLvl >= minLvl && playerLvl <= maxLvl;
	}

	public void handleRequest(Player player, int maskId) {
		if (openedRegistrations.contains(maskId)) {
			AutoGroupType type = AutoGroupType.getAGTByMaskId(maskId);
			if (type != null) {
				AutoGroup template = type.getTemplate();
				if (isInLvlRange(player.getLevel(), template.getMinLvl(), template.getMaxLvl()))
					PacketSendUtility.sendPacket(player, new SM_AUTO_GROUP(maskId));
			}
		}
	}
}
