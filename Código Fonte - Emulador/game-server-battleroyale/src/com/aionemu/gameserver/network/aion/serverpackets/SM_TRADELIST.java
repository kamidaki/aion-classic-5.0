package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.ArrayList;
import java.util.List;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.limiteditems.LimitedItem;
import com.aionemu.gameserver.model.limiteditems.LimitedTradeNpc;
import com.aionemu.gameserver.model.templates.goods.GoodsList;
import com.aionemu.gameserver.model.templates.tradelist.TradeListTemplate;
import com.aionemu.gameserver.model.templates.tradelist.TradeListTemplate.TradeTab;
import com.aionemu.gameserver.model.templates.tradelist.TradeNpcType;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.LimitedItemTradeService;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_TRADELIST extends AionServerPacket {

	private int targetObjId;
	private int playerObjId;
	private TradeNpcType tradeNpcType;
	private int buyPriceModifier;
	private boolean showBuyTab;
	private boolean showSellTab;
	private List<TradeTab> tradeTablist;
	private List<LimitedItem> limitedItems;

	public SM_TRADELIST(Player player, Npc npc, TradeListTemplate tlist, int buyPriceModifier) {
		int legionLevel = player.getLegion() == null ? 0 : player.getLegion().getLegionLevel();

		this.targetObjId = npc.getObjectId();
		this.playerObjId = player.getObjectId();
		this.tradeNpcType = tlist.getTradeNpcType();
		this.buyPriceModifier = buyPriceModifier;
		this.showBuyTab = npc.canSell();
		this.showSellTab = npc.canBuy();
		this.tradeTablist = new ArrayList<>();
		this.limitedItems = new ArrayList<>();

		for (TradeTab tab : tlist.getTradeTablist()) {
			GoodsList goodsList = DataManager.GOODSLIST_DATA.getGoodsListById(tab.getId());
			if (goodsList == null || goodsList.getLegionLevel() > legionLevel)
				continue;
			this.tradeTablist.add(tab);
		}
		LimitedTradeNpc limitedTradeNpc = LimitedItemTradeService.getInstance().getLimitedTradeNpc(tlist.getNpcId());
		if (limitedTradeNpc != null)
			this.limitedItems.addAll(limitedTradeNpc.getLimitedItems());
	}

	/**
	 * Layout 5.0 medido nas capturas oficiais (9 lojas): sem o D 100 da 4.5, e cada item limitado ocupa 16 bytes.
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(targetObjId);
		writeC(tradeNpcType.index()); // reward, abyss or normal
		writeD(buyPriceModifier); // Vendor Buy Price Modifier
		writeC(showBuyTab ? 1 : 0);
		writeC(showSellTab ? 1 : 0);
		writeH(tradeTablist.size());
		for (TradeTab tradeTabl : tradeTablist)
			writeD(tradeTabl.getId());
		writeH(limitedItems.size());
		for (LimitedItem limitedItem : limitedItems) {
			writeD(limitedItem.getItemId());
			writeD(limitedItem.getBuyCount(playerObjId)); // no oficial vai de 0 para 1 depois de comprar um
			writeD(limitedItem.getSellLimit()); // 0 em todas as capturas; significado nao confirmado
			writeD(tabDoItem(limitedItem.getItemId()));
		}
	}

	private int tabDoItem(int itemId) {
		for (TradeTab tab : tradeTablist) {
			GoodsList goodsList = DataManager.GOODSLIST_DATA.getGoodsListById(tab.getId());
			if (goodsList != null && goodsList.getItemIdList().contains(itemId))
				return tab.getId();
		}
		return tradeTablist.isEmpty() ? 0 : tradeTablist.get(0).getId();
	}
}
