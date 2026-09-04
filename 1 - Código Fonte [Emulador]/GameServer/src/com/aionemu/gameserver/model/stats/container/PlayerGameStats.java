package com.aionemu.gameserver.model.stats.container;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.EmotionType;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Equipment;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;
import com.aionemu.gameserver.model.stats.calc.AdditionStat;
import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.model.templates.item.ArmorType;
import com.aionemu.gameserver.model.templates.item.ItemAttackType;
import com.aionemu.gameserver.model.templates.item.WeaponStats;
import com.aionemu.gameserver.model.templates.item.WeaponType;
import com.aionemu.gameserver.model.templates.stats.PlayerStatsTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.S_ACTION;
import com.aionemu.gameserver.network.aion.serverpackets.S_STATUS;
import com.aionemu.gameserver.taskmanager.tasks.PacketBroadcaster.BroadcastMode;
import com.aionemu.gameserver.utils.PacketSendUtility;

public class PlayerGameStats extends CreatureGameStats<Player> {
	private int cachedSpeed;
	private int cachedAttackSpeed;

	public PlayerGameStats(Player owner) {
		super(owner);
	}

	@Override
	protected void onStatsChange() {
		super.onStatsChange();
		updateStatsAndSpeedVisually();
	}

	public void updateStatsAndSpeedVisually() {
		updateStatsVisually();
		checkSpeedStats();
	}

	public void updateStatsVisually() {
		owner.addPacketBroadcastMask(BroadcastMode.UPDATE_STATS);
	}

	private void checkSpeedStats() {
		int current = getMovementSpeed().getCurrent();
		int currentAttackSpeed = getAttackSpeed().getCurrent();
		if (current != cachedSpeed || currentAttackSpeed != cachedAttackSpeed) {
			owner.addPacketBroadcastMask(BroadcastMode.UPDATE_SPEED);
		}
		cachedSpeed = current;
		cachedAttackSpeed = currentAttackSpeed;
	}

