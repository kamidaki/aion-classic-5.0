/*
 * This file is part of aion-emu <aion-emu.com>.
 *
 * aion-emu is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * aion-emu is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with aion-emu.  If not, see <http://www.gnu.org/licenses/>.
 */
package com.aionemu.gameserver.utils.idfactory;

import com.aionemu.commons.database.dao.DAOManager;
import com.aionemu.commons.utils.GenericValidator;
import com.aionemu.gameserver.dao.*;
import com.aionemu.gameserver.model.gameobjects.AionObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.BitSet;
import java.util.Collection;
import java.util.concurrent.locks.ReentrantLock;

/**
 * This class is responsible for id generation for all Aion-Emu objects.<br>
 * This class is Thread-Safe.<br>
 * Based on Java 4.8 Retail implementation.
 *
 * @author SoulKeeper, Neon
 */
public class IDFactory {

	private static final Logger log = LoggerFactory.getLogger(IDFactory.class);

	/**
	 * Npcs with objectIds that match this bit pattern are always invisible on client side:
	 * ??0??000000??00?0?11001010101??
	 * We forbid them to ensure they'll never get assigned to an entity.
	 */
	private static final int INVALID_ID_BIT_MASK = 0b0010011111100110101111111111100;
	private static final int INVALID_ID_BITCHECK = 0b0000000000000000001100101010100; // 6484

	/**
	 * Bitset that is used for all id's.<br>
	 * We are allowing BitSet to grow over time, so in the end it can be as big as {@link Integer#MAX_VALUE}
	 */
	private final BitSet idList;

	/**
	 * Synchronization of bitset
	 */
	private final ReentrantLock lock;

	/**
	 * Id that will be used as minimal on next id request
	 */
	private volatile int nextMinId = 1;

	private IDFactory() {
		idList = new BitSet();
		lock = new ReentrantLock();
		lockIds(0);
		// Here should be calls to all IDFactoryAwareDAO implementations to initialize
		// used values in IDFactory
		lockIds(DAOManager.getDAO(PlayerDAO.class).getUsedIDs());
		lockIds(DAOManager.getDAO(InventoryDAO.class).getUsedIDs());
		lockIds(DAOManager.getDAO(LegionDAO.class).getUsedIDs());
		lockIds(DAOManager.getDAO(MailDAO.class).getUsedIDs());
		lockIds(DAOManager.getDAO(GuideDAO.class).getUsedIDs());
		lockIds(DAOManager.getDAO(PlayerWardrobeDAO.class).getUsedIDs());
		lockIds(DAOManager.getDAO(AccountBlackCloudDAO.class).getUsedIDs());
		log.info("IDFactory: " + getUsedCount() + " id's used.");
	}

	public static final IDFactory getInstance() {
		return SingletonHolder.instance;
	}

	/**
	 * Returns next free id.
	 *
	 * @return next free id
	 * @throws IDFactoryError if there is no free id's
	 */
	public int nextId() {
		try {
			lock.lock();
			int id = nextValidId(nextMinId);
			idList.set(id);
			nextMinId = id + 1;
			return id;
		} finally {
			lock.unlock();
		}
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
	 * Locks given ids.
	 *
	 * @param ids ids to lock
	 */
	private void lockIds(int... ids) {
		if (ids == null) {
			return;
		}
		try {
			lock.lock();
			for (int id : ids) {
				boolean status = idList.get(id);
				if (status) {
					log.warn("ID {} is already taken in database! Duplicate ID detected, skipping to avoid crash.", id);
					continue;
				}
				idList.set(id);
			}
		} finally {
			lock.unlock();
		}
	}

	/**
	 * Locks given ids.
	 *
	 * @param ids ids to lock
	 */
	public void lockIds(Iterable<Integer> ids) {
		if (ids == null) {
			return;
		}
		try {
			lock.lock();
			for (int id : ids) {
				boolean status = idList.get(id);
				if (status) {
					log.warn("ID {} is already taken in database! Duplicate ID detected, skipping to avoid crash.", id);
					continue;
				}
				idList.set(id);
			}
		} finally {
			lock.unlock();
		}
	}

	/**
	 * Releases given id
	 *
	 * @param id id to release
	 */
	public void releaseId(int id) {
		try {
			lock.lock();
			if (!idList.get(id)) {
				log.warn("Couldn't release ID {} because it wasn't taken", id);
				return;
			}
			idList.clear(id);
			if (id < nextMinId || nextMinId == Integer.MIN_VALUE) {
				nextMinId = id;
			}
		} finally {
			lock.unlock();
		}
	}

	public void releaseIds(Collection<Integer> ids) {
		if (GenericValidator.isBlankOrNull(ids)) {
			return;
		}

		try {
			lock.lock();
			for (Integer id : ids) {
				if (id != null) {
					releaseId(id);
				}
			}
		} finally {
			lock.unlock();
		}
	}

	public void releaseObjectIds(Collection<? extends AionObject> unusedObjects) {
		if (GenericValidator.isBlankOrNull(unusedObjects)) {
			return;
		}

		try {
			lock.lock();
			for (AionObject obj : unusedObjects) {
				if (obj != null) {
					releaseId(obj.getObjectId());
				}
			}
		} finally {
			lock.unlock();
		}
	}

	/**
	 * Returns amount of used ids
	 *
	 * @return amount of used ids
	 */
	public int getUsedCount() {
		try {
			lock.lock();
			return idList.cardinality();
		} finally {
			lock.unlock();
		}
	}

	@SuppressWarnings("synthetic-access")
	private static class SingletonHolder {
		protected static final IDFactory instance = new IDFactory();
	}
}
