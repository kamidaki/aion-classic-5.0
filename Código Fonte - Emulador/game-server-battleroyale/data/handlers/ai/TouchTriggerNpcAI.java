package ai;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.BoundRadius;
import com.aionemu.gameserver.utils.PositionUtil;

/**
 * Objeto de toque: dispara quando um jogador entra no volume de colisão do NPC, sem aggro e sem atacar.
 * <p>
 * Volume (5.0 oficial, Tiamaranta Mesa): na horizontal, raio do NPC + raio do jogador; na vertical, da base do NPC até a altura dele
 * ({@code upper}) contra a altura do jogador. Nas capturas todo disparo caiu dentro dele (anel: até 1,7 m na horizontal e de +1,6 a +4,9 m acima
 * da base, dentro dos 7,5 m do anel). O aviso de movimento chega a cada 500 ms e o jogador voa a até 18 m/s, então o teste é feito ao longo do
 * trecho percorrido desde o último aviso, não só no ponto atual.
 */
public abstract class TouchTriggerNpcAI extends GeneralNpcAI {

	private final Map<Integer, LastPosition> lastPositions = new ConcurrentHashMap<>();
	private final AtomicBoolean triggered = new AtomicBoolean();

	public TouchTriggerNpcAI(Npc owner) {
		super(owner);
	}

	/**
	 * Chamado uma única vez, no primeiro toque.
	 */
	protected abstract void onTouch(Player player);

	protected boolean canTrigger(Player player) {
		return true;
	}

	@Override
	protected void handleSpawned() {
		triggered.set(false);
		lastPositions.clear();
		super.handleSpawned();
	}

	@Override
	protected void handleCreatureSee(Creature creature) {
		checkTouch(creature); // sem aggro
	}

	@Override
	protected void handleCreatureMoved(Creature creature) {
		checkTouch(creature); // sem aggro
	}

	@Override
	protected void handleCreatureNotSee(Creature creature) {
		lastPositions.remove(creature.getObjectId());
		super.handleCreatureNotSee(creature);
	}

	@Override
	protected void handleCreatureAggro(Creature creature) {
	}

	@Override
	protected boolean handleCreatureNeedsSupport(Creature creature) {
		return false;
	}

	@Override
	protected void handleAttack(Creature creature) {
	}

	@Override
	protected boolean canHandleEvent(AIEventType eventType) {
		if (eventType == AIEventType.CREATURE_MOVED)
			return !triggered.get();
		return super.canHandleEvent(eventType);
	}

	private void checkTouch(Creature creature) {
		if (!(creature instanceof Player player) || triggered.get())
			return;
		long now = System.currentTimeMillis();
		LastPosition from = lastPositions.put(player.getObjectId(), new LastPosition(player.getX(), player.getY(), player.getZ(), now));
		if (player.isDead() || getOwner().isDead() || !getOwner().isSpawned() || !canTrigger(player))
			return;
		if (!touches(player, from, now))
			return;
		if (triggered.compareAndSet(false, true))
			onTouch(player);
	}

	private boolean touches(Player player, LastPosition from, long now) {
		Npc npc = getOwner();
		BoundRadius npcBound = npc.getObjectTemplate().getBoundRadius();
		BoundRadius playerBound = player.getObjectTemplate().getBoundRadius();
		float playerRadius = playerBound == null ? 0 : playerBound.getMaxOfFrontAndSide();
		float playerHeight = playerBound == null ? 0 : playerBound.getUpper();
		float radius = npcBound.getMaxOfFrontAndSide() + playerRadius;

		float x2 = player.getX(), y2 = player.getY(), z2 = player.getZ();
		float x1 = x2, y1 = y2, z1 = z2;
		// trecho percorrido desde o último aviso; mais longo do que a velocidade permite é teleporte, e aí só vale o ponto atual
		if (from != null) {
			double length = PositionUtil.getDistance(from.x, from.y, from.z, x2, y2, z2);
			if (length <= PositionUtil.calculateMaxCoveredDistance(player, now - from.time) + radius) {
				x1 = from.x;
				y1 = from.y;
				z1 = from.z;
			}
		}

		// ponto do trecho mais perto do centro do NPC na horizontal
		float dx = x2 - x1, dy = y2 - y1;
		float lengthSq = dx * dx + dy * dy;
		float t = lengthSq == 0 ? 1 : ((npc.getX() - x1) * dx + (npc.getY() - y1) * dy) / lengthSq;
		t = Math.max(0, Math.min(1, t));
		float px = x1 + dx * t, py = y1 + dy * t, pz = z1 + (z2 - z1) * t;

		if (PositionUtil.getDistance(px, py, npc.getX(), npc.getY()) > radius)
			return false;
		return pz <= npc.getZ() + npcBound.getUpper() && pz + playerHeight >= npc.getZ();
	}

	private record LastPosition(float x, float y, float z, long time) {
	}
}
