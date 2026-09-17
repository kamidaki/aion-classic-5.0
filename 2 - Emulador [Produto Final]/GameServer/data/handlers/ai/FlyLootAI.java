package ai;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.configs.main.DropConfig;
import com.aionemu.gameserver.configs.main.GroupConfig;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;
import com.aionemu.gameserver.model.team.TemporaryPlayerTeam;
import com.aionemu.gameserver.services.DialogService;
import com.aionemu.gameserver.services.drop.DropRegistrationService;
import com.aionemu.gameserver.services.drop.DropService;
import com.aionemu.gameserver.utils.PositionUtil;

/**
 * Reusable, thread-safe, concurrency-safe AI for interactive aerial chests / cubes (Fly-Loot).
 * Supports both interaction (use-item / open) and combat destruction.
 * Protects against double-loot via AtomicBoolean.
 *
 * @author Lost Academy & Antigravity
 */
@AIName("fly_loot")
public class FlyLootAI extends ActionItemNpcAI {

	private final AtomicBoolean dropRegistered = new AtomicBoolean(false);

	public FlyLootAI(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleDialogStart(Player player) {
		if (getOwner().isInState(CreatureState.DEAD) || dropRegistered.get()) {
			return;
		}
		if (DialogService.isInteractionAllowed(player, getOwner())) {
			handleUseItemStart(player);
		}
	}

	@Override
	protected void handleUseItemFinish(Player player) {
		if (player == null || getOwner().isInState(CreatureState.DEAD)) {
			return;
		}

		if (dropRegistered.compareAndSet(false, true)) {
			Collection<Player> eligibleLooters = resolveEligibleLooters(player);
			int highestLevel = getHighestLevel(player, eligibleLooters);

			DropRegistrationService.getInstance().registerDrop(
				getOwner(),
				player,
				highestLevel,
				eligibleLooters
			);

			AIActions.die(this, player);
			DropService.getInstance().requestDropList(player, getObjectId());
		}
		super.handleUseItemFinish(player);
	}

	@Override
	protected void handleDied() {
		super.handleDied();
		if (dropRegistered.compareAndSet(false, true)) {
			Player looter = getOwner().getAggroList().getMostPlayerDamage();
			if (looter != null) {
				Collection<Player> eligibleLooters = resolveEligibleLooters(looter);
				int highestLevel = getHighestLevel(looter, eligibleLooters);
				DropRegistrationService.getInstance().registerDrop(
					getOwner(),
					looter,
					highestLevel,
					eligibleLooters
				);
			}
		}
	}

	private Collection<Player> resolveEligibleLooters(Player player) {
		TemporaryPlayerTeam<?> team = player.getCurrentTeam();
		if (team == null) {
			return Collections.singletonList(player);
		}

		List<Player> eligiblePlayers = new ArrayList<>();
		boolean disableRangeChecks = DropConfig.DISABLE_RANGE_CHECK_MAPS.contains(getPosition().getMapId());
		int range = disableRangeChecks ? Integer.MAX_VALUE : GroupConfig.GROUP_MAX_DISTANCE;
		for (Player member : team.getOnlineMembers()) {
			if (PositionUtil.isInRange(member, getOwner(), range)) {
				eligiblePlayers.add(member);
			}
		}

		if (eligiblePlayers.isEmpty()) {
			eligiblePlayers.add(player);
		}

		return eligiblePlayers;
	}

	private int getHighestLevel(Player fallback, Collection<Player> players) {
		return players.stream()
			.mapToInt(Player::getLevel)
			.max()
			.orElse(fallback != null ? fallback.getLevel() : 1);
	}
}
