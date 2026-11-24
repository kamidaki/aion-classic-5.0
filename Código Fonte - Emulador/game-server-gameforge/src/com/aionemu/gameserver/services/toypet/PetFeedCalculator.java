package com.aionemu.gameserver.services.toypet;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.TreeSet;

import org.apache.commons.lang3.ArrayUtils;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.templates.pet.PetFeedResult;
import com.aionemu.gameserver.model.templates.pet.PetFlavour;
import com.aionemu.gameserver.model.templates.pet.PetRewards;

/**
 * @author Lost Academy Team & Durak
 */
public final class PetFeedCalculator {

	static byte ITEM_MAX_LEVEL = 60;
	static final short[] fullCounts;
	static final byte[] itemLevels;
	static final int[][] pointValues;

	static {
		TreeSet<Short> counts = new TreeSet<>();
		for (PetFlavour flavour : DataManager.PET_FEED_DATA.getPetFlavours()) {
			if (flavour.getFullCount() > 0)
				counts.add((short) (flavour.getFullCount() & 0xFFFF));
		}

		fullCounts = new short[counts.size()];
		int i = 0;
		Iterator<Short> countIter = counts.iterator();
		while (countIter.hasNext())
			fullCounts[i++] = countIter.next();

		itemLevels = new byte[ITEM_MAX_LEVEL / 5];
		itemLevels[0] = 5;
		for (int j = 1; j < itemLevels.length; j++)
			itemLevels[j] = (byte) (itemLevels[j - 1] + 5);

		pointValues = new int[itemLevels.length][fullCounts.length];
		calculate();
	}

	/**
	 * Calculate point values for each item levels and each max feed count
	 */
	static void calculate() {
		for (byte levelByte : itemLevels) {
			short level = (short) (levelByte & 0xFF);
			if (level < 10)
				continue;
			int countIndex = 0;
			for (short countByte : fullCounts) {
				short count = (short) (countByte & 0xFF);
				int finalLevel = level;
				if (finalLevel % 5 == 0)
					finalLevel--;
				int pointLevel = itemLevels[finalLevel / 5];
				int feedPoints = Math.max(0, pointLevel - 5) / 5 * 8;
				pointValues[finalLevel / 5][countIndex++] = getPoints(feedPoints, count);
			}
		}
	}

	/**
	 * Formula to calculate pointValues array
	 * 
	 * @param feedPoints
	 *          - feed points for item
	 * @param maxFeedCount
	 *          - max feeding count
	 * @return byte increment count after all items are fed
	 */
	static int getPoints(int feedPoints, int maxFeedCount) {
		int points = 0;
		int state = 0;
		int consumed = 0;
		while (consumed < maxFeedCount) {
			boolean needSwitch = false;
			int oldPoints = points;
			if ((state == 0 && consumed > maxFeedCount * 0.5f) || (state == 1 && consumed > maxFeedCount * 0.8f)
				|| (state == 2 && consumed > maxFeedCount * 1.05)) {
				needSwitch = true;
			}
			points += feedPoints;
			if (needSwitch) {
				state++;
				if (state == 1 && consumed <= 0.487f * maxFeedCount || state == 2 && consumed <= 0.78f * maxFeedCount) {
					state--;
					points = oldPoints;
				}
			}
			consumed++;
		}
		return points;
	}

	public static void updatePetFeedProgress(PetFeedProgress progress, int itemLevel, int maxFeedCount) {
		PetHungryLevel currHungryLevel = progress.getHungryLevel();
		if (progress.isLovedFeeded()) { // loved food
			if (progress.getLovedFoodRemaining() == 0)
				return;
			progress.setHungryLevel(PetHungryLevel.FULL);
			progress.incrementCount(true);
			return;
		}

		int oldPoints = progress.getTotalPoints();
		boolean needSwitch = false;

		if ((currHungryLevel == PetHungryLevel.HUNGRY && progress.getRegularCount() > maxFeedCount * 0.5f)
			|| (currHungryLevel == PetHungryLevel.CONTENT && progress.getRegularCount() > maxFeedCount * 0.8f)
			|| (currHungryLevel == PetHungryLevel.SEMIFULL && progress.getRegularCount() > maxFeedCount * 1.05)) {
			// forcefully switch level
			needSwitch = true;
		} else {
			int finalLevel = itemLevel;
			if (finalLevel % 5 == 0)
				finalLevel--;

			byte pointLevel = itemLevels[finalLevel / 5];
			byte pointsEarned = (byte) (Math.max(0, pointLevel - 5) / 5 * 8);
			int feedProgress = progress.getTotalPoints() + pointsEarned;
			progress.setTotalPoints(feedProgress);
		}

		if (needSwitch) {
			// just a prevention to not switch level
			PetHungryLevel nextLevel = progress.getHungryLevel().getNextValue();
			if (nextLevel == PetHungryLevel.CONTENT && progress.getRegularCount() <= 0.487f * maxFeedCount || nextLevel == PetHungryLevel.SEMIFULL
				&& progress.getRegularCount() <= 0.78f * maxFeedCount) {
				progress.setTotalPoints(oldPoints);
			} else {
				progress.setHungryLevel(nextLevel);
			}
		}
		progress.incrementCount(false);
	}

	public static PetFeedResult getReward(int fullCount, PetRewards rewardGroup, PetFeedProgress progress, int playerLevel) {
		if (progress.getHungryLevel() != PetHungryLevel.FULL || rewardGroup.getResults().size() == 0)
			return null;

		int pointsIndex = ArrayUtils.indexOf(fullCounts, (short) fullCount);
		if (pointsIndex == ArrayUtils.INDEX_NOT_FOUND)
			return null;

		if (progress.isLovedFeeded()) { // for cash feed
			if (rewardGroup.getResults().size() == 1)
				return rewardGroup.getResults().get(0);
			List<PetFeedResult> validRewards = new ArrayList<>();
			int maxLevel = 0;
			for (PetFeedResult result : rewardGroup.getResults()) {
				int resultLevel = DataManager.ITEM_DATA.getItemTemplate(result.getItem()).getLevel();
				if (resultLevel > playerLevel)
					continue;
				if (resultLevel > maxLevel) {
					maxLevel = resultLevel;
					validRewards.clear();
				}
				validRewards.add(result);
			}
			return Rnd.get(validRewards);
		}

		int rewardIndex = 0;
		int totalRewards = rewardGroup.getResults().size();
		for (int row = 1; row < pointValues.length; row++) {
			int[] points = pointValues[row];
			if (points[pointsIndex] <= progress.getTotalPoints()) {
				rewardIndex = Math.round((float) totalRewards / (pointValues.length - 1) * row) - 1;
			}
		}

		// Fix rounding discrepancy
		if (rewardIndex < 0)
			rewardIndex = 0;
		else if (rewardIndex > rewardGroup.getResults().size() - 1)
			rewardIndex = rewardGroup.getResults().size() - 1;

		return rewardGroup.getResults().get(rewardIndex);
	}
}
