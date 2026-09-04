package com.aionemu.gameserver.questEngine.handlers.models.xmlQuest.operations;

import com.aionemu.gameserver.model.EmotionType;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.S_ACTION;
import com.aionemu.gameserver.network.aion.serverpackets.S_GAUGE;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ActionItemUseOperation", propOrder = { "finish" })
public class ActionItemUseOperation extends QuestOperation {

	@XmlElement(required = true)
	protected QuestOperations finish;

	/*
	 * (non-Javadoc)
	 * @seecom.aionemu.gameserver.questEngine.handlers.models.xmlQuest.operations.QuestOperation#doOperate(com.aionemu.
	 * gameserver.services.QuestService, com.aionemu.gameserver.questEngine.model.QuestEnv)
	 */
	@Override
	public void doOperate(final QuestEnv env) {
		final Player player = env.getPlayer();
		final Npc npc;
		if (env.getVisibleObject() instanceof Npc)
			npc = (Npc) env.getVisibleObject();
		else
			return;
		final int defaultUseTime = 3000;
		PacketSendUtility.sendPacket(player, new S_GAUGE(player.getObjectId(), npc.getObjectId(), defaultUseTime, 1));
		PacketSendUtility.broadcastPacket(player,
			new S_ACTION(player, EmotionType.START_QUESTLOOT, 0, npc.getObjectId()), true);
		ThreadPoolManager.getInstance().schedule(new Runnable() {

			@Override
			public void run() {
				PacketSendUtility.sendPacket(player, new S_GAUGE(player.getObjectId(), npc.getObjectId(), defaultUseTime,
					0));
				finish.operate(env);
			}
		}, defaultUseTime);

	}

}
