package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;

import com.aionemu.gameserver.model.templates.storybook.StorybookAppraiseTemplate;
import com.aionemu.gameserver.model.templates.storybook.StorybookTemplate;

/**
 * Book of Legends (storybook/storybook.xml, gerado do client_storybook.xml, client_storybook_reward.xml e client_appraise_item.xml).
 */
@XmlRootElement(name = "storybooks")
@XmlAccessorType(XmlAccessType.FIELD)
public class StorybookData {

	@XmlElement(name = "storybook")
	private List<StorybookTemplate> storybookList = new ArrayList<>();

	@XmlElement(name = "appraise")
	private List<StorybookAppraiseTemplate> appraiseList = new ArrayList<>();

	@XmlTransient
	private final Map<Integer, StorybookTemplate> storybooks = new LinkedHashMap<>();

	@XmlTransient
	private final Map<Integer, StorybookAppraiseTemplate> appraises = new HashMap<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		for (StorybookTemplate storybook : storybookList)
			if (storybooks.put(storybook.getId(), storybook) != null)
				throw new IllegalArgumentException("Duplicate storybook " + storybook.getId());
		storybookList = null;
		for (StorybookAppraiseTemplate appraise : appraiseList) {
			int total = appraise.getResults().stream().mapToInt(StorybookAppraiseTemplate.Result::getRate).sum();
			if (total != 10000)
				throw new IllegalArgumentException("Invalid storybook appraise " + appraise.getItemId() + ": rates sum " + total);
			if (appraises.put(appraise.getItemId(), appraise) != null)
				throw new IllegalArgumentException("Duplicate storybook appraise " + appraise.getItemId());
		}
		appraiseList = null;
	}

	public StorybookTemplate getStorybook(int id) {
		return storybooks.get(id);
	}

	public Collection<StorybookTemplate> getStorybooks() {
		return Collections.unmodifiableCollection(storybooks.values());
	}

	public StorybookAppraiseTemplate getAppraise(int itemId) {
		return appraises.get(itemId);
	}

	public int size() {
		return storybooks.size();
	}

	public int appraiseSize() {
		return appraises.size();
	}
}
