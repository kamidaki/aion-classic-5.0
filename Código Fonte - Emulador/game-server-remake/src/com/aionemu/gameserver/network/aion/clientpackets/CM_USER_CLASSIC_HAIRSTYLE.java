package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.PlayerWardrobeService;

/**
 * Pedidos da lista de cabelo do Wardrobe 5.0 com um objeto só ([D]), que o cliente manda pelo serializador genérico (Game.dll 0x898FC0 e
 * vizinhos; fio = ((((op + 0xC4) ^ 0xE5) + 0xC) ^ 0xDF)):
 * <ul>
 * <li>registrar, op 0x116 = fio 0x194 (dec 0xDE), [D objeto do item]: evento 0x8A5 da aba de cabelo, também depois da confirmação ao usar o
 * item de penteado (STR_EDIT_CHAR_ITEM_USE_CONFIRM_HAIR); veio 2 vezes no log de 22/10 com o objeto do item;</li>
 * <li>apagar, op 0x117 = fio 0x195 (dec 0xDF), [D entrada]: evento 0x8A7;</li>
 * <li>trocar o penteado, op 0x11B = fio 0x199 (dec 0xEB), [D entrada]: evento 0x8A8; capturado em 2026-09-21 (20 Quna).</li>
 * </ul>
 */
public class CM_USER_CLASSIC_HAIRSTYLE extends AionClientPacket {

	public static final int REGISTER = 0x194, DELETE = 0x195, CHANGE = 0x199;

	private int objectId;

	public CM_USER_CLASSIC_HAIRSTYLE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		objectId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null)
			return;
		PlayerWardrobeService service = PlayerWardrobeService.getInstance();
		switch (getOpCode()) {
			case REGISTER -> service.registerHairstyle(player, objectId);
			case DELETE -> service.deleteHairstyle(player, objectId);
			case CHANGE -> service.changeHairstyle(player, objectId);
		}
	}
}
