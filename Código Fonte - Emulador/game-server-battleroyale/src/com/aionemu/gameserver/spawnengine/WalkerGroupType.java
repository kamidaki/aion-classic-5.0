package com.aionemu.gameserver.spawnengine;

/**
 * @author Lost Academy Team & Durak
 */
public enum WalkerGroupType {

	POINT,
	SQUARE,
	/**
	 * Cada membro anda deslocado da rota por um valor fixo (atributo offsets do walker_template, "lado:frente" por walker_index), no
	 * referencial da direção do passo para o próximo. É como o oficial monta os grupos (medido nas capturas de Sanctum e Pandaemonium).
	 */
	OFFSET

}
