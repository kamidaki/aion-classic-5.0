package com.lostacademy.nativepath;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Grade de navegação oficial do cliente 5.0 ({@code levels/<mapa>/<mapa>-path.dat}), células de 0,5 m.
 * <p>
 * Formato (decodificado das capturas oficiais em 27/10/2026; 118/118 arquivos fecham no fim, 99,1% de 122 mil pontos de chão
 * oficiais com |dz| &lt; 0,15 m):
 *
 * <pre>
 * header 128 b | [i32 n1][bloco 1: n1 b] | [i32 n2][n2 x u32] | setores de 16 m (y externo, x interno):
 *   [u8 nº de camadas] e, por camada, [u8 tipo] +
 *   tipo 16 : [u32 offset da lista no bloco 1][u16 nº de nós]          grafo explícito (pontes, bordas, prédios)
 *   demais  : [u8 lados][4 x u32 borda] + dados, célula i = sy*32 + sx
 *     0/1 [i32 z cm] piso plano | 2/3 terreno | 6/7 128 b, 1 bit (LSB primeiro): 1 bloqueado, 0 terreno
 *     8/9 [2 x i32 z] + 2 bits: 0-1 paleta, 2 terreno, 3 bloqueado
 *     10/11 [14 x i32 z] + 4 bits (nibble baixo = célula par): 0-13 paleta, 14 terreno, 15 bloqueado
 *     12/13 [i32 base] + u8: base+v, 0xFE terreno, 0xFF bloqueado | 14/15 [i32 base] + u16: 0xFFFE terreno, 0xFFFF bloqueado
 *     ímpares: + 512 b (sem significado conhecido)
 * Nó do tipo 16: [i32 z cm][u16 cx][u16 cy][u8 máscara], 2 bits por direção (x+1, y+1, x-1, y-1):
 *   01 = u16 offset do vizinho na mesma lista; 10 = u32: bits 7-31 offset absoluto do nó no bloco 1 (0/1 = camada simples
 *   na célula ao lado; bits 0-6 ainda sem significado certo). Ligações de mão única (queda livre, subida até ~1,9 m).
 * </pre>
 *
 * Os nós são lidos direto dos bytes, sob demanda; cada lista só é indexada por célula quando é usada.
 */
public final class PathDatMap {

	/** Altura do terreno (heightmap do geo do servidor) em x/y; NaN onde não há terreno. */
	public interface Terreno {
		float z(float x, float y);
	}

	/** Um piso de uma célula: nó do grafo, altura e se é andável. */
	public record Piso(long no, float z, boolean livre) {
	}

	static final int B1 = 132;
	static final int[] CORPO = { 4, 4, 0, 0, 1024, 1024, 128, 128, 264, 264, 568, 568, 1028, 1028, 2052, 2052 };
	static final int[][] DIR = { { 1, 0 }, { 0, 1 }, { -1, 0 }, { 0, -1 } };
	private static final int[] TAMANHOS = { 512, 1024, 1536, 2048, 3072, 4096, 6144 };

	private final byte[] f;
	private final Terreno terreno;
	private int tam, dim;
	private int[] setorIni;             // dim*dim+1: primeira camada de cada setor em cam*
	private byte[] camTipo;
	private int[] camOff, camN;          // tipo 16: offset da lista e nº de nós; demais: offset do byte de tipo
	private int[] listas16;              // índices de camada tipo 16 ordenados pelo offset da lista
	private final Map<Integer, Map<Integer, int[]>> celulasDaLista = new HashMap<>();

	private PathDatMap(byte[] f, Terreno terreno) {
		this.f = f;
		this.terreno = terreno;
	}

	/**
	 * @param tamanhoMundo world_size do world_maps (o path.dat de 310050000, 330040000 e 800050000 tem 512 m e não 1024: o tamanho
	 *          que fecha o arquivo é o que vale)
	 */
	public static PathDatMap carrega(Path arquivo, int tamanhoMundo, Terreno terreno) throws IOException {
		PathDatMap m = new PathDatMap(Files.readAllBytes(arquivo), terreno);
		List<Integer> tentativas = new ArrayList<>();
		tentativas.add(tamanhoMundo);
		for (int t : TAMANHOS)
			if (t != tamanhoMundo)
				tentativas.add(t);
		for (int t : tentativas)
			if (m.le(t))
				return m;
		throw new IOException("path.dat não fecha com nenhum tamanho de mapa: " + arquivo);
	}

