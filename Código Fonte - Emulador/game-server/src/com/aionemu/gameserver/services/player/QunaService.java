package com.aionemu.gameserver.services.player;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dao.AccountQunaDAO;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_QUNA;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.World;

/**
 * Quna, a moeda da conta no Classic 5.0: um saldo só por conta (account_quna), para QUNA e FREE_QUNA. Capturas: a mesma conta gastou 3 x 60
 * no retune (611 -> 491, 14/09), 33 na Auction House com outro personagem (491 -> 458) e 20 na troca de cabelo (458 -> 438), 21/09.
 * <p>
 * Os itens-moeda do cliente (182499000 QUNA e 182499001 FREE_QUNA, este dado pelas caixas wrap_quna_N) não vão para o cubo: viram saldo em
 * {@link com.aionemu.gameserver.services.item.ItemService}. A loja web credita com INSERT ... ON DUPLICATE KEY UPDATE; o jogador logado vê o
 * saldo novo no próximo login ou na próxima mudança.
 */
public final class QunaService {

	private static final Logger log = LoggerFactory.getLogger(QunaService.class);

	public static final int QUNA_ITEM_ID = 182499000;
	public static final int FREE_QUNA_ITEM_ID = 182499001;
	/** H do S 0x11B nos contextos sem captura (login, ganho, expansão do Wardrobe). */
	public static final int CODE_NONE = 0;
	/** H do S 0x11B no Reassign da skill de equipamento (C 0x107), 4 de 4 nas capturas. */
	public static final int CODE_ITEM_SKILL_REASSIGN = 0x15C;
	// client_strings_msg 5.0; o parâmetro é o valor em texto ("20" na troca de cabelo)
	private static final int MSG_GET_QUNA = 1401412; // STR_MSG_GET_QUNA
	private static final int MSG_USED_QUNA = 1401574; // STR_MSG_USED_QUNA

	private QunaService() {
	}

	public static boolean isQunaItem(int itemId) {
		return itemId == QUNA_ITEM_ID || itemId == FREE_QUNA_ITEM_ID;
	}

	/**
	 * S 0x11B com o saldo. Fora do oficial (que lê o saldo do STS na porta 6600): é o único jeito de a janela ter o saldo antes do primeiro gasto.
	 */
	public static void onEnterWorld(Player player) {
		int accountId = accountId(player);
		if (accountId == 0)
			return;
		try {
			PacketSendUtility.sendPacket(player, new SM_QUNA(CODE_NONE, AccountQunaDAO.load(accountId)));
		} catch (Exception e) {
			log.error("Quna: não foi possível ler o saldo da conta {} ({})", accountId, player.getName(), e);
		}
	}

	/**
	 * @return o saldo da conta, ou -1 se a leitura falhou
	 */
	public static long getBalance(Player player) {
		try {
			return AccountQunaDAO.load(accountId(player));
		} catch (Exception e) {
			log.error("Quna: não foi possível ler o saldo de {}", player.getName(), e);
			return -1;
		}
	}

	/**
	 * Gasta Quna da conta. No sucesso manda o S 0x11B com o saldo novo e a msg 1401574 com o valor, na ordem da troca de cabelo capturada.
	 *
	 * @param code
	 *          H do S 0x11B; {@link #CODE_NONE} fora dos contextos capturados
	 * @return false se o saldo não cobre (nada é enviado; quem chama manda a mensagem de recusa do sistema)
	 */
	public static boolean spend(Player player, long amount, int code) {
		return spend(player, amount, code, true);
	}

	/**
	 * @param usedMessage false no Reassign: depois do C 0x107 o oficial manda só o S 0x11B, sem a 1401574 (4 de 4 nas capturas)
	 */
	public static boolean spend(Player player, long amount, int code, boolean usedMessage) {
		int accountId = accountId(player);
		if (accountId == 0 || amount <= 0)
			return false;
		try {
			if (!AccountQunaDAO.tryDecrease(accountId, amount))
				return false;
			long balance = AccountQunaDAO.load(accountId);
			PacketSendUtility.sendPacket(player, new SM_QUNA(code, balance));
			if (usedMessage)
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_USED_QUNA, String.valueOf(amount)));
			log.info("Quna: {} (conta {}) gastou {}, saldo {}", player.getName(), accountId, amount, balance);
			return true;
		} catch (Exception e) {
			log.error("Quna: falha ao gastar {} da conta {} ({})", amount, accountId, player.getName(), e);
			return false;
		}
	}

	/**
	 * Credita Quna na conta do jogador, com S 0x11B e msg 1401412.
	 */
	public static boolean add(Player player, long amount) {
		int accountId = accountId(player);
		if (accountId == 0 || amount <= 0)
			return false;
		if (!addToAccount(accountId, amount))
			return false;
		PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_GET_QUNA, String.valueOf(amount)));
		return true;
	}

	/**
	 * Credita (ou tira, com valor negativo, sem deixar o saldo abaixo de 0) na conta, com ou sem personagem logado. Se um personagem da conta
	 * estiver no mundo, ele recebe o S 0x11B.
	 */
	public static boolean addToAccount(int accountId, long amount) {
		try {
			if (amount >= 0)
				AccountQunaDAO.add(accountId, amount);
			else if (!AccountQunaDAO.tryDecrease(accountId, -amount))
				return false;
			long balance = AccountQunaDAO.load(accountId);
			for (Player online : World.getInstance().getAllPlayers())
				if (accountId(online) == accountId)
					PacketSendUtility.sendPacket(online, new SM_QUNA(CODE_NONE, balance));
			log.info("Quna: conta {} {} {}, saldo {}", accountId, amount >= 0 ? "recebeu" : "perdeu", Math.abs(amount), balance);
			return true;
		} catch (Exception e) {
			log.error("Quna: falha ao somar {} na conta {}", amount, accountId, e);
			return false;
		}
	}

	private static int accountId(Player player) {
		return player.getAccount() == null ? 0 : player.getAccount().getId();
	}
}
