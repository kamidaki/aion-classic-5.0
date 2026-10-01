package com.aionemu.gameserver.model.templates.item;

import java.util.List;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.*;
import javax.xml.bind.annotation.adapters.XmlJavaTypeAdapter;

import com.aionemu.gameserver.configs.main.CustomConfig;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.loadingutils.adapters.SpaceSeparatedBytesAdapter;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.items.ItemId;
import com.aionemu.gameserver.model.items.ItemMask;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.templates.VisibleObjectTemplate;
import com.aionemu.gameserver.model.templates.item.actions.ItemActions;
import com.aionemu.gameserver.model.templates.item.enums.ArmorType;
import com.aionemu.gameserver.model.templates.item.enums.EquipType;
import com.aionemu.gameserver.model.templates.item.enums.ItemGroup;
import com.aionemu.gameserver.model.templates.item.enums.ItemSubType;
import com.aionemu.gameserver.model.templates.itemset.ItemSetTemplate;
import com.aionemu.gameserver.model.templates.stats.ModifiersTemplate;
import com.aionemu.gameserver.world.zone.ZoneName;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.NONE)
@XmlType(namespace = "", name = "ItemTemplate")
public class ItemTemplate extends VisibleObjectTemplate {

	private static final byte[] DEFAULT_LEVEL_RESTRICTION;
	static {
		DEFAULT_LEVEL_RESTRICTION = new byte[com.aionemu.gameserver.model.PlayerClass.values().length];
		java.util.Arrays.fill(DEFAULT_LEVEL_RESTRICTION, (byte) 1);
	}

	private int itemId;
	@XmlElement(name = "modifiers")
	private ModifiersTemplate modifiers;
	@XmlElement(name = "actions")
	private ItemActions actions;
	@XmlAttribute(name = "mask")
	private int mask;
	@XmlAttribute(name = "client_mask", required = true)
	private int clientMask;

	public int getClientMask() { return clientMask; }
	@XmlAttribute(name = "weapon_boost")
	private int weaponBoost;
	@XmlAttribute(name = "price")
	private int price;
	@XmlAttribute(name = "max_stack_count")
	private int maxStackCount = 1;
	@XmlAttribute(name = "item_group")
	private ItemGroup itemGroup = ItemGroup.NONE;
	@XmlAttribute(name = "combat_power")
	private int combatPower;
	@XmlAttribute(name = "enchant_group")
	private String enchantGroup;
	@XmlAttribute(name = "enchant_essence")
	private boolean enchantEssence;

