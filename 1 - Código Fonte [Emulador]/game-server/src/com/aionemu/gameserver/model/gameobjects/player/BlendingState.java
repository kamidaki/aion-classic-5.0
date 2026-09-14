package com.aionemu.gameserver.model.gameobjects.player;

import java.util.ArrayDeque;
import java.util.Deque;

import com.aionemu.gameserver.skillengine.effect.BlendingNote;
import com.aionemu.gameserver.skillengine.effect.BlendingResolver;

/**
 * Estado das 3 notas de Blending mantido pelo jogador Luminess.
 *
 * @author Antigravity
 */
public class BlendingState {

	/**
	 * Tempo máximo de validade entre notas (30 segundos).
	 */
	private static final long NOTE_TIMEOUT_MS = 30000;

	private final Deque<BlendingNote> notes = new ArrayDeque<>(3);
	private long lastNoteTime = 0;

	public synchronized void recordNote(BlendingNote note) {
		if (note == null) {
			return;
		}
		long now = System.currentTimeMillis();
		if (lastNoteTime > 0 && (now - lastNoteTime > NOTE_TIMEOUT_MS)) {
			notes.clear();
		}
		lastNoteTime = now;

		if (notes.size() >= 3) {
			notes.removeFirst();
		}
		notes.addLast(note);
	}

	public synchronized Integer resolveCombo() {
		long now = System.currentTimeMillis();
		if (lastNoteTime > 0 && (now - lastNoteTime > NOTE_TIMEOUT_MS)) {
			notes.clear();
			return null;
		}
		if (notes.size() == 3) {
			return BlendingResolver.resolve(notes);
		}
		return null;
	}

	public synchronized void clear() {
		notes.clear();
		lastNoteTime = 0;
	}

	public synchronized boolean isComplete() {
		long now = System.currentTimeMillis();
		if (lastNoteTime > 0 && (now - lastNoteTime > NOTE_TIMEOUT_MS)) {
			notes.clear();
			return false;
		}
		return notes.size() == 3;
	}

	public synchronized Deque<BlendingNote> getNotes() {
		return new ArrayDeque<>(notes);
	}
}
