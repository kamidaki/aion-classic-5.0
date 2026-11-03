package com.lostacademy.nativepath;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import com.lostacademy.nativepath.PathDatMap.Ligacao;
import com.lostacademy.nativepath.PathDatMap.Piso;

/**
 * Busca de caminho na grade oficial ({@link PathDatMap}), com as regras medidas nas voltas oficiais de mobs
 * (43 de 44 reproduzidas em DF1 e 220040000, capturas de 27/10/2026):
 * <ul>
 * <li>nó tipo 16 usa só as ligações do arquivo (mão única: queda livre, subida até {@link #SUBIDA});</li>
 * <li>célula simples liga às vizinhas livres com |dz| &lt;= {@link #SUBIDA}; num nó tipo 16 só se entra pelo lado em que ele tem
 * ligação de volta (a lateral de uma rampa não sobe);</li>
 * <li>a divisa de setor vale nos dois sentidos;</li>
 * <li>8 direções; a queda custa {@link #QUEDA} x altura (rampa 3,2 m mais longa ganhou de queda de 11,19 m; queda de 9,15 m ganhou de
 * rampa 4,4 m mais longa);</li>
 * <li>alisamento: a reta anda pelas ligações célula a célula e ignora a altura interpolada (o oficial "atravessa" rampa e escada);
 * uma queda quebra a reta. Com {@link #seguePiso} a reta também precisa ficar a {@link #TOLERANCIA_PISO} do chão (desvio consciente
 * do oficial, para o mob não cortar rampa).</li>
 * </ul>
 * No servidor (decisão de 27/10/2026) o NPC nunca cai de borda ({@link #permiteQueda} = false: a queda do oficial é erro dele) e
 * uma rota andando mais longa que o limite conta como inalcançável. Com queda permitida o comportamento é o oficial (testes).
 */
public final class PathDatGrid {

	public static final float SUBIDA = 1.9f;
	public static final float QUEDA = 0.4f;
	public static final float TOLERANCIA_PISO = 0.5f;
	private static final int[][] DIR = PathDatMap.DIR;

	private final PathDatMap m;
	private final boolean seguePiso;
	private final boolean permiteQueda;

	/** Como o oficial: com queda de borda. */
	public PathDatGrid(PathDatMap mapa, boolean seguePiso) {
		this(mapa, seguePiso, true);
	}

	public PathDatGrid(PathDatMap mapa, boolean seguePiso, boolean permiteQueda) {
		this.m = mapa;
		this.seguePiso = seguePiso;
		this.permiteQueda = permiteQueda;
	}

	private record Viz(long no, float z) {
	}

	private static int setorDe(int c) {
		return c >> 5;
	}

	// ---------------------------------------------------------------- grafo

	/** Vizinhos andáveis; sem {@link #permiteQueda}, as ligações de queda (dz &lt; -SUBIDA) ficam de fora. */
	private List<Viz> vizinhos(long no) {
		List<Viz> v = vizinhosArquivo(no);
		if (permiteQueda)
			return v;
		float z = m.z(no);
		v.removeIf(q -> q.z() - z < -SUBIDA);
		return v;
	}

