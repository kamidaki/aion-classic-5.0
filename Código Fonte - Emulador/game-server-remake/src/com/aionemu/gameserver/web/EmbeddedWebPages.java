package com.aionemu.gameserver.web;

/**
 * Contém o HTML/CSS/JavaScript responsivo e moderno embutido para o Black Cloud Marketplace e Aion Today.
 */
public class EmbeddedWebPages {

	public static String getShopHtml() {
		return """
			<!DOCTYPE html>
			<html lang="pt-BR">
			<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<title>Black Cloud Marketplace - Aion Classic 5.0</title>
				<link rel="preconnect" href="https://fonts.googleapis.com">
				<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
				<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Cinzel:wght@600;700&display=swap" rel="stylesheet">
				<style>
					:root {
						--bg-base: #0a0d14;
						--bg-surface: rgba(18, 24, 38, 0.75);
						--bg-card: rgba(26, 34, 52, 0.6);
						--gold: #d4af37;
						--gold-light: #f3e5ab;
						--gold-gradient: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
						--accent-cyan: #00d2ff;
						--accent-purple: #9d4edd;
						--text-main: #f0f4fc;
						--text-muted: #8c9bb3;
						--border-subtle: rgba(212, 175, 55, 0.25);
						--border-glow: rgba(0, 210, 255, 0.4);
					}
					* { margin: 0; padding: 0; box-sizing: border-box; }
					body {
						font-family: 'Outfit', sans-serif;
						background: radial-gradient(circle at 50% 0%, #151d30 0%, var(--bg-base) 75%);
						color: var(--text-main);
						min-height: 100vh;
						overflow-x: hidden;
						padding-bottom: 60px;
					}
					header {
						position: sticky; top: 0; z-index: 100;
						background: rgba(10, 13, 20, 0.85);
						backdrop-filter: blur(20px);
						border-bottom: 1px solid var(--border-subtle);
						padding: 16px 36px;
						display: flex; justify-content: space-between; align-items: center;
					}
					.brand { display: flex; align-items: center; gap: 14px; }
					.brand-logo {
						width: 42px; height: 42px;
						background: linear-gradient(135deg, #d4af37, #aa771c);
						border-radius: 10px; display: grid; place-items: center;
						font-family: 'Cinzel', serif; font-size: 24px; font-weight: 700; color: #0a0d14;
						box-shadow: 0 0 20px rgba(212, 175, 55, 0.4);
					}
					.brand-title {
						font-family: 'Cinzel', serif; font-size: 20px; font-weight: 700;
						background: linear-gradient(90deg, #fff, var(--gold-light));
						-webkit-background-clip: text; -webkit-text-fill-color: transparent;
						letter-spacing: 1px;
					}
					.balance-bar {
						display: flex; gap: 20px; align-items: center;
						background: var(--bg-card); padding: 8px 18px; border-radius: 30px;
						border: 1px solid rgba(255,255,255,0.08);
					}
					.balance-item { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; }
					.balance-val { color: var(--gold-light); font-weight: 700; }

					.nav-bar {
						max-width: 1200px; margin: 24px auto 0; padding: 0 24px;
						display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;
					}
					.categories { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 6px; }
					.cat-btn {
						background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
						color: var(--text-muted); padding: 8px 20px; border-radius: 20px;
						font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
					}
					.cat-btn:hover, .cat-btn.active {
						background: linear-gradient(135deg, rgba(212,175,55,0.2), rgba(0,210,255,0.15));
						border-color: var(--gold); color: #fff;
						box-shadow: 0 4px 15px rgba(212,175,55,0.25);
					}
					.search-box {
						background: var(--bg-card); border: 1px solid rgba(255,255,255,0.1);
						padding: 8px 16px; border-radius: 20px; color: #fff; font-size: 14px; width: 220px;
						outline: none; transition: 0.3s;
					}
					.search-box:focus { border-color: var(--gold); width: 280px; box-shadow: 0 0 12px rgba(212,175,55,0.3); }

					.catalog {
						max-width: 1200px; margin: 32px auto; padding: 0 24px;
						display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 24px;
					}
					.card {
						background: var(--bg-card); border-radius: 16px; border: 1px solid var(--border-subtle);
						padding: 20px; display: flex; flex-direction: column; justify-content: space-between;
						backdrop-filter: blur(12px); transition: all 0.35s ease; position: relative; overflow: hidden;
					}
					.card::before {
						content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
						background: radial-gradient(circle, rgba(212,175,55,0.08) 0%, transparent 60%);
						opacity: 0; transition: opacity 0.4s ease; pointer-events: none;
					}
					.card:hover {
						transform: translateY(-6px);
						border-color: var(--gold); box-shadow: 0 12px 30px rgba(0,0,0,0.5), 0 0 20px rgba(212,175,55,0.2);
					}
					.card:hover::before { opacity: 1; }
					.card-badge {
						position: absolute; top: 14px; right: 14px;
						font-size: 11px; font-weight: 700; text-transform: uppercase;
						padding: 3px 10px; border-radius: 12px; letter-spacing: 0.5px;
					}
					.badge-mythic { background: rgba(255, 51, 102, 0.2); color: #ff3366; border: 1px solid #ff3366; }
					.badge-eternal { background: rgba(255, 170, 0, 0.2); color: #ffaa00; border: 1px solid #ffaa00; }
					.badge-fabled { background: rgba(0, 210, 255, 0.2); color: var(--accent-cyan); border: 1px solid var(--accent-cyan); }
					.card-icon {
						width: 72px; height: 72px; margin: 12px auto;
						background: rgba(0,0,0,0.4); border-radius: 14px;
						border: 2px solid rgba(255,255,255,0.1); display: grid; place-items: center;
						font-size: 32px; box-shadow: inset 0 0 15px rgba(0,0,0,0.8);
					}
					.card-name { font-size: 17px; font-weight: 700; margin-bottom: 6px; text-align: center; }
					.card-desc { font-size: 12.5px; color: var(--text-muted); text-align: center; margin-bottom: 18px; line-height: 1.4; }
					.card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: auto; }
					.card-price { font-size: 16px; font-weight: 800; color: var(--gold); }
					.buy-btn {
						background: linear-gradient(135deg, #d4af37, #b8860b);
						border: none; color: #0a0d14; font-weight: 700; font-size: 13px;
						padding: 8px 18px; border-radius: 18px; cursor: pointer; transition: 0.2s;
					}
					.buy-btn:hover {
						background: linear-gradient(135deg, #f3e5ab, #d4af37);
						transform: scale(1.05); box-shadow: 0 0 15px rgba(212,175,55,0.6);
					}
					.toast {
						position: fixed; bottom: 30px; right: 30px;
						background: rgba(18, 24, 38, 0.95); border: 1px solid var(--gold);
						padding: 16px 24px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.7);
						display: none; align-items: center; gap: 12px; z-index: 1000; animation: slideUp 0.3s ease;
					}
					@keyframes slideUp { from { transform: translateY(50px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
				</style>
			</head>
			<body>
				<header>
					<div class="brand">
						<div class="brand-logo">A</div>
						<div class="brand-title">BLACK CLOUD MARKETPLACE</div>
					</div>
					<div class="balance-bar">
						<div class="balance-item">🪙 <span class="balance-val" id="tollVal">2.500</span> Tolls</div>
						<div class="balance-item">💎 <span class="balance-val">100.000.000</span> Kinah</div>
						<div class="balance-item">🌙 <span class="balance-val">150</span> Luna</div>
					</div>
				</header>

				<div class="nav-bar">
					<div class="categories">
						<button class="cat-btn active" onclick="filterCat('all')">Todos</button>
						<button class="cat-btn" onclick="filterCat('wings')">Asas Lendárias</button>
						<button class="cat-btn" onclick="filterCat('mounts')">Montarias</button>
						<button class="cat-btn" onclick="filterCat('costumes')">Trajes & Cosméticos</button>
						<button class="cat-btn" onclick="filterCat('consumables')">Consumíveis</button>
					</div>
					<input type="text" class="search-box" placeholder="Buscar no catálogo..." oninput="searchItems(this.value)">
				</div>

				<div class="catalog" id="catalogGrid"></div>

				<div class="toast" id="toast">
					<span style="font-size: 20px;">✨</span>
					<div>
						<div style="font-weight: 700; color: var(--gold);" id="toastTitle">Compra Realizada!</div>
						<div style="font-size: 12px; color: var(--text-muted);" id="toastDesc">O item foi enviado para o seu inventário.</div>
					</div>
				</div>

				<script>
					const items = [
						{ id: 1, cat: 'wings', name: 'Asas da Luz Sagrada', desc: 'Asas míticas com rastro dourado e bônus de voo de +30%.', price: 950, badge: 'Mítico', badgeCls: 'badge-mythic', icon: '🪶' },
						{ id: 2, cat: 'wings', name: 'Asas de Tempestade Tiamat', desc: 'Asas esculpidas em éter sombrio com velocidade de planeio acelerada.', price: 800, badge: 'Eterno', badgeCls: 'badge-eternal', icon: '🦅' },
						{ id: 3, cat: 'mounts', name: 'Crocante Dourado Veloz', desc: 'Montaria veloz de 12.0m/s com aceleração e salto estendido.', price: 1200, badge: 'Mítico', badgeCls: 'badge-mythic', icon: '🐆' },
						{ id: 4, cat: 'mounts', name: 'Leão Astral Alado', desc: 'Montaria nobre que permite correr e planar suavemente sobre os mapas.', price: 1100, badge: 'Eterno', badgeCls: 'badge-eternal', icon: '🦁' },
						{ id: 5, cat: 'costumes', name: 'Uniforme Militar Lost Academy', desc: 'Traje de gala exclusivo com ombreiras douradas e capa bordada.', price: 650, badge: 'Fabled', badgeCls: 'badge-fabled', icon: '🥋' },
						{ id: 6, cat: 'costumes', name: 'Armadura Cerimonial de Atreia', desc: 'Vestimenta cerimonial de alta patente para Elyos e Asmodianos.', price: 600, badge: 'Fabled', badgeCls: 'badge-fabled', icon: '🛡️' },
						{ id: 7, cat: 'consumables', name: 'Poção Maior de Recuperação x100', desc: 'Restaura instantaneamente 3.500 HP e MP sem tempo de recarga elevado.', price: 80, badge: 'Fabled', badgeCls: 'badge-fabled', icon: '🧪' },
						{ id: 8, cat: 'consumables', name: 'Pergaminho de Velocidade de Corrida x50', desc: 'Aumenta a velocidade de movimento em +30% durante 15 minutos.', price: 50, badge: 'Fabled', badgeCls: 'badge-fabled', icon: '📜' }
					];

					let currentTolls = 2500;

					function renderCatalog(filtered) {
						const grid = document.getElementById('catalogGrid');
						grid.innerHTML = filtered.map(item => `
							<div class="card">
								<span class="card-badge ${item.badgeCls}">${item.badge}</span>
								<div class="card-icon">${item.icon}</div>
								<div>
									<div class="card-name">${item.name}</div>
									<div class="card-desc">${item.desc}</div>
								</div>
								<div class="card-footer">
									<div class="card-price">${item.price} Tolls</div>
									<button class="buy-btn" onclick="buyItem('${item.name}', ${item.price})">Comprar</button>
								</div>
							</div>
						`).join('');
					}

					function filterCat(cat) {
						document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
						event.target.classList.add('active');
						if (cat === 'all') renderCatalog(items);
						else renderCatalog(items.filter(i => i.cat === cat));
					}

					function searchItems(query) {
						const q = query.toLowerCase();
						renderCatalog(items.filter(i => i.name.toLowerCase().includes(q) || i.desc.toLowerCase().includes(q)));
					}

					function buyItem(name, price) {
						if (currentTolls < price) {
							showToast('Saldo Insuficiente', 'Você precisa de mais Tolls para comprar este item.');
							return;
						}
						currentTolls -= price;
						document.getElementById('tollVal').innerText = currentTolls.toLocaleString('pt-BR');
						showToast('Compra Confirmada!', `${name} foi adicionado ao seu inventário.`);
					}

					function showToast(title, desc) {
						const t = document.getElementById('toast');
						document.getElementById('toastTitle').innerText = title;
						document.getElementById('toastDesc').innerText = desc;
						t.style.display = 'flex';
						setTimeout(() => { t.style.display = 'none'; }, 3500);
					}

					renderCatalog(items);
				</script>
			</body>
			</html>
			""";
	}

