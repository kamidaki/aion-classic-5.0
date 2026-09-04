package com.aionemu.gameserver.ai2.handler;

import com.aionemu.gameserver.ai2.AIState;
import com.aionemu.gameserver.ai2.AISubState;
import com.aionemu.gameserver.ai2.NpcAI;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.S_NPC_HTML_MESSAGE;
import com.aionemu.gameserver.questEngine.QuestEngine;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.utils.PacketSendUtility;

import java.util.*;

public class TalkEventHandler
{
	public static void onTalk(NpcAI npcAI, Creature creature) {
		onSimpleTalk(npcAI, creature);
		if (creature instanceof Player player) {			List<Integer> relatedQuests = QuestEngine.getInstance().getQuestNpc(npcAI.getOwner().getNpcId()).getOnTalkEvent();
			if (QuestEngine.getInstance().onDialog(new QuestEnv(npcAI.getOwner(), player, 0, -1))) {
				return;
			}
			PacketSendUtility.sendPacket(player, new S_NPC_HTML_MESSAGE(npcAI.getOwner().getObjectId(), 10));
			for (int questId: relatedQuests) {
                if (player.getQuestStateList().hasQuest(questId)) {
					final QuestState qs = player.getQuestStateList().getQuestState(questId);
					if (qs == null || qs.getStatus() != QuestStatus.REWARD) {
						continue;
					}
					PacketSendUtility.sendPacket(player, new S_NPC_HTML_MESSAGE(npcAI.getOwner().getObjectId(), 5, questId));
					return;
				}
            }
		}
	}
	
	public static void onSimpleTalk(NpcAI npcAI, Creature creature) {
		if (npcAI.getOwner().getObjectTemplate().isDialogNpc()) {
            npcAI.setSubStateIfNot(AISubState.TALK);
            npcAI.getOwner().setTarget(creature);
        }
	}
	
	public static void onFinishTalk(NpcAI npcAI, Creature creature) {
		Npc owner = npcAI.getOwner();
		if (owner.isTargeting(creature.getObjectId())) {
			if (npcAI.getState() != AIState.FOLLOWING) {
				owner.setTarget(null);
			}
			npcAI.think();
		}
	}
	
	public static void onSimpleFinishTalk(NpcAI npcAI, Creature creature) {
		Npc owner = npcAI.getOwner();
		if (owner.isTargeting(creature.getObjectId()) && npcAI.setSubStateIfNot(AISubState.NONE)) {
			owner.setTarget(null);
		}
	}
}