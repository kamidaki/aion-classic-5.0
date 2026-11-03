package com.aionemu.gameserver.model.gameobjects;

/**
 * Mercadoria do Black Cloud Mail (NPShop 5.0): pertence à conta e espera na aba "Black Cloud" da janela do correio até um personagem
 * resgatar. O id é o Q que o cliente devolve no C_SA_CONFIRMGOODS; o nome é o do produto, não o do item (captura oficial: "[Event]
 * Major Ancient Crown Chest (10 pieces)" entrega 1 item).
 *
 * @param registerTime
 *          segundos Unix de quando a mercadoria chegou na conta
 */
public record BlackCloudGoods(long id, int accountId, String name, int itemId, long itemCount, int registerTime) {
}