	private List<Viz> vizinhosArquivo(long no) {
		List<Viz> out = new ArrayList<>(6);
		int cx = m.cx(no), cy = m.cy(no);
		float z = m.z(no);
		if (PathDatMap.ehNo(no)) {
			List<Ligacao> lig = m.ligacoes(no);
			Set<Integer> ligadas = new HashSet<>();
			for (Ligacao l : lig)
				ligadas.add(l.dir());
			for (int d = 0; d < 4; d++) {                       // divisa de setor nos dois sentidos
				int tx = cx + DIR[d][0], ty = cy + DIR[d][1];
				if (ligadas.contains(d) || (setorDe(tx) == setorDe(cx) && setorDe(ty) == setorDe(cy)))
					continue;
				for (Piso p : m.pisos(tx, ty))
					if (p.livre() && Math.abs(p.z() - z) <= SUBIDA)
						out.add(new Viz(p.no(), p.z()));
			}
			for (Ligacao l : lig) {
				int tx = cx + DIR[l.dir()][0], ty = cy + DIR[l.dir()][1];
				if (l.tipo() == 1) {
					int abs = (int) l.valor();
					long q = PathDatMap.chaveNo(PathDatMap.camadaDe(no), abs);
					out.add(new Viz(q, m.zNo(q)));
				} else {
					long v = l.valor();
					int off = (int) (v >>> 7);
					if (off > 1) {
						long q = PathDatMap.chaveNo(m.camadaDoNo(off), off);
						out.add(new Viz(q, m.zNo(q)));
					} else {
						// camada simples: os bits 0-6 não são o índice da camada; piso livre mais perto da altura de origem e,
						// sem nenhum a SUBIDA, o andar pela ordem de altura (permite queda na divisa)
						List<Piso> livres = new ArrayList<>();
						for (Piso p : m.pisos(tx, ty))
							if (p.livre())
								livres.add(p);
						Piso perto = null;
						for (Piso p : livres)
							if (Math.abs(p.z() - z) <= SUBIDA && (perto == null || Math.abs(p.z() - z) < Math.abs(perto.z() - z)))
								perto = p;
						if (perto == null && !livres.isEmpty()) {
							livres.sort((a, b) -> Float.compare(a.z(), b.z()));
							perto = livres.get(Math.min((int) (v & 0x7F), livres.size() - 1));
						}
						if (perto != null)
							out.add(new Viz(perto.no(), perto.z()));
					}
				}
			}
			return out;
		}
		for (int d = 0; d < 4; d++) {
			int tx = cx + DIR[d][0], ty = cy + DIR[d][1];
			for (Piso p : m.pisos(tx, ty)) {
				if (!p.livre() || Math.abs(p.z() - z) > SUBIDA)
					continue;
				if (PathDatMap.ehNo(p.no())) {
					int volta = (d + 2) % 4;
					boolean temVolta = false;
					for (Ligacao l : m.ligacoes(p.no()))
						temVolta |= l.dir() == volta;
					if (!temVolta)
						continue;
				}
				out.add(new Viz(p.no(), p.z()));
			}
		}
		return out;
	}

	private static float custo(float h, float dz) {
		return h + (dz < -SUBIDA ? QUEDA * -dz : 0f);
	}

	/** Distância máxima em células (0,5 m) para achar piso quando o ponto caiu numa célula sem piso livre (parede, borda). */
	private static final int RAIO_RECUPERA = 3;

	/**
	 * Distância vertical máxima entre um ponto pedido e o piso: passos de rota antigos (4.x) e posições de spawn ficam até ~4 m acima do
	 * chão onde o NPC de fato anda; acima disso o ponto é aéreo e não é da grade.
	 */
	public static final float TOLERANCIA_PONTO = 4f;

	/**
	 * Nó livre de (x, y) com altura a até {@link #TOLERANCIA_PONTO} de z (o mais perto); se a célula não tiver (o NPC encostou numa
	 * parede ou o alvo está numa borda), o mais perto em até {@link #RAIO_RECUPERA} células. 0 se não houver.
	 */
	public long noEm(float x, float y, float z) {
		int cx = (int) (x / 0.5f), cy = (int) (y / 0.5f);
		for (int r = 0; r <= RAIO_RECUPERA; r++) {
			long melhor = 0;
			float custo = Float.MAX_VALUE;
			for (int dx = -r; dx <= r; dx++)
				for (int dy = -r; dy <= r; dy++) {
					if (Math.max(Math.abs(dx), Math.abs(dy)) != r)
						continue;
					for (Piso p : m.pisos(cx + dx, cy + dy)) {
						float dz = Math.abs(p.z() - z);
						if (!p.livre() || dz > TOLERANCIA_PONTO)
							continue;
						float c = (float) Math.hypot(dx, dy) * 0.5f + dz;
						if (c < custo) {
							custo = c;
							melhor = p.no();
						}
					}
				}
			if (melhor != 0)
				return melhor;
		}
		return 0;
	}

