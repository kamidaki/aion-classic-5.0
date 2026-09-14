package com.aionemu.gameserver.model.stats.container;

import java.util.concurrent.Future;

import com.aionemu.gameserver.configs.administration.AdminConfig;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.zone.ZoneType;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ATTACK_STATUS.LOG;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ATTACK_STATUS.TYPE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_EP_UPDATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_EP_UPDATE_OTHER;
import com.aionemu.gameserver.network.aion.serverpackets.SM_FLY_TIME;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SP_UPDATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SP_UPDATE_OTHER;
import com.aionemu.gameserver.network.aion.serverpackets.SM_STATUPDATE_HP;
import com.aionemu.gameserver.network.aion.serverpackets.SM_STATUPDATE_MP;
import com.aionemu.gameserver.services.LifeStatsRestoreService;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.taskmanager.tasks.TeamStatUpdater;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * @author Lost Academy Team & Durak
 */
public class PlayerLifeStats extends CreatureLifeStats<Player> {

	/** SP do Revenant (TH_/MO_): 5.0 oficial satura em 100 sem aviso */
	public static final int MAX_SP = 100;
	/** EP (Ki) do Brawler (ST_): ao chegar a 100 vira 0 e entra o Fever */
	public static final int MAX_EP = 100;
	/** Fever_Check: buff de 20 s com BoostContextSkill FeverCondition, que libera as skills _high */
	public static final int FEVER_SKILL_ID = 3148;

	private final Object fpLock = new Object();
	private int flightReducePeriod = 2;
	private int flightReduceValue = 1;
	private int currentFp;
	private Future<?> flyRestoreTask;
	private Future<?> flyReduceTask;

	private final Object classPointLock = new Object();
	private final long classPointTickAnchor = System.currentTimeMillis();
	private int currentSp;
	private int currentEp;
	private int sentSp;
	private int sentEp;
	private Future<?> classPointFlushTask;

	public PlayerLifeStats(Player owner) {
		super(owner, owner.getGameStats().getMaxHp().getCurrent(), owner.getGameStats().getMaxMp().getCurrent());
		this.currentFp = owner.getGameStats().getFlyTime().getCurrent();
	}

	@Override
	protected void onHpChanged(int previousHp, int newHp, Creature effector) {
		if (isFullyRestoredHp()) // FIXME: Temp Fix: Reset aggro list when hp is full
			owner.getAggroList().clear();
		if (owner.isSpawned()) {
			sendHpPacketUpdate();
			sendGroupPacketUpdate();
			if (previousHp == 0 || newHp < previousHp)
				triggerRestoreTask();
			if (previousHp == 0)
				triggerFpRestore();
		}
		super.onHpChanged(previousHp, newHp, effector);
	}

	@Override
	protected void onMpChanged(int previousMp, int newMp) {
		super.onMpChanged(previousMp, newMp);
		if (owner.isSpawned()) {
			sendMpPacketUpdate();
			sendGroupPacketUpdate();
			if (newMp < previousMp)
				triggerRestoreTask();
		}
	}

	private void sendGroupPacketUpdate() {
		if (owner.isInTeam())
			TeamStatUpdater.getInstance().add(owner);
	}

	@Override
	public void synchronizeWithMaxStats() {
		if (isDead())
			return;

		super.synchronizeWithMaxStats();
		currentFp = getMaxFp();

		if (owner.isSpawned()) {
			sendHpPacketUpdate();
			sendMpPacketUpdate();
			sendFpPacketUpdate();
		}
	}

	@Override
	public void updateCurrentStats() {
		super.updateCurrentStats();

		if (!isFullyRestoredHpMp())
			triggerRestoreTask();

		if (getMaxFp() < currentFp)
			currentFp = getMaxFp();

		if (owner.getFlyState() == 0)
			triggerFpRestore();
	}

	private void sendHpPacketUpdate() {
		PacketSendUtility.sendPacket(owner, new SM_STATUPDATE_HP(getCurrentHp(), getMaxHp()));
	}

	private void sendMpPacketUpdate() {
		PacketSendUtility.sendPacket(owner, new SM_STATUPDATE_MP(getCurrentMp(), getMaxMp()));
	}

