package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.configs.administration.AdminConfig;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gm.GmPanelCommands;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.gmhandler.*;
import com.aionemu.gameserver.network.aion.gmhandler.CmdLevelUpDown.LevelUpDownState;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE_CODE;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.utils.PacketSendUtility;


public class CM_GM_COMMAND_SEND extends AionClientPacket {

	private String cmd = "";
	private String params = "";
	private Player admin;

	public CM_GM_COMMAND_SEND(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		admin = getConnection().getActivePlayer();
		String clientCmd = readS();

		int index = clientCmd.indexOf(" ");

		cmd = clientCmd;
		if (index >= 0) {
			cmd = clientCmd.substring(0, index).toUpperCase();
			params = clientCmd.substring(index + 1);
		}
	}

	@Override
	protected void runImpl() {
		if (admin == null) {
			return;
		}

		// check accesslevel - not needed but to be sure
		if (admin.getAccessLevel() < AdminConfig.GM_PANEL) {
			return;
		}

		switch (GmPanelCommands.getValue(cmd)) {
			case REMOVE_SKILL_DELAY_ALL:
				// new CmdRemoveSkillDelayAll(admin); // TODO
				break;
			case ITEMCOOLTIME:
				new CmdItemCoolTime(admin);
				break;
			case ATTRBONUS:
				new CmdAttrBonus(admin, params);
				break;
			case TELEPORTTO:
				new CmdTeleportTo(admin, params);
				break;
			case TELEPORT_TO_NAMED:
				new CmdTeleportToNamed(admin, params);
				break;
			case RESURRECT:
				new CmdResurrect(admin, "");
				break;
			case INVISIBLE:
				new CmdInvisible(admin, "");
				break;
			case VISIBLE:
				new CmdVisible(admin, "");
				break;
			case LEVELDOWN:
				new CmdLevelUpDown(admin, params, LevelUpDownState.DOWN);
				break;
			case LEVELUP:
				QuestState elyos = admin.getQuestStateList().getQuestState(10521);
				QuestState asmo = admin.getQuestStateList().getQuestState(20521);
				if (admin.getLevel() >= 85 && admin.getRace() == Race.ELYOS && elyos.getStatus() != QuestStatus.COMPLETE) {
					PacketSendUtility.sendPacket(admin, new S_MESSAGE_CODE(1403187, 81));
					break;
				}
				else if (admin.getLevel() >= 85 && admin.getRace() == Race.ASMODIANS && asmo.getStatus() != QuestStatus.COMPLETE) {
					PacketSendUtility.sendPacket(admin, new S_MESSAGE_CODE(1403187, 81));
					break;
				}
				else {
					new CmdLevelUpDown(admin, params, LevelUpDownState.UP);
					break;
				}
			case WISHID:
				new CmdWishId(admin, params);
				break;
			case DELETECQUEST:
				new CmdDeleteQuest(admin, params);
				break;
			case GIVETITLE:
				new CmdGiveTitle(admin, params);
				break;
			case DELETE_ITEMS:
				PacketSendUtility.sendMessage(admin, "Invalid command: " + cmd.toString());
				break;
			case CHANGECLASS:
				new CmdChangeClass(admin, params);
				break;
			case CLASSUP:
				new CmdChangeClass(admin, params);
				break;
			case WISH:
				new CmdWish(admin, params);
				break;
			case ADDQUEST:
				new CmdStartQuest(admin, params);
				break;
			case ENDQUEST:
				new CmdEndQuest(admin, params);
				break;
			case ADDSKILL:
				new CmdAddSkill(admin, params);
				break;
			case SETINVENTORYGROWTH:
				new CmdSetInventoryGrowth(admin,params);
				break;
			case SKILLPOINT:
			case COMBINESKILL:
			case DELETESKILL:
			case ENCHANT100:
			case SEARCH:
			case BOOKMARK_ADD:
				PacketSendUtility.sendMessage(admin, "Invalid command: " + cmd.toString());
				break;
			case SET_ENCHANTCOUNT:
				new CmdSetEnchantCount(admin,params);
				break;
			default:
				PacketSendUtility.sendMessage(admin, "Invalid command: " + cmd.toString());
				break;
		}
	}

}