	public int getCombatPower() { return combatPower; }
	public String getEnchantGroup() { return enchantGroup; }
	public boolean isEnchantEssence() { return enchantEssence; }
	@XmlAttribute(name = "pack_count")
	private int packCount;
	@XmlAttribute(name = "level")
	private int level;
	@XmlAttribute(name = "quality")
	private ItemQuality itemQuality;
	@XmlAttribute(name = "item_type")
	private ItemType itemType = ItemType.NORMAL;
	@XmlAttribute(name = "attack_type")
	private ItemAttackType attackType;
	@XmlAttribute(name = "attack_gap")
	private float attackGap;
	@XmlAttribute(name = "desc")
	private int description;
	@XmlAttribute(name = "option_slot_bonus")
	private int optionSlotBonus;
	@XmlAttribute(name = "rnd_bonus")
	private int rndBonusId = 0;
	@XmlAttribute(name = "rnd_count")
	private int maxTuneCount = -1;
	@XmlAttribute(name = "race")
	private Race race = Race.PC_ALL;
	@XmlAttribute(name = "return_world")
	private int returnWorldId;
	@XmlAttribute(name = "return_alias")
	private String returnAlias;
	@XmlElement(name = "godstone")
	private GodstoneInfo godstoneInfo;
	@XmlElement(name = "stigma")
	private Stigma stigma;
	@XmlAttribute(name = "name_en")
	private String nameEn;
	@XmlAttribute(name = "name_pt")
	private String namePt;
	@Deprecated
	@XmlAttribute(name = "name")
	private String name;
	@XmlJavaTypeAdapter(SpaceSeparatedBytesAdapter.class)
	@XmlAttribute(name = "restrict")
	private byte[] levelRestrictions = DEFAULT_LEVEL_RESTRICTION;
	@XmlJavaTypeAdapter(SpaceSeparatedBytesAdapter.class)
	@XmlAttribute(name = "restrict_max")
	private byte[] maxLevelRestrictions;
	@XmlAttribute(name = "m_slots")
	private int manastoneSlots;
	@XmlAttribute(name = "s_slots")
	private int specialSlots;
	@XmlAttribute(name = "max_enchant")
	private int maxEnchant;
	@XmlAttribute(name = "max_enchant_bonus")
	private int maxEnchantBonus;
	@XmlAttribute(name = "enchant_type")
	private int enchantType;
	@XmlAttribute(name = "max_tampering")
	private int maxTampering;
	@XmlAttribute(name = "casting_delay")
	private int castingDelay;
	@XmlAttribute(name = "temp_exchange_time")
	private int temExchangeTime;
	@XmlAttribute(name = "expire_time")
	private int expireTime;
	@XmlElement(name = "weapon_stats")
	private WeaponStats weaponStats;
	@XmlAttribute(name = "activate_target")
	private ItemActivationTarget activationTarget;
	@XmlAttribute(name = "tempering_name")
	private String temperingName;
	@XmlAttribute(name = "enchant_name")
	private String enchantName;
	@XmlAttribute(name = "activate_count")
	private int activationCount;
	@XmlAttribute(name = "activate_combat")
	private boolean activateCombat;
	@XmlAttribute(name = "self_resurrect")
	private boolean selfResurrect;
	@XmlAttribute(name = "robot")
	private Integer robotId;
	@XmlElement(name = "tradein_list")
	private TradeinList tradeinList;
	@XmlElement(name = "acquisition")
	private Acquisition acquisition;
	@XmlElement(name = "disposition")
	private Disposition disposition;
	@XmlElement(name = "improve")
	private Improvement improvement;
	@XmlElement(name = "uselimits")
	private ItemUseLimits useLimits;
	@XmlElement(name = "inventory")
	private ExtraInventory extraInventory;
	@XmlElement(name = "idian")
	private Idian idianAction;
	@XmlAttribute(name = "can_exceed_enchant")
	private boolean canExceedEnchant;
	@XmlAttribute(name = "exceed_enchant_skill")
	private ExceedEnchantSkillSetType exceedEnchantSkill;

	private static final WeaponStats emptyWeaponStats = new WeaponStats();
	private static final ItemUseLimits emptyUseLimits = new ItemUseLimits();

	@XmlID
	@XmlAttribute(name = "id", required = true)
	private void setXmlUid(String uid) {
		itemId = Integer.parseInt(uid);
	}

	void afterUnmarshal(Unmarshaller u, Object parent) {
		if (itemGroup == null)
			itemGroup = ItemGroup.NONE;
		if (weaponStats == null)
			weaponStats = emptyWeaponStats;
		if (useLimits == null)
			useLimits = emptyUseLimits;

		int classCount = PlayerClass.values().length;
		if (levelRestrictions != null && levelRestrictions.length < classCount) {
			byte[] newRestr = new byte[classCount];
			System.arraycopy(levelRestrictions, 0, newRestr, 0, levelRestrictions.length);
			boolean allNonZero = true;
			byte minVal = 0;
			for (byte b : levelRestrictions) {
				if (b == 0) {
					allNonZero = false;
					break;
				}
				if (minVal == 0 || (b & 0xFF) < (minVal & 0xFF)) {
					minVal = b;
				}
			}
			if (allNonZero && minVal > 0) {
				for (int i = levelRestrictions.length; i < classCount; i++) {
					newRestr[i] = minVal;
				}
			}
			levelRestrictions = newRestr;
		}

		if (maxLevelRestrictions != null && maxLevelRestrictions.length < classCount) {
			byte[] newMax = new byte[classCount];
			System.arraycopy(maxLevelRestrictions, 0, newMax, 0, maxLevelRestrictions.length);
			boolean allNonZero = true;
			byte maxVal = 0;
			for (byte b : maxLevelRestrictions) {
				if (b == 0) {
					allNonZero = false;
					break;
				}
				if (maxVal == 0 || (b & 0xFF) > (maxVal & 0xFF)) {
					maxVal = b;
				}
			}
			if (allNonZero && maxVal > 0) {
				for (int i = maxLevelRestrictions.length; i < classCount; i++) {
					newMax[i] = maxVal;
				}
			}
			maxLevelRestrictions = newMax;
		}

		// check if it can be randomized
		if (getItemSlot() == 0)
			maxTuneCount = 0;
		else if (maxTuneCount == -1) {
			if (maxEnchantBonus == 0 && optionSlotBonus == 0 && rndBonusId == 0)
				maxTuneCount = 0;
		}
	}

