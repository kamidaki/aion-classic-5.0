package com.aionemu.gameserver.skillengine.model;

/**
 * @author Lost Academy Team & Durak
 */
public class ChainSkill {

	private String category;
	private int useCount = 0;
	private long lastUseTime = 0;
	private boolean alter;

	public ChainSkill(String category) {
		this.category = category;
	}

	public void clear() {
		this.category = "";
		this.useCount = 0;
		this.lastUseTime = 0;
		this.alter = false;
	}

	public String getCategory() {
		return category;
	}

	public void setCategory(String name) {
		this.category = name;
	}

	/**
	 * @return True se a cadeia é alterchain (5.0): uma skill sem cadeia usada no meio não a quebra.
	 */
	public boolean isAlter() {
		return alter;
	}

	public void setAlter(boolean alter) {
		this.alter = alter;
	}

	public int getUseCount() {
		return useCount;
	}

	public void increaseUseCount() {
		this.useCount++;
		this.lastUseTime = System.currentTimeMillis();
	}

	/**
	 * @return The time when this chain skill was last activated, 0 if never.
	 */
	public long getLastUseTime() {
		return lastUseTime;
	}
}
