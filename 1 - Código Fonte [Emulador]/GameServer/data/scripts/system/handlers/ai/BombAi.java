package ai;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Future;

import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.ai.BombTemplate;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.utils.ThreadPoolManager;

@AIName("bomb")
public class BombAi extends AggressiveNpcAI {

	private BombTemplate template;
	private final List<Future<?>> tasks = new ArrayList<>();

	public BombAi() {
		super();
	}

	public BombAi(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleSpawned() {
		super.handleSpawned();
		bombSkill();
	}

	@Override
	protected void handleDied() {
		super.handleDied();
		cancelTasks();
	}

	@Override
	protected void handleDespawned() {
		super.handleDespawned();
		cancelTasks();
	}

	private void bombSkill() {
		template = DataManager.AI_DATA.getAiTemplate().get(getNpcId()).getBombs().getBombTemplate();
		addTask(ThreadPoolManager.getInstance().schedule(() -> useSkill(template.getSkillId()), template.getCd()));
	}

	private void addTask(Future<?> task) {
		if (task == null)
			return;
		synchronized (tasks) {
			tasks.add(task);
		}
	}

	private void cancelTasks() {
		synchronized (tasks) {
			for (Future<?> task : tasks) {
				if (task != null && !task.isDone())
					task.cancel(true);
			}
			tasks.clear();
		}
	}

	private void useSkill(int skill) {
		AIActions.targetSelf(this);
		AIActions.useSkill(this, skill);
		int duration = DataManager.SKILL_DATA.getSkillTemplate(skill).getDuration();
		addTask(ThreadPoolManager.getInstance().schedule(() -> AIActions.deleteOwner(BombAi.this), duration != 0 ? duration + 1000 : 0));
	}
}