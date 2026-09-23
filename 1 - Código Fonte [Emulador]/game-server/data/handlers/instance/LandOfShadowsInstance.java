package instance;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicBoolean;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.instance.handlers.GeneralInstanceHandler;
import com.aionemu.gameserver.instance.handlers.InstanceID;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.spawns.SpawnTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.WorldMapInstance;

/**
 * Land of Shadows (IDTutorialQ, 390000000): instancia das campanhas 10153/20153.
 * <p>
 * Roteiro medido na captura oficial subida-1-60-2026-08-28.pcapng (Asmodiano, S_WORLD 390000000 ate a saida pela
 * Inggril em 1.451 s). Tempos entre parenteses sao da captura, relativos ao gatilho de cada etapa.
 * <ul>
 * <li>Entrada: a forma de Daeva do Tempo da classe ({@code <FI|KN|...>_<L|D>_START}, ShapeChange do cliente). Aos 60 s,
 * as mensagens de abertura, os dois primeiros gossips e a Inggril/Inggness perto da entrada, e o veu (804145) da
 * entrada some.</li>
 * <li>Controladores: Set_Ctrl (804139-804142) e MSG_Ctrl (804149-804154) disparam quando o jogador entra no srange
 * deles (20 e 10 m, sensory_range do cliente; medido 17-20 e 5-10 m). MSG_Ctrl manda duas falas de Ariel/Asphel com
 * 5 s de intervalo e some; Set_Ctrl chama o boss/named da area.</li>
 * <li>Bosses 224333/224334/224335: ao morrer, guardas da area saem, nasce um bau mimico (804156/804161/804168) que ao
 * morrer vira o bau real (804157/804162/804169); abrir o bau real remove o veu seguinte.</li>
 * <li>Named de duas fases: 224319 -> 224320 e 224317 -> 224318, no ponto onde a primeira morreu.</li>
 * <li>No boss 3 um veu fecha a arena quando o jogador entra (x < 310) e some com a morte dele; depois nascem as
 * bonus box, o bau e a Inggril/Inggness, que faz a saida (acao 104, IDTutorialQ_Teleport_Out_*_AI).</li>
 * </ul>
 * Os NPCs Asmodianos (gossip 804124-804133, Inggril 804135) viram os Elyos (804114-804123, Inggness 804134) no mesmo
 * ponto quando quem entra e Elyos: no cliente os dois lados tem o mesmo spot, e na captura so aparece o da raca.
 */
@InstanceID(390000000)
public class LandOfShadowsInstance extends GeneralInstanceHandler {

	private static final int VEU = 804145;
	private static final int ELYOS_DELTA = 10; // 8041(2x) Asmodiano -> 8041(1x) Elyos; 804135 -> 804134
	private static final Map<PlayerClass, String> FORMA = Map.ofEntries(Map.entry(PlayerClass.GLADIATOR, "FI"),
		Map.entry(PlayerClass.TEMPLAR, "KN"), Map.entry(PlayerClass.ASSASSIN, "AS"), Map.entry(PlayerClass.RANGER, "RA"),
		Map.entry(PlayerClass.SORCERER, "WI"), Map.entry(PlayerClass.SPIRIT_MASTER, "EL"), Map.entry(PlayerClass.CHANTER, "CH"),
		Map.entry(PlayerClass.CLERIC, "PR"), Map.entry(PlayerClass.THUNDERER, "TH"), Map.entry(PlayerClass.REVENANT, "TH"),
		Map.entry(PlayerClass.BRAWLER, "BM"), Map.entry(PlayerClass.LUMINESS, "LU"), Map.entry(PlayerClass.GUNNER, "GU"),
		Map.entry(PlayerClass.PHOENIX, "GU"), Map.entry(PlayerClass.SOUL_REAPER, "RB"));
	// MSG_Ctrl -> duas falas (STR_MSG_IDTutorialQ_Ariel_NN / _Asphel_NN)
	private static final Map<Integer, int[]> FALAS = Map.of(804149, new int[] { 1404335, 1404336 }, 804150,
		new int[] { 1404337, 1404338 }, 804151, new int[] { 1404339, 1404340 }, 804152, new int[] { 1404341, 1404342 }, 804153,
		new int[] { 1404343, 1404344 }, 804154, new int[] { 1404345, 1404346 });

