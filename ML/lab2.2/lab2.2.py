import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_percentage_error


# 1. Чтение данных

df = pd.read_csv('lab2_2_DS.csv')
# Переименуем столбцы для удобства (в файле длинные названия)
df.columns = ['Temperature', 'Sales']
print("Первые строки данных:")
print(df.head())
print("\nСтатистика:")
print(df.describe())

X = df[['Temperature']].values
y = df['Sales'].values


# 2. Разделение на train / test

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

print(f"\nОбучающая выборка: {len(X_train)} точек")
print(f"Тестовая выборка:  {len(X_test)} точек")


# 3. Полиномиальная регрессия разных степеней
#    (степень 1 = обычная линейная регрессия)

degrees = [1, 2, 3, 4]  # минимум 3 разных степени + линейная

results = []
models = {}

print("\n" + "=" * 60)
print("РЕЗУЛЬТАТЫ ПО СТЕПЕНЯМ")
print("=" * 60)

for deg in degrees:
    # Pipeline: сначала создаём признаки x, x², x³..., потом обычная регрессия
    model = make_pipeline(
        PolynomialFeatures(degree=deg, include_bias=False),
        LinearRegression()
    )

    # Обучаем
    model.fit(X_train, y_train)

    # Предсказываем на тесте
    y_pred = model.predict(X_test)
    models[deg] = model

    # Метрики
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred) * 100

    results.append({
        'Степень': deg,
        'MSE': round(mse, 2),
        'R2': round(r2, 4),
        'MAPE%': round(mape, 2)
    })

    name = "Линейная" if deg == 1 else f"Полином степени {deg}"
    print(f"{name}: MSE={mse:.2f}, R²={r2:.4f}, MAPE={mape:.2f}%")


# 4. Таблица метрик

results_df = pd.DataFrame(results)
print("\n" + "=" * 60)
print("ТАБЛИЦА МЕТРИК (на тестовой выборке)")
print("=" * 60)
print(results_df.to_string(index=False))


# 5. График всех кривых на одном рисунке

plt.figure(figsize=(12, 7))

# Точки данных
plt.scatter(X_train, y_train, color='skyblue', s=45, label='Train', alpha=0.7, zorder=3)
plt.scatter(X_test, y_test, color='black', s=55, label='Test', marker='x', zorder=4)

# Кривые
x_range = np.linspace(X.min() - 0.3, X.max() + 0.3, 400).reshape(-1, 1)
colors = {1: 'blue', 2: 'green', 3: 'red', 4: 'orange'}
linestyles = {1: '-', 2: '-', 3: '--', 4: '-.'}

for deg in degrees:
    y_range = models[deg].predict(x_range)
    label = 'Линейная (степень 1)' if deg == 1 else f'Полином степени {deg}'
    plt.plot(x_range, y_range, color=colors[deg], linewidth=2.2,
             linestyle=linestyles[deg], label=label, zorder=2)

plt.xlabel('Temperature (°C)', fontsize=12)
plt.ylabel('Ice Cream Sales (units)', fontsize=12)
plt.title('Полиномиальная регрессия разных степеней\n(включая обычную линейную)', fontsize=14)
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
print(f"Лучшая степень по R² на тесте: {int(best['Степень'])}")
print(f"  R²   = {best['R2']}")
print(f"  MSE  = {best['MSE']}")
print(f"  MAPE = {best['MAPE%']}%")
print("""
Обоснование выбора степени:
- Смотрим метрики именно на ТЕСТОВОЙ выборке (не на train!).
- Выбираем степень с максимальным R² и минимальным MSE.
- Слишком высокая степень часто приводит к переобучению:
  модель хорошо запоминает train, но плохо работает на test.
- Для зависимости «температура → продажи мороженого» обычно
  оптимальна степень 2 или 3 (нелинейная, но не слишком гибкая).
""")