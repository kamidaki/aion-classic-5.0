package com.aionemu.gameserver.questEngine.handlers;

import static com.aionemu.gameserver.model.DialogAction.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.QuestService;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.world.zone.ZoneName;

/**
 * Campanha (category1=mission) do Classic 5.0 descrita por uma tabela de etapas.
 * <p>
 * A tabela sai dos dados oficiais do cliente: o {@code quest_summary} de {@code dialogs/quest/quest_qNNNNN.html} dá a ordem das
 * etapas (a var 0 é a etapa 0), as páginas {@code selectN} dão o diálogo de cada NPC e {@code quest_script_monster.csv} fixa a var das
 * etapas de abate, área sensorial e uso de item ({@code Progress(n)}, {@code Progress(a~!b)}, {@code SECTION_0==n; SECTION_1<k}).
 * <p>
 * Comportamento medido nas capturas (subida-1-60, outros2 de 22/09):
 * <ul>
 * <li>a campanha entra sozinha em START (sem NPC de aceite) quando o nível e a anterior da cadeia permitem, e as seguintes aparecem
 * LOCKED;</li>
 * <li>{@code selectN} → {@code selectN_1}...: o cliente manda a própria página como ação e o servidor devolve a página;</li>
 * <li>a ação final ({@code SETPROn}, {@code SET_SUCCEED}) grava a var, manda o S_QUEST e fecha o diálogo (página 0);</li>
 * <li>no NPC de recompensa: {@code select_success} (10002) → ação 1009 → página de recompensa → ação 8..23 → COMPLETE com var 0, e a
 * seguinte da cadeia vai de LOCKED para START no mesmo instante.</li>
 * </ul>
 */
public abstract class CampaignQuestHandler extends AbstractQuestHandler {

	/** Próxima var que marca a missão como pronta para recompensa (REWARD). */
	protected static final int REWARD = -1;
	private static final int SELECT_SUCCESS = 10002;
	private static final int CHECK_OK = 10000;
	private static final int CHECK_FAIL = 10001;
	/** Cada {@code selectN} ocupa 341 IDs de página (select1 = 1011, select2 = 1352...); as subpáginas ficam dentro do bloco. */
	private static final int PAGE_BLOCK = 341;

	private final int[] preQuests;
	private final List<Step> steps = new ArrayList<>();
	private final Set<Integer> rewardNpcs = new LinkedHashSet<>();
	/** Var em que o NPC de recompensa fecha a missão ainda em START (-1 = só a partir de REWARD). */
	private int rewardFromVar = -1;
	/** Página do NPC de recompensa nessa var (0 = select_success). */
	private int rewardFromPage;

	protected CampaignQuestHandler(int questId, int... preQuests) {
		super(questId);
		this.preQuests = preQuests;
		defineSteps();
	}

	/** Declara as etapas com os métodos abaixo, na ordem do {@code quest_summary}. */
	protected abstract void defineSteps();

	private enum Kind {
		TALK, CHECK, KILL, KILL_SECTION, SENSORY, USE_OBJECT, USE_OBJECTS, ITEM_USE, ENTER_WORLD
	}

	static final class Step {

		final Kind kind;
		final int var;
		final int next;
		final int[] ids;
		int page;
		int count = 1;
		int slot;
		int itemId;
		String zone;
		float x, y, z, radius;
		int giveItemId, giveItemCount;
		boolean rewardAtEnd;
		int failPage = CHECK_FAIL;
		boolean okShowsReward;
		final Map<Integer, Integer> branches = new HashMap<>();

		Step(Kind kind, int var, int next, int... ids) {
			this.kind = kind;
			this.var = var;
			this.next = next;
			this.ids = ids;
		}

		boolean has(int id) {
			for (int i : ids)
				if (i == id)
					return true;
			return false;
		}
	}

	private Step add(Step step) {
		steps.add(step);
		return step;
	}

	/** Conversa na var {@code var}: página {@code selectN} e ação final ({@code SETPROn}) que leva a {@code next}. */
	protected final void talk(int var, int selectN, int next, int... npcIds) {
		add(new Step(Kind.TALK, var, next, npcIds)).page = page(selectN);
	}

	/** Conversa que entrega item de trabalho na ação final (ex.: a Clodia da 10160 dá o frasco vazio). */
	protected final void talkGive(int var, int selectN, int next, int itemId, int count, int... npcIds) {
		Step s = add(new Step(Kind.TALK, var, next, npcIds));
		s.page = page(selectN);
		s.giveItemId = itemId;
		s.giveItemCount = count;
	}

