package com.aionemu.gameserver.dataholders;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;

import com.aionemu.gameserver.model.templates.item.OptionClearTemplate;

/**
 * Manastone and godstone removal rules of the Classic 5.0 option clear window, by socketed stone item id.
 */
@XmlRootElement(name = "option_clears")
@XmlAccessorType(XmlAccessType.FIELD)
public class OptionClearData {

	@XmlElement(name = "option_clear")
	private List<OptionClearTemplate> templates;

	@XmlTransient
	private final Map<Integer, OptionClearTemplate> templatesByStoneId = new HashMap<>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		templatesByStoneId.clear();
		if (templates != null) { // um arquivo sem nenhuma regra e valido para o JAXB e nao pode derrubar o boot
			for (OptionClearTemplate template : templates)
				templatesByStoneId.put(template.getItemId(), template);
			templates = null;
		}
	}

	public int size() {
		return templatesByStoneId.size();
	}

	public OptionClearTemplate getByStoneId(int itemId) {
		return templatesByStoneId.get(itemId);
	}
}
