package com.aionemu.gameserver.ai.handler;

import java.util.Collections;

import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.controllers.attack.AttackResult;
import com.aionemu.gameserver.controllers.attack.AttackStatus;
import com.aionemu.gameserver.model.TribeClass;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.npc.NpcTemplateType;
import com.aionemu.gameserver.network.aion.serverpackets.S_ATTACK;
import com.aionemu.gameserver.utils.MathUtil;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.geo.GeoService;
import com.aionemu.gameserver.world.knownlist.Visitor;

/**
 * @author ATracer
 */
public class AggroEventHandler {

	public static void onAggro(NpcAI npcAI, final Creature myTarget) {
		final Npc owner = npcAI.getOwner();
		if (myTarget.getAdminNeutral() == 1 || myTarget.getAdminNeutral() == 3 || myTarget.getAdminEnmity() == 1
			|| myTarget.getAdminEnmity() == 3) {
			return;
		}

		PacketSendUtility.broadcastPacket(owner, new S_ATTACK(owner, myTarget, 0, 633, 0, Collections.singletonList(new AttackResult(0, AttackStatus.NORMALHIT))));
		ThreadPoolManager.getInstance().schedule(new AggroNotifier(owner, myTarget, true), 500);
	}

	public static boolean onCreatureNeedsSupport(NpcAI npcAI, Creature notMyTarget) {
		Npc owner = npcAI.getOwner();
		if (notMyTarget.isSupportFrom(owner) && MathUtil.isInRange(owner, notMyTarget, owner.getAggroRange())
			&& GeoService.getInstance().canSee(owner, notMyTarget)) {
			VisibleObject myTarget = notMyTarget.getTarget();
			if (myTarget instanceof Creature targetCreature) {
				PacketSendUtility.broadcastPacket(owner, new S_ATTACK(owner, targetCreature, 0, 633, 0, Collections.singletonList(new AttackResult(0, AttackStatus.NORMALHIT))));
				ThreadPoolManager.getInstance().schedule(new AggroNotifier(owner, targetCreature, false), 500);
				return true;
			}
		}
		return false;
	}

	public static boolean onGuardAgainstAttacker(NpcAI npcAI, Creature attacker) {
		Npc owner = npcAI.getOwner();
		TribeClass tribe = owner.getTribe();
		if (!tribe.isGuard() && owner.getObjectTemplate().getNpcTemplateType() != NpcTemplateType.GUARD) {
			return false;
		}
		VisibleObject target = attacker.getTarget();
		if (target instanceof Player playerTarget) {
			if (!owner.isEnemy(playerTarget) && owner.isEnemy(attacker) && MathUtil.isInRange(owner, playerTarget, owner.getAggroRange()) && GeoService.getInstance().canSee(owner, attacker)) {
				owner.getAggroList().startHate(attacker);
				return true;
			}
		}
		return false;
	}

	private static final class AggroNotifier implements Runnable {

		private Npc aggressive;
		private Creature target;
		private final boolean broadcast;

		AggroNotifier(Npc aggressive, Creature target, boolean broadcast) {
			this.aggressive = aggressive;
			this.target = target;
			this.broadcast = broadcast;
		}

		@Override
		public void run() {
			aggressive.getAggroList().addHate(target, 1);
			if (broadcast) {
				aggressive.getKnownList().doOnAllNpcs(new Visitor<Npc>() {
					@Override
					public void visit(Npc object) {
						object.getAi().onCreatureEvent(AIEventType.CREATURE_NEEDS_SUPPORT, aggressive);
					}
				});
			}
			aggressive = null;
			target = null;
		}
	}
}
