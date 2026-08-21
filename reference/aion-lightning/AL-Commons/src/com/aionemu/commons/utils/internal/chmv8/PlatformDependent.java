/**
 * This file is part of Aion-Lightning <aion-lightning.org>.
 *
 *  Aion-Lightning is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  Aion-Lightning is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details. *
 *  You should have received a copy of the GNU General Public License
 *  along with Aion-Lightning.
 *  If not, see <http://www.gnu.org/licenses/>.
 */


package com.aionemu.commons.utils.internal.chmv8;

/**
 * @author Rolandas
 */
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

/**
 * O backport ConcurrentHashMapV8 / JSR-166 existia porque o Java 6 e 7 nao tinham a implementacao
 * sem lock. A partir do Java 8 ela e a propria {@link ConcurrentHashMap} do JDK, entao esta classe
 * ficou sendo apenas a fabrica que os chamadores ja usavam -- o caminho de fallback do codigo
 * original, agora o unico.
 */
public final class PlatformDependent {

	private PlatformDependent() {
	}

	/**
	 * Creates a new fastest {@link ConcurrentMap} implementation for the current platform.
	 */
	public static <K, V> ConcurrentMap<K, V> newConcurrentHashMap() {
		return new ConcurrentHashMap<K, V>();
	}

	/**
	 * Creates a new fastest {@link ConcurrentMap} implementation for the current platform.
	 */
	public static <K, V> ConcurrentMap<K, V> newConcurrentHashMap(int initialCapacity) {
		return new ConcurrentHashMap<K, V>(initialCapacity);
	}

	/**
	 * Creates a new fastest {@link ConcurrentMap} implementation for the current platform.
	 */
	public static <K, V> ConcurrentMap<K, V> newConcurrentHashMap(int initialCapacity, float loadFactor) {
		return new ConcurrentHashMap<K, V>(initialCapacity, loadFactor);
	}

	/**
	 * Creates a new fastest {@link ConcurrentMap} implementation for the current platform.
	 */
	public static <K, V> ConcurrentMap<K, V> newConcurrentHashMap(
					int initialCapacity, float loadFactor, int concurrencyLevel) {
		return new ConcurrentHashMap<K, V>(initialCapacity, loadFactor, concurrencyLevel);
	}

	/**
	 * Creates a new fastest {@link ConcurrentMap} implementation for the current platform.
	 */
	public static <K, V> ConcurrentMap<K, V> newConcurrentHashMap(Map<? extends K, ? extends V> map) {
		return new ConcurrentHashMap<K, V>(map);
	}
}
