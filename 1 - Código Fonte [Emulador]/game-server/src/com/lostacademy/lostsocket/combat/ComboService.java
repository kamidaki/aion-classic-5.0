package com.lostacademy.lostsocket.combat;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dao.ParticipationPointsDAO;
import com.aionemu.gameserver.dao.PlayerHitsDAO;
import com.aionemu.gameserver.model.ChatType;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.skillengine.effect.AbnormalState;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.lostacademy.Dps_Meter.DpsService;

/**
 * Combat Combo and Participation Points Tracking Service.
 * Synchronizes real-time hits, timeouts, abnormal states, records, and participation points.
 */
public class ComboService {

	private static final Logger log = LoggerFactory.getLogger(ComboService.class);
	private static final ComboService instance = new ComboService();

	public static ComboService getInstance() {
		return instance;
	}

	private static final int COMBO_TIMEOUT_START_MS = 4000;
	private static final int COMBO_TIMEOUT_FLOOR_MS = 2000;
	private static final int COMBO_TIMEOUT_LOCK_HIT = 50;

	private final ConcurrentHashMap<Integer, ComboState> playerCombos = new ConcurrentHashMap<>();
	private final ConcurrentHashMap<Integer, ConcurrentHashMap<Integer, TargetHitState>> playerTargetHits = new ConcurrentHashMap<>();
	private final ConcurrentHashMap<Integer, Boolean> playerComboHidden = new ConcurrentHashMap<>();

	private final AtomicLong generationCounter = new AtomicLong(0);

	private static class ComboState {
		int hits;
		int totalDamage;
		int currentTimeoutMs;
		long generation;
		ScheduledFuture<?> timeoutTask;

		ComboState(int hits, int totalDamage, int currentTimeoutMs, long generation) {
			this.hits = hits;
			this.totalDamage = totalDamage;
			this.currentTimeoutMs = currentTimeoutMs;
			this.generation = generation;
		}
	}

	private static class TargetHitState {
		int hits = 0;
		int maxCombo = 0;
	}

	private int computeTimeout(int hits) {
		if (hits <= 1) return COMBO_TIMEOUT_START_MS;
		if (hits >= COMBO_TIMEOUT_LOCK_HIT) return COMBO_TIMEOUT_FLOOR_MS;
		float step = (float)(COMBO_TIMEOUT_START_MS - COMBO_TIMEOUT_FLOOR_MS) / (COMBO_TIMEOUT_LOCK_HIT - 1);
		int t = (int)(COMBO_TIMEOUT_START_MS - step * (hits - 1));
		return Math.max(COMBO_TIMEOUT_FLOOR_MS, t);
	}

	public void setComboUiHidden(int playerId, boolean hidden) {
		playerComboHidden.put(playerId, hidden);
	}

	public boolean isComboUiHidden(int playerId) {
		return playerComboHidden.getOrDefault(playerId, Boolean.FALSE);
	}

	public void onPlayerHit(Player attacker, Creature target, int hitDamage) {
		if (attacker == null || target == null || attacker.equals(target)) return;
		int playerId = attacker.getObjectId();

		// If user configured to hide Combo UI, do not process combo chaining
		if (isComboUiHidden(playerId)) return;

		int targetId = target.getObjectId();
		long gen = generationCounter.incrementAndGet();

		ComboState state = playerCombos.compute(playerId, (id, current) -> {
			if (current != null) {
				cancelTimeout(current);
				int newHits = current.hits + 1;
				int newDmg = current.totalDamage + hitDamage;
				int newTimeout = computeTimeout(newHits);
				return new ComboState(newHits, newDmg, newTimeout, gen);
			} else {
				return new ComboState(1, hitDamage, COMBO_TIMEOUT_START_MS, gen);
			}
		});

		String title = getComboTitle(state.hits);
		String event = (state.hits == 1) ? "COMBO_START" : "COMBO_UPDATE";

		DpsService.sendComboEvent(attacker, event, state.hits, hitDamage, state.totalDamage, state.currentTimeoutMs, title);
		scheduleTimeout(attacker, playerId, gen, state.currentTimeoutMs);

		// Record target hits for aggressive NPCs
		if (target instanceof Npc npc) {
			boolean isAggro = isAggressiveNpc(npc);
			if (isAggro) {
				playerTargetHits.computeIfAbsent(playerId, k -> new ConcurrentHashMap<>())
					.compute(targetId, (k, v) -> {
						if (v == null) v = new TargetHitState();
						v.hits++;
						if (state.hits > v.maxCombo) {
							v.maxCombo = state.hits;
						}
						return v;
					});
			}
		}
	}

