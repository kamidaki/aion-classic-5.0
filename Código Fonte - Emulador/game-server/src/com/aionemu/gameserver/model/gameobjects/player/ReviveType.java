package com.aionemu.gameserver.model.gameobjects.player;

public enum ReviveType {
	/**
	 * Revive to bindpoint
	 */
	BIND_REVIVE(0),
	/**
	 * Revive from rebirth effect
	 */
	REBIRTH_REVIVE(1),
	/**
	 * Self-Rez Stone
	 */
	ITEM_SELF_REVIVE(2),
	/**
	 * Revive from skill
	 */
	SKILL_REVIVE(3),
	/**
	 * Revive to Kisk
	 */
	KISK_REVIVE(4),
	/**
	 * Revive to Instance Start point
	 */
	INSTANCE_REVIVE(6),
	/**
	 * Revive to Obelisk
	 */
	OBELISK_REVIVE(8),
	/**
	 * Classic 5.0: botão "Kibelisk" (STR_RESURRECT_BUTTON_RP), revive no ponto registrado ou na cidade sem registro
	 * (STR_DEATH_NOT_REGISTERED_RESURRECT_POINT). Nas capturas: 25% de HP/MP num ponto fixo do mapa, 5 de 5.
	 */
	RESURRECT_POINT_REVIVE(9);

	private int typeId;

	/**
	 * Constructor.
	 * 
	 * @param typeId
	 */
	private ReviveType(int typeId) {
		this.typeId = typeId;
	}

	public int getReviveTypeId() {
		return typeId;
	}

	public static ReviveType getReviveTypeById(int id) {
		for (ReviveType rt : values()) {
			if (rt.typeId == id)
				return rt;
		}
		throw new IllegalArgumentException("Unsupported revive type: " + id);
	}
}
