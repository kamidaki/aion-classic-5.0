package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlList;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.Race;

/**
 * Missões da Legion (legion/legion_mission.xml, gerado do europe/PC/client_achievement_guild.xml e do PC/client_achievement_guild_action.xml).
 */
@XmlRootElement(name = "legion_mission")
@XmlAccessorType(XmlAccessType.FIELD)
public class LegionMissionData {

	@XmlElement(name = "mission", required = true)
	private List<Mission> missionList = new ArrayList<>();

	@XmlElement(name = "action_template", required = true)
	private List<Action> actionList = new ArrayList<>();

	@XmlTransient
	private final Map<Integer, Mission> missions = new HashMap<>();

	@XmlTransient
	private final Map<Integer, Action> actions = new HashMap<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		for (Action action : actionList) {
			action.targets = action.targetList == null ? Set.of() : Set.copyOf(action.targetList);
			action.targetList = null;
			actions.put(action.id, action);
		}
		for (Mission mission : missionList) {
			for (ActionRef ref : mission.actionRefs)
				if (!actions.containsKey(ref.id))
					throw new IllegalArgumentException("Legion mission " + mission.id + " uses unknown action " + ref.id);
			missions.put(mission.id, mission);
		}
		actionList = null;
	}

	public Mission getMission(int id) {
		return missions.get(id);
	}

	public Action getAction(int id) {
		return actions.get(id);
	}

	/**
	 * @return as missões de um período para a raça e a atividade da Legion, na ordem do id
	 */
	public List<Mission> getMissions(Period period, Race race, Activity activity) {
		return missionList.stream().filter(m -> m.period == period && m.race.matches(race) && m.activity == activity).toList();
	}

	public int size() {
		return missions.size();
	}

	@XmlType(name = "LegionMissionPeriod")
	public enum Period {
		DAILY,
		WEEKLY,
		RETURN
	}

	@XmlType(name = "LegionMissionActivity")
	public enum Activity {
		NONE,
		PVP,
		PVE,
		GATHER
	}

	@XmlType(name = "LegionMissionActionType")
	public enum ActionType {
		QUESTCLEAR,
		HUNT,
		ENTERWORLD,
		COLLECTITEM,
		ITEMPLAY,
		PVP,
		GATHERING,
		POINTCHANGE,
		USECRUSH,
		BUYNPC,
		VENDOR
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionMission")
	public static class Mission {

		@XmlAttribute(required = true)
		private int id;

		@XmlAttribute(required = true)
		private String name;

		@XmlAttribute(required = true)
		private Period period;

		@XmlAttribute(required = true)
		private LegionDonationData.GroupRace race;

		@XmlAttribute(required = true)
		private Activity activity;

		@XmlAttribute(name = "min_level", required = true)
		private int minLevel;

		@XmlAttribute(name = "max_level", required = true)
		private int maxLevel;

		@XmlElement(name = "action", required = true)
		private List<ActionRef> actionRefs = new ArrayList<>();

		@XmlElement(name = "stage", required = true)
		private List<Stage> stages = new ArrayList<>();

		public int getId() {
			return id;
		}

		public Period getPeriod() {
			return period;
		}

		public List<Integer> getActionIds() {
			return actionRefs.stream().map(r -> r.id).toList();
		}

		public List<Stage> getStages() {
			return Collections.unmodifiableList(stages);
		}

		public boolean isLevelAllowed(int level) {
			return level >= minLevel && level <= maxLevel;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionMissionActionRef")
	private static class ActionRef {

		@XmlAttribute(required = true)
		private int id;
	}

	/**
	 * Estágio: com {@code count} ações concluídas a Legion ganha exp de crescimento, essência e fragmentos.
	 */
	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionMissionStage")
	public static class Stage {

		@XmlAttribute(required = true)
		private int count;

		@XmlAttribute(required = true)
		private int exp;

		@XmlAttribute(required = true)
		private int essence;

		@XmlAttribute(name = "essence_piece", required = true)
		private int essencePiece;

		public int getCount() {
			return count;
		}

		public int getExp() {
			return exp;
		}

		public int getEssence() {
			return essence;
		}

		public int getEssencePiece() {
			return essencePiece;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionMissionAction")
	public static class Action {

		@XmlAttribute(required = true)
		private int id;

		@XmlAttribute(required = true)
		private String name;

		@XmlAttribute(required = true)
		private ActionType type;

		@XmlAttribute
		private int code;

		@XmlAttribute(name = "max_progress", required = true)
		private int maxProgress;

		@XmlAttribute(name = "level_gap")
		private int levelGap;

		@XmlList
		@XmlElement(name = "items")
		private List<Integer> itemTargets;

		@XmlList
		@XmlElement(name = "npcs")
		private List<Integer> npcTargets;

		@XmlList
		@XmlElement(name = "quests")
		private List<Integer> questTargets;

		@XmlList
		@XmlElement(name = "worlds")
		private List<Integer> worldTargets;

		@XmlTransient
		private List<Integer> targetList;

		@XmlTransient
		private Set<Integer> targets;

		void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
			targetList = new ArrayList<>();
			for (List<Integer> list : List.of(nullToEmpty(itemTargets), nullToEmpty(npcTargets), nullToEmpty(questTargets), nullToEmpty(worldTargets)))
				targetList.addAll(list);
			itemTargets = npcTargets = questTargets = worldTargets = null;
		}

		private static List<Integer> nullToEmpty(List<Integer> list) {
			return list == null ? List.of() : list;
		}

		public int getId() {
			return id;
		}

		public ActionType getType() {
			return type;
		}

		/**
		 * @return código do tipo no S 0x15C (0 para os tipos que nenhuma captura mostrou)
		 */
		public int getCode() {
			return code;
		}

		public int getMaxProgress() {
			return maxProgress;
		}

		public int getLevelGap() {
			return levelGap;
		}

		/**
		 * @return true se o id (item, NPC, quest ou mundo, conforme o tipo) conta; tipos sem alvo (PvP, coleta) contam qualquer um
		 */
		public boolean matches(int targetId) {
			return targets.isEmpty() ? type == ActionType.PVP || type == ActionType.GATHERING : targets.contains(targetId);
		}
	}
}