	private final AtomicBoolean iniciado = new AtomicBoolean();
	private final AtomicBoolean veuBoss3 = new AtomicBoolean();
	private final Set<Integer> disparados = ConcurrentHashMap.newKeySet();
	private volatile Race raca = Race.ASMODIANS;
	private volatile boolean destruida;
	private Future<?> vigia;

	public LandOfShadowsInstance(WorldMapInstance instance) {
		super(instance);
	}

	@Override
	public void onEnterInstance(Player player) {
		aplicaForma(player);
		if (!iniciado.compareAndSet(false, true))
			return;
		raca = player.getRace();
		if (raca == Race.ELYOS)
			for (Npc gossip : instance.getNpcs(804124, 804125, 804126, 804127, 804128, 804129, 804130, 804131, 804132, 804133)) {
				SpawnTemplate s = gossip.getSpawn();
				gossip.getController().delete();
				spawn(gossip.getNpcId() - ELYOS_DELTA, s.getX(), s.getY(), s.getZ(), s.getHeading());
			}
		depois(60000, () -> { // S_INVINCIBLE_TIME 60000 na entrada; a abertura vem aos 61,6 s
			sendMsg(new SM_SYSTEM_MESSAGE(1404349)); // STR_MSG_IDTutorialQ_Start_Buff_01
			sendMsg(new SM_SYSTEM_MESSAGE(1404329)); // Ariel_01
		});
		depois(60800, () -> {
			spawn(daRaca(804124), 681.97f, 521.97f, 338.43f, (byte) 0);
			spawn(daRaca(804135), 700.53f, 500.77f, 338.25f, (byte) 30);
			spawn(daRaca(804125), 649.47f, 529.19f, 339.62f, (byte) 105);
		});
		depois(64200, () -> sendMsg(new SM_SYSTEM_MESSAGE(1404457))); // Normal_Kill_UI_Start
		depois(64400, () -> {
			sendMsg(new SM_SYSTEM_MESSAGE(1404330)); // Asphel_01
			apaga(VEU, 675.36f, 518.71f);
		});
		vigia = ThreadPoolManager.getInstance().scheduleAtFixedRate(this::vigia, 1000, 1000);
	}

	@Override
	public void onLeaveInstance(Player player) {
		SkillTemplate forma = forma(player);
		if (forma != null)
			player.getEffectController().removeEffect(forma.getSkillId());
	}

	@Override
	public void onInstanceDestroy() {
		destruida = true;
		if (vigia != null)
			vigia.cancel(false);
	}

