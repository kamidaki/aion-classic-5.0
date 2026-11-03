package com.aionemu.gameserver.utils.collections;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class SplitList<Type> implements Iterable<ListPart<Type>> {

	private final List<Type> listToSplit;
	private final boolean oneTimeSplitOnEmptyData;

	/**
	 * @param listToSplit
	 *          List of elements to split
	 * @param oneTimeSplitOnEmptyData
	 *          true if an empty list should produce one split with an empty list
	 */
	public SplitList(List<Type> listToSplit, boolean oneTimeSplitOnEmptyData) {
		this.listToSplit = listToSplit;
		this.oneTimeSplitOnEmptyData = oneTimeSplitOnEmptyData;
	}

	private List<ListPart<Type>> partitionList() {
		if (listToSplit.isEmpty() && oneTimeSplitOnEmptyData)
			return Collections.singletonList(newListPart(1, true));
		else if (listToSplit.isEmpty())
			return Collections.emptyList();

		List<ListPart<Type>> parts = new ArrayList<>();
		int startIndex = 0, partNo = 1;
		while (startIndex < listToSplit.size()) {
			ListPart<Type> listPart = newListPart(partNo++, false);
			while (startIndex < listToSplit.size() && listPart.fits(listToSplit.get(startIndex)))
				listPart.add(listToSplit.get(startIndex++));
			parts.add(listPart);
		}
		if (!parts.isEmpty()) {
			ListPart<Type> types = parts.get(parts.size() - 1);
			types.setLast(true);
		}
		return parts;
	}

	@Override
	public Iterator<ListPart<Type>> iterator() {
		return partitionList().iterator();
	}

	protected abstract ListPart<Type> newListPart(int partNo, boolean isLast);

}
