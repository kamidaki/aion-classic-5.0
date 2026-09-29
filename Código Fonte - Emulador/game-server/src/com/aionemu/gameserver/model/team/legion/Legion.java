package com.aionemu.gameserver.model.team.legion;

import java.sql.Timestamp;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.LegionGrowthData;
import com.aionemu.gameserver.dataholders.LegionSettingsData;
import com.aionemu.gameserver.model.gameobjects.AionObject;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.legion.LegionHistoryAction.Type;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ICON_INFO;
import com.aionemu.gameserver.services.LegionService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.World;

/**
 * @author Lost Academy Team & Durak
 */
public class Legion extends AionObject {

	private String legionName;
	private int legionLevel = 1;
	private long contributionPoints = 0;
	private List<Integer> memberIds = new CopyOnWriteArrayList<>();
	// padrão de Legion recém-criada no S_GUILD_INFO 5.0 (AinzOO 11/09 e Lost Academy 22/09): o Deputy já vem com 0x2000 e 0x4000
	private short deputyPermission = 0x7E0C;
	private short centurionPermission = 0x1C08;
	private short legionaryPermission = 0x1800;
	private short volunteerPermission = 0x800;
	private int disbandTime;
	private Announcement announcement;
	private LegionEmblem legionEmblem = new LegionEmblem();
	private final LegionWarehouse legionWarehouse;
	private final Map<Type, List<LegionHistoryEntry>> legionHistoryByType = new EnumMap<>(Type.class);
	private final AtomicBoolean hasBonus = new AtomicBoolean(false);
	private int occupiedLegionDominion = 0;
	private int currentLegionDominion = 0;
	private int lastLegionDominion = 0;
	// Crescimento (legion_growth.xml, do client_guild_growth.xml): a Legion recém-criada chega com nível 1 e exp 0 no S_GUILD_INFO (Lost Academy
	// 22/09) e ganha exp, essência e fragmentos com as missões (S 0x164 e S 0x163); a Org Asmo estava no nível 44 com 88500.
	private int growthLevel = 1;
	private int growthExp = 0;
	private int essence = 0;
	private int essencePiece = 0;

	public Legion(int legionId, String legionName) {
		super(legionId);
		this.legionName = legionName;
		this.legionWarehouse = new LegionWarehouse(this);
		setHistory(Collections.emptyMap());
	}

	public int getLegionId() {
		return getObjectId();
	}

	@Override
	public String getName() {
		return legionName;
	}

	public void setName(String legionName) {
		this.legionName = legionName;
	}

	public void setMemberIds(List<Integer> memberIds) {
		this.memberIds = memberIds;
	}

	public List<Integer> getMemberIds() {
		return memberIds;
	}

	public List<LegionMember> getMembers() {
		return streamMembers().collect(Collectors.toList());
	}

	private Stream<LegionMember> streamMembers() {
		return memberIds.stream().map(LegionService.getInstance()::getLegionMember).filter(Objects::nonNull);
	}

	public List<Player> getOnlinePlayers() {
		return memberIds.stream().map(World.getInstance()::getPlayer).filter(Objects::nonNull).collect(Collectors.toList());
	}

	public LegionMember getBrigadeGeneral() {
		return streamMembers().filter(LegionMember::isBrigadeGeneral).findFirst().orElseThrow();
	}

	public boolean addLegionMember(int playerObjId) {
		if (canAddMember()) {
			memberIds.add(playerObjId);
			return true;
		}
		return false;
	}

	public void removeMember(int playerObjId) {
		memberIds.remove((Integer) playerObjId);
	}

	public void setLegionPermissions(short deputyPermission, short centurionPermission, short legionaryPermission, short volunteerPermission) {
		this.deputyPermission = deputyPermission;
		this.centurionPermission = centurionPermission;
		this.legionaryPermission = legionaryPermission;
		this.volunteerPermission = volunteerPermission;
	}

	public short getDeputyPermission() {
		return deputyPermission;
	}