	/**
	 * @return the currentFp
	 */
	@Override
	public int getCurrentFp() {
		return this.currentFp;
	}

	@Override
	public int getMaxFp() {
		return owner.getGameStats().getFlyTime().getCurrent();
	}

	/**
	 * @return FP percentage 0 - 100
	 */
	public int getFpPercentage() {
		return 100 * currentFp / getMaxFp();
	}

	/**
	 * This method is called whenever caller wants to restore creatures' FP
	 * 
	 * @param value
	 * @return
	 */
	public int increaseFp(TYPE type, int value, int skillId, LOG log) {
		synchronized (fpLock) {
			if (isDead()) {
				return 0;
			}
			int newFp = this.currentFp + value;
			if (newFp > getMaxFp()) {
				newFp = getMaxFp();
				value = getMaxFp() - this.currentFp;
			}
			if (currentFp != newFp) {
				this.currentFp = newFp;
				onIncreaseFp(type, value, skillId, log);
			}
		}

		return currentFp;

	}

	/**
	 * This method is called whenever caller wants to reduce creatures' FP
	 * 
	 * @return Current flight points
	 */
	public int reduceFp(TYPE type, int value, int skillId, LOG log) {
		synchronized (fpLock) {
			int newFp = this.currentFp - value;

			if (newFp < 0) {
				newFp = 0;
				value = this.currentFp;
			}

			this.currentFp = newFp;
		}

		onReduceFp(type, value, skillId, log);

		return currentFp;
	}

	public int setCurrentFp(int value) {
		synchronized (fpLock) {
			int newFp = value;

			if (newFp < 0)
				newFp = 0;

			this.currentFp = newFp;
		}

		onReduceFp(null, value, 0, null);

		return currentFp;
	}

	protected void onIncreaseFp(TYPE type, int value, int skillId, LOG log) {
		if (value > 0) {
			sendAttackStatusPacketUpdate(type, value, skillId, log);
			sendFpPacketUpdate();
		}
	}

	protected void onReduceFp(TYPE type, int value, int skillId, LOG log) {
		sendAttackStatusPacketUpdate(type, value, skillId, log);
		sendFpPacketUpdate();
	}

	public void sendFpPacketUpdate() {
		PacketSendUtility.sendPacket(owner, new SM_FLY_TIME(currentFp, getMaxFp()));
	}

	/**
	 * this method should be used only on FlyTimeRestoreService
	 */
	public void restoreFp() {
		// how much fly time restoring per 6 second.
		increaseFp(TYPE.NATURAL_FP, 3, 0, LOG.REGULAR);
	}

	public void specialrestoreFp() {
		if (owner.getGameStats().getStat(StatEnum.REGEN_FP, 0).getCurrent() != 0)
			increaseFp(TYPE.NATURAL_FP, owner.getGameStats().getStat(StatEnum.REGEN_FP, 0).getCurrent() / 3, 0, LOG.REGULAR);
	}

	public void triggerFpRestore() {
		synchronized (restoreLock) {
			cancelFpReduce();
			if (flyRestoreTask == null && !isDead() && !isFlyTimeFullyRestored()) {
				flyRestoreTask = LifeStatsRestoreService.getInstance().scheduleFpRestoreTask(this);
			}
		}
	}

	public void cancelFpRestore() {
		synchronized (restoreLock) {
			if (flyRestoreTask != null && !flyRestoreTask.isCancelled()) {
				flyRestoreTask.cancel(false);
				flyRestoreTask = null;
			}
		}
	}

	public void triggerFpReduce() {
		if (owner.hasAccess(AdminConfig.UNLIMITED_FLIGHT_TIME) || isDead())
			return;
		synchronized (restoreLock) {
			if (owner.isFlying()) {
				boolean isInFlyArea = owner.isInsideZoneType(ZoneType.FLY) && !owner.isInsideZoneType(ZoneType.NO_FLY);
				flightReduceValue = isInFlyArea ? 1 : 2;
				flightReducePeriod = isInFlyArea && owner.isInGlidingState() ? 2 : 1;
			} else {
				return;
			}
			cancelFpRestore();
			if (flyReduceTask == null && !isDead())
				flyReduceTask = LifeStatsRestoreService.getInstance().scheduleFpReduceTask(this);
		}
	}

