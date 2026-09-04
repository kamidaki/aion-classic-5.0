package ai;

import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.ai.BombTemplate;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("bomb")
public class BombAi extends AggressiveNpcAI
{
	private BombTemplate template;
	
	@Override
	protected void handleSpawned() {
		bombSkill();
	}
	
	private void bombSkill() {
		template = DataManager.AI_DATA.getAiTemplate().get(getNpcId()).getBombs().getBombTemplate();
		ThreadPoolManager.getInstance().schedule(new Runnable() {
			@Override
			public void run() {
				useSkill(template.getSkillId());
			}
		}, template.getCd());
	}
	
	private void useSkill(int skill) {
		AIActions.targetSelf(this);
		AIActions.useSkill(this, skill);
		int duration = DataManager.SKILL_DATA.getSkillTemplate(skill).getDuration();
		ThreadPoolManager.getInstance().schedule(new Runnable() {
			@Override
			public void run() {
				AIActions.deleteOwner(BombAi.this);
			}
		}, duration != 0 ? duration + 1000 : 0);
	}
}