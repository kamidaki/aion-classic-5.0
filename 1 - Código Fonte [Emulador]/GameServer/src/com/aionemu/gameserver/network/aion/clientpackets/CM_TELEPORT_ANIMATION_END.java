package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.teleport.TeleportService2;

/**
 * O cliente avisa que terminou a animacao de teleporte e esta pronto para receber o mapa novo.
 * Opcode de fio 0x009D, corpo vazio.
 *
 * Medido na captura oficial (subida-1-60, sessao 1), nos dois unicos teleportes que ela tem --
 * indices 584-587 e 14018-14030. O desenho e sempre o mesmo:
 *
 * <pre>
 *   S  S_REQUEST_TELEPORT        t = 0
 *   C  0x009D (este pacote)      t = 2050 ms / 2019 ms
 *   S  S_WORLD                   t = 2230 ms / 2431 ms
 *   C  CM_LEVEL_READY            t = 3490 ms / 4285 ms
 * </pre>
 *
 * Ou seja: quem manda a troca de mapa acontecer e o cliente, nao um relogio do servidor. Antes
 * disto o opcode estava registrado como CM_OPEN_STATICDOOR, que fazia readD() num corpo de zero
 * bytes -- o rastro respondia "Missing D for" e a confirmacao ia para o lixo.
 */
public class CM_TELEPORT_ANIMATION_END extends AionClientPacket {

	public CM_TELEPORT_ANIMATION_END(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		// sem corpo
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null) {
			return;
		}
		TeleportService2.confirmaAnimacaoDeTeleporte(player);
	}
}
