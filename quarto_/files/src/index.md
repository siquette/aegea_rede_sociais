---
title: Inteligência de Mídia
toc: false
style: |
  body { max-width: 960px; margin: 0 auto; font-family: 'Inter', system-ui, sans-serif; }
  h1 { font-size: 2.4rem; font-weight: 800; color: #1a202c; border-bottom: 4px solid #3498db; padding-bottom: 0.5rem; }
  h2 { font-size: 1.6rem; font-weight: 700; color: #2c3e50; margin-top: 3rem; }
  .hero { background: linear-gradient(135deg, #1a202c 0%, #2c3e50 100%); color: white; padding: 3rem 2rem; border-radius: 16px; margin: 2rem 0; }
  .hero h1 { color: white; border-bottom-color: #2ecc71; font-size: 2rem; }
  .hero p { color: #bdc3c7; line-height: 1.7; }
  .insight-box { background: #ebf5fb; border-left: 4px solid #3498db; padding: 1rem 1.5rem; border-radius: 0 8px 8px 0; margin: 1.5rem 0; }
  .kpi-row { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1.5rem 0; }
  .kpi { flex: 1; min-width: 140px; background: #f8f9fa; border-radius: 12px; padding: 1.2rem; text-align: center; border-left: 4px solid #3498db; }
  .kpi .value { font-size: 2rem; font-weight: 700; color: #2c3e50; }
  .kpi .label { font-size: 0.8rem; color: #6c757d; }
  .kpi.pos { border-left-color: #2ecc71; }
  .kpi.neg { border-left-color: #e74c3c; }
---

<div class="hero">
<h1>📊 Inteligência de Mídia — Satisfação e Reputação</h1>
<p>
Este relatório transforma dados brutos de clipping de mídia em inteligência acionável.
Use os filtros para explorar diferentes recortes — cada gráfico se atualiza em tempo real.
Os textos explicam <strong>como ler</strong> cada visualização; a análise é sua.
</p>
</div>

```js
// ── Carregar dados ──────────────────────────────────────────────
const raw = await FileAttachment("data/clipping.csv").csv({typed: true});

// Parsing de data (formato brasileiro: dd/mm/yyyy ou ISO)
function parseDate(d) {
  if (!d) return null;
  if (d instanceof Date) return d;
  const s = String(d);
  // Try ISO first
  const iso = new Date(s);
  if (!isNaN(iso)) return iso;
  // Try dd/mm/yyyy
  const parts = s.split("/");
  if (parts.length === 3) return new Date(parts[2], parts[1]-1, parts[0]);
  return null;
}

const data = raw
  .map(d => ({...d, Data: parseDate(d.Data), Tier: d.Tier || "Null"}))
  .filter(d => d.Data != null)
  .sort((a,b) => a.Data - b.Data);

// Mês formatado
data.forEach(d => {
  const m = d.Data.getMonth()+1;
  const y = d.Data.getFullYear();
  d.Ano_Mes = `${y}-${String(m).padStart(2,"0")}`;
});

// Pesos
const tierWeights = {"Muito Relevante":8, "Relevante":4, "Menos Relevante":1, "Null":1};
data.forEach(d => d.Peso = tierWeights[d.Tier] || 1);
```

```js
// ── Filtros interativos ─────────────────────────────────────────
const grupos = ["Todos", ...new Set(data.map(d=>d.Grupo).filter(Boolean).sort())];
const midias = ["Todos", ...new Set(data.map(d=>d.Mídia).filter(Boolean).sort())];
const categorias = ["Todos", ...new Set(data.map(d=>d.Categoria).filter(Boolean).sort())];
const tiers = ["Todos", ...["Muito Relevante","Relevante","Menos Relevante","Null"]];

const selGrupo = view(Inputs.select(grupos, {label: "Grupo", value: "Todos"}));
const selMidia = view(Inputs.select(midias, {label: "Mídia", value: "Todos"}));
const selTier = view(Inputs.select(tiers, {label: "Tier", value: "Todos"}));
const selCat = view(Inputs.select(categorias, {label: "Categoria", value: "Todos"}));
const minVol = view(Inputs.range([1, 50], {label: "Volume mínimo (veículos)", step: 1, value: 5}));
```

```js
// ── Filtrar dados ───────────────────────────────────────────────
const filtered = data.filter(d => {
  if (selGrupo !== "Todos" && d.Grupo !== selGrupo) return false;
  if (selMidia !== "Todos" && d.Mídia !== selMidia) return false;
  if (selTier !== "Todos" && d.Tier !== selTier) return false;
  if (selCat !== "Todos" && d.Categoria !== selCat) return false;
  return true;
});

const sent = filtered.filter(d => d.Classificação !== "PUBLICIDADE");

// NSS functions
function calcNSS(arr) {
  if (arr.length === 0) return 0;
  const pos = arr.filter(d => d.Classificação === "POSITIVA").length;
  const neg = arr.filter(d => d.Classificação === "NEGATIVA").length;
  return ((pos - neg) / arr.length * 100);
}

function calcNSSw(arr) {
  if (arr.length === 0) return 0;
  const wPos = arr.filter(d=>d.Classificação==="POSITIVA").reduce((s,d)=>s+d.Peso,0);
  const wNeg = arr.filter(d=>d.Classificação==="NEGATIVA").reduce((s,d)=>s+d.Peso,0);
  const wTot = arr.reduce((s,d)=>s+d.Peso,0);
  return ((wPos - wNeg) / wTot * 100);
}

const nssVal = calcNSS(sent);
const nsswVal = calcNSSw(sent);
```

<div class="kpi-row">
  <div class="kpi ${nssVal >= 0 ? 'pos' : 'neg'}">
    <div class="value">${nssVal >= 0 ? '+' : ''}${nssVal.toFixed(1)}</div>
    <div class="label">NSS Simples</div>
  </div>
  <div class="kpi ${nsswVal >= 0 ? 'pos' : 'neg'}">
    <div class="value">${nsswVal >= 0 ? '+' : ''}${nsswVal.toFixed(1)}</div>
    <div class="label">NSS Ponderado</div>
  </div>
  <div class="kpi">
    <div class="value">${sent.length.toLocaleString()}</div>
    <div class="label">Menções Orgânicas</div>
  </div>
  <div class="kpi">
    <div class="value">${new Set(sent.map(d=>d.Veículo_de_comunicacao)).size}</div>
    <div class="label">Veículos Únicos</div>
  </div>
</div>

## O Saldo de Imagem

O **NSS** funciona como um saldo bancário da reputação. A fórmula: `(Positivas − Negativas) / Total × 100`. Se temos 100 notícias, 70 positivas e 30 negativas, o NSS é **+40** — cada 100 menções tem 40 a mais de positivas.

O gráfico abaixo mostra quais **temas** puxam esse saldo para cima (barras verdes, à direita) ou para baixo (barras vermelhas, à esquerda). Quanto mais longa a barra, maior a contribuição daquele tema para o sentimento geral.

```js
// NSS por Categoria
{
  const catData = d3.rollups(sent, v => {
    const p = v.filter(d=>d.Classificação==="POSITIVA").length;
    const n = v.filter(d=>d.Classificação==="NEGATIVA").length;
    return {nss: (p-n)/v.length*100, n: v.length};
  }, d => d.Categoria)
  .map(([cat, {nss, n}]) => ({cat, nss: +nss.toFixed(1), n}))
  .sort((a,b) => a.nss - b.nss);

  display(Plot.plot({
    height: Math.max(300, catData.length * 28),
    marginLeft: 180,
    marginRight: 60,
    x: {label: "NSS →", grid: true},
    y: {label: null, domain: catData.map(d=>d.cat)},
    color: {range: ["#e74c3c", "#2ecc71"], domain: [-100, 100]},
    marks: [
      Plot.barX(catData, {x: "nss", y: "cat", fill: d => d.nss >= 0 ? "#2ecc71" : "#e74c3c", tip: true,
        channels: {Volume: "n"}}),
      Plot.text(catData, {x: "nss", y: "cat", text: d => `${d.nss >= 0 ? '+' : ''}${d.nss.toFixed(0)}`, 
        dx: d => d.nss >= 0 ? 5 : -5, textAnchor: d => d.nss >= 0 ? "start" : "end", fontSize: 11}),
      Plot.ruleX([0], {stroke: "#2c3e50", strokeWidth: 2}),
    ]
  }));
}
```

## O Efeito Megafone

A mídia não é democrática. Uma matéria na TV Globo atinge milhões; um blog local, dezenas. O **NSS Ponderado** multiplica cada menção pelo peso do veículo (Muito Relevante = 8×, Relevante = 4×, Menos Relevante = 1×).

**Como ler:** Se a linha vermelha (ponderada) fica **abaixo** da verde (simples), significa que os grandes veículos são mais críticos que a média. A distância entre as linhas é a medida do "efeito megafone". A linha tracejada no zero é a fronteira entre saldo positivo e negativo.

```js
// NSS temporal
{
  const meses = [...new Set(sent.map(d=>d.Ano_Mes))].sort();
  const temporal = meses.map(m => {
    const dm = sent.filter(d=>d.Ano_Mes===m);
    return {mes: m, simples: calcNSS(dm), ponderado: calcNSSw(dm), n: dm.length};
  });

  display(Plot.plot({
    height: 380,
    x: {label: "Mês", tickRotate: -45},
    y: {label: "NSS", grid: true},
    marks: [
      Plot.ruleY([0], {stroke: "#bdc3c7", strokeDasharray: "4,4"}),
      Plot.lineY(temporal, {x: "mes", y: "simples", stroke: "#2ecc71", strokeWidth: 3, tip: true,
        channels: {N: "n"}, title: d => `Simples: ${d.simples.toFixed(1)} (N=${d.n})`}),
      Plot.dot(temporal, {x: "mes", y: "simples", fill: "#2ecc71", r: 5}),
      Plot.lineY(temporal, {x: "mes", y: "ponderado", stroke: "#e74c3c", strokeWidth: 3, strokeDasharray: "8,4"}),
      Plot.dot(temporal, {x: "mes", y: "ponderado", fill: "#e74c3c", r: 5, symbol: "diamond"}),
    ]
  }));

  display(html`<div style="text-align:center;font-size:0.85rem;color:#6c757d;">
    <span style="color:#2ecc71;">●</span> NSS Simples &nbsp;&nbsp;
    <span style="color:#e74c3c;">◆</span> NSS Ponderado
  </div>`);
}
```

## Evolução Temática

O heatmap abaixo cruza **temas** (linhas) com **meses** (colunas). A cor mostra o NSS: verde = sentimento positivo, vermelho = negativo, branco = neutro.

**Como ler:** Procure **linhas horizontais persistentemente vermelhas** — são temas com crise crônica. Uma célula vermelha isolada pode ser evento pontual. Transições de vermelho para verde indicam recuperação.

```js
{
  // Top 8 categorias por volume
  const topCats = d3.rollups(sent, v => v.length, d => d.Categoria)
    .sort((a,b) => b[1] - a[1])
    .slice(0, 8)
    .map(d => d[0]);
  
  const meses = [...new Set(sent.map(d=>d.Ano_Mes))].sort();
  
  const heatData = [];
  for (const cat of topCats) {
    for (const mes of meses) {
      const sub = sent.filter(d => d.Categoria === cat && d.Ano_Mes === mes);
      const n = sub.length;
      if (n >= 3) {
        const p = sub.filter(d=>d.Classificação==="POSITIVA").length;
        const ng = sub.filter(d=>d.Classificação==="NEGATIVA").length;
        heatData.push({cat, mes, nss: +((p-ng)/n*100).toFixed(1), n});
      } else {
        heatData.push({cat, mes, nss: null, n});
      }
    }
  }

  display(Plot.plot({
    height: Math.max(300, topCats.length * 45),
    marginLeft: 180,
    padding: 0.05,
    x: {label: null, tickRotate: -45},
    y: {label: null, domain: topCats},
    color: {type: "diverging", scheme: "RdYlGn", domain: [-100, 100], legend: true, label: "NSS"},
    marks: [
      Plot.cell(heatData.filter(d => d.nss != null), {x: "mes", y: "cat", fill: "nss", tip: true,
        channels: {Volume: "n"}}),
      Plot.text(heatData.filter(d => d.nss != null), {x: "mes", y: "cat", 
        text: d => d.nss >= 0 ? `+${d.nss.toFixed(0)}` : d.nss.toFixed(0),
        fill: d => Math.abs(d.nss) > 50 ? "white" : "#1a202c", fontSize: 10}),
      Plot.cell(heatData.filter(d => d.nss == null), {x: "mes", y: "cat", fill: "#f0f0f0"}),
      Plot.text(heatData.filter(d => d.nss == null), {x: "mes", y: "cat", text: "—", fill: "#bdc3c7", fontSize: 10}),
    ]
  }));
}
```

## Radiografia dos Atores

Cada ponto é um veículo de mídia posicionado num mapa estratégico. A posição horizontal mostra o **volume** (quantas matérias publicou); a vertical mostra o **sentimento** (NSS).

**Como ler:** A linha tracejada no zero divide aliados (acima) de detratores (abaixo). O **quadrante inferior direito** é a zona de perigo — alto volume com sentimento negativo. Passe o mouse sobre os pontos para ver o nome do veículo.

```js
{
  const prof = d3.rollups(sent, v => {
    const p = v.filter(d=>d.Classificação==="POSITIVA").length;
    const n = v.filter(d=>d.Classificação==="NEGATIVA").length;
    return {total: v.length, nss: +((p-n)/v.length*100).toFixed(1), tier: d3.mode(v.map(d=>d.Tier))};
  }, d => d.Veículo_de_comunicacao)
  .map(([name, v]) => ({name, ...v}))
  .filter(d => d.total >= minVol);

  display(Plot.plot({
    height: 480,
    x: {label: "Volume (log) →", type: "log", grid: true},
    y: {label: "← NSS →", grid: true},
    color: {type: "diverging", scheme: "RdYlGn", domain: [-100, 100]},
    marks: [
      Plot.ruleY([0], {stroke: "#34495e", strokeDasharray: "4,4"}),
      Plot.dot(prof, {x: "total", y: "nss", fill: "nss", r: 7, stroke: "#2c3e50", strokeWidth: 0.5,
        tip: true, channels: {Veículo: "name", Tier: "tier"}}),
    ]
  }));
}
```

<div class="insight-box">
<strong>💡 Dica de leitura:</strong> Cada seção deste relatório responde uma pergunta diferente. Os filtros no topo afetam todos os gráficos simultaneamente — use-os para comparar grupos, mídias, categorias e tiers. O objetivo não é dar uma resposta única, mas fornecer as ferramentas para você construir a sua.
</div>
