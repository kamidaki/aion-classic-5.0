package com.aionemu.gameserver.model.templates.item;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;

import java.util.List;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "TradeinList", propOrder = {"tradeinItem"})
public class TradeinList
{
    @XmlElement(name = "tradein_item")
    protected List<TradeinItem> tradeinItem;
	
    public List<TradeinItem> getTradeinItem() {
        return this.tradeinItem;
    }
	
    public TradeinItem getFirstTradeInItem() {
        return this.tradeinItem.get(0);
    }
}