	public void onNpcDeath(Npc npc) {
		if (npc == null) return;
		boolean isAggressive = isAggressiveNpc(npc);
		int targetId = npc.getObjectId();

		for (Integer playerId : playerTargetHits.keySet()) {
			ConcurrentHashMap<Integer, TargetHitState> map = playerTargetHits.get(playerId);
			if (map != null) {
				TargetHitState hitState = map.remove(targetId);
				if (hitState != null && isAggressive) {
					// Check if Combo UI is hidden for this player.
					// If hidden, participation points are NOT rewarded even if objectives are achieved!
					if (isComboUiHidden(playerId)) {
						continue;
					}

					Player player = com.aionemu.gameserver.world.World.getInstance().getPlayer(playerId);
					if (player != null && player.isOnline() && player.getAccount() != null) {
						int accountId = player.getAccount().getId();
						int hits = hitState.hits;
						int maxCombo = hitState.maxCombo;

						Thread.ofVirtual().name("Combo-Reward-" + playerId).start(() -> {
							try {
								var result = PlayerHitsDAO.addHitsAndClaimRewards(accountId, playerId, hits, maxCombo);
								int pointsEarned = result.pointsEarned();
								int newBetterHits = result.betterAmountHits();

								if (pointsEarned > 0) {
									ParticipationPointsDAO.addPoints(accountId, pointsEarned);
									long currentTotal = ParticipationPointsDAO.getPoints(accountId);

									PacketSendUtility.sendMessage(player,
										"\uE0DE Você acumulou " + (pointsEarned * 1000) + " golpes e ganhou " + pointsEarned + " Ponto(s) de Participação!",
										ChatType.WHITE);

									DpsService.sendParticipationGained(player, pointsEarned, currentTotal);
								}

								if (newBetterHits == maxCombo && maxCombo > 0) {
									DpsService.sendNewRecord(player, maxCombo);
								}
							} catch (Exception e) {
								log.error("Erro ao processar recompensa de hits para player {}", playerId, e);
							}
						});
					}
				}
			}
		}
	}

	private boolean isAggressiveNpc(Npc npc) {
		if (npc == null) return false;
		if (npc.getAi() != null && npc.getAi().getName() != null && npc.getAi().getName().toLowerCase().contains("aggressive")) {
			return true;
		}
		if (npc.getObjectTemplate() != null && npc.getObjectTemplate().getAiName() != null &&
			npc.getObjectTemplate().getAiName().toLowerCase().contains("aggressive")) {
			return true;
		}
		return false;
	}

	private void cancelTimeout(ComboState state) {
		if (state != null && state.timeoutTask != null && !state.timeoutTask.isCancelled()) {
			state.timeoutTask.cancel(false);
		}
	}

	private void scheduleTimeout(Player player, int playerId, long generation, int timeoutMs) {
		ScheduledFuture<?> timeoutTask = ThreadPoolManager.getInstance().schedule(() -> {
			handleTimeout(player, playerId, generation);
		}, timeoutMs);

		AtomicBoolean attached = new AtomicBoolean(false);
		playerCombos.computeIfPresent(playerId, (id, state) -> {
			if (state.generation == generation) {
				state.timeoutTask = timeoutTask;
				attached.set(true);
			}
			return state;
		});
		if (!attached.get()) {
			timeoutTask.cancel(false);
		}
	}

