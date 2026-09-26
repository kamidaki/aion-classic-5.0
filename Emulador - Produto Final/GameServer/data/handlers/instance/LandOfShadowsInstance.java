package instance;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.drop.DropItem;
import com.aionemu.gameserver.instance.handlers.GeneralInstanceHandler;
import com.aionemu.gameserver.instance.handlers.InstanceID;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.instance.InstanceBuff;
import com.aionemu.gameserver.model.templates.spawns.SpawnTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_STATS_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_UNK_01BD;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.drop.DropRegistrationService;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.WorldMapInstance;

/**
 * Land of Shadows (IDTutorialQ, 390000000): instancia das campanhas 10153/20153.
 * <p>
 * Roteiro medido na captura oficial subida-1-60-2026-08-28.pcapng (Asmodiano, S_WORLD 390000000 ate a saida pela
 * Inggril em 1.451 s). Tempos entre parenteses sao da captura, relativos ao gatilho de cada etapa.
 * <ul>
 * <li>Entrada: a forma de Daeva do Tempo da classe ({@code <FI|KN|...>_<L|D>_START}, ShapeChange do cliente). Ao se
 * afastar cerca de 5 m do ponto inicial, comecam as mensagens de abertura; 0,8 s depois surgem os dois primeiros
 * gossips e a Inggril/Inggness perto da entrada, e 4,4 s depois o veu (804145) da entrada some.</li>
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
	private static final int VAR_CHECKPOINT = 1;
	private static final int VAR_NORMAIS = 2;
	private static final int VAR_NAMEDS = 3;
	private static final int VAR_BOSSES = 4;
	private static final int BENCAO_REINO_DAS_SOMBRAS = 19;
	private static final int DURACAO_BENCAO = 86_400_000;
	private static final int ELYOS_DELTA = 10; // 8041(2x) Asmodiano -> 8041(1x) Elyos; 804135 -> 804134
	private static final float ENTRADA_X = 730.58f;
	private static final float ENTRADA_Y = 513.26f;
	private static final float DISTANCIA_GATILHO_ABERTURA = 5f;
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
	private final AtomicBoolean aberturaIniciada = new AtomicBoolean();
	private final AtomicBoolean veuBoss3 = new AtomicBoolean();
	private final AtomicInteger normaisMortos = new AtomicInteger();
	private final AtomicInteger namedsMortos = new AtomicInteger();
	private final AtomicInteger bossesMortos = new AtomicInteger();
	private final Set<Integer> disparados = ConcurrentHashMap.newKeySet();
	private final Map<Integer, InstanceBuff> bencaos = new ConcurrentHashMap<>();
	private volatile Race raca = Race.ASMODIANS;
	private volatile boolean destruida;
	private volatile boolean criada; // o spawn inicial do mapa vem antes do onInstanceCreate
	private Future<?> vigia;

	public LandOfShadowsInstance(WorldMapInstance instance) {
		super(instance);
	}

	@Override
	public void onEnterInstance(Player player) {
		raca = player.getRace();
		aplicaForma(player);
		aplicaBencao(player);
		if (!iniciado.compareAndSet(false, true)) {
			return;
		}
		QuestState qs = estadoTutorial(player);
		int checkpoint = qs == null ? 0 : qs.getQuestVarById(VAR_CHECKPOINT);
		if (qs != null && checkpoint == 0 && player.getX() < 700) { // compatibilidade com personagens salvos antes desta persistência
			checkpoint = player.getX() < 350 ? 8 : player.getX() < 540 ? 5 : player.getY() > 660 ? 2 : 1;
			qs.setQuestVarById(VAR_CHECKPOINT, checkpoint);
		}
		if (qs != null) {
			normaisMortos.set(qs.getQuestVarById(VAR_NORMAIS));
			namedsMortos.set(qs.getQuestVarById(VAR_NAMEDS));
			bossesMortos.set(qs.getQuestVarById(VAR_BOSSES));
		}
		if (raca == Race.ELYOS)
			for (Npc gossip : instance.getNpcs(804124, 804125, 804126, 804127, 804128, 804129, 804130, 804131, 804132, 804133)) {
				SpawnTemplate s = gossip.getSpawn();
				gossip.getController().delete();
				spawn(gossip.getNpcId() - ELYOS_DELTA, s.getX(), s.getY(), s.getZ(), s.getHeading());
			}
		if (checkpoint > 0)
			restauraCheckpoint(player, checkpoint);
		vigia = ThreadPoolManager.getInstance().scheduleAtFixedRate(this::vigia, 250, 250);
	}

	/** Inicia uma unica vez a sequencia oficial ao jogador deixar o ponto de entrada. */
	private void iniciaAbertura() {
		if (!aberturaIniciada.compareAndSet(false, true))
			return;
		gravaCheckpoint(1);
		sendMsg(new SM_SYSTEM_MESSAGE(1404349)); // STR_MSG_IDTutorialQ_Start_Buff_01
		sendMsg(new SM_SYSTEM_MESSAGE(1404329)); // Ariel_01
		depois(800, () -> {
			spawn(daRaca(804124), 681.97f, 521.97f, 338.43f, (byte) 0);
			spawn(daRaca(804135), 700.53f, 500.77f, 338.25f, (byte) 30);
			spawn(daRaca(804125), 649.47f, 529.19f, 339.62f, (byte) 105);
		});
		depois(4200, () -> sendMsg(new SM_SYSTEM_MESSAGE(1404457))); // Normal_Kill_UI_Start
		depois(4850, () -> enviaObjetivo(SM_UNK_01BD.NORMAL, 1)); // a captura usa contador interno 1 para exibir 0/20
		depois(4400, () -> {
			sendMsg(new SM_SYSTEM_MESSAGE(1404330)); // Asphel_01
			apaga(VEU, 675.36f, 518.71f);
		});
	}

	@Override
	public void onInstanceCreate() {
		criada = true;
	}

	@Override
	public void onSpawn(VisibleObject object) {
		// fogo de cenario (224328): na captura ele reacende 15 s depois de morrer lancando a 19389 (queimadura de 1 m)
		if (criada && object instanceof Npc npc && npc.getNpcId() == 224328)
			depois(500, () -> npc.getController().useSkill(19389));
	}

	@Override
	public void onLeaveInstance(Player player) {
		SkillTemplate forma = forma(player);
		if (forma != null)
			player.getEffectController().removeEffect(forma.getSkillId());
		InstanceBuff bencao = bencaos.remove(player.getObjectId());
		if (bencao != null)
			bencao.endEffect(player);
	}

	@Override
	public void onInstanceDestroy() {
		destruida = true;
		if (vigia != null)
			vigia.cancel(false);
	}

	@Override
	public void onDie(Npc npc) {
		atualizaObjetivos(npc.getNpcId());
		float x = npc.getX(), y = npc.getY(), z = npc.getZ();
		switch (npc.getNpcId()) {
			case 224305 -> apaga(VEU, 610.01f, 617.78f); // primeiro named: o veu que o 804139 fechou abre na morte dele
			case 224319 -> spawn(224320, x, y, z, npc.getHeading()); // Sikara Rider desmonta
			case 224317 -> spawn(224318, x, y, z, npc.getHeading()); // Pagati Strider desmonta
			case 224333 -> { // boss 1
				gravaCheckpoint(3);
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
				int rewardNpcId = npc.getNpcId() + nivelCubo(npc) - 1;
				spawn(rewardNpcId, x, y, z, (byte) 0);
			}
			case 804157, 804158, 804159, 804160 -> { // bau do boss 1 aberto
				gravaCheckpoint(4);
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
				gravaCheckpoint(6);
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
			case 804162, 804163, 804164, 804165 -> { // bau do boss 2 aberto
				gravaCheckpoint(7);
				sendMsg(new SM_SYSTEM_MESSAGE(1404447)); // Boss2_02
				apaga(VEU, 466.45f, 513.25f);
			}
			case 224335 -> { // boss 3
				gravaCheckpoint(9);
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
			if (!aberturaIniciada.get() && PositionUtil.getDistance(player.getX(), player.getY(), ENTRADA_X, ENTRADA_Y) >= DISTANCIA_GATILHO_ABERTURA)
				iniciaAbertura();
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
				depois(750, () -> enviaObjetivo(SM_UNK_01BD.NAMED, 1));
				depois(1000, () -> spawn(VEU, 610.01f, 617.78f, 360.93f, (byte) 0));
				depois(4300, () -> {
					sendMsg(new SM_SYSTEM_MESSAGE(1404334)); // Asphel_03
					ctrl.getController().delete();
				});
			}
			case 804140 -> { // boss 1 (o controlador fica)
				gravaCheckpoint(2);
				spawn(224333, 609.15f, 707.29f, 355.11f, (byte) 90);
				depois(2100, () -> {
					sendMsg(new SM_SYSTEM_MESSAGE(1404444)); // Boss1_01
					sendMsg(new SM_SYSTEM_MESSAGE(1404455)); // Boss_Kill_UI_Start
					depois(650, () -> enviaObjetivo(SM_UNK_01BD.BOSS, 1));
				});
			}
			case 804141 -> { // boss 2
				gravaCheckpoint(5);
				sendMsg(new SM_SYSTEM_MESSAGE(1404446)); // Boss2_01
				depois(450, () -> ctrl.getController().delete());
				depois(900, () -> spawn(224334, 477.38f, 513.57f, 342.19f, (byte) 90));
			}
			case 804142 -> { // boss 3
				gravaCheckpoint(8);
				sendMsg(new SM_SYSTEM_MESSAGE(1404448)); // Boss3_01
				depois(400, () -> ctrl.getController().delete());
				depois(900, () -> spawn(224335, 287.60f, 513.26f, 350.77f, (byte) 0));
			}
		}
	}

	/** Atualiza os tres contadores do painel. O protocolo usa progresso + 1 (1 exibe zero). */
	private void atualizaObjetivos(int npcId) {
		if (npcId >= 224300 && npcId <= 224316 && npcId != 224305 && npcId != 224310 && npcId != 224315)
			avancaObjetivo(normaisMortos, 20, SM_UNK_01BD.NORMAL, VAR_NORMAIS);
		else if (npcId == 224305 || npcId == 224310 || npcId == 224315 || npcId == 224318 || npcId == 224320)
			avancaObjetivo(namedsMortos, 5, SM_UNK_01BD.NAMED, VAR_NAMEDS);
		else if (npcId == 224333 || npcId == 224334 || npcId == 224335)
			avancaObjetivo(bossesMortos, 3, SM_UNK_01BD.BOSS, VAR_BOSSES);
	}

	private void avancaObjetivo(AtomicInteger progresso, int maximo, int objetivo, int varId) {
		int anterior;
		do {
			anterior = progresso.get();
			if (anterior >= maximo)
				return;
		} while (!progresso.compareAndSet(anterior, anterior + 1));
		int atual = anterior + 1;
		gravaVar(varId, atual);
		enviaObjetivo(objetivo, atual + 1);
	}

	private void enviaObjetivo(int objetivo, int contador) {
		PacketSendUtility.broadcastToMap(instance, new SM_UNK_01BD(objetivo, contador));
	}

	private int nivelCubo(Npc npc) {
		for (int skillId = 19984; skillId >= 19981; skillId--)
			if (npc.getEffectController().hasAbnormalEffect(skillId))
				return skillId - 19979; // 19981 = nivel 2, 19984 = nivel 5
		return 2; // o primeiro crescimento e garantido; fallback para acerto letal/efeito removido
	}

	@Override
	public void onDropRegistered(Npc npc, int winnerObj) {
		Set<DropItem> drops = DropRegistrationService.getInstance().getCurrentDropMap().get(npc.getObjectId());
		if (drops == null)
			return;
		int itemId;
		int count = 1;
		int npcId = npc.getNpcId();
		if (npcId >= 804157 && npcId <= 804160) {
			int enchant = Rnd.get((npcId - 804157) * 3 + 4, (npcId - 804157) * 3 + 6);
			itemId = 188058635 + enchant; // weapon +4..+15
		} else if (npcId >= 804162 && npcId <= 804165) {
			int enchant = Rnd.get((npcId - 804162) * 3 + 4, (npcId - 804162) * 3 + 6);
			itemId = 188058665 + enchant * 5; // shoes +4..+15
		} else if (npcId >= 804169 && npcId <= 804172) {
			int enchant = Rnd.get((npcId - 804169) * 3 + 4, (npcId - 804169) * 3 + 6);
			itemId = 188058662 + enchant * 5; // gloves +4..+15
		} else if (npcId == 804174) {
			itemId = 188058385;
		} else if (npcId == 804175) {
			itemId = 164000224;
			count = 30;
		} else {
			return;
		}
		drops.clear();
		drops.add(DropRegistrationService.getInstance().regDropItem(1, winnerObj, npcId, itemId, count));
	}

	private QuestState estadoTutorial(Player player) {
		int questId = player.getRace() == Race.ELYOS ? 10153 : 20153;
		QuestState qs = player.getQuestStateList().getQuestState(questId);
		return qs != null && qs.getStatus() == QuestStatus.START && qs.getQuestVarById(0) == 2 ? qs : null;
	}

	private void gravaCheckpoint(int checkpoint) {
		gravaVar(VAR_CHECKPOINT, checkpoint);
	}

	private void gravaVar(int varId, int value) {
		for (Player player : instance.getPlayersInside()) {
			QuestState qs = estadoTutorial(player);
			if (qs != null && qs.getQuestVarById(varId) != value)
				qs.setQuestVarById(varId, value);
		}
	}

	/** Reconstrói a etapa indispensável quando a instância vazia já foi destruída antes do login. */
	private void restauraCheckpoint(Player player, int checkpoint) {
		aberturaIniciada.set(true);
		aplicaBencao(player);
		apaga(VEU, 675.36f, 518.71f);
		if (getNpc(daRaca(804135)) == null)
			spawn(daRaca(804135), 700.53f, 500.77f, 338.25f, (byte) 30);
		enviaObjetivo(SM_UNK_01BD.NORMAL, normaisMortos.get() + 1);
		enviaObjetivo(SM_UNK_01BD.NAMED, namedsMortos.get() + 1);
		enviaObjetivo(SM_UNK_01BD.BOSS, bossesMortos.get() + 1);

		if (checkpoint >= 2)
			deleteAliveNpcs(804140);
		if (checkpoint >= 5)
			deleteAliveNpcs(804141);
		if (checkpoint >= 8)
			deleteAliveNpcs(804142);

		switch (checkpoint) {
			case 2 -> spawn(224333, 609.15f, 707.29f, 355.11f, (byte) 90);
			case 3 -> spawn(804156, 609.32f, 707.21f, 355.11f, (byte) 45);
			case 4 -> apaga(VEU, 600.27f, 675.67f);
			case 5 -> spawn(224334, 477.38f, 513.57f, 342.19f, (byte) 90);
			case 6 -> spawn(804161, 470.08f, 513.22f, 342.19f, (byte) 45);
			case 7 -> apaga(VEU, 466.45f, 513.25f);
			case 8 -> spawn(224335, 287.60f, 513.26f, 350.77f, (byte) 0);
			case 9 -> {
				apaga(VEU, 317.58f, 513.30f);
				spawn(804174, 277.25f, 516.51f, 351.55f, (byte) 110);
				spawn(daRaca(804135), 275.63f, 513.94f, 351.55f, (byte) 0);
				spawn(804175, 277.32f, 511.53f, 351.55f, (byte) 10);
				spawn(804168, 284.48f, 513.86f, 350.77f, (byte) 45);
			}
		}
	}

	private void aplicaBencao(Player player) {
		InstanceBuff bencao = bencaos.computeIfAbsent(player.getObjectId(), _ -> new InstanceBuff(BENCAO_REINO_DAS_SOMBRAS));
		bencao.applyEffect(player, DURACAO_BENCAO);
		// O icone IDTutorialQ_Buff e resolvido pelo cliente a partir do bonusattr 19 ao receber o novo bloco de stats.
		PacketSendUtility.sendPacket(player, new SM_STATS_INFO(player));
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
