package com.aionemu.gameserver.ai.poll;


public class SimpleAIAnswer implements AIAnswer {

	private final boolean answer;

	/**
	 * @param answer
	 */
	SimpleAIAnswer(boolean answer) {
		this.answer = answer;
	}

	@Override
	public boolean isPositive() {
		return answer;
	}

	@Override
	public Object getResult() {
		return answer;
	}

}
