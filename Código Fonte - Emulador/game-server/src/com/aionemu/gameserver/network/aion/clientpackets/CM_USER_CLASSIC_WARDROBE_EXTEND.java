package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.HexFormat;
import java.util.Set;

import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.PlayerWardrobeService;

/**
 * Expansão de slot do Wardrobe (wardrobe_extend_dialog: Quna ou item), decodificado 0xFB (cru 0x189): [H 1][C forma de pagamento], 1 = Quna e
 * 2 = item. Não há captura oficial; o opcode vem da ordem da 2.7 (a expansão logo depois do APPLY, que na 5.0 andou para 0xFA) e foi confirmado
 * no cliente real em 21/09: pagando com Quna, o corpo veio 01 00 01. O 2 = item é a nota da fonte 2.4 ("use key in official = 01 00 02").
 * <p>
 * O corpo inteiro vai para o log, para conferir a forma de pagamento por item quando ela for usada.
 */
public class CM_USER_CLASSIC_WARDROBE_EXTEND extends AionClientPacket {

	private byte[] body;

	public CM_USER_CLASSIC_WARDROBE_EXTEND(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		body = readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null)
			return;
		LoggerFactory.getLogger(CM_USER_CLASSIC_WARDROBE_EXTEND.class).info("Wardrobe: expansão pedida por {}, corpo {}", player.getName(),
			HexFormat.of().formatHex(body));
		int payment = body.length > 0 ? body[body.length - 1] & 0xFF : 0;
		PlayerWardrobeService.getInstance().extendSlots(player, payment);
	}
}
