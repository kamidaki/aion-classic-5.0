import com.aionemu.commons.network.packet.BaseServerPacket;
import com.aionemu.loginserver.network.aion.SessionKey;

import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * Monta os pacotes pelo caminho real (writeImpl) e confere os offsets que o Game.dll testa.
 * Reproduz o preambulo de AionServerPacket.write: short de tamanho + byte de opcode.
 */
public class VerifyLoginPackets {

    static int failures = 0;

    static byte[] build(BaseServerPacket pkt, int opcode) throws Exception {
        ByteBuffer buf = ByteBuffer.allocate(8192).order(ByteOrder.LITTLE_ENDIAN);
        pkt.setBuf(buf);
        buf.putShort((short) 0);
        buf.put((byte) opcode);
        Method writeImpl = pkt.getClass().getDeclaredMethod("writeImpl",
                Class.forName("com.aionemu.loginserver.network.aion.LoginConnection"));
        writeImpl.setAccessible(true);
        writeImpl.invoke(pkt, (Object) null);
        byte[] out = new byte[buf.position() - 2];
        System.arraycopy(buf.array(), 2, out, 0, out.length);   // descarta o short de tamanho
        return out;
    }

    static void check(String what, int actual, int expected) {
        boolean ok = actual == expected;
        if (!ok) failures++;
        System.out.printf("  [%s] %-46s = 0x%02X (esperado 0x%02X)%n",
                ok ? "OK " : "X  ", what, actual, expected);
    }

    static void checkLen(String what, int actual, int expected) {
        boolean ok = actual == expected;
        if (!ok) failures++;
        System.out.printf("  [%s] %-46s = %d (esperado %d)%n",
                ok ? "OK " : "X  ", what, actual, expected);
    }

    public static void main(String[] args) throws Exception {
        byte[] rsa = new byte[128];
        for (int i = 0; i < 128; i++) rsa[i] = (byte) (0xA0 + (i & 0x0F));
        byte[] bf = new byte[16];
        for (int i = 0; i < 16; i++) bf[i] = (byte) (0xB0 + i);

        System.out.println("SM_INIT (Classic 4.5)");
        Class<?> smInit = Class.forName("com.aionemu.loginserver.network.aion.serverpackets.SM_INIT");
        Constructor<?> c = smInit.getDeclaredConstructor(byte[].class, byte[].class, int.class);
        c.setAccessible(true);
        byte[] init = build((BaseServerPacket) c.newInstance(rsa, bf, 0x11223344), 0x00);

        checkLen("tamanho total", init.length, 177);
        check("0x00 opcode", init[0x00] & 0xFF, 0x00);
        check("0x09 primeiro byte do modulo RSA", init[0x09] & 0xFF, rsa[0] & 0xFF);
        check("0x88 ultimo byte do modulo RSA", init[0x88] & 0xFF, rsa[127] & 0xFF);
        check("0x89 zero", init[0x89] & 0xFF, 0x00);
        check("0x95 primeiro byte da chave Blowfish", init[0x95] & 0xFF, bf[0] & 0xFF);
        check("0xA4 ultimo byte da chave Blowfish", init[0xA4] & 0xFF, bf[15] & 0xFF);
        check("0xA8 flag que habilita o RSA", init[0xA8] & 0xFF, 0xFD);
        check("0xA9 versao major", init[0xA9] & 0xFF, 0x04);
        check("0xAA versao minor", init[0xAA] & 0xFF, 0x05);
        check("0xAB zero", init[0xAB] & 0xFF, 0x00);
        check("0xAC zero", init[0xAC] & 0xFF, 0x00);

        // a CryptEngine deriva o tamanho do primeiro pacote; tem que dar 192
        int len = init.length + 4 + 4;
        len += 8 - len % 8;
        checkLen("tamanho apos a CryptEngine", len, 192);

        System.out.println("\nSM_LOGIN_OK (Classic 4.5)");
        Class<?> smOk = Class.forName("com.aionemu.loginserver.network.aion.serverpackets.SM_LOGIN_OK");
        Constructor<?> c2 = smOk.getDeclaredConstructor(SessionKey.class);
        c2.setAccessible(true);
        byte[] ok = build((BaseServerPacket) c2.newInstance(new SessionKey(0x0A0B0C0D, 0x01020304, 0, 0)), 0x03);

        checkLen("tamanho total", ok.length, 78);   // 1 opcode + 77 de corpo
        check("0x11 flags de conta (bit 0x10 = TOS)", ok[0x01 + 0x10] & 0xFF, 0x3F);
        check("0x21 assinatura [0]", ok[0x01 + 0x20] & 0xFF, 0xFF);
        check("0x22 assinatura [1]", ok[0x01 + 0x21] & 0xFF, 0xFE);
        check("0x31 termos aceitos", ok[0x01 + 0x30] & 0xFF, 0x01);

        System.out.println(failures == 0
                ? "\n>>> todos os offsets conferem"
                : "\n>>> " + failures + " divergencia(s)");
        System.exit(failures == 0 ? 0 : 1);
    }
}