	@Override
	public Stat getMaxHp() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), owner.getLevel());
		return getStat(StatEnum.MAXHP, pst.getMaxHp());
	}

	public Stat getMaxMp() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), owner.getLevel());
		int base = pst.getMaxMp();
		return this.getStat(StatEnum.MAXMP, base);
	}

	public Stat getStrikeResist() {
		return getStat(StatEnum.PHYSICAL_CRITICAL_RESIST, 0);
	}

	public Stat getStrikeFort() {
		return getStat(StatEnum.PHYSICAL_CRITICAL_DAMAGE_REDUCE, 0);
	}

	public Stat getSpellResist() {
		return getStat(StatEnum.MAGICAL_CRITICAL_RESIST, 0);
	}

	public Stat getSpellFort() {
		return getStat(StatEnum.MAGICAL_CRITICAL_DAMAGE_REDUCE, 0);
	}

	public Stat getMaxDp() {
		return getStat(StatEnum.MAXDP, 4000);
	}

	public Stat getMaxSp() {
		return getStat(StatEnum.MAX_SP, 100);
	}

	public Stat getFlyTime() {
		return getStat(StatEnum.FLY_TIME, 60); // ...1 Min
	}

	public Stat getAllSpeed() {
		return getStat(StatEnum.ALLSPEED, 7500);
	}

	@Override
	public Stat getAttackSpeed() {
		int base = 1500;
		Equipment equipment = owner.getEquipment();
		Item mainHandWeapon = equipment.getMainHandWeapon();
		if (mainHandWeapon != null) {
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null && ws.getAttackSpeed() > 0) {
				base = ws.getAttackSpeed();
			}
			Item offWeapon = equipment.getOffHandWeapon();
			if (offWeapon == mainHandWeapon) {
				offWeapon = null;
			}
			if (offWeapon != null && offWeapon.getItemTemplate().isWeapon()) {
				WeaponStats offWs = offWeapon.getItemTemplate().getWeaponStats();
				if (offWs != null && offWs.getAttackSpeed() > 0) {
					base += offWs.getAttackSpeed() / 4;
				}
			}
		}
		Stat aSpeed = getStat(StatEnum.ATTACK_SPEED, base);
		return aSpeed;
	}

	@Override
	public Stat getBCastingTime() {
		int base = 0;
		int casterClass = owner.getPlayerClass().getClassId();
		if (casterClass == 7 || // Sorcerer.
				casterClass == 8) { // Spirit-Master.
			base = 800;
		}
		return getStat(StatEnum.BOOST_CASTING_TIME, base);
	}

	@Override
	public Stat getConcentration() {
		int base = 0;
		int sorcerer1 = owner.getPlayerClass().getClassId();
		int spiritMaster1 = owner.getPlayerClass().getClassId();
		if (sorcerer1 == 7) {
			base = 25;
		} else if (spiritMaster1 == 8 && owner.getLevel() >= 55) {
			base = 100;
		}
		return getStat(StatEnum.CONCENTRATION, base);
	}

	@Override
	public Stat getRootResistance() {
		return getStat(StatEnum.ROOT_RESISTANCE, 0);
	}

	@Override
	public Stat getSnareResistance() {
		return getStat(StatEnum.SNARE_RESISTANCE, 0);
	}

	@Override
	public Stat getBindResistance() {
		return getStat(StatEnum.BIND_RESISTANCE, 0);
	}

	@Override
	public Stat getFearResistance() {
		return getStat(StatEnum.FEAR_RESISTANCE, 0);
	}

	@Override
	public Stat getSleepResistance() {
		return getStat(StatEnum.SLEEP_RESISTANCE, 0);
	}

	@Override
	public Stat getPDef() {
		return getStat(StatEnum.PHYSICAL_DEFENSE, 0);
	}

	@Override
	public Stat getMResist() {
		int base = 0;
		int assassin = owner.getPlayerClass().getClassId();
		if (assassin == 4 && owner.getLevel() >= 37) {
			base = 30;
		}
		return getStat(StatEnum.MAGICAL_RESIST, base);
	}

	@Override
	public Stat getMBResist() {
		int base = 0;
		int cleric = owner.getPlayerClass().getClassId();
		int sorcerer2 = owner.getPlayerClass().getClassId();
		int spiritMaster2 = owner.getPlayerClass().getClassId();
		if (cleric == 10 && owner.getLevel() >= 55) {
			base = 140;
		}
		if (sorcerer2 == 7 && owner.getLevel() >= 55) {
			base = 180;
		}
		if (spiritMaster2 == 8 && owner.getLevel() >= 55) {
			base = 180;
		}
		return getStat(StatEnum.MAGIC_SKILL_BOOST_RESIST, base);
	}

	@Override
	public Stat getMovementSpeed() {
		Stat movementSpeed;
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(),
				owner.getLevel());
		if (owner.isInState(CreatureState.FLYING)) {
			movementSpeed = getStat(StatEnum.FLY_SPEED, Math.round(pst.getFlySpeed() * 1000.0f));
		} else if (owner.isInState(CreatureState.FLIGHT_TELEPORT)) {
			movementSpeed = getStat(StatEnum.SPEED, 12000);
		} else if (owner.isInState(CreatureState.WALKING)) {
			movementSpeed = getStat(StatEnum.SPEED, Math.round(pst.getWalkSpeed() * 1000.0f));
		} else {
			movementSpeed = owner.isInFlyingState()
					? this.getStat(StatEnum.FLY_SPEED, Math.round(pst.getFlySpeed() * 1000.0f))
					: (owner.isInState(CreatureState.FLIGHT_TELEPORT)
							&& !owner.isInState(CreatureState.RESTING)
									? this.getStat(StatEnum.SPEED, 12000)
									: (owner.isInState(CreatureState.WALKING)
											? this.getStat(StatEnum.SPEED, Math.round(pst.getWalkSpeed() * 1000.0f))
											: (this.getAllSpeed().getBonus() != 0
													? this.getStat(StatEnum.SPEED, this.getAllSpeed().getCurrent())
													: this.getStat(StatEnum.SPEED,
															Math.round(pst.getRunSpeed() * 1000.0f)))));
		}
		return movementSpeed;
	}

	@Override
	public Stat getAttackRange() {
		int base = 1500;
		int minWeaponRange = Integer.MAX_VALUE;
		Equipment equipment = owner.getEquipment();
		Item mainHandWeapon = equipment.getMainHandWeapon();
		Item offHandWeapon = equipment.getOffHandWeapon();
		if (mainHandWeapon != null) {
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null && ws.getAttackRange() > 0) {
				minWeaponRange = ws.getAttackRange();
			}
		}
		if (offHandWeapon != null && !equipment.isShieldEquipped() && offHandWeapon.getItemTemplate().isWeapon()) {
			WeaponStats offWs = offHandWeapon.getItemTemplate().getWeaponStats();
			if (offWs != null && offWs.getAttackRange() > 0) {
				minWeaponRange = Math.min(minWeaponRange, offWs.getAttackRange());
			}
		}
		return getStat(StatEnum.ATTACK_RANGE, minWeaponRange == Integer.MAX_VALUE ? base : minWeaponRange);
	}

	@Override
	public Stat getMDef() {
		return getStat(StatEnum.MAGICAL_DEFEND, 0);
	}

	@Override
	public Stat getPower() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), owner.getLevel());
		return getStat(StatEnum.POWER, pst.getPower());
	}

	@Override
	public Stat getHealth() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), owner.getLevel());
		return getStat(StatEnum.HEALTH, pst.getHealth());
	}

	@Override
	public Stat getAccuracy() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), owner.getLevel());
		return getStat(StatEnum.ACCURACY, pst.getAccuracy());
	}

	@Override
	public Stat getAgility() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), owner.getLevel());
		return getStat(StatEnum.AGILITY, pst.getAgility());
	}

	@Override
	public Stat getKnowledge() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), owner.getLevel());
		return getStat(StatEnum.KNOWLEDGE, pst.getKnowledge());
	}

	@Override
	public Stat getWill() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), owner.getLevel());
		return getStat(StatEnum.WILL, pst.getWill());
	}

	@Override
	public Stat getEvasion() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), owner.getLevel());
		return getStat(StatEnum.EVASION, pst.getEvasion());
	}

	@Override
	public Stat getParry() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), owner.getLevel());
		int base = pst.getParry();
		Item mainHandWeapon = owner.getEquipment().getMainHandWeapon();
		if (mainHandWeapon != null) {
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null) {
				base += ws.getParry();
			}
		}
		return getStat(StatEnum.PARRY, base);
	}

	@Override
	public Stat getBlock() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), owner.getLevel());
		return getStat(StatEnum.BLOCK, pst.getBlock());
	}

	private boolean isMagicalWeapon(Item weapon) {
		if (weapon == null || weapon.getItemTemplate() == null) {
			return false;
		}
		ItemAttackType type = weapon.getItemTemplate().getAttackType();
		return type != null && type.isMagical();
	}

	@Override
	public Stat getMainHandPAttack() {
		int base = 18;
		Equipment equipment = owner.getEquipment();
		Item mainHandWeapon = equipment != null ? equipment.getMainHandWeapon() : null;
		if (mainHandWeapon != null && mainHandWeapon.getItemTemplate() != null) {
			if (isMagicalWeapon(mainHandWeapon)) {
				return new AdditionStat(StatEnum.MAIN_HAND_POWER, 0, this.owner);
			}
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null) {
				base = ws.getMeanDamage();
			}
		}
		Stat stat = this.getStat(StatEnum.PHYSICAL_ATTACK, base);
		return this.getStat(StatEnum.MAIN_HAND_POWER, stat);
	}

	public Stat getOffHandPAttack() {
		Item offHandWeapon;
		Equipment equipment = owner.getEquipment();
		if (equipment == null) {
			return new AdditionStat(StatEnum.OFF_HAND_POWER, 0, this.owner);
		}
		Item mainHandWeapon = equipment.getMainHandWeapon();
		if (mainHandWeapon == (offHandWeapon = equipment.getOffHandWeapon())) {
			offHandWeapon = null;
		}
		if (offHandWeapon != null && offHandWeapon.getItemTemplate() != null && offHandWeapon.getItemTemplate().isWeapon()) {
			if (isMagicalWeapon(offHandWeapon)) {
				return new AdditionStat(StatEnum.OFF_HAND_POWER, 0, this.owner);
			}
			WeaponStats ws = offHandWeapon.getItemTemplate().getWeaponStats();
			int base = ws != null ? ws.getMeanDamage() : 0;
			base = (int) ((double) base * 0.98);
			Stat stat = this.getStat(StatEnum.PHYSICAL_ATTACK, base);
			return this.getStat(StatEnum.OFF_HAND_POWER, stat);
		}
		return new AdditionStat(StatEnum.OFF_HAND_POWER, 0, this.owner);
	}

	@Override
	public Stat getMainHandPCritical() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(), (owner.getLevel()));
		int base = pst != null ? pst.getMainHandCritRate() : 10;
		Equipment equipment = owner.getEquipment();
		Item mainHandWeapon = equipment != null ? equipment.getMainHandWeapon() : null;
		if (mainHandWeapon != null && mainHandWeapon.getItemTemplate() != null && !isMagicalWeapon(mainHandWeapon)) {
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null) {
				base = ws.getPhysicalCritical();
			}
		} else if (mainHandWeapon != null && mainHandWeapon.hasEffectiveFusion() && mainHandWeapon.getItemTemplate() != null) {
			WeaponStats ws1 = mainHandWeapon.getItemTemplate().getWeaponStats();
			WeaponStats ws2 = mainHandWeapon.getEffectiveFusionTemplate() != null ? mainHandWeapon.getEffectiveFusionTemplate().getWeaponStats() : null;
			base += (ws1 != null ? ws1.getPhysicalCritical() : 0) + (ws2 != null ? ws2.getPhysicalCritical() : 0);
		}
		return this.getStat(StatEnum.PHYSICAL_CRITICAL, base);
	}

	public Stat getOffHandPCritical() {
		Item offHandWeapon;
		Equipment equipment = owner.getEquipment();
		if (equipment == null) {
			return new AdditionStat(StatEnum.OFF_HAND_CRITICAL, 0, this.owner);
		}
		Item mainHandWeapon = equipment.getMainHandWeapon();
		if (mainHandWeapon == (offHandWeapon = equipment.getOffHandWeapon())) {
			offHandWeapon = null;
		}
		if (offHandWeapon != null && offHandWeapon.getItemTemplate() != null && offHandWeapon.getItemTemplate().isWeapon()
				&& !isMagicalWeapon(offHandWeapon)) {
			WeaponStats ws = offHandWeapon.getItemTemplate().getWeaponStats();
			int base = ws != null ? ws.getPhysicalCritical() : 0;
			return this.getStat(StatEnum.PHYSICAL_CRITICAL, base);
		}
		return new AdditionStat(StatEnum.OFF_HAND_CRITICAL, 0, this.owner);
	}

	@Override
	public Stat getMainHandPAccuracy() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(),
				owner.getLevel());
		int base = pst.getMainHandAccuracy();
		Equipment equipment = owner.getEquipment();
		Item mainHandWeapon = equipment.getMainHandWeapon();
		if (mainHandWeapon != null) {
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null) {
				base += ws.getPhysicalAccuracy();
			}
		}
		return this.getStat(StatEnum.PHYSICAL_ACCURACY, base);
	}

	public Stat getOffHandPAccuracy() {
		Item offHandWeapon;
		Equipment equipment = owner.getEquipment();
		Item mainHandWeapon = equipment.getMainHandWeapon();
		if (mainHandWeapon == (offHandWeapon = equipment.getOffHandWeapon())) {
			offHandWeapon = null;
		}
		if (offHandWeapon != null && offHandWeapon.getItemTemplate().isWeapon()) {
			PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(),
					owner.getLevel());
			int base = pst.getMainHandAccuracy();
			WeaponStats ws = offHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null) {
				base += ws.getPhysicalAccuracy();
			}
			return this.getStat(StatEnum.PHYSICAL_ACCURACY, base);
		}
		return new AdditionStat(StatEnum.OFF_HAND_ACCURACY, 0, this.owner);
	}

	@Override
	public Stat getMAttack() {
		int base;
		Equipment equipment = owner.getEquipment();
		Item mainHandWeapon = equipment != null ? equipment.getMainHandWeapon() : null;
		if (mainHandWeapon != null && mainHandWeapon.getItemTemplate() != null) {
			if (!isMagicalWeapon(mainHandWeapon)) {
				return new AdditionStat(StatEnum.MAGICAL_ATTACK, 0, owner);
			}
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			base = ws != null ? ws.getMeanDamage() : 0;
		} else {
			base = Rnd.get(16, 20);
		}
		return getStat(StatEnum.MAGICAL_ATTACK, base);
	}

	@Override
	public Stat getMainHandMAttack() {
		int base = 0;
		Equipment equipment = owner.getEquipment();
		Item mainHandWeapon = equipment != null ? equipment.getMainHandWeapon() : null;
		if (mainHandWeapon != null && mainHandWeapon.getItemTemplate() != null) {
			if (!isMagicalWeapon(mainHandWeapon)) {
				return new AdditionStat(StatEnum.MAIN_HAND_POWER, 0, this.owner);
			}
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			base = ws != null ? ws.getMeanDamage() : 0;
		}
		Stat stat = this.getStat(StatEnum.MAGICAL_ATTACK, base);
		return this.getStat(StatEnum.MAIN_HAND_POWER, stat);
	}

	@Override
	public Stat getOffHandMAttack() {
		Item offHandWeapon;
		Equipment equipment = owner.getEquipment();
		if (equipment == null) {
			return new AdditionStat(StatEnum.OFF_HAND_POWER, 0, this.owner);
		}
		Item mainHandWeapon = equipment.getMainHandWeapon();
		if (mainHandWeapon == (offHandWeapon = equipment.getOffHandWeapon())) {
			offHandWeapon = null;
		}
		if (offHandWeapon != null && offHandWeapon.getItemTemplate() != null && offHandWeapon.getItemTemplate().isWeapon()) {
			if (!isMagicalWeapon(offHandWeapon)) {
				return new AdditionStat(StatEnum.OFF_HAND_POWER, 0, this.owner);
			}
			WeaponStats ws = offHandWeapon.getItemTemplate().getWeaponStats();
			int base = ws != null ? ws.getMeanDamage() : 0;
			base = (int) ((double) base * 0.98);
			Stat stat = this.getStat(StatEnum.MAGICAL_ATTACK, base);
			return this.getStat(StatEnum.OFF_HAND_POWER, stat);
		}
		return new AdditionStat(StatEnum.OFF_HAND_POWER, 0, this.owner);
	}

	@Override
	public Stat getMBoost() {
		int base = 0;
		Equipment equipment = owner.getEquipment();
		Item mainHandWeapon = equipment != null ? equipment.getMainHandWeapon() : null;
		if (mainHandWeapon != null && mainHandWeapon.getItemTemplate() != null) {
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null) {
				base += ws.getBoostMagicalSkill();
			}
		}
		return this.getStat(StatEnum.BOOST_MAGICAL_SKILL, base);
	}

	@Override
	public Stat getMAccuracy() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(owner.getPlayerClass(),
				owner.getLevel());
		int base = pst != null ? pst.getMagicAccuracy() : 0;
		Equipment equipment = owner.getEquipment();
		Item mainHandWeapon = equipment != null ? equipment.getMainHandWeapon() : null;
		if (mainHandWeapon != null && mainHandWeapon.getItemTemplate() != null) {
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null) {
				base += ws.getMagicalAccuracy();
			}
		}
		return this.getStat(StatEnum.MAGICAL_ACCURACY, base);
	}

	public Stat getMainHandMAccuracy() {
		PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(this.owner.getPlayerClass(),
				this.owner.getLevel());
		int base = pst != null ? pst.getMagicAccuracy() : 0;
		Equipment equipment = this.owner.getEquipment();
		Item mainHandWeapon = equipment != null ? equipment.getMainHandWeapon() : null;
		if (mainHandWeapon != null && mainHandWeapon.getItemTemplate() != null) {
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null) {
				base += ws.getMagicalAccuracy();
			}
		}
		Stat stat = getStat(StatEnum.MAGICAL_ACCURACY, base);
		int HAGI = this.owner.getGameStats().getStat(StatEnum.AGILITY, 0).getCurrent();
		int MAccuracyCalculation = Math.round(2286 * HAGI / (376.0F + HAGI));
		stat.addToBonus(MAccuracyCalculation);
		return stat;
	}

	public Stat getOffHandMAccuracy() {
		Equipment equipment = this.owner.getEquipment();
		if (equipment == null) {
			return new AdditionStat(StatEnum.OFF_HAND_MAGICAL_ACCURACY, 0, this.owner);
		}
		Item offHandWeapon = equipment.getOffHandWeapon();
		if ((offHandWeapon != null) && (offHandWeapon.getItemTemplate() != null) && (offHandWeapon.getItemTemplate().isWeapon())
				&& (!offHandWeapon.getItemTemplate().isTwoHandWeapon())) {
			PlayerStatsTemplate pst = DataManager.PLAYER_STATS_DATA.getTemplate(this.owner.getPlayerClass(),
					this.owner.getLevel());
			int base = pst != null ? pst.getMagicAccuracy() : 0;
			WeaponStats ws = offHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null) {
				base += ws.getMagicalAccuracy();
			}
			return getStat(StatEnum.MAGICAL_ACCURACY, base);
		}
		return new AdditionStat(StatEnum.OFF_HAND_MAGICAL_ACCURACY, 0, this.owner);
	}

	@Override
	public Stat getMCritical() {
		int base = 50;
		Equipment equipment = owner.getEquipment();
		Item mainHandWeapon = equipment != null ? equipment.getMainHandWeapon() : null;
		if (mainHandWeapon != null && isMagicalWeapon(mainHandWeapon) && mainHandWeapon.getItemTemplate() != null) {
			WeaponStats ws = mainHandWeapon.getItemTemplate().getWeaponStats();
			if (ws != null) {
				base += ws.getPhysicalCritical();
			}
		}
		return this.getStat(StatEnum.MAGICAL_CRITICAL, base);
	}

	@Override
	public Stat getHpRegenRate() {
		int base = owner.getLevel() + 3;
		if (owner.isInState(CreatureState.RESTING)) {
			base *= 8;
		}
		base *= getHealth().getCurrent() / 100f;
		return getStat(StatEnum.REGEN_HP, base);
	}

	@Override
	public Stat getMpRegenRate() {
		int base = owner.getLevel() + 8;
		if (owner.isInState(CreatureState.RESTING)) {
			base *= 8;
		}
		base *= getWill().getCurrent() / 100f;
		return getStat(StatEnum.REGEN_MP, base);
	}

	@Override
	public void updateStatInfo() {
		PacketSendUtility.sendPacket(owner, new S_STATUS(owner));
	}

	@Override
	public void updateSpeedInfo() {
		PacketSendUtility.broadcastPacket(owner, new S_ACTION(owner, EmotionType.START_EMOTE2, 0, 0), true);
	}
}