	/** Ação final alternativa da última etapa declarada (ex.: 10161 {@code SETPRO7} pula as correntes de vento). */
	protected final void branch(int dialogActionId, int next) {
		steps.get(steps.size() - 1).branches.put(dialogActionId, next);
	}

	/** {@code CHECK_USER_HAS_QUEST_ITEM}: confere os {@code collect_items} do quest_data, tira do inventário e vai a {@code next}. */
	protected final void check(int var, int selectN, int next, int... npcIds) {
		add(new Step(Kind.CHECK, var, next, npcIds)).page = page(selectN);
	}

	/**
	 * Conferência que já entrega: com os itens, REWARD e página de recompensa; sem, a página {@code failSelectN} (10235: select2 CHECK,
	 * select5 FINISH_DIALOG, sem check_user_item_ok).
	 */
	protected final void checkReward(int var, int selectN, int failSelectN, int... npcIds) {
		Step s = add(new Step(Kind.CHECK, var, REWARD, npcIds));
		s.page = page(selectN);
		s.failPage = page(failSelectN);
		s.okShowsReward = true;
		reward(npcIds);
	}

	/** Abates que somam na própria var 0: {@code Progress(a~!b)} = {@code kill(a, b - a, ...)}; termina em {@code b}. */
	protected final void kill(int fromVar, int count, int... npcIds) {
		add(new Step(Kind.KILL, fromVar, fromVar + count, npcIds)).count = count;
	}

	/** Como {@link #kill}, mas o último abate já deixa a missão em REWARD. */
	protected final void killToReward(int fromVar, int count, int... npcIds) {
		Step s = add(new Step(Kind.KILL, fromVar, fromVar + count, npcIds));
		s.count = count;
		s.rewardAtEnd = true;
	}

	/** Abates que somam em outra var: {@code SECTION_0==var; SECTION_slot<count}; termina em {@code next}. */
	protected final void killSection(int var, int slot, int count, int next, int... npcIds) {
		Step s = add(new Step(Kind.KILL_SECTION, var, next, npcIds));
		s.slot = slot;
		s.count = count;
	}

	/** Área sensorial ({@code sourceType=sensoryArea}): chegar perto do NPC invisível. */
	protected final void sensory(int var, int next, int npcId) {
		add(new Step(Kind.SENSORY, var, next, npcId));
	}

	/** Objeto sem página ({@code quest_use_item}): terminar a barra de uso avança a var. */
	protected final void useObject(int var, int next, int... npcIds) {
		add(new Step(Kind.USE_OBJECT, var, next, npcIds));
	}

	/** Vários usos do mesmo tipo de objeto, um por var: {@code useObjects(a, n)} vai de {@code a} a {@code a + n}. */
	protected final void useObjects(int fromVar, int count, int... npcIds) {
		add(new Step(Kind.USE_OBJECTS, fromVar, fromVar + count, npcIds)).count = count;
	}

	/** Uso de item em área ({@code sourceType=itemUseArea}): a zona {@code ITEM_USE} do servidor. */
	protected final void itemUseArea(int var, int next, int itemId, String zoneName) {
		Step s = add(new Step(Kind.ITEM_USE, var, next));
		s.itemId = itemId;
		s.zone = zoneName;
	}

	/**
	 * Uso de item em área que o servidor não tem como zona: raio em torno do marcador oficial do {@code mission_mission0.xml} do cliente
	 * (o polígono da {@code usearea_*} não está nos dados extraídos).
	 */
	protected final void itemUseAt(int var, int next, int itemId, int worldId, float x, float y, float z, float radius) {
		Step s = add(new Step(Kind.ITEM_USE, var, next, worldId));
		s.itemId = itemId;
		s.x = x;
		s.y = y;
		s.z = z;
		s.radius = radius;
	}

	/** Uso de item do cubo em qualquer lugar (ex.: 10168 {@code ([%17]/1)} com o cristal de memória). */
	protected final void itemUse(int var, int next, int itemId) {
		add(new Step(Kind.ITEM_USE, var, next)).itemId = itemId;
	}

	/** Chegar a um mapa. */
	protected final void enterWorld(int var, int next, int worldId) {
		add(new Step(Kind.ENTER_WORLD, var, next, worldId));
	}

	/** NPC que entrega a recompensa (última etapa do {@code quest_summary}). */
	protected final void reward(int... npcIds) {
		for (int id : npcIds)
			rewardNpcs.add(id);
	}

