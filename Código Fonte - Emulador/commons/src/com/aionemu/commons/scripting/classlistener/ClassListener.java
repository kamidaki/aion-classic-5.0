package com.aionemu.commons.scripting.classlistener;

/**
 * @author Lost Academy Team & Durak
 */
public interface ClassListener {

	/**
	 * This method is invoked after classes were loaded.
	 * 
	 * @param classes
	 *          all loaded classes by script context
	 */
	public void postLoad(Class<?>[] classes);

	/**
	 * This method is invoked before class unloading. As argument are passes all loaded classes
	 * 
	 * @param classes
	 *          all loaded classes (they are going to be unloaded) by script context
	 */
	public void preUnload(Class<?>[] classes);
}
