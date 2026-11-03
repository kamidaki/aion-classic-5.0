package com.aionemu.gameserver.model;

/**
 * @author Lost Academy Team & Durak
 */
public enum CreatureType {

	/** These are regular monsters */
	ATTACKABLE(0),
	/** These are Peace npc, which you cannot talk to */
	PEACE(2),
	/** These are monsters that are pre-aggressive */
	AGGRESSIVE(8),
	// unk
	INVULNERABLE(10),
	/**
	 * Objeto de nivel: o cliente nao mostra barra de vida, nao deixa selecionar e nao troca o cursor. E o que o
	 * servidor oficial 5.0 manda para todo NPC de tribo NONE -- torres (802313/802314/802315), WindBox, MistOn e
	 * os corredores de avanco de Tiamaranta, entre outros (7 de 7 na captura 08_Spawns_Mapas_Tiamaranta_Mesa).
	 */
	NONE(34),
	/** These are non attackable NPCs, which you can talk to */
	FRIEND(38),

	SUPPORT(54);

	private int id;

	CreatureType(int id) {
		this.id = id;
	}

	public int getId() {
		return id;
	}
}