	private boolean le(int tamanho) {
		try {
			int d = tamanho / 16;
			int off = B1 + i32(128);
			off += 4 + 4 * i32(off);
			int[] ini = new int[d * d + 1];
			List<int[]> cams = new ArrayList<>();
			for (int s = 0; s < d * d; s++) {
				ini[s] = cams.size();
				int n = u8(off++);
				for (int l = 0; l < n; l++) {
					int t = u8(off);
					if (t == 16) {
						cams.add(new int[] { 16, i32(off + 1), u16(off + 5) });
						off += 7;
					} else {
						if (t > 15)
							return false;
						cams.add(new int[] { t, off, 0 });
						off += 18 + CORPO[t] + (t % 2 == 1 ? 512 : 0);
					}
				}
			}
			ini[d * d] = cams.size();
			if (off != f.length)
				return false;
			tam = tamanho;
			dim = d;
			setorIni = ini;
			camTipo = new byte[cams.size()];
			camOff = new int[cams.size()];
			camN = new int[cams.size()];
			List<Integer> l16 = new ArrayList<>();
			for (int i = 0; i < cams.size(); i++) {
				int[] c = cams.get(i);
				camTipo[i] = (byte) c[0];
				camOff[i] = c[1];
				camN[i] = c[2];
				if (c[0] == 16)
					l16.add(i);
			}
			listas16 = l16.stream().sorted((a, b) -> Integer.compare(camOff[a], camOff[b])).mapToInt(Integer::intValue).toArray();
			return true;
		} catch (ArrayIndexOutOfBoundsException e) {
			return false;
		}
	}

	public int getTamanho() {
		return tam;
	}

	// ---------------------------------------------------------------- chaves de nó

	/** Nó tipo 16: camada (índice global) + offset absoluto no bloco 1. */
	static long chaveNo(int camada, int abs) {
		return (1L << 62) | ((long) camada << 32) | (abs & 0xFFFFFFFFL);
	}

	/** Célula de camada simples (camada = índice global; -1 = setor sem camada, terreno puro). */
	static long chaveCelula(int camada, int cx, int cy) {
		return (2L << 62) | ((long) (camada + 1) << 30) | ((long) cx << 15) | cy;
	}

	static boolean ehNo(long chave) {
		return (chave >>> 62) == 1;
	}

	static int camadaDe(long chave) {
		return ehNo(chave) ? (int) ((chave >>> 32) & 0x3FFFFFFF) : (int) ((chave >>> 30) & 0xFFFFFFFFL & 0xFFFFFFFL) - 1;
	}

	static int absDe(long chave) {
		return (int) chave;
	}

	public int cx(long chave) {
		return ehNo(chave) ? u16(B1 + absDe(chave) + 4) : (int) ((chave >>> 15) & 0x7FFF);
	}

	public int cy(long chave) {
		return ehNo(chave) ? u16(B1 + absDe(chave) + 6) : (int) (chave & 0x7FFF);
	}

	/** Altura do nó tipo 16 (a da célula simples vem de {@link #pisos}). */
	float zNo(long chave) {
		return i32(B1 + absDe(chave)) / 100f;
	}

	// ---------------------------------------------------------------- ligações dos nós tipo 16

	/** Ligação de um nó tipo 16: direção, tipo (1 = mesma lista, 2 = outro setor) e valor (offset absoluto do destino / u32 cru). */
	record Ligacao(int dir, int tipo, long valor) {
	}

	List<Ligacao> ligacoes(long no) {
		int abs = absDe(no), p = B1 + abs + 9, m = u8(B1 + abs + 8);
		int lista = camOff[camadaDe(no)];
		List<Ligacao> out = new ArrayList<>(4);
		for (int d = 0; d < 4; d++) {
			int c = (m >> (2 * d)) & 3;
			if (c == 1) {
				out.add(new Ligacao(d, 1, lista + u16(p)));
				p += 2;
			} else if (c >= 2) {
				out.add(new Ligacao(d, 2, i32(p) & 0xFFFFFFFFL));
				p += 4;
			}
		}
		return out;
	}

	/** Camada (índice global) da lista tipo 16 que contém o offset absoluto. */
	int camadaDoNo(int abs) {
		int lo = 0, hi = listas16.length - 1, r = -1;
		while (lo <= hi) {
			int mid = (lo + hi) >>> 1;
			if (camOff[listas16[mid]] <= abs) {
				r = listas16[mid];
				lo = mid + 1;
			} else
				hi = mid - 1;
		}
		return r;
	}

