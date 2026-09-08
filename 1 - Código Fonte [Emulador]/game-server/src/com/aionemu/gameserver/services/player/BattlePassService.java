package com.aionemu.gameserver.services.player;

import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dao.PlayerBattlePassDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattlePassQuest;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattlePassReward;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattlePassSeason;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattleQuestState;
import com.aionemu.gameserver.model.templates.battle_pass.*;
import com.aionemu.gameserver.network.aion.serverpackets.*;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.idfactory.IDFactory;

public class BattlePassService {

	private static final Logger log = LoggerFactory.getLogger(BattlePassService.class);

	private final List<BattlePassSeasonTemplate> season = new CopyOnWriteArrayList<>();
	private final Map<Integer, List<BattlePassQuestTemplate>> seasonQuest = new ConcurrentHashMap<>();

	private Timestamp start;
	private Timestamp end;
	private Timestamp endWeekly;

	public void init() {
		initBattlePass();
		initResetTime();
		log.info("BattlePassService initialized.");
	}

	public void initBattlePass() {
		long now = System.currentTimeMillis();
		DataManager.BATTLE_PASS_DATA.getAllTemplate().forEach((template) -> {
			if (template.getStartDate().getTime() <= now && template.getEndDate().getTime() >= now) {
				season.add(template);
			}
		});
		DataManager.BATTLE_PASS_QUEST_DATA.getAllTemplate().forEach((template) -> {
			this.season.forEach((s) -> {
				if (s.getId() == template.getPassId()) {
					seasonQuest.computeIfAbsent(s.getId(), k -> new ArrayList<>()).add(template);
				}
			});
		});
	}

	public void onEnterWorld(Player player) {
		player.getPlayerBattlePass().setBattlePassQuest(PlayerBattlePassDAO.loadPlayerBattleQuest(player));
		player.getPlayerBattlePass().setBattlePassSeason(PlayerBattlePassDAO.loadPlayerBattlePass(player));
		this.season.forEach((s) -> {
			if (!player.getPlayerBattlePass().getBattlePassSeason().containsKey(s.getId())) {
				addSeasonToPlayer(player, s.getId());
			}
			List<BattlePassQuestTemplate> quests = this.seasonQuest.get(s.getId());
			if (quests != null) {
				quests.forEach((q) -> {
					if (!player.getPlayerBattlePass().haveQuest(q.getId())) {
						Timestamp endQuest;
						if (q.getType() == BattleQuestType.DAILY) {
							endQuest = this.end;
						} else if (q.getType() == BattleQuestType.WEEKLY) {
							endQuest = this.endWeekly;
						} else {
							endQuest = s.getEndDate();
						}
						BattlePassQuest battlePassQuest = new BattlePassQuest(IDFactory.getInstance().nextId(), q.getId(), q.getType(), BattleQuestState.START, 0, this.start, endQuest);
						if (q.getRace() == Race.PC_ALL || q.getRace() == player.getRace()) {
							player.getPlayerBattlePass().getBattlePassQuest().put(battlePassQuest.getObjectId(), battlePassQuest);
							PlayerBattlePassDAO.storeQuest(player, battlePassQuest);
						}
					}
				});
			}
		});
		PacketSendUtility.sendPacket(player, new S_CLEAR_ACHIEVEMENT_EVENT());
		PacketSendUtility.sendPacket(player, new S_CREATE_ACHIEVEMENT_EVENT(player));
		PacketSendUtility.sendPacket(player, new S_BATTLEPASS_LIST(player));
	}

	public void onUpdateBattlePassMission(Player player, int value, int count, BattlePassAction type) {
		if (player == null || player.getPlayerBattlePass() == null) {
			return;
		}
		List<BattlePassQuest> questUpdateList = new ArrayList<>();
		List<BattlePassQuest> questFinishList = new ArrayList<>();
		player.getPlayerBattlePass().getBattlePassQuest().forEach((id, quest) -> {
			if (quest.getActionTemplate() != null && quest.getActionTemplate().getType() == type && quest.getState() == BattleQuestState.START) {
				int progress = quest.getStep() + count;
				questUpdateList.add(quest);
				if (quest.getActionTemplate().getRequired() != null && quest.getActionTemplate().getRequired().getType() == ActionRequiredType.SPECIFIC) {
					if (quest.getActionTemplate().getRequired().getValues().contains(value)) {
						quest.setStep(progress);
					}
				} else {
					quest.setStep(progress);
				}
				if (quest.getStep() >= quest.getActionTemplate().getCount()) {
					quest.setStep(quest.getActionTemplate().getCount());
					questFinishList.add(quest);
				} else {
					PlayerBattlePassDAO.updateQuest(player, quest);
				}
			}
		});
		if (!questUpdateList.isEmpty()) {
			PacketSendUtility.sendPacket(player, new S_PROGRESS_ACHIEVEMENT(questUpdateList));
		}
		if (!questFinishList.isEmpty()) {
			onFinishQuest(player, questFinishList);
		}
	}