	// ---------------------------------------------------------------- A*

	/** Mesmo que {@link #caminho(long, long, int, float)} sem limite de comprimento. */
	public List<Long> caminho(long a, long b, int limite) {
		return caminho(a, b, limite, Float.MAX_VALUE);
	}

	/**
	 * A* em 8 direções (diagonal = dois passos ortogonais válidos). Rotas mais longas que maxComprimento metros são podadas: alvo
	 * inalcançável ou longe demais termina sem varrer o mapa. Estruturas em arrays (sem objeto por nó) e vizinhos calculados uma vez
	 * por nó em cada busca.
	 *
	 * @return nós do caminho (início e fim incluídos) ou null
	 */
	public List<Long> caminho(long a, long b, int limite, float maxComprimento) {
		Busca s = new Busca();
		int bx = m.cx(b), by = m.cy(b);
		int ia = s.indice(a);
		s.g[ia] = 0;
		s.pai[ia] = -1;
		s.push(ia, heuristica(a, bx, by));
		int n = 0, ib = -1;
		while (s.tam > 0) {
			int iu = s.pop();
			if (s.fechado[iu])
				continue;
			s.fechado[iu] = true;
			long u = s.chave[iu];
			if (u == b) {
				ib = iu;
				break;
			}
			if (++n > limite)
				break;
			int ux = m.cx(u), uy = m.cy(u);
			float zu = s.z(iu, this);
			int[] orto = s.viz(iu, this);
			for (int k = 0; k < orto.length; k++)
				relaxa(s, iu, orto[k], custo(0.5f, s.z(orto[k], this) - zu), bx, by, maxComprimento);
			for (int k = 0; k < orto.length; k++)
				for (int iv2 : s.viz(orto[k], this)) {
					long v2 = s.chave[iv2];
					if (Math.abs(m.cx(v2) - ux) == 1 && Math.abs(m.cy(v2) - uy) == 1)
						relaxa(s, iu, iv2, custo(0.7071f, s.z(iv2, this) - zu), bx, by, maxComprimento);
				}
		}
		if (ib < 0)
			return null;
		List<Long> out = new ArrayList<>();
		for (int i = ib; i >= 0; i = s.pai[i])
			out.add(0, s.chave[i]);
		return out;
	}

	private void relaxa(Busca s, int iu, int iv, float passo, int bx, int by, float max) {
		if (s.fechado[iv])
			return;
		float c = s.g[iu] + passo;
		if (c >= s.g[iv])
			return;
		float f = c + heuristica(s.chave[iv], bx, by);
		if (f > max)
			return; // mais longo que o limite: inalcançável para esta busca
		s.g[iv] = c;
		s.pai[iv] = iu;
		s.push(iv, f);
	}

	private float heuristica(long no, int bx, int by) {
		int hx = Math.abs(m.cx(no) - bx), hy = Math.abs(m.cy(no) - by);
		return 0.5f * (Math.max(hx, hy) + 0.4142f * Math.min(hx, hy));
	}

	/** Estado de uma busca: nós numa tabela hash aberta, g/pai/fechado/vizinhos em arrays, heap binário de índices. */
	private static final class Busca {

		long[] tabela = new long[1 << 14]; // chave + 1 (0 = vazio)
		int[] tabelaIdx = new int[1 << 14];
		long[] chave = new long[4096];
		float[] g = new float[4096], zs = new float[4096];
		int[] pai = new int[4096];
		boolean[] fechado = new boolean[4096];
		int[][] viz = new int[4096][];
		int n;
		int[] heap = new int[4096];
		float[] heapF = new float[4096];
		int tam;

		int indice(long k) {
			if (n * 2 >= tabela.length)
				rehash();
			int msk = tabela.length - 1, h = (int) (mix(k) & msk);
			while (tabela[h] != 0) {
				if (tabela[h] == k + 1)
					return tabelaIdx[h];
				h = (h + 1) & msk;
			}
			if (n == chave.length)
				cresce();
			tabela[h] = k + 1;
			tabelaIdx[h] = n;
			chave[n] = k;
			g[n] = Float.MAX_VALUE;
			zs[n] = Float.NaN;
			pai[n] = -1;
			return n++;
		}