	public int getMask() {
		return mask;
	}

	public long getItemSlot() {
		return itemGroup != null ? itemGroup.getValidEquipmentSlots() : 0L;
	}

	public boolean isClassSpecific(PlayerClass playerClass) {
		int ord = playerClass.ordinal();
		boolean related = ord < levelRestrictions.length && levelRestrictions[ord] > 0;
		if (!related && playerClass.getStartingClass() != playerClass) {
			int startOrd = playerClass.getStartingClass().ordinal();
			related = startOrd < levelRestrictions.length && levelRestrictions[startOrd] > 0;
		}
		return related;
	}

	public int getRequiredLevel(PlayerClass playerClass) {
		int ord = playerClass.ordinal();
		int requiredLevel = ord < levelRestrictions.length ? (levelRestrictions[ord] & 0xFF) : 0;
		if (requiredLevel == 0 && playerClass.getStartingClass() != playerClass) {
			int startOrd = playerClass.getStartingClass().ordinal();
			requiredLevel = startOrd < levelRestrictions.length ? (levelRestrictions[startOrd] & 0xFF) : 0;
		}
		return requiredLevel == 0 ? -1 : requiredLevel;
	}

	public byte getMaxLevelRestrict(PlayerClass playerClass) {
		if (maxLevelRestrictions != null) {
			int ord = playerClass.ordinal();
			byte max = ord < maxLevelRestrictions.length ? maxLevelRestrictions[ord] : 0;
			if (max == 0 && playerClass.getStartingClass() != playerClass) {
				int startOrd = playerClass.getStartingClass().ordinal();
				max = startOrd < maxLevelRestrictions.length ? maxLevelRestrictions[startOrd] : 0;
			}
			return max;
		}
		return 0;
	}

	public List<StatFunction> getModifiers() {
		if (modifiers != null) {
			return modifiers.getModifiers();
		}
		return null;
	}

	public ItemActions getActions() {
		return actions;
	}

	public ItemSubType getItemSubType() {
		return itemGroup != null ? itemGroup.getItemSubType() : ItemSubType.NONE;
	}

	public EquipType getEquipmentType() {
		return itemGroup != null ? itemGroup.getEquipType() : EquipType.NONE;
	}

	public long getPrice() {
		return price;
	}

	public int getLevel() {
		return level;
	}

	public ItemQuality getItemQuality() {
		return itemQuality;
	}

	public ItemType getItemType() {
		return itemType;
	}

	@Override
	public int getL10nId() {
		return description;
	}

	public int getNameId() {
		return description;
	}

	public long getMaxStackCount() {
		if (isKinah()) {
			if (CustomConfig.ENABLE_KINAH_CAP) {
				return CustomConfig.KINAH_CAP_VALUE;
			} else {
				return Long.MAX_VALUE;
			}
		}
		return maxStackCount;
	}

	public ItemAttackType getAttackType() {
		return attackType;
	}

	public float getAttackGap() {
		return attackGap;
	}

	public int getOptionSlotBonus() {
		return optionSlotBonus;
	}

	public boolean isNoEnchant() {
		return (getMask() & ItemMask.NO_ENCHANT) == ItemMask.NO_ENCHANT;
	}

