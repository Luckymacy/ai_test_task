import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState({
    income: 0,
    expenses: 0,
    balance: 0,
  });

  useEffect(() => {
    fetch("http://127.0.0.1:8001/api/transactions")
      .then((response) => response.json())
      .then((data) => setTransactions(data))
      .catch((error) => console.error("Transactions error:", error));

    fetch("http://127.0.0.1:8001/api/summary")
      .then((response) => response.json())
      .then((data) => setSummary(data))
      .catch((error) => console.error("Summary error:", error));
  }, []);

  return (
    <div className="dashboard">
      <h1>Dress Rental Planner</h1>
      <p className="subtitle">Фінансова панель студії оренди одягу</p>

      <div className="cards">
        <div className="card">
          <h3>Доходи</h3>
          <p>{Number(summary.income).toFixed(2)} грн</p>
        </div>

        <div className="card">
          <h3>Витрати</h3>
          <p>{Number(summary.expenses).toFixed(2)} грн</p>
        </div>

        <div className="card">
          <h3>Баланс</h3>
          <p>{Number(summary.balance).toFixed(2)} грн</p>
        </div>
      </div>

      <h2>Фінансові операції</h2>

      <table>
        <thead>
          <tr>
            <th>Дата</th>
            <th>Клієнт</th>
            <th>Тип</th>
            <th>Сума</th>
            <th>Категорія</th>
            <th>Опис</th>
          </tr>
        </thead>

        <tbody>
          {transactions.map((transaction) => (
            <tr key={transaction.id}>
              <td>{transaction.date}</td>
              <td>{transaction.client_name || "-"}</td>
              <td>{transaction.type}</td>
              <td>{Number(transaction.amount).toFixed(2)} грн</td>
              <td>{transaction.category}</td>
              <td>{transaction.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;