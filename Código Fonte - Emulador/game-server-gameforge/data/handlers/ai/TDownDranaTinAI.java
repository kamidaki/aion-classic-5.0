package ai;

import java.util.concurrent.Future;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.controllers.observer.ActionObserver;
import com.aionemu.gameserver.controllers.observer.ObserverType;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_COLLECT_OBJECT_PROGRESS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.DialogService;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * 802959 Tdown_Black_Drana_Tin ("Blood Drana Products") do Balic Treasury: coleta com a barra própria do cliente (ui craft_ui_always).
 * <p>
 * 5.0 oficial (Balic Treasury.pcapng, 29/10): C 0x131 [obj] → S 0x195 estado 0 → a cada ~1,9 s S 0x195 estado 1 com o progresso subindo
 * de 570 a 2439 (Balic Elyos.pcapng, 30/10: 1440, 570, 1411, 947, 1616, 724, 1468 e 951, 2307, 2370, 775, 1807) → S 0x195 estado 3
 * com 10000 → dois S_ADD_INVENTORY de 186020383 (Blood Drana Products, não empilha) e S_REMOVE_OBJECT [obj][1]; o objeto voltou depois no
 * mesmo ponto (respawn do spawn).
 * <p>
 * Cancelamento (Balic Elyos.pcapng): o jogador começa a andar → S 0x195 estado 4 com o progresso em que parou e STR_NEW_LOOTING_DISCONNECT
 * (1403759). Também para, sem pacote, se o jogador morrer, sair ou o objeto sumir.
 */
@AIName("tdown_drana_tin")
public class TDownDranaTinAI extends NpcAI {

	private static final int ITEM_ID = 186020383;
	private static final int ITEM_COUNT = 2;
	private static final int STEP_MS = 1900;
	private static final int MIN_STEP = 570, MAX_STEP = 2439; // menor e maior passo visto nas duas capturas
	private static final int STR_NEW_LOOTING_DISCONNECT = 1403759;

	private Player collector;
	private Future<?> task;
	private int progress;
	private ActionObserver moveObserver;

	public TDownDranaTinAI(Npc owner) {
		super(owner);
	}

	@Override
	protected synchronized void handleDialogStart(Player player) {
		if (collector != null || isDead() || !DialogService.isInteractionAllowed(player, getOwner()))
			return;
		collector = player;
		progress = 0;
		PacketSendUtility.sendPacket(player, new SM_COLLECT_OBJECT_PROGRESS(SM_COLLECT_OBJECT_PROGRESS.START, 0));
		moveObserver = new ActionObserver(ObserverType.MOVE) {

			@Override
			public void moved() {
				cancelByMove(player);
			}
		};
		player.getObserveController().attach(moveObserver);
		task = ThreadPoolManager.getInstance().scheduleAtFixedRate(this::step, STEP_MS, STEP_MS);
	}

	private synchronized void cancelByMove(Player player) {
		if (collector != player)
			return;
		int stoppedAt = progress;
		stop();
		PacketSendUtility.sendPacket(player, new SM_COLLECT_OBJECT_PROGRESS(SM_COLLECT_OBJECT_PROGRESS.CANCELED, stoppedAt));
		PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(STR_NEW_LOOTING_DISCONNECT));
	}

	private synchronized void step() {
		Player player = collector;
		if (player == null)
			return;
		if (!player.isOnline() || player.isDead() || !getOwner().isSpawned()) {
			stop();
			return;
		}
		progress = Math.min(SM_COLLECT_OBJECT_PROGRESS.MAX_PROGRESS, progress + Rnd.get(MIN_STEP, MAX_STEP));
		if (progress < SM_COLLECT_OBJECT_PROGRESS.MAX_PROGRESS) {
			PacketSendUtility.sendPacket(player, new SM_COLLECT_OBJECT_PROGRESS(SM_COLLECT_OBJECT_PROGRESS.PROGRESS, progress));
			return;
		}
		stop();
		PacketSendUtility.sendPacket(player, new SM_COLLECT_OBJECT_PROGRESS(SM_COLLECT_OBJECT_PROGRESS.SUCCESS, progress));
		ItemService.addItem(player, ITEM_ID, ITEM_COUNT);
		getOwner().getController().deleteAndScheduleRespawn();
	}

	private void stop() {
		if (moveObserver != null && collector != null)
			collector.getObserveController().removeObserver(moveObserver);
		moveObserver = null;
		if (task != null)
			task.cancel(false);
		task = null;
		collector = null;
	}

	@Override
	protected synchronized void handleDespawned() {
		stop();
		super.handleDespawned();
	}
}
