package com.aionemu.gameserver.model.team.legion;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Uma missão da Legion no período atual: instância (a mesma que o cliente recebe no S 0x15C e no S 0x15D), início do período, última
 * atualização, estágios já recompensados e o progresso de cada ação.
 * <p>
 * Dono: a diária e a de retorno são por personagem e a semanal é da Legion (escolha do usuário em 29/09; as capturas só têm um membro por Legion,
 * então não mostram de quem é o progresso).
 */
public class LegionMissionProgress {

	public enum Owner {
		PLAYER,
		LEGION
	}

	private final int missionId;
	private final long instanceId;
	private final long periodStart;
	private long lastUpdate;
	private int rewardedStages;
	private final List<Action> actions;

	public LegionMissionProgress(int missionId, long instanceId, long periodStart, long lastUpdate, int rewardedStages, List<Action> actions) {
		this.missionId = missionId;
		this.instanceId = instanceId;
		this.periodStart = periodStart;
		this.lastUpdate = lastUpdate;
		this.rewardedStages = rewardedStages;
		this.actions = new ArrayList<>(actions);
	}

	public int getMissionId() {
		return missionId;
	}

	public long getInstanceId() {
		return instanceId;
	}

	/**
	 * @return a última instância usada: a da missão e as das ações vêm em sequência, como no oficial (0x36A537 a 0x36A53C)
	 */
	public long getLastInstanceId() {
		return instanceId + actions.size();
	}

	public long getPeriodStart() {
		return periodStart;
	}

	public synchronized long getLastUpdate() {
		return lastUpdate;
	}

	public synchronized int getRewardedStages() {
		return rewardedStages;
	}

	public synchronized void setRewardedStages(int rewardedStages) {
		this.rewardedStages = rewardedStages;
	}

	public synchronized List<Action> getActions() {
		return actions.stream().map(Action::copy).toList();
	}

	public Action getAction(int actionId) {
		synchronized (this) {
			return actions.stream().filter(a -> a.actionId == actionId).findFirst().orElse(null);
		}
	}

	/**
	 * Soma progresso na ação, até o máximo.
	 *
	 * @return o novo progresso, ou -1 se a ação já estava concluída
	 */
	public synchronized int addProgress(int actionId, int amount, int maxProgress, long now) {
		Action action = actions.stream().filter(a -> a.actionId == actionId).findFirst().orElseThrow();
		if (action.progress >= maxProgress)
			return -1;
		action.progress = Math.min(maxProgress, action.progress + amount);
		action.lastUpdate = now;
		lastUpdate = now;
		return action.progress;
	}

	/**
	 * @return as ações "id:instância:progresso:atualização" separadas por ponto e vírgula, como gravadas no banco
	 */
	public synchronized String getActionsText() {
		return actions.stream().map(a -> a.actionId + ":" + a.instanceId + ":" + a.progress + ":" + a.lastUpdate).collect(Collectors.joining(";"));
	}

	public static List<Action> parseActions(String text) {
		List<Action> actions = new ArrayList<>();
		if (text != null)
			for (String part : text.split(";")) {
				if (part.isBlank())
					continue;
				String[] f = part.trim().split(":");
				actions.add(new Action(Integer.parseInt(f[0]), Long.parseLong(f[1]), Integer.parseInt(f[2]), Long.parseLong(f[3])));
			}
		return actions;
	}

	public static final class Action {

		private final int actionId;
		private final long instanceId;
		private int progress;
		private long lastUpdate;

		public Action(int actionId, long instanceId, int progress, long lastUpdate) {
			this.actionId = actionId;
			this.instanceId = instanceId;
			this.progress = progress;
			this.lastUpdate = lastUpdate;
		}

		private Action copy() {
			return new Action(actionId, instanceId, progress, lastUpdate);
		}

		public int getActionId() {
			return actionId;
		}

		public long getInstanceId() {
			return instanceId;
		}

		public int getProgress() {
			return progress;
		}

		public long getLastUpdate() {
			return lastUpdate;
		}
	}
}
