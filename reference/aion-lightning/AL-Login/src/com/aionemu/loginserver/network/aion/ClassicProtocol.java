/**
 * This file is part of Aion-Lightning <aion-lightning.org>.
 *
 *  Aion-Lightning is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  Aion-Lightning is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details. *
 *  You should have received a copy of the GNU General Public License
 *  along with Aion-Lightning.
 *  If not, see <http://www.gnu.org/licenses/>.
 */


package com.aionemu.loginserver.network.aion;

/**
 * Constantes do protocolo de login do Aion Classic 4.5 (cliente GameForge x64,
 * ProductVersion 4526.0820.0706.7137).
 *
 * Nao sao opcoes: cada valor aqui e uma condicao que o proprio Game.dll testa. Errar qualquer um
 * deles nao gera erro de rede -- o cliente simplesmente para de avancar, sem mensagem. Os offsets
 * citados sao do Game.dll x64 e estao detalhados em docs/reverse/game-dll-x64-findings.md.
 *
 * O que varia por instalacao (bracket do servidor) fica em {@link com.aionemu.loginserver.configs.Config}.
 */
public final class ClassicProtocol {

	private ClassicProtocol() {
	}

	/**
	 * Byte lido em SM_INIT+0xA8. O cliente faz {@code movzx ecx,[rdx+0xA8]; lea eax,[rcx-0xFD]}
	 * antes de habilitar o RSA e a chave Blowfish da sessao. Sem ele o handshake nao fecha.
	 * Rotina em 0x842301.
	 */
	public static final int INIT_RSA_ENABLE_FLAG = 0xFD;

	/**
	 * Versao do cliente que segue o flag acima, em SM_INIT+0xA9: {@code 04 05 00 00}.
	 */
	public static final int CLIENT_VERSION_MAJOR = 0x04;
	public static final int CLIENT_VERSION_MINOR = 0x05;

	/**
	 * Tamanho total de SM_INIT antes da cifragem. O conteudo do Classic ocupa 173 bytes; os 4 bytes
	 * restantes sao zeros. Manter 177 nao e cosmetico: a CryptEngine deriva o tamanho do primeiro
	 * pacote de {@code len+8 arredondado para multiplo de 8}, e 177 e o unico valor que resulta nos
	 * 192 bytes que o cliente espera.
	 */
	public static final int INIT_PACKET_SIZE = 177;

	/**
	 * Flags de conta em SM_LOGIN_OK+0x10..0x1F. O cliente testa o bit 0x10 em 0x717BE2
	 * ({@code test bl,0x10}); com ele zerado a sessao trava na tela de Termos de Servico.
	 * 0x3F liga tambem os bits de conta ativa e maior de idade.
	 */
	public static final int ACCOUNT_FLAGS = 0x0000003F;

	/**
	 * Assinatura obrigatoria em SM_LOGIN_OK+0x20 e +0x21, conferida em 0x717B40. Sem ela o cliente
	 * nunca chega ao {@code cmp eax,0x102} que abre a tela de selecao de servidor.
	 */
	public static final int LOGIN_OK_SIGNATURE_0 = 0xFF;
	public static final int LOGIN_OK_SIGNATURE_1 = 0xFE;

	/**
	 * Termos de servico aceitos, em SM_LOGIN_OK+0x30.
	 */
	public static final int TOS_ACCEPTED = 0x00000001;

	/**
	 * Campo ServerBits de cada entrada de SM_SERVER_LIST. O cliente faz {@code bt r15d,10} em
	 * 0x842B20 e descarta a entrada se o bit 10 (0x400) estiver zerado -- e o bit que marca
	 * "servidor Classic". O 0x1 restante e o marcador de servidor normal.
	 */
	public static final int SERVER_BITS = 0x00000401;
}