	public void onEnchant(Player player, int enchantLevel) {
		if (player == null || player.getPlayerBattlePass() == null) {
			return;
		}
		List<BattlePassQuest> questFinishList = new ArrayList<>();
		player.getPlayerBattlePass().getBattlePassQuest().forEach((id, quest) -> {
			if (quest.getActionTemplate() != null && quest.getActionTemplate().getType() == BattlePassAction.SUCCESS_ENCHANT && quest.getState() == BattleQuestState.START) {
				if (quest.getActionTemplate().getEnchant() != null && enchantLevel >= quest.getActionTemplate().getEnchant().getLevel()) {
					quest.setStep(quest.getActionTemplate().getCount());
					questFinishList.add(quest);
				}
			}
		});
		if (!questFinishList.isEmpty()) {
			onFinishQuest(player, questFinishList);
		}
	}

	public void onWinAp(Player player, int ap) {
		if (player == null || player.getPlayerBattlePass() == null) {
			return;
		}
		List<BattlePassQuest> questFinishList = new ArrayList<>();
		List<BattlePassQuest> questUpdateList = new ArrayList<>();
		player.getPlayerBattlePass().getBattlePassQuest().forEach((id, quest) -> {
			if (quest.getActionTemplate() != null && quest.getActionTemplate().getType() == BattlePassAction.CHANGE_AP && quest.getState() == BattleQuestState.START) {
				int newValue = ap + quest.getStep();
				quest.setStep(newValue);
				if (quest.getStep() >= quest.getActionTemplate().getCount()) {
					questFinishList.add(quest);
				} else {
					questUpdateList.add(quest);
					PlayerBattlePassDAO.updateQuest(player, quest);
				}
			}
		});
		if (!questUpdateList.isEmpty()) {
			PacketSendUtility.sendPacket(player, new S_PROGRESS_ACHIEVEMENT(questUpdateList));
		}
		if (!questFinishList.isEmpty()) {
			onFinishQuest(player, questFinishList);
		}
	}

	public void onFinishQuest(Player player, List<BattlePassQuest> quests) {
		List<BattlePassQuest> questList = new ArrayList<>();
		quests.forEach((quest) -> {
			quest.setState(BattleQuestState.REWARD);
			PlayerBattlePassDAO.updateQuest(player, quest);
			questList.add(quest);
		});
		PacketSendUtility.sendPacket(player, new S_PROGRESS_ACHIEVEMENT(questList));
		onUpdatePass(player, questList);
	}