		float z(int i, PathDatGrid grade) {
			if (Float.isNaN(zs[i]))
				zs[i] = grade.m.z(chave[i]);
			return zs[i];
		}

		int[] viz(int i, PathDatGrid grade) {
			if (viz[i] == null) {
				List<Viz> l = grade.vizinhos(chave[i]);
				int[] r = new int[l.size()];
				for (int k = 0; k < r.length; k++) {
					r[k] = indice(l.get(k).no());
					if (Float.isNaN(zs[r[k]]))
						zs[r[k]] = l.get(k).z();
				}
				viz[i] = r;
			}
			return viz[i];
		}

		private static long mix(long k) {
			k ^= k >>> 33;
			k *= 0xff51afd7ed558ccdL;
			k ^= k >>> 33;
			return k;
		}

		private void rehash() {
			long[] t = tabela;
			int[] ti = tabelaIdx;
			tabela = new long[t.length * 2];
			tabelaIdx = new int[t.length * 2];
			int msk = tabela.length - 1;
			for (int i = 0; i < t.length; i++)
				if (t[i] != 0) {
					int h = (int) (mix(t[i] - 1) & msk);
					while (tabela[h] != 0)
						h = (h + 1) & msk;
					tabela[h] = t[i];
					tabelaIdx[h] = ti[i];
				}
		}

		private void cresce() {
			int c = chave.length * 2;
			chave = Arrays.copyOf(chave, c);
			g = Arrays.copyOf(g, c);
			zs = Arrays.copyOf(zs, c);
			pai = Arrays.copyOf(pai, c);
			fechado = Arrays.copyOf(fechado, c);
			viz = Arrays.copyOf(viz, c);
		}

		void push(int i, float fi) {
			if (tam == heap.length) {
				heap = Arrays.copyOf(heap, tam * 2);
				heapF = Arrays.copyOf(heapF, tam * 2);
			}
			int k = tam++;
			while (k > 0) {
				int p = (k - 1) >>> 1;
				if (heapF[p] <= fi)
					break;
				heap[k] = heap[p];
				heapF[k] = heapF[p];
				k = p;
			}
			heap[k] = i;
			heapF[k] = fi;
		}

		int pop() {
			int r = heap[0];
			int ult = heap[--tam];
			float uf = heapF[tam];
			int k = 0;
			while (true) {
				int c = 2 * k + 1;
				if (c >= tam)
					break;
				if (c + 1 < tam && heapF[c + 1] < heapF[c])
					c++;
				if (heapF[c] >= uf)
					break;
				heap[k] = heap[c];
				heapF[k] = heapF[c];
				k = c;
			}
			if (tam > 0) {
				heap[k] = ult;
				heapF[k] = uf;
			}
			return r;
		}
	}

	// ---------------------------------------------------------------- alisamento

	public float[] ponto(long no) {
		return new float[] { m.cx(no) * 0.5f + 0.25f, m.cy(no) * 0.5f + 0.25f, m.z(no) };
	}

	private List<int[]> celulas(float[] p, float[] q) {
		List<int[]> out = new ArrayList<>();
		int n = Math.max(2, (int) (Math.hypot(q[0] - p[0], q[1] - p[1]) * 8));
		for (int k = 0; k <= n; k++) {
			float f = (float) k / n;
			int cx = (int) ((p[0] + (q[0] - p[0]) * f) / 0.5f), cy = (int) ((p[1] + (q[1] - p[1]) * f) / 0.5f);
			if (!out.isEmpty()) {
				int[] u = out.get(out.size() - 1);
				if (u[0] == cx && u[1] == cy)
					continue;
				if (Math.abs(cx - u[0]) + Math.abs(cy - u[1]) == 2)
					out.add(new int[] { cx, u[1] });
			}
			out.add(new int[] { cx, cy });
		}
		return out;
	}

