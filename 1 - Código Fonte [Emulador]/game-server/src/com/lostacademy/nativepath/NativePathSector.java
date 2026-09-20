package com.lostacademy.nativepath;

/**
 * =========================================================================================
 * LOST ACADEMY — SISTEMA OFICIAL DE NAVEGAÇÃO NATIVA CRYENGINE (*-PATH.DAT)
 * =========================================================================================
 * Representação de alto desempenho de um Setor Espacial de 16m x 16m.
 *
 * Cada setor corresponde a uma célula da grade macro do CryEngine (varredura Y/X em passos de 16m)
 * e subdivide-se internamente em uma matriz de 32x32 subcélulas de resolução 0.5m x 0.5m.
 *
 * Um setor pode conter múltiplas camadas verticais (terreno natural, pontes, passarelas, túneis,
 * pisos de castelos, navios, telhados), cada uma possuindo suas próprias regras de colisão e
 * mapa de elevação com precisão milimétrica.
 *
 * @author KAMIDAKI & Equipe Lost Academy
 */
public final class NativePathSector {

	/**
	 * Representa uma camada vertical específica dentro de um setor de 16m x 16m.
	 */
	public static final class Layer {
		/**
		 * Tipo canônico da camada no formato CryEngine (0 a 16):
		 * - 0, 1: Base de elevação plana (pontes planas, pisos rígidos).
		 * - 2, 3: Terreno natural puro (herda cota do terreno).
		 * - 4, 5: Grade de elevação 32x32 (32-bit float/int).
		 * - 6, 7: Bitmap de bloqueio de 128 bytes (1024 bits = 32x32 subcélulas de 0.5m).
		 * - 8, 9: Rampa/escada com paleta de 2 bits por subcélula.
		 * - 10, 11: Malha de elevação compacta de 4 bits (nibbles) por subcélula.
		 * - 12, 13: Cota base + offsets de elevação em centímetros (1 byte por subcélula).
		 * - 14, 15: Cota base + elevação de alta precisão em centímetros (2 bytes short por subcélula).
		 * - 16: Índice espacial de conectividade/links CryEngine.
		 */
		private final byte type;

		/**
		 * Cota vertical base em metros (baseElev / 100.0f).
		 * Representa a altitude média do piso ou suporte estrutural da camada.
		 */
		private final float baseElev;

		/**
		 * Mapa de bits de bloqueio (16 inteiros long de 64 bits = 1024 bits = 32x32 subcélulas).
		 * Convenção CryEngine:
		 * - Bit 1: Obstáculo físico intransitável (parede, guarda-corpo, pilar, decoração sólida).
		 * - Bit 0: Transitável / solo livre para caminhada.
		 * Se for nulo, a camada é 100% transitável por padrão (ex: terreno natural tipos 2/3 ou base 0/1).
		 */
		private final long[] blockedBits;

		/**
		 * Matriz opcional de elevação detalhada por subcélula (tamanho 1024 = 32x32).
		 * Armazenada em centímetros relativos ou absolutos para reduzir o consumo de memória RAM.
		 */
		private final short[] subElevs;

		/**
		 * Construtor completo da camada com matrizes compactas de bits e elevação.
		 *
		 * @param type        Tipo da camada conforme especificação do CryEngine (0..16).
		 * @param baseElev    Elevação base em metros (ou Float.NaN se indefinida).
		 * @param blockedBits Vetor com os 1024 bits de colisão (ou null se 100% transitável).
		 * @param subElevs    Vetor de 1024 elevações em centímetros (ou null se plana).
		 */
		public Layer(byte type, float baseElev, long[] blockedBits, short[] subElevs) {
			this.type = type;
			this.baseElev = baseElev;
			this.blockedBits = blockedBits;
			this.subElevs = subElevs;
		}

		/**
		 * Retorna o tipo canônico da camada (0..16).
		 */
		public byte getType() {
			return type;
		}

		/**
		 * Retorna a elevação base da camada em metros.
		 */
		public float getBaseElev() {
			return baseElev;
		}

		/**
		 * Indica se a camada possui uma cota base explícita decodificada do arquivo binário.
		 */
		public boolean hasExplicitBase() {
			return !Float.isNaN(baseElev);
		}

		/**
		 * Verifica em tempo constante O(1) se a subcélula específica (0..31, 0..31) é transitável.
		 *
		 * Decodificação binária oficial CryEngine (Desassemblagem 0x100E2DCC):
		 * - Cada linha contém 32 subcélulas = 4 bytes.
		 * - Índice do bit = (subY * 32) + subX.
		 * - Localização no array de 16 longs: longIdx = bitIdx >>> 6; máscara = 1L << (bitIdx & 63).
		 * - Retorna true se o bit for 0 (livre); false se o bit for 1 (bloqueado por obstáculo).
		 *
		 * @param subX Índice horizontal da subcélula (0 a 31).
		 * @param subY Índice vertical da subcélula (0 a 31).
		 * @return true se o agente puder pisar e caminhar sobre esta subcélula; false caso contrário.
		 */
		public boolean isWalkable(int subX, int subY) {
			if (blockedBits == null) {
				return true;
			}
			int bitIdx = (subY << 5) | subX; // subY * 32 + subX (0..1023)
			int longIdx = bitIdx >>> 6;      // bitIdx / 64
			long mask = 1L << (bitIdx & 63);
			return (blockedBits[longIdx] & mask) == 0;
		}

