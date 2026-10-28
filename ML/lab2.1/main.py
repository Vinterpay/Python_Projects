import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.metrics import mean_absolute_error, r2_score, mean_absolute_percentage_error

# ============================================================
# 1. Чтение данных
# ============================================================
df = pd.read_csv('lab2_1_DS.csv')
print("Первые строки данных:")
print(df.head())
print("\nСтатистика:")
print(df.describe())

# Признаки (X) и целевая переменная (y)
X = df[['age', 'experience']].values  # два признака
y = df['income'].values

# ============================================================
# 2. Разделение на обучающую и тестовую выборки (важно!)
# ============================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

print(f"\nОбучающая выборка: {len(X_train)} точек")
print(f"Тестовая выборка:  {len(X_test)} точек")

# ============================================================
# 3. Создаём и обучаем 4 модели
# ============================================================
models = {
    'Linear': LinearRegression(),
    'Ridge': Ridge(alpha=1.0),
    'Lasso': Lasso(alpha=1.0),
    'ElasticNet': ElasticNet(alpha=1.0, l1_ratio=0.5)
}

results = []
predictions = {}

print("\n" + "=" * 60)
print("ПАРАМЕТРЫ МОДЕЛЕЙ")
print("=" * 60)

for name, model in models.items():
    # Обучаем модель
    model.fit(X_train, y_train)

    # Предсказываем на тестовой выборке
    y_pred = model.predict(X_test)
    predictions[name] = y_pred

    # Считаем метрики
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred) * 100

    results.append({
        'Модель': name,
        'MAE': round(mae, 2),
        'R2': round(r2, 4),
        'MAPE%': round(mape, 2)
    })

    print(f"\n{name}:")
    print(f"  intercept (b) = {model.intercept_:.2f}")
    print(f"  коэффициенты (age, experience) = {model.coef_}")

# ============================================================
# 4. Таблица метрик
# ============================================================
results_df = pd.DataFrame(results)
print("\n" + "=" * 60)
print("ТАБЛИЦА МЕТРИК (на тестовой выборке)")
print("=" * 60)
print(results_df.to_string(index=False))

# ============================================================
# 5. График: предсказанные vs реальные значения
# ============================================================
plt.figure(figsize=(12, 7))

# Идеальная линия y = x
min_val = min(y_test.min(), min(p.min() for p in predictions.values()))
max_val = max(y_test.max(), max(p.max() for p in predictions.values()))
plt.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=1.5, label='Идеал (y = x)')

colors = {'Linear': 'blue', 'Ridge': 'green', 'Lasso': 'red', 'ElasticNet': 'orange'}
markers = {'Linear': 'o', 'Ridge': 's', 'Lasso': '^', 'ElasticNet': 'D'}

for name, y_pred in predictions.items():
    plt.scatter(y_test, y_pred, color=colors[name], s=70, alpha=0.75,
                label=name, marker=markers[name])

plt.xlabel('Реальный доход (income)', fontsize=12)
plt.ylabel('Предсказанный доход', fontsize=12)
plt.title('Сравнение моделей линейной регрессии\n(точки ближе к пунктиру = лучше)', fontsize=14)
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


# 6. Вывод

best_idx = results_df['R2'].idxmax()
best = results_df.loc[best_idx]

print("\n" + "=" * 60)
print("ВЫВОД")
print("=" * 60)
print(f"Лучшая модель по R²: {best['Модель']}")
print(f"  R²   = {best['R2']}")
print(f"  MAE  = {best['MAE']}")
print(f"  MAPE = {best['MAPE%']}%")
print("""
Обоснование:
- Смотрим на метрики именно на ТЕСТОВОЙ выборке.
- Чем выше R² и ниже MAE/MAPE — тем лучше модель.
- Регуляризация (Ridge/Lasso/ElasticNet) помогает, когда данных мало
  или есть риск переобучения. В данном случае сравниваем результаты.
""")