// Mostra data e ora
function aggiornaDataEOra() {
  const oggi = new Date();
  const opzioniData = { day: '2-digit', month: 'short', year: 'numeric' };
  document.getElementById("data").textContent = oggi.toLocaleDateString('it-IT', opzioniData);

  const ore = String(oggi.getHours()).padStart(2, '0');
  const minuti = String(oggi.getMinutes()).padStart(2, '0');
  document.getElementById("ora").textContent = `${ore}:${minuti}`;
}

setInterval(aggiornaDataEOra, 1000);
aggiornaDataEOra();

// Carica le squadre da localStorage oppure parte da vuoto
const squadre = JSON.parse(localStorage.getItem("squadre") || "[]");

function salva() {
  localStorage.setItem("squadre", JSON.stringify(squadre));
}

// Funzione per convertire in numeri romani
function numeroRomano(n) {
  const numeri = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"];
  return numeri[n - 1] || n;
}

// Costruzione dinamica della tabella
function renderTabella() {
  const tabella = document.getElementById("tabella-squadre");
  tabella.innerHTML = "";

  for (let i = 0; i < squadre.length; i++) {
    const riga = document.createElement("div");
    riga.classList.add("riga");

    const colNumero = document.createElement("div");
    colNumero.classList.add("cella", "numero");
    colNumero.textContent = numeroRomano(i + 1);

    const colSquadra = document.createElement("div");
    colSquadra.classList.add("cella", "squadra");
    colSquadra.textContent = squadre[i].join(", ");

    const colAzioni = document.createElement("div");
    colAzioni.classList.add("cella", "azioni");
    colAzioni.innerHTML = `
      <button onclick="duplica(${i})">🔁</button>
      <button onclick="rimuovi(${i})">🗑️</button>
    `;

    riga.appendChild(colNumero);
    riga.appendChild(colSquadra);
    riga.appendChild(colAzioni);
    tabella.appendChild(riga);
  }

  document.getElementById("conteggio").textContent = squadre.length;
}

// Aggiunta nuova squadra
document.querySelector(".btn-aggiungi").addEventListener("click", () => {
  const input = document.getElementById("giocatori");
  const erroreDiv = document.getElementById("errore");
  const giocatori = input.value.split(",").map(g => g.trim()).filter(g => g);

  if (giocatori.length < 3 || giocatori.length > 5) {
    erroreDiv.textContent = "⚠️ Una squadra deve avere da 3 a 5 giocatori.";
    return;
  }

  erroreDiv.textContent = "";

  fetch("/aggiungi", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ squadra: giocatori })
  })
  .then(() => {
    input.value = "";
    caricaDati(); // aggiorna la tabella
  });
});

function caricaDati() {
  fetch("/dati")
    .then(res => res.json())
    .then(data => {
      squadre.length = 0;
      data.prenotazioni.forEach(s => squadre.push(s));
      renderTabella();
    });
}

// Duplica squadra
function rimuovi(index) {
  fetch("/rimuovi", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ index })
  }).then(() => caricaDati());
}

function duplica(index) {
  fetch("/duplica", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ index })
  }).then(() => caricaDati());
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/static/sw.js");
}

// Prima renderizzazione
caricaDati();