	public boolean isItemDyePermitted() {
		return (getMask() & ItemMask.DYEABLE) == ItemMask.DYEABLE;
	}

	public Race getRace() {
		return race;
	}

	public int getWeaponBoost() {
		return weaponBoost;
	}

	public boolean isWeapon() {
		return getEquipmentType() == EquipType.WEAPON;
	}

	public boolean isArmor() {
		return getEquipmentType() == EquipType.ARMOR;
	}

	public boolean isKinah() {
		return itemId == ItemId.KINAH;
	}

	public boolean isStigma() {
		return stigma != null;
	}

	public boolean isGreaterStigma() {
		return stigma != null && stigma.getKind() == Stigma.StigmaKind.GREATER;
	}

	public int getCastingDelay() {
		return castingDelay;
	}

	/**
	 * @return id of the associated ItemSetTemplate or null if none
	 */
	public ItemSetTemplate getItemSet() {
		return DataManager.ITEM_SET_DATA.getItemSetTemplateByItemId(itemId);
	}

	/**
	 * Checks if the ItemTemplate belongs to an item set
	 */
	public boolean isItemSet() {
		return getItemSet() != null;
	}

	public GodstoneInfo getGodstoneInfo() {
		return godstoneInfo;
	}

	@Override
	public String getName() {
		if (namePt != null && !namePt.isEmpty()) {
			return namePt;
		}
		if (name != null && !name.isEmpty()) {
			return name;
		}
		return nameEn == null ? "" : nameEn;
	}

	@Override
	public String getNameEn() {
		if (nameEn != null && !nameEn.isEmpty()) {
			return nameEn;
		}
		if (name != null && !name.isEmpty()) {
			return name;
		}
		return namePt == null ? "" : namePt;
	}

	@Override
	public int getTemplateId() {
		return itemId;
	}

	public int getReturnWorldId() {
		return returnWorldId;
	}

	public String getReturnAlias() {
		return returnAlias;
	}

	public Stigma getStigma() {
		return stigma;
	}

	public int getManastoneSlots() {
		return manastoneSlots;
	}

	public int getSpecialSlots() {
		return specialSlots;
	}

	public int getMaxEnchantLevel() {
		return maxEnchant;
	}

	public int getMaxEnchantBonus() {
		return maxEnchantBonus;
	}

	public boolean hasLimitOne() {
		return (getMask() & ItemMask.LIMIT_ONE) == ItemMask.LIMIT_ONE;
	}

	public boolean isTradeable() {
		return (getMask() & ItemMask.TRADEABLE) == ItemMask.TRADEABLE;
	}

	public boolean isCanFuse() {
		return (getMask() & ItemMask.CAN_COMPOSITE_WEAPON) == ItemMask.CAN_COMPOSITE_WEAPON;
	}

	public boolean canSplit() {
		return (getMask() & ItemMask.CAN_SPLIT) == ItemMask.CAN_SPLIT;
	}

	public boolean isSoulBound() {
		return (getMask() & ItemMask.SOUL_BOUND) == ItemMask.SOUL_BOUND;
	}

	public boolean isBreakable() {
		return (getMask() & ItemMask.BREAKABLE) == ItemMask.BREAKABLE;
	}

	public boolean isDeletable() {
		return (getMask() & ItemMask.DELETABLE) == ItemMask.DELETABLE;
	}

	public boolean isCanPolish() {
		return (getMask() & ItemMask.CAN_POLISH) == ItemMask.CAN_POLISH;
	}

	public boolean isTwoHandWeapon() {
		if (!isWeapon())
			return false;
		return getItemSubType() == ItemSubType.TWO_HAND;
	}
	
	public boolean isOneHandWeapon() {
		if (!isWeapon())
			return false;
		return getItemSubType() == ItemSubType.ONE_HAND;
	}

	public int getTempExchangeTime() {
		return temExchangeTime;
	}

	public int getEnchantType() {
		return enchantType;
	}

	public int getExpireTime() {
		return expireTime;
	}

