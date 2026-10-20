package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerAppearance;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_STATUS_OTHER (S 0x02) do 5.0: personagem de outro jogador para a janela de detalhe (lupa do ranking, C 0x133), seguido dos S 0x40 do
 * equipamento.
 * <p>
 * Medido em 4 amostras (Kodra e Kakarott na captura outros 2026-09-21 06:10, Tursia e Kakarott nas 06_Sistemas_Novos de 20/10), 500 b depois
 * do nome mais a string do fim:
 * <ul>
 * <li>[S nome][D 100000 + raça*2 + gênero][C classe][C raça][C gênero][C 0] e 19 bytes 0;</li>
 * <li>os 67 bytes de aparência do S_PUT_USER (iguais byte a byte no Kodra) e C 10;</li>
 * <li>o nível em H no offset 118 depois do nome (61 no Kodra, o mesmo do S_PUT_USER dele);</li>
 * <li>H 6, H 4, C 4, C 4 e C 0x0B iguais nas 4 amostras, de jogadores diferentes;</li>
 * <li>vão 0 os campos que variam sem significado provado: um colar equipado (121001261/121001290, duas vezes), 561/569, um C 0/1, a string
 * do fim (vazia em 3 amostras, 3 ícones na Tursia) e os dois D depois dela (0, 9 ou 281).</li>
 * </ul>
 * O comando de console "status" também usa este pacote.
 */
public class SM_STATUS_OTHER extends AionServerPacket {

	private final String name;
	private final int raceId;
	private final int genderId;
	private final int classId;
	private final int level;
	private final PlayerAppearance appearance;

	public SM_STATUS_OTHER(Player player) {
		this(player.getCommonData(), player.getPlayerAppearance());
	}

	public SM_STATUS_OTHER(PlayerCommonData pcd, PlayerAppearance appearance) {
		this.name = pcd.getName();
		this.raceId = pcd.getRace().getRaceId();
		this.genderId = pcd.getGender().getGenderId();
		this.classId = pcd.getPlayerClass().getClassId();
		this.level = pcd.getLevel();
		this.appearance = appearance;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeS(name);
		writeD(100000 + raceId * 2 + genderId);
		writeC(classId);
		writeC(raceId);
		writeC(genderId);
		writeC(0);
		writeB(new byte[19]);
		writeAppearance(appearance);
		writeC(10);
		writeB(new byte[3]);
		writeD(0); // colar equipado (sem prova do porquê)
		writeD(0); // 561/569
		writeH(6);
		writeH(4);
		writeB(new byte[5]);
		writeC(4);
		writeC(0);
		writeC(4);
		writeH(level);
		writeB(new byte[12]);
		writeC(0x0B);
		writeC(0); // 0 no Kodra, 1 nos outros
		writeC(0);
		writeD(0); // o mesmo colar
		writeB(new byte[345]);
		writeH(0);
		writeS(""); // vazia, ou 3 ícones na Tursia
		writeD(1);
		writeD(0); // 0, 9 ou 281
		writeD(0);
	}
}
