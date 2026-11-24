package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;
import com.aionemu.gameserver.network.aion.AionConnection;

/**
 * Mudança na lista de cabelo do Wardrobe 5.0 (0x178; sem nome na tabela de pacotes do Game.dll): [C ação] + o registro
 * ({@link AbstractHairstylePacket#writeHairstyle}). Sem captura oficial.
 * <p>
 * Tratador do Game.dll 0x8CC860 (corpo lido em 0x8D8BB0): 1 acrescenta o penteado à lista, 2 e 3 tiram/atualizam pelo objeto e 4 grava o
 * favorito. É o mesmo esquema do S 0x124 do guarda-roupa (1 registrar, 2 apagar, 3 tingir, 4 favorito).
 */
public class SM_USER_CLASSIC_HAIRSTYLE_DATA_UPDATED extends AbstractHairstylePacket {

	public static final int REGISTERED = 1, DELETED = 2, FAVORITE = 4;

	private final int action;
	private final int ownerObjectId;
	private final WardrobeEntry entry;

	public SM_USER_CLASSIC_HAIRSTYLE_DATA_UPDATED(int action, int ownerObjectId, WardrobeEntry entry) {
		this.action = action;
		this.ownerObjectId = ownerObjectId;
		this.entry = entry;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(action);
		writeHairstyle(ownerObjectId, entry);
	}
}