	public final WeaponStats getWeaponStats() {
		return weaponStats;
	}

	public int getActivationCount() {
		return activationCount;
	}

	/**
	 * -1 if no id, can be values 0, 1, 2
	 */
	public int getExtraInventoryId() {
		if (extraInventory == null) {
			return -1;
		}
		return extraInventory.getId();
	}

	public void modifyMask(boolean apply, int filter) {
		if (apply)
			mask |= filter;
		else
			mask &= ~filter;
	}

	public boolean isStackable() {
		return this.maxStackCount > 1;
	}

	public boolean hasAreaRestriction() {
		return useLimits.getUseArea() != null;
	}

	public ZoneName getUseArea() {
		return useLimits.getUseArea();
	}

	/**
	 * @return the tradeinList
	 */
	public TradeinList getTradeinList() {
		return tradeinList;
	}

	/**
	 * @return the acquisition
	 */
	public Acquisition getAcquisition() {
		return acquisition;
	}

	/**
	 * @return the rndBonusId, 0 if no bonus exists
	 */
	public int getStatBonusSetId() {
		return rndBonusId;
	}

	/**
	 * @return the maxTuneCount, 0 if can not be randomized
	 */
	public int getMaxTuneCount() {
		return maxTuneCount;
	}

	public boolean canTune() {
		return maxTuneCount != 0;
	}

	/**
	 * @return the conditioning
	 */
	public Improvement getImprovement() {
		return improvement;
	}

	/**
	 * @return the useLimits
	 */
	public ItemUseLimits getUseLimits() {
		return useLimits;
	}

	public Disposition getDisposition() {
		return disposition;
	}

	public boolean hasWorldRestrictions() {
		return !useLimits.getOwnershipWorldIds().isEmpty();
	}

	public boolean isItemRestrictedToWorld(int worldId) {
		List<Integer> ownershipWorldIds = useLimits.getOwnershipWorldIds();
		if (ownershipWorldIds.isEmpty())
			return false;
		return ownershipWorldIds.contains(worldId);
	}

	public boolean isCloth() {
		// not sure about LT_HEAD and CL_HEAD, check in retail
		return isArmor() && (getItemGroup().getArmorType() != ArmorType.ACCESSORY && getItemGroup() != ItemGroup.BELT || getItemGroup() == ItemGroup.HEAD);
	}

	public boolean isPotion() {
		return itemId >= 162000000 && itemId < 163000000;
	}

	public Idian getIdianAction() {
		return idianAction;
	}

	public boolean isCombinationItem() {
		return getItemGroup() == ItemGroup.COMBINATION;
	}

	public boolean isEnchantmentStone() {
		return getItemGroup() == ItemGroup.ENCHANTMENT;
	}

	public ItemActivationTarget getActivationTarget() {
		if (getActivationRace() == null)
			return activationTarget;
		return null;
	}

	public Race getActivationRace() {
		return activationTarget == null ? null : activationTarget.getRace();
	}

	public boolean isCombatActivated() {
		return activateCombat;
	}

	/**
	 * @return true para as pedras que ressuscitam o próprio dono morto pelo C_DEAD_RESTART tipo 2 (mgrouptag I_RESURRECT do cliente)
	 */
	public boolean isSelfResurrect() {
		return selfResurrect;
	}

	public Integer getRobotId() {
		if (robotId == null)
			return 0;
		return robotId;
	}

	public int getPackCount() {
		return packCount;
	}

	public int getMaxTampering() {
		return maxTampering;
	}

	public ItemGroup getItemGroup() {
		return itemGroup == null ? ItemGroup.NONE : itemGroup;
	}

	public int[] getRequiredSkills() {
		return itemGroup != null ? itemGroup.getRequiredSkills() : new int[0];
	}

	public String getTemperingName() { return null; }

	public String getEnchantName() {
		return enchantName;
	}

	public boolean canExceedEnchant() {
		return canExceedEnchant;
	}

	public ExceedEnchantSkillSetType getExceedEnchantSkill() {
		return exceedEnchantSkill;
	}

}