	/** Reta de a até b andando pelas ligações, célula a célula, sem queda; termina no próprio b. */
	private boolean ve(long a, long b, boolean piso) {
		float[] p = ponto(a), q = ponto(b);
		List<int[]> cel = celulas(p, q);
		long u = a;
		for (int k = 1; k < cel.size(); k++) {
			int[] c = cel.get(k);
			float zu = m.z(u);
			Viz melhor = null;
			for (Viz v : vizinhos(u))
				if (m.cx(v.no()) == c[0] && m.cy(v.no()) == c[1] && v.z() - zu >= -SUBIDA
					&& (melhor == null || Math.abs(v.z() - zu) < Math.abs(melhor.z() - zu)))
					melhor = v;
			if (melhor == null)
				return false;
			u = melhor.no();
			if (piso) {
				float f = (float) k / cel.size(), zi = p[2] + (q[2] - p[2]) * f;
				if (Math.abs(melhor.z() - zi) > TOLERANCIA_PISO)
					return false;
			}
		}
		return u == b;
	}

	/** Pontos do caminho alisado (o primeiro é o início). Uma queda fica como dois pontos fixos (borda e pé). */
	public List<float[]> alisa(List<Long> nos) {
		List<float[]> P = new ArrayList<>();
		for (long u : nos)
			P.add(ponto(u));
		List<Integer> quebras = new ArrayList<>();
		quebras.add(0);
		for (int k = 1; k < P.size(); k++)
			if (P.get(k)[2] - P.get(k - 1)[2] < -SUBIDA)
				quebras.add(k);
		quebras.add(P.size());
		List<float[]> out = new ArrayList<>();
		out.add(P.get(0));
		for (int s = 0; s + 1 < quebras.size(); s++) {
			int a = quebras.get(s), b = quebras.get(s + 1);
			if (a > 0)
				out.add(P.get(a));
			int i = a;
			while (i < b - 1) {
				int j = b - 1;
				while (j > i + 1 && !ve(nos.get(i), nos.get(j), seguePiso))
					j--;
				out.add(P.get(j));
				i = j;
			}
		}
		return out;
	}

	/** Altura do piso livre da célula de (x, y) mais perto de z; NaN se a célula não tem piso livre (parede, obstáculo). */
	public float alturaPiso(float x, float y, float z) {
		float melhor = Float.NaN, dz = Float.MAX_VALUE;
		for (Piso p : m.pisos((int) (x / 0.5f), (int) (y / 0.5f)))
			if (p.livre() && Math.abs(p.z() - z) < dz) {
				dz = Math.abs(p.z() - z);
				melhor = p.z();
			}
		return melhor;
	}

	/** Dá para andar em linha reta de (x1,y1,z1) até (x2,y2,z2) pelas ligações da grade, sem queda. */
	public boolean retaAndavel(float x1, float y1, float z1, float x2, float y2, float z2) {
		long a = noEm(x1, y1, z1), b = noEm(x2, y2, z2);
		return a != 0 && b != 0 && (a == b || ve(a, b, false));   // decisão de passagem (puxão): sem o "seguir o piso", que é só visual
	}

	/** Caminho alisado de (x1,y1,z1) até (x2,y2,z2), sem o ponto de início; null se não houver. */
	public List<float[]> encontra(float x1, float y1, float z1, float x2, float y2, float z2, int limite) {
		return encontra(x1, y1, z1, x2, y2, z2, limite, Float.MAX_VALUE);
	}

	/** Idem, com rota de no máximo maxComprimento metros (mais longa = inalcançável). */
	public List<float[]> encontra(float x1, float y1, float z1, float x2, float y2, float z2, int limite, float maxComprimento) {
		long a = noEm(x1, y1, z1), b = noEm(x2, y2, z2);
		if (a == 0 || b == 0)
			return null;
		List<Long> c = caminho(a, b, limite, maxComprimento);
		if (c == null)
			return null;
		List<float[]> r = alisa(c);
		r.remove(0);
		return r;
	}
}
