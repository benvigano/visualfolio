> [!NOTE]
> While a [preview](https://demo.visualfol.io/demo-login/) is already available online for demonstration purposes, Visualfolio is in an early stage of development and is not ready for real-world use.

<br><br>

<p align="center">
  <a href="https://visualfol.io/" target="_blank" rel="noopener noreferrer">
    <img src="https://github.com/user-attachments/assets/91436dfa-7c73-4be2-8fba-8de1b9b4e864" alt="Visualfolio logo" style="width: 200px; height: auto;">
  </a>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Language-Python-3776AB" alt="Python">
  <img src="https://img.shields.io/badge/Framework-Django-092E20" alt="Django">
  <img src="https://img.shields.io/badge/Visualization-Plotly-3F4F75" alt="Plotly">
  <img src="https://img.shields.io/badge/Styling-Tailwind%20CSS-06B6D4" alt="Tailwind CSS">
</p>

---

<p align="center">
  Visualfolio is a highly-visual, <strong>open source, personal finance dashboard</strong> that gives the user a full view of all their holdings, transactions, and trades across bank accounts, investment platforms, and digital wallets.
</p>
<br><br>

## Pages

### Streamgraph
The Home page Streamgraph is a specialized visualization designed to display total asset value over time, **visually isolating fluctuations due to earnings/expenses** from **fluctuations due to changes in asset value.**

<p align="center">
    <img src="https://github.com/user-attachments/assets/9418f0e2-85d4-4601-a480-def221e0c183" alt="Home page screen capture" style="width: 900px; height: auto;">
</p>

- The top boundary reflects transactions (earnings/expenses). An outgoing transaction is represented as a downward movement. An incoming transaction, instead, is represented by an upward extension of the stream. Transactions are represented as vertical movements as they happen instantaneously.
- The bottom boundary reflects investment profit or loss. The expansion here is inverted: an increase in asset value causes the stream to extend downwards, whereas a decrease in asset value makes the lower boundary move upwards, thus shrinking the stream.
- As a result, the thickness of the stream reflects the total asset value at all times.
<br><br>
**Notice:** Stack division is available only if the user does not use non-fiat currency assets for transactions (trades instead are supported by the visualization). If the user has performed transactions using assets of other classes, the streamgraph is displayed as a single area.

### Assets
Visualfolio aims to provide a unified view of all the user's assets across all their accounts by seamlessly aggregating data from multiple sources.
<p align="center">
    <img src="https://github.com/user-attachments/assets/b7c0ed5c-57fd-42c2-9ffa-899349c383e3" alt="Assets page screen capture" style="width: 900px; height: auto;">
</p>

### Sources of earning
<p align="center">
    <img src="https://github.com/user-attachments/assets/4050fc33-b15a-4f51-afe0-5ee923a073b4" alt="Earnings page screen capture" style="width: 900px; height: auto;">
</p>

## ER diagram
![Mermaid](https://img.shields.io/badge/diagrammer-Mermaid-pink?logo=mermaid&logoColor=white)
<p align="center">
    <img src="https://github.com/user-attachments/assets/5c83f579-0631-4deb-8648-9ddc9415040b" alt="ER Diagram" style="width: 700px; height: auto;">
</p>

## Roadmap
- Bank data API integration ([GoCardless](https://gocardless.com/bank-account-data/), [Salt Edge](https://www.saltedge.com/))
- Manual account setup for accounts not supported by the bank data API (single or batch-upload for transactions)
- Create logomark (add to logotype and as favicon)