	public void onGetReward(Player player, int passId) {
		if (player.getInventory().isFull() || player.getInventory().isFullSpecialCube()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_DEVAPASS_REWARD_INVENTORY_FULL);
			return;
		}
		BattlePassSeason season = player.getPlayerBattlePass().getBattlePassSeason().get(passId);
		if (season == null) {
			return;
		}
		season.getRewards().forEach((id, battlePassReward) -> {
			if (battlePassReward.getTemplate() != null && battlePassReward.getTemplate().getLevel() <= season.getLevel()) {
				if (!battlePassReward.isRewarded()) {
					battlePassReward.setRewarded(true);
					if (player.getRace() == Race.ELYOS) {
						battlePassReward.getTemplate().getLightBasic().forEach((passReward -> ItemService.addItem(player, passReward.getItemId(), passReward.getCount())));
					} else {
						battlePassReward.getTemplate().getDarkBasic().forEach((passReward -> ItemService.addItem(player, passReward.getItemId(), passReward.getCount())));
					}
				}
				if (player.getAccount() != null && player.getAccount().getMembership() == 2) {
					if (!battlePassReward.isUnlockReward()) {
						battlePassReward.setUnlockReward(true);
						if (player.getRace() == Race.ELYOS) {
							battlePassReward.getTemplate().getLightUnlock().forEach((passReward -> ItemService.addItem(player, passReward.getItemId(), passReward.getCount())));
						} else {
							battlePassReward.getTemplate().getDarkUnlock().forEach((passReward -> ItemService.addItem(player, passReward.getItemId(), passReward.getCount())));
						}
					}
				}
				PlayerBattlePassDAO.updateReward(player, battlePassReward);
			}
		});
		PacketSendUtility.sendPacket(player, new S_BATTLEPASS_UPDATED(season));
	}

	public void onUpdatePass(Player player, List<BattlePassQuest> quests) {
		quests.forEach((quest) -> {
			BattlePassSeason season = player.getPlayerBattlePass().getBattlePassSeason().get(quest.getSeasonId());
			if (season != null && quest.getTemplate() != null) {
				long exp = season.getExp() + quest.getTemplate().getCompleteExp();
				if (exp >= 100) {
					if (season.getTemplate() != null && season.getLevel() < season.getTemplate().getMaxLevel() - 1) {
						season.setExp(exp);
						onLevelUpPass(player, season);
					} else if (season.getTemplate() != null && season.getLevel() >= season.getTemplate().getMaxLevel() - 1) {
						season.setLevel(season.getTemplate().getMaxLevel());
						season.setExp(100);
						PlayerBattlePassDAO.updateSeason(player, season);
						PacketSendUtility.sendPacket(player, new S_BATTLEPASS_UPDATED(season));
					}
				} else {
					season.setExp(exp);
					PlayerBattlePassDAO.updateSeason(player, season);
					PacketSendUtility.sendPacket(player, new S_BATTLEPASS_UPDATED(season));
				}
			}
			quest.setState(BattleQuestState.COMPLETE);
			PlayerBattlePassDAO.updateQuest(player, quest);
			PacketSendUtility.sendPacket(player, new S_REWARD_ACHIEVEMENT_EVENT_RESULT(quest));
		});
	}

	public void onLevelUpPass(Player player, BattlePassSeason season) {
		int level = 0;
		while (season.getExp() >= 100) {
			level += 1;
			season.setExp(season.getExp() - 100);
		}
		season.setLevel(season.getLevel() + level);
		PlayerBattlePassDAO.updateSeason(player, season);
		PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_DEVAPASS_LEVEL_UP(season.getLevel()));
		PacketSendUtility.sendPacket(player, new S_BATTLEPASS_UPDATED(season));
	}

	public void addSeasonToPlayer(Player player, int id) {
		BattlePassSeasonTemplate seasonTemplate = DataManager.BATTLE_PASS_DATA.getSeasonById(id);
		if (seasonTemplate == null) {
			return;
		}
		BattlePassSeason battlePassSeason = new BattlePassSeason(seasonTemplate.getId(), 1, 0);
		player.getPlayerBattlePass().getBattlePassSeason().put(battlePassSeason.getId(), battlePassSeason);
		List<BattlePassRewardTemplate> rewards = DataManager.BATTLE_PASS_REWARD_DATA.getRewardBySeasonId(battlePassSeason.getId());
		if (rewards != null) {
			rewards.forEach((rewardTemplate) -> {
				BattlePassReward reward = new BattlePassReward(rewardTemplate.getId(), false, false);
				player.getPlayerBattlePass().getBattlePassSeason().get(battlePassSeason.getId()).getRewards().put(rewardTemplate.getLevel(), reward);
				PlayerBattlePassDAO.storeReward(player, reward, seasonTemplate.getId());
			});
		}
		PlayerBattlePassDAO.storeSeason(player, battlePassSeason);
	}

	public void onRestart() {
		Timestamp date = new Timestamp(System.currentTimeMillis());
		final Calendar calendar = Calendar.getInstance();
		calendar.setTimeInMillis(date.getTime());
		if (calendar.get(Calendar.DAY_OF_WEEK) == Calendar.WEDNESDAY) {
			PlayerBattlePassDAO.deleteQuest(BattleQuestType.WEEKLY);
			PlayerBattlePassDAO.deleteQuest(BattleQuestType.DAILY);
		} else {
			PlayerBattlePassDAO.deleteQuest(BattleQuestType.DAILY);
		}
	}

	public void initResetTime() {
		this.start = new Timestamp(System.currentTimeMillis());
		// Daily reset 9h00 tomorrow
		Calendar cal = Calendar.getInstance();
		cal.setTimeInMillis(System.currentTimeMillis());
		cal.add(Calendar.DAY_OF_WEEK, 1);
		cal.set(Calendar.HOUR_OF_DAY, 9);
		cal.set(Calendar.MINUTE, 0);
		cal.set(Calendar.SECOND, 0);
		cal.set(Calendar.MILLISECOND, 0);
		this.end = new Timestamp(cal.getTimeInMillis());

		// Weekly reset 9h00 Wednesday
		Calendar cal2 = Calendar.getInstance();
		cal2.add(Calendar.DAY_OF_WEEK, Calendar.WEDNESDAY);
		cal2.set(Calendar.HOUR_OF_DAY, 9);
		cal2.set(Calendar.MINUTE, 0);
		cal2.set(Calendar.SECOND, 0);
		cal2.set(Calendar.MILLISECOND, 0);
		this.endWeekly = new Timestamp(cal2.getTimeInMillis());
	}

	public static BattlePassService getInstance() {
		return SingletonHolder.instance;
	}

	private static class SingletonHolder {
		protected static final BattlePassService instance = new BattlePassService();
	}
}
