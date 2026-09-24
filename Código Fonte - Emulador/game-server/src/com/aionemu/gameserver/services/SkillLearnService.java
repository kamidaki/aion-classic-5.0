package com.aionemu.gameserver.services;

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.animations.ActionAnimation;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.skill.PlayerSkillEntry;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ACTION_ANIMATION;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SKILL_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SKILL_REMOVE;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.SkillLearnTemplate;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * @author Lost Academy Team & Durak
 */
public class SkillLearnService {

	private static final Logger log = LoggerFactory.getLogger(SkillLearnService.class);
	private static final ThreadLocal<Boolean> syncingBlendedSkills = ThreadLocal.withInitial(() -> false);

	public static void onLearnSkill(Player player, int skillId, int skillLevel, boolean isNew) {
		PlayerSkillEntry skill = player.getSkillList().getSkillEntry(skillId);
		if (skill.isProfessionSkill())
			switch (skillLevel) {
				case 1, 100, 200, 300, 400, 450, 500 -> {
					if (skillLevel != 1 || skill.isCraftingSkill()) // exclude lvl 1 tapping skills
						PacketSendUtility.broadcastPacket(player, new SM_ACTION_ANIMATION(player.getObjectId(), ActionAnimation.CRAFT_LEVEL_UP), true);
				}
			}
		if (player.getEffectController() != null) { // null on character creation
			if (player.isSpawned())
				sendPacket(player, skill, isNew);
			SkillTemplate skillTemplate = DataManager.SKILL_DATA.getSkillTemplate(skillId);
			if (skillTemplate.isPassive()) {
				try {
					SkillEngine.getInstance().applyEffectDirectly(skillTemplate, skillLevel, player, player);
				} catch (RuntimeException e) {
					// passiva com template quebrado não pode impedir o login (que ensina as automáticas que faltam) nem a subida de nível
					log.error("Could not apply passive skill " + skillId + " to " + player, e);
				}
			}
			if (skill.isProfessionSkill() && (skill.getSkillLevel() == 399 || skill.getSkillLevel() == 499))
				player.getController().updateNearbyQuests();
		}
		if (skill.isCraftingSkill() || skill.isMorphSkill())
			RecipeService.autoLearnRecipes(player, skillId, skillLevel);
		syncBlendedSkills(player);
	}

	private static void sendPacket(Player player, PlayerSkillEntry skill, boolean isNew) {
		if (skill.isProfessionSkill()) {
			if (skill.isTappingSkill())
				PacketSendUtility.sendPacket(player, new SM_SKILL_LIST(skill, isNew ? 1330004 : 1330005));
			else
				PacketSendUtility.sendPacket(player, new SM_SKILL_LIST(skill, isNew ? 1330061 : 1330064));
		} else if (isNew)
			PacketSendUtility.sendPacket(player,
				new SM_SKILL_LIST(skill, skill.isStigmaSkill() ? 1300401 : 1300050));
		else
			PacketSendUtility.sendPacket(player, new SM_SKILL_LIST(skill, 0));
	}

	/**
	 * Adds all missing skills and recipes that can be auto-learned for the given level range.
	 */
	public static void learnNewSkills(Player player, int fromLevel, int toLevel) {
		PlayerClass playerClass = player.getCommonData().getPlayerClass();
		PlayerClass playerStartClass = playerClass.getStartingClass() != playerClass ? playerClass.getStartingClass() : null;
		for (int level = toLevel; level >= fromLevel; level--) { // reversed order to add only the highest of each skill (more efficient)
			if (level < 10 && playerStartClass != null) // add missing start class skills if already switched class
				autoLearnSkills(player, level, playerStartClass, player.getRace());
			autoLearnSkills(player, level, playerClass, player.getRace());
		}

		// upgrade human gathering to daeva essence tapping
		if (toLevel >= 10 && player.getCommonData().isDaeva() && player.getSkillList().isSkillPresent(30001)) {
			if (!player.getSkillList().isSkillPresent(30002))
				player.getSkillList().addSkill(player, 30002, player.getSkillList().getSkillLevel(30001));
			removeSkill(player, 30001);
		}
		syncBlendedSkills(player);
	}

	public static void learnTemporarySkill(Player player, int skillId, int skillLevel) {
		player.getSkillList().addTemporarySkill(player, skillId, skillLevel);
	}

	/**
	 * Adds auto-learned skills to the player, according to the specified level, class and race.
	 */
	private static void autoLearnSkills(Player player, int level, PlayerClass playerClass, Race playerRace) {
		for (SkillLearnTemplate template : DataManager.SKILL_TREE_DATA.getTemplatesFor(playerClass, level, playerRace)) {
			if (!template.isAutolearn())
				continue;
			if (template.getSkillId() == 30001 && player.getCommonData().isDaeva()) // no human gathering for daevas
				continue;

			player.getSkillList().addSkill(player, template.getSkillId(), template.getSkillLevel());
		}
	}

	public static boolean learnSkillBook(Player player, int skillId) {
		return learnSkillBook(player, skillId, 1);
	}

	public static boolean learnSkillBook(Player player, int skillId, int fallbackSkillLevel) {
		List<SkillLearnTemplate> skills = DataManager.SKILL_TREE_DATA.getSkillsForSkill(skillId, player.getPlayerClass(), player.getRace(),
			player.getLevel());
		boolean learned = false;
		if (skills != null && !skills.isEmpty()) {
			for (SkillLearnTemplate skill : skills) {
				if (player.getSkillList().addSkill(player, skillId, skill.getSkillLevel()))
					learned = true;
			}
		} else {
			int lvl = fallbackSkillLevel > 0 ? fallbackSkillLevel : 1;
			learned = player.getSkillList().addSkill(player, skillId, lvl);
		}
		return learned;
	}

	public static boolean removeSkill(Player player, int skillId) {
		PlayerSkillEntry skill = player.getSkillList().getSkillEntry(skillId);
		if (skill != null) {
			SkillTemplate skillTemplate = DataManager.SKILL_DATA.getSkillTemplate(skillId);
			if (skillTemplate.isPassive() || skillTemplate.isToggle() || skillTemplate.isDeityAvatar() || skillTemplate.getStack().startsWith("WS_"))
				player.getEffectController().removeEffect(skillId);
			player.getSkillList().removeSkill(skillId);
			PacketSendUtility.sendPacket(player, new SM_SKILL_REMOVE(skill));
			syncBlendedSkills(player);
			return true;
		}
		return false;
	}

	private static void syncBlendedSkills(Player player) {
		if (syncingBlendedSkills.get())
			return;
		syncingBlendedSkills.set(true);
		try {
			for (SkillLearnTemplate template : DataManager.SKILL_TREE_DATA.getBlendedSkillsFor(player.getPlayerClass(), player.getRace())) {
				boolean shouldKnow = template.hasBlendingSources(player.getSkillList());
				boolean knows = player.getSkillList().isSkillPresent(template.getSkillId());
				if (shouldKnow && !knows)
					learnTemporarySkill(player, template.getSkillId(), template.getSkillLevel());
				else if (!shouldKnow && knows)
					removeSkill(player, template.getSkillId());
			}
		} finally {
			syncingBlendedSkills.remove();
		}
	}
}
