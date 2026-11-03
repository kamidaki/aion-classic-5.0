package com.aionemu.gameserver.utils.idfactory;

import java.util.BitSet;
import java.util.Collection;
import java.util.concurrent.locks.ReentrantLock;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.utils.GenericValidator;
import com.aionemu.gameserver.dao.*;
import com.aionemu.gameserver.model.gameobjects.AionObject;

/**
 * @author Lost Academy Team & Durak
 */
public class IDFactory {

	private static final Logger log = LoggerFactory.getLogger(IDFactory.class);

	/**
	 * Npcs with objectIds that match this bit pattern are always invisible on client side, not sure why:
	 * 
	 * <pre>
	 * ??0??000000??00?0?11001010101??
	 * </pre>
	 * 
	 * Invalid ID examples:
	 * 
	 * <pre>
	 * 6484, 6485, 6486, 6487,
	 * 14676, 14677, 14678, 14679,
	 * 39252, 39253, 39254, 39255,
	 * 47444, 47445, 47446, 47447,
	 * 268628, 268629, 268630, 268631,
	 * ...
	 * 1812773204, 1812773205, 1812773206, 1812773207
	 * </pre>
	 * 
	 * We forbid them to ensure they'll never get assigned to an npc.
	 */
	private static final int INVALID_ID_BIT_MASK = 0b0010011111100110101111111111100;
	private static final int INVALID_ID_BITCHECK = 0b0000000000000000001100101010100; // 6484

	/**
	 * Bitset that is used for all id's.<br>
	 * We are allowing BitSet to grow over time, so in the end it can be as big as {@link Integer#MAX_VALUE}
	 */
	private final BitSet idList = new BitSet();

	/**
	 * 5.0 oficial: o objectId diz o tipo do objeto nos 2 bits altos. NPC (S_PUT_NPC, também pet e invocação) vem de 0x80000000 (40.872 de 40.872
	 * nas capturas), objeto do mundo (S_PUT_OBJECT) de 0xC0000000 (457 de 457); jogador e item ficam abaixo de 0x80000000. Com NPC na faixa baixa o
	 * cliente o confunde com outro tipo de entidade e desenha efeitos de skill em NPCs que não receberam nenhum.
	 */
	public static final int NPC_ID_BASE = 0x80000000;
	public static final int WORLD_OBJECT_ID_BASE = 0xC0000000;
	private static final int TYPED_ID_INDEX_MASK = 0x3FFFFFFF;
	// 0xFFFFFFFF (-1) nunca é entregue: o RiftInformer e outros usam -1 como marca
	private static final int TYPED_ID_MAX_INDEX = TYPED_ID_INDEX_MASK - 1;

	private final BitSet npcIds = new BitSet();
	private final BitSet worldObjectIds = new BitSet();
	private int nextNpcIndex = 1;
	private int nextWorldObjectIndex = 1;

	/**
	 * Synchronization of bitset
	 */
	private final ReentrantLock lock = new ReentrantLock();

	/**
	 * Id that will be used as minimal on next id request
	 */
	private volatile int nextMinId = 1;

	private IDFactory() {
		lockIds(0);
		initializeUsedIds();
		log.info("IDFactory: {} IDs used.", getUsedCount());
	}

	public static IDFactory getInstance() {
		return SingletonHolder.instance;
	}

	/**
	 * Returns next free id.
	 *
	 * @return next free id
	 * @throws IDFactoryError
	 *           if there is no free id's
	 */
	public int nextId() {
		lock.lock();
		try {
			int id = nextValidId(nextMinId);
			idList.set(id);
			nextMinId = id + 1;
			return id;
		} finally {
			lock.unlock();
		}
	}

	/**
	 * @return próximo id livre da faixa de NPC (0x80000000+): npc, invocação, kisk, armadilha etc.
	 */
	public int nextNpcId() {
		lock.lock();
		try {
			int index = nextTypedIndex(npcIds, nextNpcIndex, NPC_ID_BASE);
			npcIds.set(index);
			nextNpcIndex = index + 1;
			return NPC_ID_BASE | index;
		} finally {
			lock.unlock();
		}
	}