	public short getCenturionPermission() {
		return centurionPermission;
	}

	public short getLegionaryPermission() {
		return legionaryPermission;
	}

	public short getVolunteerPermission() {
		return volunteerPermission;
	}

	public int getLegionLevel() {
		return legionLevel;
	}

	public void setLegionLevel(int legionLevel) {
		this.legionLevel = legionLevel;
		getLegionWarehouse().updateLimit(getWarehouseExpansions());
	}

	public void addContributionPoints(long contributionPoints) {
		this.contributionPoints += contributionPoints;
	}

	public void setContributionPoints(long contributionPoints) {
		this.contributionPoints = contributionPoints;
	}

	public long getContributionPoints() {
		return contributionPoints;
	}

	/**
	 * @return o próximo nível do legion_settings.xml, ou null se a Legion já está no último
	 */
	public LegionSettingsData.Level getNextLevel() {
		return DataManager.LEGION_SETTINGS_DATA.getLevel(legionLevel + 1);
	}

	/**
	 * @return true se a Legion tem os membros exigidos pelo próximo nível (min_member do client_guild_setting.xml)
	 */
	public boolean hasRequiredMembers() {
		LegionSettingsData.Level next = getNextLevel();
		return next != null && getMemberIds().size() >= next.getRequiredMembers();
	}

	/**
	 * @return kinah para subir ao próximo nível (gold do client_guild_setting.xml), ou 0 no último nível
	 */
	public long getKinahPrice() {
		LegionSettingsData.Level next = getNextLevel();
		return next == null ? 0 : next.getKinah();
	}

	/**
	 * @return pontos de contribuição para subir ao próximo nível (exp do client_guild_setting.xml), ou 0 no último nível
	 */
	public long getContributionPrice() {
		LegionSettingsData.Level next = getNextLevel();
		return next == null ? 0 : next.getRequiredContribution();
	}

	/**
	 * @return true se o nível atual ainda tem vaga (max_member do client_guild_setting.xml)
	 */
	private boolean canAddMember() {
		LegionSettingsData.Level current = DataManager.LEGION_SETTINGS_DATA.getLevel(legionLevel);
		return current != null && getMemberIds().size() < current.getMaxMembers();
	}

	public Announcement getAnnouncement() {
		return announcement;
	}

	public void setAnnouncement(Announcement announcement) {
		this.announcement = announcement;
	}

	/**
	 * @param disbandTime
	 *          the disbandTime to set
	 */
	public void setDisbandTime(int disbandTime) {
		this.disbandTime = disbandTime;
	}

	/**
	 * @return the disbandTime
	 */
	public int getDisbandTime() {
		return disbandTime;
	}

	/**
	 * @return true if currently disbanding
	 */
	public boolean isDisbanding() {
		return disbandTime > 0;
	}

	/**
	 * This function checks if object id is in list
	 *
	 * @param playerObjId
	 * @return true if ID is found in the list
	 */
	public boolean isMember(int playerObjId) {
		return memberIds.contains(playerObjId);
	}

	/**
	 * @param legionEmblem
	 *          the legionEmblem to set
	 */
	public void setLegionEmblem(LegionEmblem legionEmblem) {
		this.legionEmblem = legionEmblem;
	}

	/**
	 * @return the legionEmblem
	 */
	public LegionEmblem getLegionEmblem() {
		return legionEmblem;
	}

	public LegionWarehouse getLegionWarehouse() {
		return legionWarehouse;
	}

	public int getWarehouseExpansions() {
		return getLegionLevel() - 1;
	}

	public List<LegionHistoryEntry> getHistory(Type type) {
		List<LegionHistoryEntry> history = legionHistoryByType.get(type);
		synchronized (history) {
			return new ArrayList<>(history);
		}
	}

