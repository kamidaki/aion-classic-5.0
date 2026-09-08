package com.aionemu.commons.scripting.classlistener;

import java.util.ArrayList;
import java.util.List;

/**
 * @author Lost Academy Team & Durak
 */
public class AggregatedClassListener implements ClassListener {

	private final List<ClassListener> classListeners;

	public AggregatedClassListener() {
		classListeners = new ArrayList<>();
	}

	public AggregatedClassListener(List<ClassListener> classListeners) {
		this.classListeners = classListeners;
	}

	public List<ClassListener> getClassListeners() {
		return classListeners;
	}

	public void addClassListener(ClassListener cl) {
		classListeners.add(cl);
	}

	@Override
	public void postLoad(Class<?>[] classes) {
		for (ClassListener cl : classListeners) {
			cl.postLoad(classes);
		}
	}

	@Override
	public void preUnload(Class<?>[] classes) {
		for (int i = classListeners.size() - 1; i >= 0; i--) {
			classListeners.get(i).preUnload(classes);
		}
	}
}
