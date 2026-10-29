package com.aionemu.gameserver.ai.manager;

import com.lostacademy.nativepath.PathDatService;
import com.aionemu.gameserver.ai.AILogger;
import com.aionemu.gameserver.ai.AIState;
import com.aionemu.gameserver.ai.AISubState;
import com.aionemu.gameserver.ai.AttackIntention;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.controllers.attack.AggroTarget;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.ai.handler.AttackEventHandler;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * @author Lost Academy Team & Durak
 */
public class AttackManager {

	public static void startAttacking(NpcAI npcAI) {
		if (npcAI.isLogging()) {
			AILogger.info(npcAI, "AttackManager: startAttacking");
		}
		npcAI.getOwner().getGameStats().setFightStartingTime();
		VisibleObject target = npcAI.getOwner().getTarget();
		if (target instanceof Creature) // may be null at this point (-> triggering then TARGET_GIVEUP)
			EmoteManager.emoteStartAttacking(npcAI.getOwner(), (Creature) target);
		scheduleNextAttack(npcAI);
	}

	public static void scheduleNextAttack(NpcAI npcAI) {
		if (npcAI.isLogging()) {
			AILogger.info(npcAI, "AttackManager: scheduleNextAttack");
		}
		// don't start attack while in casting substate
		AISubState subState = npcAI.getSubState();
		if (subState == AISubState.NONE) {
			chooseAttack(npcAI, npcAI.getOwner().getGameStats().getNextAttackInterval());
		} else {
			if (npcAI.isLogging()) {
				AILogger.info(npcAI, "Will not choose attack in substate" + subState);
			}
		}
	}

	protected static void chooseAttack(NpcAI npcAI, int delay) {
		VisibleObject target = npcAI.getOwner().getTarget();
		if (target instanceof Player player && player.isFlying() && AttackEventHandler.isGroundNpc(npcAI.getOwner())) {
			if (!AttackEventHandler.isWithinAttackRange(npcAI.getOwner(), player)) {
				AttackEventHandler.fleeFromAirborneAttacker(npcAI, player);
				return;
			}
		}

		AttackIntention attackIntention = npcAI.chooseAttackIntention();
		if (npcAI.isLogging()) {
			AILogger.info(npcAI, "AttackManager: chooseAttack " + attackIntention + " delay " + delay);
		}
		if (!npcAI.canThink()) {
			return;
		}
		switch (attackIntention) {
			case SIMPLE_ATTACK:
				SimpleAttackManager.performAttack(npcAI, delay);
				break;
			case SKILL_ATTACK:
				SkillAttackManager.performAttack(npcAI, delay);
				break;
			case FINISH_ATTACK:
				npcAI.think();
				break;
			case HOLD_AGGRO: // confere o alvo de novo no próximo intervalo de ataque, sem atacar
				ThreadPoolManager.getInstance().schedule(() -> {
					if (npcAI.isInState(AIState.FIGHT) && npcAI.canThink())
						scheduleNextAttack(npcAI);
				}, Math.max(delay, 1000));
				break;
		}
	}

	public static void targetTooFar(NpcAI npcAI) {
		Npc npc = npcAI.getOwner();
		if (npcAI.isLogging()) {
			AILogger.info(npcAI, "AttackManager: attackTimeDelta " + npc.getGameStats().getLastAttackTimeDelta());
		}

		VisibleObject target = npc.getTarget();
		if (target == null || !(target instanceof Creature creature) || creature.isDead()) {
			npcAI.onGeneralEvent(AIEventType.TARGET_GIVEUP);
			return;
		}

		// Se o alvo estiver voando e o npc for terrestre, só foge se estiver fora do alcance
		if (target instanceof Player player && player.isFlying() && AttackEventHandler.isGroundNpc(npc)) {
			if (!AttackEventHandler.isWithinAttackRange(npc, player)) {
				AttackEventHandler.fleeFromAirborneAttacker(npcAI, player);
				return;
			}
		}

		// switch target if there is more hated creature
		if (npc.getGameStats().getLastChangeTargetTimeDelta() > 5) {
			Creature mostHated = npc.getAggroList().getTarget(AggroTarget.MOST_HATED);
			if (mostHated != null && !npc.isTargeting(mostHated.getObjectId())) {
				if (npcAI.isLogging()) {
					AILogger.info(npcAI, "AttackManager: switching target during chase");
				}
				npcAI.onCreatureEvent(AIEventType.TARGET_CHANGED, mostHated);
				return;
			}
		}

		// O monstro só desiste da perseguição se o jogador se afastar a mais de 60 metros (mesmo sem visão)
		if (checkGiveupDistance(npcAI)) {
			npcAI.onGeneralEvent(AIEventType.TARGET_GIVEUP);
			return;
		}

		if (npcAI.isMoveSupported()) {
			npc.getMoveController().moveToTargetObject();
			return;
		}
		npcAI.onGeneralEvent(AIEventType.TARGET_GIVEUP);
	}

	private static final long GIVEUP_SEM_ATACAR_MS = 8000;
	private static final long GIVEUP_INALCANCAVEL_MS = 2000;

	private static boolean checkGiveupDistance(NpcAI npcAI) {
		Npc npc = npcAI.getOwner();
		VisibleObject target = npc.getTarget();
		if (target != null) {
			if (npcAI.isLogging())
				AILogger.info(npcAI, "AttackManager: distanceToTarget " + PositionUtil.getDistance(npc, target, false));
			// Regra rigorosa: monstro só desiste da perseguição se o alvo se afastar a mais de 60 metros
			if (!PositionUtil.isInRange(npc, target, 60.0f, false)) {
				return true;
			}
			if (PathDatService.getInstance().usaGrade(npc)) {
				// Mapa com grade: desiste só quando não há rota andando de até 100 m até o alvo, por 2 s seguidos (decisão de 27/10/2026:
				// enquanto houver caminho, ele persegue, mesmo que a volta pela rampa leve mais que os 8 s do oficial)
				if (PathDatService.getInstance().millisInalcancavel(npc) >= GIVEUP_INALCANCAVEL_MS) {
					return true;
				}
			} else if (!npc.isInInstance() && npc.getGameStats().getMillisSemAtacar() > GIVEUP_SEM_ATACAR_MS) {
				// Sem grade (oficial, capturas de 27/10/2026, 21 desistências): o mob que não consegue atacar desiste ~8 s depois do aggro
				// (6,9-8,8 s) ou do último ataque dele (9,4-10,7 s, contando a animação), a 3-35 m do alvo
				return true;
			}
		} else {
			return true;
		}
		double distanceToHome = npc.getDistanceToSpawnLocation();
		// Tether de retorno ao lar para evitar que o mob seja arrastado infinitamente pelo mapa
		int chaseHome = Math.max(150, npc.getPosition().getWorldMapInstance().getTemplate().getAiInfo().getChaseHome());
		if (distanceToHome > chaseHome) {
			return true;
		}
		return false;
	}
}