	/**
	 * NPC de recompensa que fecha a missão ainda em START, na var {@code var}: a última etapa não tem página própria, só o
	 * {@code select_success}. Captura outros2 (22/09, 22100): 10002 -> ação 1009 -> S_QUEST st=4 -> página de recompensa.
	 */
	protected final void rewardAt(int var, int... npcIds) {
		reward(npcIds);
		rewardFromVar = var;
	}

	/** Como {@link #rewardAt}, mas o NPC abre uma página própria ({@code selectN} com SELECT_QUEST_REWARD), ex.: 10233 select2. */
	protected final void rewardAtPage(int var, int selectN, int... npcIds) {
		rewardAt(var, npcIds);
		rewardFromPage = page(selectN);
	}

	private static int page(int selectN) {
		return 1011 + (selectN - 1) * PAGE_BLOCK;
	}

	@Override
	public void register() {
		qe.registerOnLevelChanged(questId);
		qe.registerOnQuestCompleted(questId);
		for (Step s : steps) {
			switch (s.kind) {
				case TALK, CHECK -> {
					for (int id : s.ids) {
						qe.registerQuestNpc(id).addOnTalkEvent(questId);
						qe.registerCanAct(questId, id); // só vale para objeto quest_use_item com página (ex.: obelisco 730225 da 10161)
					}
				}
				case KILL, KILL_SECTION -> {
					for (int id : s.ids)
						qe.registerQuestNpc(id).addOnKillEvent(questId);
				}
				case SENSORY -> qe.registerQuestNpc(s.ids[0]).addOnAtDistanceEvent(questId);
				case USE_OBJECT, USE_OBJECTS -> {
					for (int id : s.ids) {
						qe.registerQuestNpc(id).addOnTalkEvent(questId);
						qe.registerCanAct(questId, id);
					}
				}
				case ITEM_USE -> qe.registerQuestItem(s.itemId, questId);
				case ENTER_WORLD -> qe.registerOnEnterWorld(questId);
			}
		}
		for (int id : rewardNpcs)
			qe.registerQuestNpc(id).addOnTalkEvent(questId);
	}

	private QuestState activeState(Player player) {
		QuestState qs = player.getQuestStateList().getQuestState(questId);
		return qs != null && qs.getStatus() == QuestStatus.START ? qs : null;
	}

	private Step current(QuestState qs, Kind kind) {
		int var = qs.getQuestVarById(0);
		for (Step s : steps) {
			if (s.kind != kind)
				continue;
			if (kind == Kind.KILL || kind == Kind.USE_OBJECTS ? var >= s.var && var < s.next : var == s.var)
				return s;
		}
		return null;
	}

	/** Grava a próxima var (zerando os contadores das outras) ou REWARD. */
	static void apply(QuestState qs, int next) {
		if (next == REWARD)
			qs.setStatus(QuestStatus.REWARD);
		else
			qs.setQuestVar(next);
	}

	/** {@link #apply} + S_QUEST + {@link #onAdvance}. */
	private void advance(QuestEnv env, QuestState qs, int next) {
		int from = qs.getQuestVarById(0);
		apply(qs, next);
		updateQuestStatus(env);
		onAdvance(env, from, next);
	}

