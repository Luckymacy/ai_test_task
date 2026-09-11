import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8001";

function App() {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState({
    income: 0,
    expenses: 0,
    balance: 0,
  });

  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    type: "income",
    amount: "",
    category: "",
    description: "",
  });

  const loadData = async () => {
    setLoading(true);
    setError("");

    try {
      const transactionsResponse = await fetch(
        `${API_URL}/api/transactions?transaction_type=${filter}`
      );

      if (!transactionsResponse.ok) {
        throw new Error("Не вдалося завантажити операції");
      }

      const transactionsData = await transactionsResponse.json();

      const summaryResponse = await fetch(`${API_URL}/api/summary`);

      if (!summaryResponse.ok) {
        throw new Error("Не вдалося завантажити підсумок");
      }

      const summaryData = await summaryResponse.json();

      setTransactions(transactionsData);
      setSummary(summaryData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filter]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!form.amount || Number(form.amount) <= 0) {
      setError("Сума повинна бути більшою за 0");
      return;
    }

    if (!form.category.trim() || !form.description.trim()) {
      setError("Заповни категорію та опис");
      return;
    }

    try {
      setError("");

      const response = await fetch(`${API_URL}/api/transactions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          type: form.type,
          amount: Number(form.amount),
          category: form.category,
          description: form.description,
        }),
      });

      if (!response.ok) {
        throw new Error("Не вдалося додати операцію");
      }

      setForm({
        type: "income",
        amount: "",
        category: "",
        description: "",
      });

      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    const confirmed = window.confirm(
      "Видалити цю фінансову операцію?"
    );

    if (!confirmed) return;

    try {
      setError("");

      const response = await fetch(
        `${API_URL}/api/transactions/${id}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error("Не вдалося видалити операцію");
      }

      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <p className="brand-kicker">RENTAL STUDIO</p>

          <h1>The Muse Edit</h1>

          <p className="subtitle">
            Фінансова панель студії оренди одягу
          </p>
        </div>
      </header>

      <main className="dashboard">
        <div className="cards">
          <div className="card">
            <span className="card-label">Доходи</span>
            <p>{Number(summary.income).toFixed(2)} грн</p>
          </div>

          <div className="card">
            <span className="card-label">Витрати</span>
            <p>{Number(summary.expenses).toFixed(2)} грн</p>
          </div>

          <div className="card balance-card">
            <span className="card-label">Баланс</span>
            <p>{Number(summary.balance).toFixed(2)} грн</p>
          </div>
        </div>

        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="section-kicker">NEW ENTRY</p>
              <h2>Додати фінансову операцію</h2>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="transaction-form">
            <select
              name="type"
              value={form.type}
              onChange={handleChange}
            >
              <option value="income">Дохід</option>
              <option value="expense">Витрата</option>
            </select>

            <input
              type="number"
              name="amount"
              placeholder="Сума"
              value={form.amount}
              onChange={handleChange}
              min="0.01"
              step="0.01"
            />

            <input
              type="text"
              name="category"
              placeholder="Категорія"
              value={form.category}
              onChange={handleChange}
            />

            <input
              type="text"
              name="description"
              placeholder="Опис"
              value={form.description}
              onChange={handleChange}
            />

            <button type="submit">Додати операцію</button>
          </form>
        </section>

        <section className="panel">
          <div className="operations-header">
            <div>
              <p className="section-kicker">HISTORY</p>
              <h2>Фінансові операції</h2>
            </div>

            <select
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            >
              <option value="all">Усі</option>
              <option value="income">Доходи</option>
              <option value="expense">Витрати</option>
            </select>
          </div>

          {loading && (
            <p className="state-message">
              Завантаження даних...
            </p>
          )}

          {error && (
            <p className="state-message error-message">
              {error}
            </p>
          )}

          {!loading && !error && transactions.length === 0 && (
            <p className="state-message">
              Фінансових операцій поки немає.
            </p>
          )}

          {!loading && !error && transactions.length > 0 && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Дата</th>
                    <th>Клієнт</th>
                    <th>Тип</th>
                    <th>Сума</th>
                    <th>Категорія</th>
                    <th>Опис</th>
                    <th>Дія</th>
                  </tr>
                </thead>

                <tbody>
                  {transactions.map((transaction) => (
                    <tr key={transaction.id}>
                      <td>{transaction.date}</td>
                      <td>{transaction.client_name || "-"}</td>
                      <td>
                        <span
                          className={
                            transaction.type === "income"
                              ? "type-badge income"
                              : "type-badge expense"
                          }
                        >
                          {transaction.type === "income"
                            ? "Дохід"
                            : "Витрата"}
                        </span>
                      </td>
                      <td>
                        {Number(transaction.amount).toFixed(2)} грн
                      </td>
                      <td>{transaction.category}</td>
                      <td>{transaction.description}</td>
                      <td>
                        <button
                          className="delete-button"
                          onClick={() =>
                            handleDelete(transaction.id)
                          }
                        >
                          Видалити
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;