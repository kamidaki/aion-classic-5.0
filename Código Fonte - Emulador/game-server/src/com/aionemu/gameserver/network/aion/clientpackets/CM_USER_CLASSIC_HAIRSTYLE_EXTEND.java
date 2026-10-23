package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.PlayerWardrobeService;

/**
 * Expansão de slot da lista de cabelo do Wardrobe, decodificado 0xEA (cru 0x198): [H 1][C forma de pagamento], 1 = Quna e 2 = item. Sem
 * captura oficial.
 * <p>
 * Game.dll: a aba de cabelo (WardrobeHair, eventos 0x8A3/0x8A4 em 0x702D11) manda pelo serializador genérico 0x898FC0 o pacote 0x11A com
 * [H 1][C 1 ou 2]. O serializador grava o opcode como ((((op + 0xC4) ^ 0xE5) + 0xC) ^ 0xDF), que para 0x11A dá o cru 0x198; a mesma conta
 * dá 0x199 para o 0x11B, que é o C 0xEB (troca de penteado) da captura de 2026-09-21.
 */
public class CM_USER_CLASSIC_HAIRSTYLE_EXTEND extends AionClientPacket {

	private int payment;

	public CM_USER_CLASSIC_HAIRSTYLE_EXTEND(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		readH();
		payment = readC();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			PlayerWardrobeService.getInstance().extendHairstyleSlots(player, payment);
	}
}
