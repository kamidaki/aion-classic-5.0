package com.aionemu.gameserver.utils.collections;

import com.aionemu.gameserver.network.aion.AionServerPacket;

import java.util.List;
import java.util.function.Function;

/**
 * @author Lost Academy Team & Durak
 */
public class DynamicServerPacketBodySplitList<Type> extends DynamicElementCountSplitList<Type> {

	/**
	 * @param listToSplit
	 *          List of elements to split
	 * @param oneTimeSplitOnEmptyData
	 *          true if an empty list should produce one split with an empty list
	 * @param staticBodyByteSize
	 *          static server packet body size, that will be subtracted from the maximum body size to determine the usable body size in bytes
	 * @param byteLengthCalculator
	 *          {@link Function} that will calculate the byte length of one element
	 */
	public DynamicServerPacketBodySplitList(List<Type> listToSplit, boolean oneTimeSplitOnEmptyData, int staticBodyByteSize,
		Function<Type, Integer> byteLengthCalculator) {
		super(listToSplit, oneTimeSplitOnEmptyData, AionServerPacket.MAX_USABLE_PACKET_BODY_SIZE - staticBodyByteSize, byteLengthCalculator);
	}

}