	private void handleTimeout(Player player, int playerId, long generation) {
		if (player == null) return;
		ComboState[] removed = new ComboState[1];
		playerCombos.compute(playerId, (id, state) -> {
			if (state == null || state.generation != generation)
				return state;
			removed[0] = state;
			return null;
		});
		if (removed[0] != null) {
			String title = getComboTitle(removed[0].hits);
			DpsService.sendComboEvent(player, "COMBO_BREAK", removed[0].hits, 0, removed[0].totalDamage, removed[0].currentTimeoutMs, title);
			DpsService.sendComboEvent(player, "COMBO_FINAL", removed[0].hits, 0, removed[0].totalDamage, removed[0].currentTimeoutMs, title);
		}
	}

	public void onCCApplied(Player player) {
		resetCombo(player, "COMBO_CC_BREAK");
	}

	public void onPlayerDeath(Player player) {
		resetCombo(player, "COMBO_DEATH");
	}

	public void onRemoveShock(Player player) {
		if (player == null) return;
		int playerId = player.getObjectId();
		ComboState state = playerCombos.remove(playerId);
		int finalHits = (state != null) ? state.hits : 0;
		int finalDamage = (state != null) ? state.totalDamage : 0;
		int finalTimeout = (state != null) ? state.currentTimeoutMs : COMBO_TIMEOUT_START_MS;
		cancelTimeout(state);
		DpsService.sendComboEvent(player, "COMBO_REMOVE_SHOCK", finalHits, 0, finalDamage, finalTimeout, getComboTitle(finalHits));
	}

	public void onMapChange(Player player) {
		resetCombo(player, "COMBO_RESET");
	}

	public void onPlayerLogout(Player player) {
		if (player == null) return;
		int playerId = player.getObjectId();
		ComboState state = playerCombos.remove(playerId);
		cancelTimeout(state);
		playerTargetHits.remove(playerId);
		playerComboHidden.remove(playerId);
	}

	private void resetCombo(Player player, String reason) {
		if (player == null) return;
		int playerId = player.getObjectId();
		ComboState state = playerCombos.remove(playerId);
		if (state != null) {
			cancelTimeout(state);
			DpsService.sendComboEvent(player, reason, state.hits, 0, state.totalDamage, state.currentTimeoutMs, getComboTitle(state.hits));
		}
	}

	public void sendAbnormalState(Player player, AbnormalState state) {
		if (player == null || state == null) return;
		int detailId = 99;
		String stateName = state.name();
		switch (state) {
			case STUN:
			case STUMBLE:
			case STAGGER:
			case OPENAERIAL:
			case SPIN:
				detailId = 1;
				stateName = "Atordoamento";
				break;
			case PARALYZE:
				detailId = 2;
				stateName = "Paralisia";
				break;
			case SILENCE:
				detailId = 3;
				stateName = "Silenciamento";
				break;
			case BIND:
			case ROOT:
				detailId = 4;
				stateName = "Preso";
				break;
			case POISON:
				detailId = 5;
				stateName = "Envenenamento";
				break;
			case BLEED:
				detailId = 6;
				stateName = "Sangramento";
				break;
			case FEAR:
				detailId = 7;
				stateName = "Medo";
				break;
			case SLEEP:
				detailId = 8;
				stateName = "Adormecimento";
				break;
			case BLIND:
				detailId = 9;
				stateName = "Cego";
				break;
			case DISEASE:
				detailId = 10;
				stateName = "Doenca";
				break;
			case CURSE:
				detailId = 11;
				stateName = "Maldicao";
				break;
			case CONFUSE:
			case CHARM:
				detailId = 12;
				stateName = "Confusao";
				break;
			default:
				break;
		}
		if (detailId != 99) {
			DpsService.sendAbnormalState(player, detailId, stateName);
		}
	}

	public String getComboTitle(int hits) {
		if (hits >= 80) return "Aniquilador";
		if (hits >= 70) return "Insano";
		if (hits >= 65) return "Lendário";
		if (hits >= 60) return "Dominador";
		if (hits >= 55) return "Rei";
		if (hits >= 40) return "Brutal";
		if (hits >= 30) return "Monstruoso";
		if (hits >= 20) return "Implacável";
		if (hits >= 15) return "Solador";
		if (hits >= 10) return "Matador";
		return "";
	}
}
