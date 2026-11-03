package com.aionemu.gameserver.model.gameobjects.player;

import com.aionemu.gameserver.model.Gender;

/**
 * Edicao confirmada na tela de aparencia (C_EDIT_CHARACTER), aplicada quando o cliente pede a volta ao mundo (C_ENTER_WORLD). Fora do mundo
 * o inventario nao esta carregado, entao o ticket so pode sair ali.
 */
public record PendingCharacterEdit(Gender gender, PlayerAppearance appearance) {}
