package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_CHANGE_DIRECTION;
import com.aionemu.gameserver.services.DialogService;
import com.aionemu.gameserver.utils.ThreadPoolManager;

public class CM_CLOSE_DIALOG extends AionClientPacket
{
	private int targetObjectId;
	
	public CM_CLOSE_DIALOG(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}
	
	@Override
	protected void readImpl() {
		targetObjectId = readD();
	}
	
	@Override
	protected void runImpl() {
		final Player player = getConnection().getActivePlayer();
        if (player == null || !player.isSpawned()) {
            return;
        } if (player.isProtectionActive()) {
            player.getController().stopProtectionActiveTask();
        } if (player.isCasting()) {
            player.getController().cancelCurrentSkill();
        } if (player.getController().isInShutdownProgress()) {
            return;
        }
		final VisibleObject obj = player.getKnownList().getObject(targetObjectId);
		final AionConnection client = getConnection();
		if(obj == null) {
			return;
		} if (obj instanceof Npc npc) {			npc.getAi().onCreatureEvent(AIEventType.DIALOG_FINISH, player);
			DialogService.onCloseDialog(npc, player);
			ThreadPoolManager.getInstance().schedule(new Runnable() {
				@Override
				public void run() {
					client.sendPacket(new S_CHANGE_DIRECTION(targetObjectId, (byte)obj.getHeading()));
				}
			}, 1200);
		} if (player.getMailbox() != null && player.getMailbox().mailBoxState != 0) {
            player.getMailbox().mailBoxState = 0;
        }
	}
}