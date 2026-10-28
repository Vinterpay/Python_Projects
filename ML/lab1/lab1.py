import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# 1. Чтение данных

# Можно менять имя файла и названия столбцов — программа универсальна
df = pd.read_csv('lab1_DS.csv')  # <-- путь к твоему файлу

print("Первые 5 строк данных:")
print(df.head())
print("\nНазвания столбцов:", df.columns.tolist())


# Выбор столбцов X и Y (программа позволяет выбирать любой столбец)

# В данном файле: YearsExperience → X, Salary → Y
x_col = 'YearsExperience'  # <-- сюда можно поставить другой столбец
y_col = 'Salary'  # <-- сюда можно поставить другой столбец

X = df[x_col].values.astype(float)
Y = df[y_col].values.astype(float)


# 2. Статистическая информация

print("\n" + "=" * 50)
print("СТАТИСТИКА ПО ДАННЫМ")
print("=" * 50)
print(f"Количество точек: {len(X)}")
print(f"\n{x_col}:")
print(f"  min = {X.min():.2f}")
print(f"  max = {X.max():.2f}")
print(f"  среднее = {X.mean():.2f}")
print(f"\n{y_col}:")
print(f"  min = {Y.min():.2f}")
print(f"  max = {Y.max():.2f}")
print(f"  среднее = {Y.mean():.2f}")


# 3. График исходных точек

plt.figure(figsize=(10, 6))
plt.scatter(X, Y, color='blue', s=50, label='Исходные данные')
plt.xlabel(x_col)
plt.ylabel(y_col)
plt.title('Исходные данные')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()  # Первый график (п.4 задания)


# 4. Метод наименьших квадратов (формулы)
# Формулы:
# a = (n * Σ(xy) - Σx * Σy) / (n * Σ(x²) - (Σx)²)
# b = (Σy - a * Σx) / n
# Прямая: y = a*x + b

n = len(X)
sum_x = np.sum(X)
sum_y = np.sum(Y)
sum_xy = np.sum(X * Y)
sum_x2 = np.sum(X ** 2)

a = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
b = (sum_y - a * sum_x) / n

print("\n" + "=" * 50)
print("ПАРАМЕТРЫ РЕГРЕССИОННОЙ ПРЯМОЙ")
print("=" * 50)
print(f"Наклон (a) = {a:.4f}")
print(f"Свободный член (b) = {b:.4f}")
print(f"Уравнение: y = {a:.4f} * x + {b:.4f}")


# 5. График с регрессионной прямой


x_line = np.linspace(X.min(), X.max(), 100)
y_line = a * x_line + b

plt.figure(figsize=(10, 6))
plt.scatter(X, Y, color='blue', s=50, label='Исходные данные')
plt.plot(x_line, y_line, color='red', linewidth=2, label=f'Регрессия: y = {a:.2f}x + {b:.2f}')
plt.xlabel(x_col)
plt.ylabel(y_col)
plt.title('Линейная регрессия (метод наименьших квадратов)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()  # Второй график (п.6 задания)


# 6. График с квадратами ошибок (закрашенными)

plt.figure(figsize=(10, 6))
plt.scatter(X, Y, color='blue', s=50, label='Исходные данные', zorder=5)
plt.plot(x_line, y_line, color='red', linewidth=2, label='Регрессионная прямая', zorder=4)

# Рисуем квадраты ошибок
for i in range(len(X)):
    y_pred = a * X[i] + b
    # Вертикальная линия ошибки
    plt.plot([X[i], X[i]], [Y[i], y_pred], color='gray', linestyle='--', alpha=0.6, zorder=2)

    # Квадрат ошибки (закрашенный)
    error = Y[i] - y_pred
    # Чтобы квадрат был виден, берём сторону = |error|
    side = abs(error)
    # Рисуем квадрат слева или справа от точки в зависимости от знака
    if error >= 0:
        # Ошибка вверх — квадрат вверх
        rect = plt.Rectangle((X[i] - side / 2, y_pred), side, side,
                             fill=True, color='orange', alpha=0.3, zorder=1)
    else:
        # Ошибка вниз — квадрат вниз
        rect = plt.Rectangle((X[i] - side / 2, Y[i]), side, side,
                             fill=True, color='orange', alpha=0.3, zorder=1)
    plt.gca().add_patch(rect)

plt.xlabel(x_col)
plt.ylabel(y_col)
plt.title('Квадраты ошибок (метод наименьших квадратов)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()  # Третий график (п.7 задания)

print("\nВсе три графика показаны. Работа завершена.")