	/**
	 * @return próximo id livre da faixa de objeto do mundo (0xC0000000+): coleta e objeto estático
	 */
	public int nextWorldObjectId() {
		lock.lock();
		try {
			int index = nextTypedIndex(worldObjectIds, nextWorldObjectIndex, WORLD_OBJECT_ID_BASE);
			worldObjectIds.set(index);
			nextWorldObjectIndex = index + 1;
			return WORLD_OBJECT_ID_BASE | index;
		} finally {
			lock.unlock();
		}
	}

	private int nextTypedIndex(BitSet ids, int searchIndex, int base) {
		int index = ids.nextClearBit(searchIndex);
		while (index <= TYPED_ID_MAX_INDEX && isInvalidId(base | index))
			index = ids.nextClearBit(index + 1);
		if (index > TYPED_ID_MAX_INDEX)
			throw new IDFactoryError("All IDs of range 0x" + Integer.toHexString(base) + " are used");
		return index;
	}

	public void releaseId(int id) {
		lock.lock();
		try {
			if (!release(id)) {
				log.debug("Couldn't release ID {} because it wasn't taken", id);
			}
		} finally {
			lock.unlock();
		}
	}

	public void releaseObjectIds(Collection<? extends AionObject> unusedObjects) {
		if (GenericValidator.isBlankOrNull(unusedObjects))
			return;

		lock.lock();
		try {
			unusedObjects.forEach(obj -> {
				if (!release(obj.getObjectId())) {
					log.debug("Couldn't release object ID of {} (ID wasn't taken)", obj);
				}
			});
		} finally {
			lock.unlock();
		}
	}

	/**
	 * @return amount of used ids
	 */
	public int getUsedCount() {
		lock.lock();
		try {
			return idList.cardinality() + npcIds.cardinality() + worldObjectIds.cardinality();
		} finally {
			lock.unlock();
		}
	}

	private void initializeUsedIds() {
		lockIds(PlayerDAO.getUsedIDs());
		lockIds(InventoryDAO.getUsedIDs());
		lockIds(PlayerRegisteredItemsDAO.getUsedIDs());
		lockIds(LegionDAO.getUsedIDs());
		lockIds(MailDAO.getUsedIDs());
		lockIds(GuideDAO.getUsedIDs());
		lockIds(HousesDAO.getUsedIDs());
		lockIds(PlayerPetsDAO.getUsedIDs());
		lockIds(PlayerWardrobeDAO.getUsedIDs());
		lockIds(PlayerHairstyleDAO.getUsedIDs());
		lockIds(PlayerBattlePassDAO.getUsedIDs());
	}

	private int nextValidId(int searchIndex) {
		int id = idList.nextClearBit(searchIndex);
		if (id == Integer.MIN_VALUE) {
			throw new IDFactoryError("All IDs are used, please clear your database");
		}
		return isInvalidId(id) ? nextValidId(id + 1) : id;
	}

	private boolean isInvalidId(int id) {
		return (id & INVALID_ID_BIT_MASK) == INVALID_ID_BITCHECK;
	}

	/**
	 * Internal helper method without synchronization, to lock IDs during instantiation (public ID allocation should only happen via {@link #nextId()})
	 *
	 * @param ids
	 *          ids to lock
	 * @throws IDFactoryError
	 *           if some of the id's are already locked
	 */
	private void lockIds(int... ids) {
		for (int id : ids) {
			if (idList.get(id)) {
				throw new IDFactoryError("ID " + id + " is already taken, fatal error!!!");
			}
			idList.set(id);
		}
	}

	/**
	 * Internal helper method without synchronization
	 * 
	 * @return True if the ID could be released, false if it was not taken
	 */
	private boolean release(int id) {
		switch (id >>> 30) {
			case 2 -> {
				return releaseTyped(npcIds, id, true);
			}
			case 3 -> {
				return releaseTyped(worldObjectIds, id, false);
			}
		}
		if (!idList.get(id))
			return false;
		idList.clear(id);
		if (id < nextMinId || nextMinId == Integer.MIN_VALUE)
			nextMinId = id;
		return true;
	}

	private boolean releaseTyped(BitSet ids, int id, boolean npc) {
		int index = id & TYPED_ID_INDEX_MASK;
		if (!ids.get(index))
			return false;
		ids.clear(index);
		if (npc) {
			if (index < nextNpcIndex)
				nextNpcIndex = index;
		} else if (index < nextWorldObjectIndex) {
			nextWorldObjectIndex = index;
		}
		return true;
	}

	private static class SingletonHolder {

		private static final IDFactory instance = new IDFactory();
	}
}