	public void cancelFpReduce() {
		synchronized (restoreLock) {
			if (flyReduceTask != null && !flyReduceTask.isCancelled()) {
				flyReduceTask.cancel(false);
				flyReduceTask = null;
			}
		}
	}

	public boolean isFlyTimeFullyRestored() {
		return getMaxFp() == currentFp;
	}

	public int getCurrentSp() {
		return currentSp;
	}

	public int getCurrentEp() {
		return currentEp;
	}

	/**
	 * Valor lido do banco no login. Não gera pacote: o SP sai no S_STATUS e o 5.0 oficial não manda 0x175 no login.
	 */
	public void setCurrentSp(int sp) {
		synchronized (classPointLock) {
			currentSp = sentSp = Math.clamp(sp, 0, MAX_SP);
		}
	}

	public void setCurrentEp(int ep) {
		synchronized (classPointLock) {
			currentEp = sentEp = Math.clamp(ep, 0, MAX_EP);
		}
	}

	public void increaseSp(int value) {
		changeSp(value);
	}

	public void reduceSp(int value) {
		changeSp(-value);
	}

	private void changeSp(int delta) {
		synchronized (classPointLock) {
			int newSp = Math.clamp((long) currentSp + delta, 0, MAX_SP);
			if (newSp == currentSp)
				return;
			currentSp = newSp;
		}
		scheduleClassPointFlush();
	}

	/**
	 * 5.0 oficial (duas capturas do Brawler): +10 por golpe com EP_Recover_10; o golpe que leva o Ki a 100 aplica o Fever_Check no mesmo instante e o Ki
	 * vai a 0 no tick seguinte; durante o Fever nenhum golpe enche o Ki.
	 */
	public void increaseEp(int value) {
		if (value <= 0 || owner.getEffectController().hasAbnormalEffect(FEVER_SKILL_ID))
			return;
		boolean fever;
		synchronized (classPointLock) {
			int newEp = Math.min(MAX_EP, currentEp + value);
			fever = newEp == MAX_EP;
			currentEp = fever ? 0 : newEp;
		}
		if (fever)
			SkillEngine.getInstance().applyEffectDirectly(FEVER_SKILL_ID, owner, owner);
		scheduleClassPointFlush();
	}

	/**
	 * 5.0 oficial: 0x14B/0x166 e 0x175/0x176 saem num tick de 1 s com fase fixa por sessão, e só quando o valor mudou desde o último envio.
	 */
	private void scheduleClassPointFlush() {
		synchronized (classPointLock) {
			if (classPointFlushTask != null)
				return;
			long sinceAnchor = System.currentTimeMillis() - classPointTickAnchor;
			classPointFlushTask = ThreadPoolManager.getInstance().schedule(this::flushClassPoints, 1000 - sinceAnchor % 1000);
		}
	}

	private void flushClassPoints() {
		int sp, ep;
		boolean sendSp, sendEp;
		synchronized (classPointLock) {
			classPointFlushTask = null;
			sp = currentSp;
			ep = currentEp;
			sendSp = sp != sentSp;
			sendEp = ep != sentEp;
			sentSp = sp;
			sentEp = ep;
		}
		if (sendSp) {
			PacketSendUtility.sendPacket(owner, new SM_SP_UPDATE(sp));
			PacketSendUtility.broadcastPacket(owner, new SM_SP_UPDATE_OTHER(owner.getObjectId(), sp), true);
		}
		if (sendEp) {
			PacketSendUtility.sendPacket(owner, new SM_EP_UPDATE(ep));
			PacketSendUtility.broadcastPacket(owner, new SM_EP_UPDATE_OTHER(owner.getObjectId(), ep), true);
		}
	}

	@Override
	public void cancelAllTasks() {
		super.cancelAllTasks();
		cancelFpReduce();
		cancelFpRestore();
		synchronized (classPointLock) {
			if (classPointFlushTask != null) {
				classPointFlushTask.cancel(false);
				classPointFlushTask = null;
			}
		}
	}

	public int getFlightReducePeriod() {
		return flightReducePeriod;
	}

	public int getFlightReduceValue() {
		return flightReduceValue;
	}
}