	public static String getTodayHtml() {
		return """
			<!DOCTYPE html>
			<html lang="pt-BR">
			<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<title>Aion Today - Portal Oficial Classic 5.0</title>
				<link rel="preconnect" href="https://fonts.googleapis.com">
				<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
				<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Cinzel:wght@700&display=swap" rel="stylesheet">
				<style>
					:root {
						--bg: #090c12;
						--card: rgba(19, 26, 42, 0.7);
						--gold: #d4af37;
						--gold-glow: rgba(212, 175, 55, 0.3);
						--cyan: #00d2ff;
						--red: #ff3366;
						--green: #2ecc71;
						--text: #f0f4fc;
						--muted: #8b9bb4;
					}
					* { margin: 0; padding: 0; box-sizing: border-box; }
					body {
						font-family: 'Outfit', sans-serif;
						background: radial-gradient(ellipse at 50% 0%, #172338 0%, var(--bg) 80%);
						color: var(--text); padding: 32px 24px; min-height: 100vh;
					}
					.container { max-width: 1080px; margin: 0 auto; }
					.hero {
						text-align: center; margin-bottom: 36px; padding: 28px 20px;
						background: linear-gradient(180deg, rgba(212,175,55,0.08) 0%, transparent 100%);
						border-radius: 20px; border: 1px solid rgba(212,175,55,0.2);
					}
					.hero h1 {
						font-family: 'Cinzel', serif; font-size: 32px; font-weight: 700;
						background: linear-gradient(90deg, #fff, var(--gold));
						-webkit-background-clip: text; -webkit-text-fill-color: transparent;
						margin-bottom: 8px;
					}
					.hero p { color: var(--muted); font-size: 14px; }
					.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; }
					.panel {
						background: var(--card); border-radius: 16px; border: 1px solid rgba(255,255,255,0.08);
						padding: 24px; backdrop-filter: blur(16px);
					}
					.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
					.panel-title { font-size: 16px; font-weight: 700; color: var(--gold); display: flex; align-items: center; gap: 8px; }
					.siege-item {
						display: flex; justify-content: space-between; align-items: center;
						padding: 12px 14px; background: rgba(0,0,0,0.25); border-radius: 10px; margin-bottom: 10px;
						border-left: 3px solid var(--gold);
					}
					.siege-name { font-weight: 600; font-size: 14px; }
					.siege-time { font-size: 12px; color: var(--muted); }
					.status-badge {
						font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 8px;
					}
					.status-active { background: rgba(46, 204, 113, 0.2); color: var(--green); border: 1px solid var(--green); }
					.status-soon { background: rgba(241, 196, 15, 0.2); color: #f1c40f; border: 1px solid #f1c40f; }
					.event-card {
						padding: 14px; background: rgba(0,0,0,0.25); border-radius: 12px; margin-bottom: 12px;
					}
					.event-title { font-weight: 700; font-size: 14px; color: var(--cyan); margin-bottom: 4px; }
					.event-desc { font-size: 12px; color: var(--muted); line-height: 1.4; }
				</style>
			</head>
			<body>
				<div class="container">
					<div class="hero">
						<h1>AION TODAY - ATREIA EM FOCO</h1>
						<p>Cronograma diário de fortalezas, eventos ativos e destaques do Classic 5.0</p>
					</div>

					<div class="grid">
						<div class="panel">
							<div class="panel-header">
								<div class="panel-title">⚔️ CRONOGRAMA DE CERCAS (SIEGE)</div>
								<span class="status-badge status-active">AO VIVO</span>
							</div>
							<div class="siege-item">
								<div>
									<div class="siege-name">Fortaleza do Altar da Avareza (Inggison)</div>
									<div class="siege-time">Início: 20:00 • Término: 21:00</div>
								</div>
								<span class="status-badge status-active">EM DISPUTA</span>
							</div>
							<div class="siege-item">
								<div>
									<div class="siege-name">Fortaleza de Vorgaltem (Gelkmaros)</div>
									<div class="siege-time">Início: 21:30 • Término: 22:30</div>
								</div>
								<span class="status-badge status-soon">EM BREVE</span>
							</div>
							<div class="siege-item">
								<div>
									<div class="siege-name">Núcleo do Abismo (Fortaleza Divina)</div>
									<div class="siege-time">Sábado e Domingo às 22:00</div>
								</div>
								<span class="status-badge status-soon">PROGRAMADO</span>
							</div>
						</div>

						<div class="panel">
							<div class="panel-header">
								<div class="panel-title">🌟 EVENTOS DA SEMANA</div>
								<span class="status-badge status-active">ATIVO</span>
							</div>
							<div class="event-card">
								<div class="event-title">🔥 Bônus Global: 2x XP & 2x Drop Rate</div>
								<div class="event-desc">Aproveite taxas dobradas de evolução e coleta de itens épicos em todos os mapas até domingo!</div>
							</div>
							<div class="event-card">
								<div class="event-title">⚡ Desafio do Daeva Pass - Temporada Ativa</div>
								<div class="event-desc">Complete missões diárias e semanais para desbloquear recompensas lendárias e visuais de prestígio.</div>
							</div>
							<div class="event-card">
								<div class="event-title">🐉 Incursão dos Chefes Mundiais (World Bosses)</div>
								<div class="event-desc">Rakanishu e Mastarius despertam às 23:00 em zonas de disputa com recompensas exclusivas de ranking.</div>
							</div>
						</div>
					</div>
				</div>
			</body>
			</html>
			""";
	}
}
