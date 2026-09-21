package com.aionemu.gameserver.services.player;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Future;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.GameServer;
import com.aionemu.gameserver.dao.InventoryDAO;
import com.aionemu.gameserver.dao.PlayerMorosDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.MorosData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerMoros;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.network.aion.serverpackets.SM_MOROS_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * Moreth, Chronicle of Time (MOROS) do Classic 5.0: o jogador grava itens do inventário (C 0x111), que somem e viram pontos; os pontos sobem o
 * nível, e cada nível dá a sua passiva (moros/moros.xml). Cada item gravado gasta um registro, que volta sozinho depois de 30 min.
 * <p>
 * Capturas: o 0x169 sai no login logo depois do 0x14D e a cada gravação, depois dos 0x1C (motivo 0xFA), sem mensagem de sistema. A passiva não vai
 * no S_ADD_SKILL (o cliente mostra a skill pelo nível do 0x169), então é aplicada direto como efeito. Pontos por gravação: soma de ponto x
 * quantidade de cada item, vezes o valor em % do nível atual (captura: 1 ponto no nível 1, 200% = 2).
 */
public final class MorosService {

	private static final Logger log = LoggerFactory.getLogger(MorosService.class);
	/** Espaços da janela de gravação (ui/game/moros_dialog.xml, item1 a item18). */
	public static final int MAX_SLOTS = 18;
	/** Registros com o contador cheio: 20 nas 40 amostras do 0x169. */
	public static final int MAX_RECORDS = 20;
	/** Tempo até um registro gasto voltar: 30 min 6 s na captura do Book of Legends (STR_MSG_MOROS_COUNT). */
	public static final long RESTORE_MILLIS = 30 * 60 * 1000L;
	/** STR_MSG_MOROS_RESTRICT: "Can only be used once you reach level 50." */
	public static final int MIN_PLAYER_LEVEL = 50;
	// client_strings_msg 5.0
	private static final int MSG_UNRECORDABLE_COUNT = 1401989; // STR_MSG_MOROS_UNRECORDABLE_COUNT
	private static final int MSG_UNRECORDABLE_ITEM = 1401990; // STR_MSG_MOROS_UNRECORDABLE_ITEM
	private static final int MSG_LEVELUP = 1401991; // STR_MSG_MOROS_LEVELUP
	private static final int MSG_RESTRICT = 1401994; // STR_MSG_MOROS_RESTRICT
	private static final int MSG_RECORD_CAN_NOT = 1401995; // STR_MSG_MOROS_RECORD_CAN_NOT
	private static final int MSG_RECORD_FAIL = 1401996; // STR_MSG_MOROS_RECORD_FAIL
	private static final int MSG_COUNT = 1402006; // STR_MSG_MOROS_COUNT
	private static final int MSG_UNRECORDABLE_POINT = 1402008; // STR_MSG_MOROS_UNRECORDABLE_POINT
	private static final int MSG_EQUIPPED_ITEM = 1402018; // STR_MSG_MOROS_EQUIPED_ITEM
	private static final int MSG_TEMPORARY_EXCHANGE_ITEM = 1402019; // STR_MSG_MOROS_TEMPORARY_EXCHANGE_ITEM
	private static final int MSG_PACKED_ITEM = 1403695; // STR_MSG_PACK_CANNOT_MOROS_REGIST

	private static final Map<Integer, Future<?>> restoreTasks = new ConcurrentHashMap<>();

	private MorosService() {
	}

	/**
	 * Carrega o estado e aplica a passiva do nível. Chamado ao montar o personagem, antes de entrar no mundo.
	 */
	public static void onLoad(Player player) {
		PlayerMoros moros;
		try {
			moros = PlayerMorosDAO.load(player.getObjectId());
		} catch (Exception e) {
			log.error("Moreth: não foi possível carregar {}; o sistema fica fora nesta sessão", player.getName(), e);
			return;
		}
		if (DataManager.MOROS_DATA.getLevel(moros.getLevel()) == null) {
			log.warn("Moreth: nível {} de {} fora dos dados, voltando ao máximo", moros.getLevel(), player.getName());
			moros.setLevelAndPoints(DataManager.MOROS_DATA.getMaxLevel(), 0);
		}
		moros.restore(System.currentTimeMillis()); // o que venceu com o personagem fora volta sem aviso
		player.setMoros(moros);
		applyPassive(player, moros.getLevel());
	}

	/**
	 * S 0x169 do login e o agendamento dos registros que ainda vão voltar.
	 */
	public static void onEnterWorld(Player player) {
		sendInfo(player);
		scheduleRestore(player);
	}

	public static void onLogout(Player player) {
		Future<?> task = restoreTasks.remove(player.getObjectId());
		if (task != null)
			task.cancel(false);
	}

	public static void sendInfo(Player player) {
		PlayerMoros moros = player.getMoros();
		if (moros != null)
			PacketSendUtility.sendPacket(player, new SM_MOROS_INFO(moros.getLevel(), moros.getPoints(), moros.getRecords(MAX_RECORDS)));
	}