	@Override
	public void onDie(Npc npc) {
		float x = npc.getX(), y = npc.getY(), z = npc.getZ();
		switch (npc.getNpcId()) {
			case 224305 -> apaga(VEU, 610.01f, 617.78f); // primeiro named: o veu que o 804139 fechou abre na morte dele
			case 224319 -> spawn(224320, x, y, z, npc.getHeading()); // Sikara Rider desmonta
			case 224317 -> spawn(224318, x, y, z, npc.getHeading()); // Pagati Strider desmonta
			case 224333 -> { // boss 1
				apaga(804108, 614.30f, 646.11f);
				apaga(804109, 605.65f, 657.24f);
				apaga(804104, 607.62f, 636.96f);
				depois(900, () -> {
					spawn(804143, 607.50f, 707.20f, 355.11f, (byte) 0);
					spawn(804156, 609.32f, 707.21f, 355.11f, (byte) 45);
				});
				depois(1100, () -> sendMsg(new SM_SYSTEM_MESSAGE(1404453))); // TREASUREBOX_Ariel_01
			}
			case 804156, 804161, 804168 -> { // bau mimico -> bau real no mesmo ponto
				sendMsg(new SM_SYSTEM_MESSAGE(1404481)); // MYSTICCUBE_LEVELUP
				if (npc.getNpcId() == 804156)
					sendMsg(new SM_SYSTEM_MESSAGE(1404454)); // TREASUREBOX_Asphel_01
				spawn(npc.getNpcId() + 1, x, y, z, (byte) 0);
			}
			case 804157 -> { // bau do boss 1 aberto
				sendMsg(new SM_SYSTEM_MESSAGE(1404445)); // Boss1_02
				apaga(VEU, 600.27f, 675.67f);
				spawn(VEU, 608.11f, 695.01f, 354.85f, (byte) 0);
				spawn(VEU, 608.11f, 700.01f, 354.85f, (byte) 0);
				spawn(VEU, 607.88f, 685.08f, 354.31f, (byte) 0);
				spawn(VEU, 608.11f, 690.01f, 354.85f, (byte) 0);
				spawn(VEU, 608.11f, 681.01f, 352.53f, (byte) 0);
				spawn(VEU, 603.93f, 676.45f, 352.53f, (byte) 0);
				spawn(VEU, 606.32f, 677.56f, 352.53f, (byte) 0);
			}
			case 224334 -> { // boss 2
				apaga(804105, 515.62f, 453.95f);
				apaga(804100, 517.30f, 552.30f);
				apaga(804107, 505.84f, 562.10f);
				apaga(daRaca(804131), 476.61f, 467.82f);
				depois(900, () -> {
					spawn(804144, 470.34f, 515.40f, 342.19f, (byte) 0);
					spawn(804161, 470.08f, 513.22f, 342.19f, (byte) 45);
					sendMsg(new SM_SYSTEM_MESSAGE(1404467)); // TREASUREBOX_Ariel_03
				});
				depois(6000, () -> {
					sendMsg(new SM_SYSTEM_MESSAGE(1404468)); // TREASUREBOX_Asphel_03
					deleteAliveNpcs(804144);
				});
			}
			case 804162 -> { // bau do boss 2 aberto
				sendMsg(new SM_SYSTEM_MESSAGE(1404447)); // Boss2_02
				apaga(VEU, 466.45f, 513.25f);
			}
			case 224335 -> { // boss 3
				sendMsg(new SM_SYSTEM_MESSAGE(1404449)); // Boss3_02
				apaga(VEU, 317.58f, 513.30f);
				apaga(daRaca(804132), 350.18f, 514.38f);
				depois(900, () -> {
					spawn(804174, 277.25f, 516.51f, 351.55f, (byte) 110);
					spawn(804155, 317.53f, 516.63f, 350.77f, (byte) 0);
					spawn(daRaca(804135), 275.63f, 513.94f, 351.55f, (byte) 0);
					spawn(804175, 277.32f, 511.53f, 351.55f, (byte) 10);
					spawn(804168, 284.48f, 513.86f, 350.77f, (byte) 45);
				});
				depois(1100, () -> sendMsg(new SM_SYSTEM_MESSAGE(1404347))); // Ariel_10
				depois(6100, () -> {
					sendMsg(new SM_SYSTEM_MESSAGE(1404348)); // Asphel_10
					deleteAliveNpcs(804155);
				});
			}
		}
	}

	/** Controladores por proximidade e o veu da arena do boss 3. */
	private void vigia() {
		if (destruida)
			return;
		for (Player player : instance.getPlayersInside()) {
			if (player.isDead())
				continue;
			for (Npc ctrl : instance.getNpcs(804139, 804140, 804141, 804142, 804149, 804150, 804151, 804152, 804153, 804154)) {
				if (ctrl.isDead() || !PositionUtil.isInRange(player, ctrl, ctrl.getObjectTemplate().getAggroRange(), false))
					continue;
				if (disparados.add(ctrl.getObjectId()))
					dispara(ctrl);
			}
			Npc boss3 = getNpc(224335);
			if (boss3 != null && !boss3.isDead() && player.getX() < 310 && veuBoss3.compareAndSet(false, true))
				spawn(VEU, 317.58f, 513.30f, 352.03f, (byte) 0); // captura: nasce com o jogador em x 309,7
		}
	}