	/**
	 * Adds the history entry at the top of the list and removes entries older than a year (except the ones on the first page)
	 */
	public List<LegionHistoryEntry> addHistory(LegionHistoryEntry entry) {
		List<LegionHistoryEntry> removedEntries = new ArrayList<>();
		Type type = entry.action().getType();
		List<LegionHistoryEntry> history = legionHistoryByType.get(type);
		synchronized (history) {
			history.addFirst(entry);
			if (type == Type.REWARD || type == Type.WAREHOUSE || type == Type.CRAFT) {
				long maxMillis = System.currentTimeMillis() / 1000 - Duration.ofDays(365).toSeconds();
				while (history.getLast().epochSeconds() < maxMillis)
					removedEntries.add(history.removeLast());
			}
		}
		return removedEntries;
	}

	public void setHistory(Map<Type, List<LegionHistoryEntry>> history) {
		for (Type type : Type.values()) {
			List<LegionHistoryEntry> entries = history.get(type);
			legionHistoryByType.put(type, entries == null ? new ArrayList<>(1) : entries);
		}
	}

	public void addBonus() {
		List<Player> members = getOnlinePlayers();
		if (members.size() >= 10) {
			if (hasBonus.compareAndSet(false, true)) {
				for (Player member : members) {
					PacketSendUtility.sendPacket(member, new SM_ICON_INFO(1, true));
				}
			}
		}
	}

	public void removeBonus() {
		List<Player> members = getOnlinePlayers();
		if (members.size() < 10) {
			if (hasBonus.compareAndSet(true, false)) {
				for (Player member : members) {
					PacketSendUtility.sendPacket(member, new SM_ICON_INFO(1, false));
				}
			}
		}
	}

	public boolean hasBonus() {
		return hasBonus.get();
	}

	public synchronized int getGrowthLevel() {
		return growthLevel;
	}

	public synchronized int getGrowthExp() {
		return growthExp;
	}

	public synchronized int getEssence() {
		return essence;
	}

	public synchronized int getEssencePiece() {
		return essencePiece;
	}

	public synchronized void setGrowth(int growthLevel, int growthExp, int essence, int essencePiece) {
		this.growthLevel = growthLevel;
		this.growthExp = growthExp;
		this.essence = essence;
		this.essencePiece = essencePiece;
	}

	/**
	 * Soma exp de crescimento e sobe quantos níveis ela pagar (cada nível pede a exp do legion_growth.xml e dá a essência dele). No último nível a
	 * exp não acumula.
	 *
	 * @return níveis ganhos
	 */
	public synchronized int addGrowthExp(int amount) {
		int gained = 0;
		growthExp += amount;
		for (LegionGrowthData.Level next; (next = DataManager.LEGION_GROWTH_DATA.getLevel(growthLevel + 1)) != null && growthExp >= next.getExp();) {
			growthExp -= next.getExp();
			growthLevel++;
			essence += next.getEssence();
			essencePiece += next.getEssencePiece();
			gained++;
		}
		if (DataManager.LEGION_GROWTH_DATA.getLevel(growthLevel + 1) == null)
			growthExp = 0;
		return gained;
	}

	public synchronized void addEssence(int essence, int essencePiece) {
		this.essence += essence;
		this.essencePiece += essencePiece;
	}

	public int getOccupiedLegionDominion() {
		return occupiedLegionDominion;
	}

	public int getCurrentLegionDominion() {
		return currentLegionDominion;
	}

	public int getLastLegionDominion() {
		return lastLegionDominion;
	}

	public void setOccupiedLegionDominion(int occupiedLegionDominion) {
		this.occupiedLegionDominion = occupiedLegionDominion;
	}

	public void setCurrentLegionDominion(int currentLegionDominion) {
		this.currentLegionDominion = currentLegionDominion;
	}

	public void setLastLegionDominion(int lastLegionDominion) {
		this.lastLegionDominion = lastLegionDominion;
	}

	@Override
	public String toString() {
		return "Legion [id=" + getObjectId() + ", name=" + getName() + "]";
	}

	public record Announcement(String message, Timestamp time) {}
}
