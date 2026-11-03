package quest.gelkmaros;

import static com.aionemu.gameserver.model.DialogAction.USE_OBJECT;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;

/**
 * Campanha 20162 In Search of Shulack Fugitives. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20162.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20162InSearchOfShulackFugitives extends CampaignQuestHandler {

	private static final int BOX = 700812; // DF4_FOBJ_Q21105

	public _20162InSearchOfShulackFugitives() {
		super(20162, 20161);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799248); // Vesvola
		talk(1, 2, 2, 799280); // Shulack_DF4_3
		check(2, 3, 3, 799280); // seiva do Rotron (quest_monster drop@2); check_ok -> SELECT4
		talk(3, 4, 4, 799280); // Shulack_DF4_3 (select4)
		talk(4, 5, 5, 799366); // Shulack_DF4_6, achado na caixa DF4_FOBJ_Q21105 (ver onDialogEvent)
		talk(5, 6, 6, 799280); // Shulack_DF4_3 (select6)
		talk(6, 7, REWARD, 799276); // Shulack_DF4_4, select7 SET_SUCCEED
		reward(799268); // Nysdvor
	}

	@Override
	public void register() {
		super.register();
		qe.registerQuestNpc(BOX).addOnTalkEvent(questId);
		qe.registerCanAct(questId, BOX);
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		// handler 4.8 da 21105 (a quest de origem): a caixa solta o shulack ou um monstro e volta depois
		if (env.getTargetId() == BOX && env.getDialogActionId() == USE_OBJECT) {
			QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
			if (qs == null || qs.getStatus() != QuestStatus.START || qs.getQuestVarById(0) != 4)
				return false;
			Npc box = (Npc) env.getVisibleObject();
			spawnForFiveMinutes(Rnd.nextBoolean() ? 799366 : 216086, box.getPosition());
			box.getController().deleteAndScheduleRespawn();
			return true;
		}
		return super.onDialogEvent(env);
	}
}
