package com.aionemu.gameserver.ai;

import java.util.Collection;

import com.aionemu.gameserver.controllers.observer.DialogObserver;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.RequestResponseHandler;
import com.aionemu.gameserver.network.aion.serverpackets.S_ASK;
import com.aionemu.gameserver.questEngine.QuestEngine;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.services.drop.DropRegistrationService;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Common AI actions for entities.
 * 
 * @author ATracer
 */
@SuppressWarnings("rawtypes")
public class AIActions {

	/**
	 * Despawn and delete owner
	 */
	public static void deleteOwner(AbstractAI ai) {
		ai.getOwner().getController().onDelete();
	}

	/**
	 * Target will die with all notifications using ai's owner as the last attacker
	 */
	public static void killSilently(AbstractAI ai, Creature target) {
		target.getController().onDie(ai.getOwner());
	}

	/**
	 * AI's owner will die
	 */
	public static void dieSilently(AbstractAI ai) {
		ai.getOwner().getController().onDie(ai.getOwner());
	}

	/**
	 * AI's owner will die from specified attacker
	 */
	public static void dieSilently(AbstractAI ai, Creature attacker) {
		ai.getOwner().getController().onDie(attacker != null ? attacker : ai.getOwner());
	}

	/**
	 * Use skill or add intention to use
	 */
	public static void useSkill(AbstractAI ai, int skillId) {
		ai.getOwner().getController().useSkill(skillId);
	}

	/**
	 * Effect will be created and applied to target with 100% success
	 */
	public static void applyEffect(AbstractAI ai, SkillTemplate template, Creature target) {
		Effect effect = new Effect(ai.getOwner(), target, template, template.getLvl(), 0);
		effect.setIsForcedEffect(true);
		effect.initialize();
		effect.applyEffect();
	}

	public static void applyEffectSelf(AbstractAI ai, int skillId) {
		SkillTemplate st = DataManager.SKILL_DATA.getSkillTemplate(skillId);
		if (st != null) {
			Effect effect = new Effect(ai.getOwner(), ai.getOwner(), st, 1, st.getEffectsDuration(skillId));
			effect.initialize();
			effect.applyEffect();
		}
	}

	public static void targetSelf(AbstractAI ai) {
		ai.getOwner().setTarget(ai.getOwner());
	}

	public static void targetCreature(AbstractAI ai, Creature target) {
		ai.getOwner().setTarget(target);
	}

	public static void handleUseItemFinish(AbstractAI ai, Player player) {
		if (ai.getPosition().isInstanceMap()) {
			ai.getPosition().getWorldMapInstance().getInstanceHandler().handleUseItemFinish(player, ((Npc) ai.getOwner()));
		} else {
			ai.getPosition().getWorld().getWorldMap(ai.getPosition().getMapId()).getWorldHandler().handleUseItemFinish(player, ((Npc) ai.getOwner()));
		}
	}

	public static void fireIndividualEvent(AbstractAI ai, Npc target) {
		target.getAi().onIndividualNpcEvent(ai.getOwner());
	}

	public static void fireNpcKillInstanceEvent(AbstractAI ai, Player player) {
		ai.getPosition().getWorldMapInstance().getInstanceHandler().onDie((Npc) ai.getOwner());
	}

	public static void registerDrop(AbstractAI ai, Player player, Collection<Player> registeredPlayers) {
		DropRegistrationService.getInstance().registerDrop((Npc) ai.getOwner(), player, registeredPlayers);
	}

	public static void scheduleRespawn(NpcAI ai) {
		ai.getOwner().getController().scheduleRespawn();
	}

	public static SelectDialogResult selectDialog(AbstractAI ai, Player player, int questId, int dialogId) {
		QuestEnv env = new QuestEnv(ai.getOwner(), player, questId, dialogId);
		boolean result = QuestEngine.getInstance().onDialog(env);
		return new SelectDialogResult(result, env);
	}

	public static final class SelectDialogResult {
		private final boolean success;
		private final QuestEnv env;

		private SelectDialogResult(boolean success, QuestEnv env) {
			this.success = success;
			this.env = env;
		}

		public boolean isSuccess() {
			return success;
		}

		public QuestEnv getEnv() {
			return env;
		}
	}

	/**
	 * Add RequestResponseHandler to player with senderId equal to objectId of AI owner
	 */
	public static void addRequest(AbstractAI ai, Player player, int requestId, AIRequest request, Object... requestParams) {
		addRequest(ai, player, requestId, ai.getObjectId(), request, requestParams);
	}

	/**
	 * Add RequestResponseHandler to player, which cancels request on movement
	 */
	public static void addRequest(AbstractAI ai, Player player, int requestId, int senderId, int range, final AIRequest request,
		Object... requestParams) {

		boolean requested = player.getResponseRequester().putRequest(requestId, new RequestResponseHandler(ai.getOwner()) {

			@Override
			public void denyRequest(Creature requester, Player responder) {
				request.denyRequest(requester, responder);
			}

			@Override
			public void acceptRequest(Creature requester, Player responder) {
				request.acceptRequest(requester, responder);
			}
		});

		if (requested) {
			if (range > 0) {
				player.getObserveController().addObserver(new DialogObserver(ai.getOwner(), player, range) {
					@Override
					public void tooFar(Creature requester, Player responder) {
						request.denyRequest(requester, responder);
					}
				});
			}
			PacketSendUtility.sendPacket(player, new S_ASK(requestId, senderId, range, requestParams));
		}
	}

	/**
	 * Add RequestResponseHandler to player
	 */
	public static void addRequest(AbstractAI ai, Player player, int requestId, int senderId, final AIRequest request, Object... requestParams) {
		addRequest(ai, player, requestId, senderId, 0, request, requestParams);
	}
}
