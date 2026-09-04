package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.Gatherable;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Interagir com um objeto do mundo: opcode de fio 0x00F6, corpo de 4 bytes (o objectId).
 *
 * E o mesmo pedido para tudo o que se usa com um clique. Na captura oficial (subida-1-60, sessao 1)
 * ele aparece doze vezes e o servidor responde conforme o alvo: num NPC de dialogo vem
 * S_NPC_CHANGED_TARGET + S_NPC_HTML_MESSAGE (indices 533-536), num no de coleta vem S_GAUGE +
 * S_ACTION (indices 6023-6026). Por isso o despacho e por tipo de alvo, e nao um handler por
 * sistema.
 */
public class CM_SHOW_DIALOG extends AionClientPacket
{
	private int targetObjectId;
	
	public CM_SHOW_DIALOG(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}
	
	@Override
	protected void readImpl() {
		targetObjectId = readD();
	}
	
	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null || !player.isSpawned()) {
			return;
		}
		if (player.isTrading()) {
			return;
		}
		VisibleObject obj = player.getKnownList().getObject(targetObjectId);
		if (obj instanceof Npc) {
			((Npc) obj).getController().onDialogRequest(player);
		} else if (obj instanceof Gatherable) {
			((Gatherable) obj).getController().onStartUse(player);
		}
	}
}
