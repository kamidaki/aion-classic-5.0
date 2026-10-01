package com.aionemu.gameserver.model.templates;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class VisibleObjectTemplate implements L10n {

	/**
	 * For Npcs it will return npcid from templates xml
	 * 
	 * @return id of object template
	 */
	public abstract int getTemplateId();

	/**
	 * For Npcs it will return name from templates xml
	 * 
	 * @return name of object
	 */
	public abstract String getName();

	/**
	 * For Npcs and items it will return official English name from templates xml
	 * 
	 * @return English name of object
	 */
	public String getNameEn() {
		return getName();
	}

	/**
	 * @return
	 */
	public BoundRadius getBoundRadius() {
		return BoundRadius.DEFAULT;
	}

}