	private void dispara(Npc ctrl) {
		int[] falas = FALAS.get(ctrl.getNpcId());
		if (falas != null) {
			sendMsg(new SM_SYSTEM_MESSAGE(falas[0]));
			depois(5000, () -> {
				sendMsg(new SM_SYSTEM_MESSAGE(falas[1]));
				ctrl.getController().delete();
			});
			return;
		}
		switch (ctrl.getNpcId()) {
			case 804139 -> { // area do primeiro named: fecha o caminho ate ele morrer
				sendMsg(new SM_SYSTEM_MESSAGE(1404333)); // Ariel_03
				sendMsg(new SM_SYSTEM_MESSAGE(1404456)); // Named_Kill_UI_Start
				depois(1000, () -> spawn(VEU, 610.01f, 617.78f, 360.93f, (byte) 0));
				depois(4300, () -> {
					sendMsg(new SM_SYSTEM_MESSAGE(1404334)); // Asphel_03
					ctrl.getController().delete();
				});
			}
			case 804140 -> { // boss 1 (o controlador fica)
				spawn(224333, 609.15f, 707.29f, 355.11f, (byte) 90);
				depois(2100, () -> {
					sendMsg(new SM_SYSTEM_MESSAGE(1404444)); // Boss1_01
					sendMsg(new SM_SYSTEM_MESSAGE(1404455)); // Boss_Kill_UI_Start
				});
			}
			case 804141 -> { // boss 2
				sendMsg(new SM_SYSTEM_MESSAGE(1404446)); // Boss2_01
				depois(450, () -> ctrl.getController().delete());
				depois(900, () -> spawn(224334, 477.38f, 513.57f, 342.19f, (byte) 90));
			}
			case 804142 -> { // boss 3
				sendMsg(new SM_SYSTEM_MESSAGE(1404448)); // Boss3_01
				depois(400, () -> ctrl.getController().delete());
				depois(900, () -> spawn(224335, 287.60f, 513.26f, 350.77f, (byte) 0));
			}
		}
	}

	/** Forma de Daeva do Tempo da classe, pela pilha do cliente (BM_D_START = Brawler Asmodiano). */
	private SkillTemplate forma(Player player) {
		String classe = FORMA.get(player.getPlayerClass());
		if (classe == null)
			return null;
		List<SkillTemplate> t = DataManager.SKILL_DATA
			.getSkillTemplatesByStack(classe + (player.getRace() == Race.ELYOS ? "_L_START" : "_D_START"));
		return t == null || t.isEmpty() ? null : t.get(0);
	}

	private void aplicaForma(Player player) {
		SkillTemplate forma = forma(player);
		if (forma == null || forma.getEffects() == null) {
			log.warn("Land of Shadows: sem forma de Daeva do Tempo com efeito para " + player.getPlayerClass() + " " + player.getRace());
			return;
		}
		SkillEngine.getInstance().applyEffectDirectly(forma, forma.getLvl(), player, player);
	}

	private int daRaca(int npcIdAsmodiano) {
		if (raca != Race.ELYOS)
			return npcIdAsmodiano;
		return npcIdAsmodiano == 804135 ? 804134 : npcIdAsmodiano - ELYOS_DELTA;
	}

	/** Apaga o NPC vivo desse id mais proximo do ponto (varios 804145 e guardas repetidos no mapa). */
	private void apaga(int npcId, float x, float y) {
		instance.getNpcs(npcId).stream().filter(n -> !n.isDead())
			.min(Comparator.comparingDouble(n -> PositionUtil.getDistance(n.getX(), n.getY(), x, y)))
			.filter(n -> PositionUtil.getDistance(n.getX(), n.getY(), x, y) < 5)
			.ifPresent(n -> n.getController().delete());
	}

	private void depois(int ms, Runnable r) {
		ThreadPoolManager.getInstance().schedule(() -> {
			if (!destruida)
				r.run();
		}, ms);
	}
}