		/**
		 * Calcula a altitude vertical exata (Z) da superfície navegável na subcélula informada.
		 *
		 * Regras de derivação de altitude:
		 * 1. Se houver tabela de elevação subcelular em centímetros (subElevs), calcula cota precisa.
		 * 2. Se houver elevação base explícita (baseElev), utiliza a cota do piso rígido da camada.
		 * 3. Se for camada de terreno natural (tipos 2/3), retorna a cota de terreno fornecida.
		 *
		 * @param subX     Índice horizontal da subcélula (0 a 31).
		 * @param subY     Índice vertical da subcélula (0 a 31).
		 * @param terrainZ Altitude do terreno obtida da GeoEngine como referência.
		 * @return Altitude Z em metros da superfície desta camada.
		 */
		public float getZ(int subX, int subY, float terrainZ) {
			if (subElevs != null) {
				int idx = (subY << 5) | subX;
				short e = subElevs[idx];
				// Sentinel values da CryEngine:
				// - 0xFFFE / -2: célula sem alteração (usa terreno natural)
				// - 0xFFFF / -1: célula bloqueada / inválida
				if (e != -2 && e != -1 && Math.abs(e) < 32000) {
					if (!Float.isNaN(baseElev)) {
						return baseElev + (e / 100.0f);
					}
					return e / 100.0f;
				}
			}
			if (!Float.isNaN(baseElev)) {
				return baseElev;
			}
			return terrainZ;
		}
	}

	/**
	 * Coordenada horizontal X do canto inferior esquerdo do setor em metros (múltiplo de 16).
	 */
	private final short gridX;

	/**
	 * Coordenada vertical Y do canto inferior esquerdo do setor em metros (múltiplo de 16).
	 */
	private final short gridY;

	/**
	 * Camadas verticais presentes neste setor de 16m x 16m.
	 */
	private final Layer[] layers;

	/**
	 * Construtor imutável do setor espacial.
	 *
	 * @param gridX  Coordenada X em metros (múltiplo de 16).
	 * @param gridY  Coordenada Y em metros (múltiplo de 16).
	 * @param layers Array de camadas verticais presentes no setor.
	 */
	public NativePathSector(short gridX, short gridY, Layer[] layers) {
		this.gridX = gridX;
		this.gridY = gridY;
		this.layers = layers != null ? layers : new Layer[0];
	}

	public short getGridX() {
		return gridX;
	}

	public short getGridY() {
		return gridY;
	}

	public Layer[] getLayers() {
		return layers;
	}

	public int getLayerCount() {
		return layers.length;
	}

	/**
	 * Localiza a camada vertical ideal para um agente posicionado na altitude Z informada.
	 *
	 * Algoritmo de Seleção Oficial CryEngine:
	 * 1. Prioriza camadas cujo piso esteja imediatamente abaixo ou muito próximo aos pés do agente.
	 * 2. Evita selecionar tetos, pisos superiores ou pontes elevadas que estejam bem acima do agente.
	 * 3. Entre as camadas dentro do limite vertical permitido (maxZDiff), seleciona a de menor diferença.
	 *
	 * @param subX     Índice horizontal da subcélula (0 a 31).
	 * @param subY     Índice vertical da subcélula (0 a 31).
	 * @param z        Altitude Z atual do agente em metros.
	 * @param terrainZ Cota de terreno calculada pela GeoEngine.
	 * @param maxZDiff Tolerância máxima de busca vertical (em metros).
	 * @return A camada mais adequada ou null se nenhuma estiver ao alcance vertical.
	 */
	public Layer findBestLayer(int subX, int subY, float z, float terrainZ, float maxZDiff) {
		if (layers.length == 0) {
			return null;
		}
		if (layers.length == 1) {
			Layer l = layers[0];
			if (l.getType() == 16) {
				return null;
			}
			float lz = l.getZ(subX, subY, terrainZ);
			if (Math.abs(lz - z) <= maxZDiff) {
				return l;
			}
			return null;
		}

		Layer best = null;
		float bestDiff = Float.MAX_VALUE;

		for (Layer l : layers) {
			if (l.getType() == 16) {
				continue;
			}
			float lz = l.getZ(subX, subY, terrainZ);
			float diff = Math.abs(lz - z);

			// Favorece superfícies abaixo dos pés do agente (piso) em vez de acima (teto).
			// Camadas acima do agente têm custo 3× maior para evitar selecionar teto
			// em mapas de múltiplos pisos sobrepostos (castelos, fortalezas, dungeons).
			if (lz > z) {
				diff *= 3.0f;
			}

			if (diff <= maxZDiff && diff < bestDiff) {
				bestDiff = diff;
				best = l;
			}
		}
		return best;
	}
}