	// ---------------------------------------------------------------- pisos

	/** Todos os pisos da célula (cx, cy). Setor sem camada = terreno livre. */
	public List<Piso> pisos(int cx, int cy) {
		List<Piso> out = new ArrayList<>(3);
		int sx = cx >> 5, sy = cy >> 5;
		if (sx < 0 || sy < 0 || sx >= dim || sy >= dim)
			return out;
		float x = cx * 0.5f + 0.25f, y = cy * 0.5f + 0.25f;
		int s = sy * dim + sx, i = (cy - sy * 32) * 32 + (cx - sx * 32);
		int ini = setorIni[s], fim = setorIni[s + 1];
		if (ini == fim) {
			float z = terreno.z(x, y);
			if (!Float.isNaN(z))
				out.add(new Piso(chaveCelula(-1, cx, cy), z, true));
			return out;
		}
		for (int c = ini; c < fim; c++) {
			if (camTipo[c] == 16) {
				int[] nos = celulas(c).get(cx * 16384 + cy);
				if (nos != null)
					for (int abs : nos)
						out.add(new Piso(chaveNo(c, abs), i32(B1 + abs) / 100f, true));
				continue;
			}
			int a = camOff[c], d = a + 18, t = camTipo[c];
			float z;
			boolean livre = true;
			switch (t) {
				case 0, 1 -> z = i32(d) / 100f;
				case 2, 3 -> z = terreno.z(x, y);
				case 6, 7 -> {
					livre = ((u8(d + (i >> 3)) >> (i & 7)) & 1) == 0;
					z = terreno.z(x, y);
				}
				case 8, 9 -> {
					int v = (u8(d + 8 + (i >> 2)) >> ((i & 3) * 2)) & 3;
					z = v < 2 ? i32(d + 4 * v) / 100f : terreno.z(x, y);
					livre = v != 3;
				}
				case 10, 11 -> {
					int b = u8(d + 56 + (i >> 1)), v = (i & 1) == 1 ? b >> 4 : b & 15;
					z = v < 14 ? i32(d + 4 * v) / 100f : terreno.z(x, y);
					livre = v != 15;
				}
				case 12, 13 -> {
					int v = u8(d + 4 + i);
					z = v < 0xFE ? (i32(d) + v) / 100f : terreno.z(x, y);
					livre = v != 0xFF;
				}
				case 14, 15 -> {
					int v = u16(d + 4 + 2 * i);
					z = v < 0xFFFE ? (i32(d) + v) / 100f : terreno.z(x, y);
					livre = v != 0xFFFF;
				}
				default -> {
					continue;
				}
			}
			if (!Float.isNaN(z))
				out.add(new Piso(chaveCelula(c, cx, cy), z, livre));
		}
		return out;
	}

	/** Altura de um nó ou célula. */
	public float z(long chave) {
		if (ehNo(chave))
			return zNo(chave);
		for (Piso p : pisos(cx(chave), cy(chave)))
			if (p.no() == chave)
				return p.z();
		return Float.NaN;
	}

	private Map<Integer, int[]> celulas(int camada) {
		synchronized (celulasDaLista) {
			Map<Integer, int[]> m = celulasDaLista.get(camada);
			if (m != null)
				return m;
			m = new HashMap<>();
			int p = B1 + camOff[camada];
			for (int k = 0; k < camN[camada]; k++) {
				int abs = p - B1, cell = u16(p + 4) * 16384 + u16(p + 6), msk = u8(p + 8);
				int[] v = m.get(cell);
				m.put(cell, v == null ? new int[] { abs } : append(v, abs));
				p += 9;
				for (int d = 0; d < 4; d++) {
					int c = (msk >> (2 * d)) & 3;
					p += c == 1 ? 2 : c >= 2 ? 4 : 0;
				}
			}
			celulasDaLista.put(camada, m);
			return m;
		}
	}

	private static int[] append(int[] a, int v) {
		int[] r = Arrays.copyOf(a, a.length + 1);
		r[a.length] = v;
		return r;
	}

	// ---------------------------------------------------------------- bytes

	private int u8(int o) {
		return f[o] & 0xFF;
	}

	private int u16(int o) {
		return (f[o] & 0xFF) | (f[o + 1] & 0xFF) << 8;
	}

	private int i32(int o) {
		return (f[o] & 0xFF) | (f[o + 1] & 0xFF) << 8 | (f[o + 2] & 0xFF) << 16 | f[o + 3] << 24;
	}
}