	/**
	 * @param items
	 *          objeto -> quantidade, na ordem do pedido
	 */
	public static void record(Player player, Map<Integer, Long> items) {
		synchronized (player) {
			PlayerMoros moros = player.getMoros();
			if (moros == null)
				return;
			int message = check(player, moros, items);
			if (message != 0) {
				log.info("Moreth recusado: player={}, itens={}, mensagem={}", player.getName(), items, message);
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message));
				return;
			}
			MorosData data = DataManager.MOROS_DATA;
			Storage inventory = player.getInventory();
			long basePoints = 0;
			for (Map.Entry<Integer, Long> entry : items.entrySet()) {
				Item item = inventory.getItemByObjId(entry.getKey());
				basePoints += data.getPoint(item.getItemId()) * entry.getValue();
				if (!inventory.decreaseByObjectId(entry.getKey(), entry.getValue(), ItemUpdateType.DEC_MOROS_RECORD))
					log.error("Moreth: item {} x{} de {} sumiu depois da conferência", entry.getKey(), entry.getValue(), player.getName());
			}
			int oldLevel = moros.getLevel();
			long gained = basePoints * data.getLevel(oldLevel).getRate() / 100;
			addPoints(moros, gained);
			moros.useRecords(items.size(), System.currentTimeMillis() + RESTORE_MILLIS);
			InventoryDAO.store(player);
			PlayerMorosDAO.store(player.getObjectId(), moros);
			sendInfo(player);
			for (int level = oldLevel + 1; level <= moros.getLevel(); level++)
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_LEVELUP));
			if (moros.getLevel() != oldLevel) {
				removePassive(player, oldLevel);
				applyPassive(player, moros.getLevel());
			}
			scheduleRestore(player);
			log.info("Moreth: {} gravou {} ({} pontos x {}% = {}), nível {} -> {} com {} pontos", player.getName(), items, basePoints,
				data.getLevel(oldLevel).getRate(), gained, oldLevel, moros.getLevel(), moros.getPoints());
		}
	}

	/**
	 * @return 0 se a gravação pode ser feita, ou a mensagem de recusa
	 */
	private static int check(Player player, PlayerMoros moros, Map<Integer, Long> items) {
		if (player.getLevel() < MIN_PLAYER_LEVEL)
			return MSG_RESTRICT;
		if (!player.isOnline() || !player.isSpawned() || player.isDead() || player.isTrading() || player.hasStore() || GameServer.isShuttingDownSoon())
			return MSG_RECORD_CAN_NOT;
		if (moros.getLevel() >= DataManager.MOROS_DATA.getMaxLevel())
			return MSG_UNRECORDABLE_POINT;
		if (items.size() > moros.getRecords(MAX_RECORDS))
			return MSG_UNRECORDABLE_COUNT;
		Storage inventory = player.getInventory();
		for (Map.Entry<Integer, Long> entry : items.entrySet()) {
			Item item = inventory.getItemByObjId(entry.getKey());
			if (item == null)
				return player.getEquipment().getEquippedItemByObjId(entry.getKey()) != null ? MSG_EQUIPPED_ITEM : MSG_RECORD_FAIL;
			if (item.getItemCount() < entry.getValue())
				return MSG_RECORD_FAIL;
			if (DataManager.MOROS_DATA.getPoint(item.getItemId()) <= 0)
				return MSG_UNRECORDABLE_ITEM;
			if (item.getPackCount() > 0)
				return MSG_PACKED_ITEM;
			if (item.getTemporaryExchangeTime() > 0)
				return MSG_TEMPORARY_EXCHANGE_ITEM;
		}
		return 0;
	}

	/**
	 * Soma os pontos e sobe quantos níveis couberem; o que sobra fica no nível novo. No nível máximo os pontos param em 0.
	 */
	static void addPoints(PlayerMoros moros, long gained) {
		MorosData data = DataManager.MOROS_DATA;
		int level = moros.getLevel();
		long points = moros.getPoints() + gained;
		while (level < data.getMaxLevel() && points >= data.getLevel(level + 1).getPoints()) {
			points -= data.getLevel(level + 1).getPoints();
			level++;
		}
		moros.setLevelAndPoints(level, level >= data.getMaxLevel() ? 0 : points);
	}

	private static void scheduleRestore(Player player) {
		PlayerMoros moros = player.getMoros();
		Future<?> old = restoreTasks.remove(player.getObjectId());
		if (old != null)
			old.cancel(false);
		if (moros == null || moros.getNextRestoreTime() == 0)
			return;
		long delay = Math.max(0, moros.getNextRestoreTime() - System.currentTimeMillis());
		restoreTasks.put(player.getObjectId(), ThreadPoolManager.getInstance().schedule(() -> restore(player), delay));
	}

	private static void restore(Player player) {
		synchronized (player) {
			PlayerMoros moros = player.getMoros();
			if (moros == null || !player.isOnline())
				return;
			int restored = moros.restore(System.currentTimeMillis());
			if (restored > 0) {
				PlayerMorosDAO.store(player.getObjectId(), moros);
				for (int i = 0; i < restored; i++)
					PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_COUNT));
				sendInfo(player);
			}
			scheduleRestore(player);
		}
	}

	private static void applyPassive(Player player, int level) {
		MorosData.Level data = DataManager.MOROS_DATA.getLevel(level);
		SkillTemplate template = data == null ? null : DataManager.SKILL_DATA.getSkillTemplate(data.getSkillId());
		if (template == null || player.getEffectController() == null)
			return;
		try {
			SkillEngine.getInstance().applyEffectDirectly(template, data.getSkillLevel(), player, player);
		} catch (RuntimeException e) {
			log.error("Moreth: não foi possível aplicar a passiva {} nv {} em {}", data.getSkillId(), data.getSkillLevel(), player.getName(), e);
		}
	}

	private static void removePassive(Player player, int level) {
		MorosData.Level data = DataManager.MOROS_DATA.getLevel(level);
		if (data != null && player.getEffectController() != null)
			player.getEffectController().removeEffect(data.getSkillId());
	}
}