	/** Ação própria da missão depois de uma etapa (surgir NPC, entregar item...). {@code next} é {@link #REWARD} ao fechar. */
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
	}

	/** O que responder a uma ação de diálogo; decidido só sobre o estado, sem tocar no jogador. */
	record Reply(Type type, int value, Step step) {

		enum Type {
			NONE, PAGE, ADVANCE, CHECK, END, CLOSE, REWARD_NOW
		}

		static final Reply NONE = new Reply(Type.NONE, 0, null);
		static final Reply CLOSE = new Reply(Type.CLOSE, 0, null);
		static final Reply END = new Reply(Type.END, 0, null);

		static Reply page(int page) {
			return new Reply(Type.PAGE, page, null);
		}

		static Reply advance(int next, Step step) {
			return new Reply(Type.ADVANCE, next, step);
		}
	}

	/**
	 * @param openOnUse
	 *          USE_OBJECT abre a página da etapa: objeto de quest (barra de uso) ou NPC sem menu próprio. NPC de diálogo com menu responde a
	 *          página 10 e a quest só abre com QUEST_SELECT (capturas de 14/09).
	 */
	Reply decide(QuestState qs, int targetId, int action, boolean openOnUse) {
		if (qs == null)
			return Reply.NONE;
		if (qs.getStatus() == QuestStatus.REWARD) {
			if (!rewardNpcs.contains(targetId))
				return Reply.NONE;
			// outros2 (22/09, 20541): com a recompensa pendente neste NPC, o clique já abre o select_success
			if (action == QUEST_SELECT || action == USE_OBJECT)
				return Reply.page(SELECT_SUCCESS);
			if (action == CHECK_USER_HAS_QUEST_ITEM) // a conferência do último NPC já passou: segue para a recompensa
				return Reply.page(CHECK_OK);
			if (action == FINISH_DIALOG)
				return Reply.CLOSE;
			return Reply.END;
		}
		if (qs.getStatus() != QuestStatus.START)
			return Reply.NONE;

		int var = qs.getQuestVarById(0);
		if (var == rewardFromVar && rewardNpcs.contains(targetId)) {
			if (action == QUEST_SELECT || action == USE_OBJECT && openOnUse)
				return Reply.page(rewardFromPage != 0 ? rewardFromPage : SELECT_SUCCESS);
			if (rewardFromPage != 0 && action > rewardFromPage && action < rewardFromPage + PAGE_BLOCK)
				return Reply.page(action);
			if (action == SELECT_QUEST_REWARD)
				return new Reply(Reply.Type.REWARD_NOW, REWARD, null);
			if (action == FINISH_DIALOG)
				return Reply.CLOSE;
		}
		for (Step s : steps) {
			if (!s.has(targetId))
				continue;
			switch (s.kind) {
				case TALK, CHECK -> {
					if (s.var == var)
						return decideTalk(s, action, openOnUse);
				}
				case USE_OBJECT -> {
					if (s.var == var && action == USE_OBJECT)
						return Reply.advance(s.next, s);
				}
				case USE_OBJECTS -> {
					if (var >= s.var && var < s.next && action == USE_OBJECT)
						return Reply.advance(var + 1, s);
				}
				default -> {
				}
			}
		}
		return Reply.NONE;
	}

	private static Reply decideTalk(Step s, int action, boolean openOnUse) {
		if (action == QUEST_SELECT || action == s.page || action == USE_OBJECT && openOnUse)
			return Reply.page(s.page);
		if (action == FINISH_DIALOG)
			return Reply.CLOSE;
		Integer branchNext = s.branches.get(action);
		if (branchNext != null)
			return Reply.advance(branchNext, s);
		if (s.kind == Kind.CHECK && action == CHECK_USER_HAS_QUEST_ITEM)
			return new Reply(Reply.Type.CHECK, s.next, s);
		if (s.kind == Kind.TALK && (action >= SETPRO1 && action <= SETPRO20 || action == SET_SUCCEED))
			return Reply.advance(s.next, s);
		if (action > s.page && action < s.page + PAGE_BLOCK) // subpáginas selectN_1, selectN_1_1...
			return Reply.page(action);
		return Reply.NONE;
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
		boolean openOnUse = !isDialogNpc(env) || isUseItemObject(env);
		Reply reply = decide(qs, env.getTargetId(), env.getDialogActionId(), openOnUse);
		switch (reply.type()) {
			case PAGE -> {
				return sendQuestDialog(env, reply.value());
			}
			case CLOSE -> {
				return closeDialogWindow(env);
			}
			case END -> {
				return sendQuestEndDialog(env);
			}
			case REWARD_NOW -> {
				advance(env, qs, REWARD);
				return sendQuestEndDialog(env);
			}
			case CHECK -> {
				Step s = reply.step();
				if (!QuestService.collectItemCheck(env, true))
					return sendQuestDialog(env, s.failPage);
				advance(env, qs, reply.value());
				return s.okShowsReward ? sendQuestEndDialog(env) : sendQuestDialog(env, CHECK_OK);
			}
			case ADVANCE -> {
				Step s = reply.step();
				if (s.giveItemId != 0 && !giveQuestItem(env, s.giveItemId, s.giveItemCount))
					return closeDialogWindow(env);
				advance(env, qs, reply.value());
				// objeto só avança; conversa fecha a janela (página 0), como no oficial
				return s.kind == Kind.USE_OBJECT || s.kind == Kind.USE_OBJECTS || closeDialogWindow(env);
			}
			default -> {
				return false;
			}
		}
	}

	private static boolean isDialogNpc(QuestEnv env) {
		return env.getVisibleObject() instanceof Npc npc && npc.getObjectTemplate().isDialogNpc();
	}

	/** Objeto de quest com barra de uso: o USE_OBJECT só chega depois da barra, e é ele que abre a página. */
	private static boolean isUseItemObject(QuestEnv env) {
		return env.getVisibleObject() instanceof Npc npc
			&& ("quest_use_item".equals(npc.getObjectTemplate().getAiName()) || "quest_use_npc".equals(npc.getObjectTemplate().getAiName()));
	}

	/** Resultados de {@link #countKill} além da var/REWARD em que a etapa fechou. */
	static final int KILL_IGNORED = Integer.MIN_VALUE, KILL_COUNTED = Integer.MIN_VALUE + 1;

	/** Conta o abate no estado; devolve {@link #KILL_IGNORED}, {@link #KILL_COUNTED} ou a var/REWARD em que a etapa fechou. */
	int countKill(QuestState qs, int npcId) {
		if (qs == null || qs.getStatus() != QuestStatus.START)
			return KILL_IGNORED;
		Step s = current(qs, Kind.KILL);
		if (s != null && s.has(npcId)) {
			int var = qs.getQuestVarById(0) + 1;
			if (var < s.next) {
				qs.setQuestVarById(0, var);
				return KILL_COUNTED;
			}
			int next = s.rewardAtEnd ? REWARD : s.next;
			apply(qs, next);
			return next;
		}
		int var = qs.getQuestVarById(0);
		for (Step sec : steps) {
			if (sec.kind != Kind.KILL_SECTION || sec.var != var || !sec.has(npcId))
				continue;
			int kills = qs.getQuestVarById(sec.slot);
			if (kills >= sec.count)
				return KILL_IGNORED;
			qs.setQuestVarById(sec.slot, kills + 1);
			if (!sectionsDone(qs, var))
				return KILL_COUNTED;
			apply(qs, sec.next);
			return sec.next;
		}
		return KILL_IGNORED;
	}

	@Override
	public boolean onKillEvent(QuestEnv env) {
		QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
		int from = qs == null ? 0 : qs.getQuestVarById(0);
		int result = countKill(qs, env.getTargetId());
		if (result == KILL_IGNORED)
			return false;
		updateQuestStatus(env);
		if (result != KILL_COUNTED)
			onAdvance(env, from, result);
		return true;
	}

	/** 10162: {@code SECTION_1<1; SECTION_2<1; SECTION_3<1} na mesma var 0 -- só avança com todas completas. */
	private boolean sectionsDone(QuestState qs, int var) {
		for (Step s : steps)
			if (s.kind == Kind.KILL_SECTION && s.var == var && qs.getQuestVarById(s.slot) < s.count)
				return false;
		return true;
	}

	@Override
	public boolean onAtDistanceEvent(QuestEnv env) {
		QuestState qs = activeState(env.getPlayer());
		if (qs == null)
			return false;
		Step s = current(qs, Kind.SENSORY);
		if (s == null || !s.has(env.getTargetId()))
			return false;
		advance(env, qs, s.next);
		return true;
	}

	@Override
	public HandlerResult onItemUseEvent(QuestEnv env, Item item) {
		QuestState qs = activeState(env.getPlayer());
		if (qs == null)
			return HandlerResult.UNKNOWN;
		Step s = current(qs, Kind.ITEM_USE);
		if (s == null || s.itemId != item.getItemId())
			return HandlerResult.UNKNOWN;
		Player player = env.getPlayer();
		if (s.zone != null && !player.isInsideZone(ZoneName.get(s.zone)))
			return HandlerResult.FAILED;
		if (s.radius > 0 && (player.getWorldId() != s.ids[0] || !PositionUtil.isInRange(player, s.x, s.y, s.z, s.radius)))
			return HandlerResult.FAILED;
		if (item.getItemTemplate().getActions() != null) { // o próprio item age (ex.: disfarce 10170 = skill 2252); o CM_USE_ITEM executa a ação
			advance(env, qs, s.next);
			return HandlerResult.SUCCESS;
		}
		return HandlerResult.fromBoolean(useQuestItem(env, item, s.var, s.next == REWARD ? s.var : s.next, s.next == REWARD));
	}

	@Override
	public boolean onEnterWorldEvent(QuestEnv env) {
		QuestState qs = activeState(env.getPlayer());
		if (qs == null)
			return false;
		Step s = current(qs, Kind.ENTER_WORLD);
		if (s == null || env.getPlayer().getWorldId() != s.ids[0])
			return false;
		advance(env, qs, s.next);
		return true;
	}

	@Override
	public void onLevelChangedEvent(Player player) {
		defaultOnLevelChangedEvent(player, preQuests);
	}

	@Override
	public void onQuestCompletedEvent(QuestEnv env) {
		defaultOnQuestCompletedEvent(env, preQuests);
	}
}
