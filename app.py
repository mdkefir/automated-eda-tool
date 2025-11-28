import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from eda_core import EDAProcessor  # Импортируем наш модуль

# --- Настройки страницы ---
st.set_page_config(
    page_title="EDA Master",
    page_icon="📊",
    layout="wide"
)

# --- Заголовок ---
st.title("🛠️ Программный модуль для автоматизации EDA")
st.markdown("---")

# --- Боковая панель (Загрузка) ---
with st.sidebar:
    st.header("1. Загрузка данных")
    uploaded_file = st.file_uploader("Выберите CSV или Excel файл", type=["csv", "xlsx"])
    
    st.info("Загрузите файл, чтобы начать анализ.")

# --- Основная логика ---
if uploaded_file is not None:
    # Инициализируем наш класс-обработчик
    processor = EDAProcessor(uploaded_file, uploaded_file.name)
    df = processor.df

    if df.empty:
        # Проверяем, записал ли наш процессор конкретную ошибку
        if hasattr(processor, 'last_error') and processor.last_error:
            st.error(f"❌ Ошибка загрузки: {processor.last_error}")
            st.warning("Совет: Проверьте, что файл не поврежден. Попробуйте пересохранить его в формате CSV (UTF-8) или Excel.")
        else:
            st.error("Файл пуст или имеет неверную структуру.")
    else:
        # ... (дальше идет код создания вкладок tab1, tab2, tab3 как было раньше)
        # Создаем вкладки для удобства (как в ТЗ: Обзор, Статистика, Визуализация)
        tab1, tab2, tab3 = st.tabs(["📋 Обзор данных", "📈 Статистика", "🎨 Визуализация"])

        # === ВКЛАДКА 1: ОБЗОР ===
        with tab1:
            st.subheader("Общая информация")
            col1, col2, col3 = st.columns(3)
            rows, cols = processor.get_shape()
            
            col1.metric("Строки", rows)
            col2.metric("Столбцы", cols)
            col3.metric("Дубликаты", processor.get_duplicates())

            st.write("### Первые 5 строк данных")
            st.dataframe(df.head())
            
            st.write("### Типы данных")
            st.dataframe(pd.DataFrame(df.dtypes, columns=['Тип данных']).astype(str).T)

            st.write("### Пропущенные значения")
            missing_df = processor.get_missing_values()
            if not missing_df.empty:
                st.dataframe(missing_df)
                st.warning("В данных есть пропуски! Обратите внимание.")
            else:
                st.success("Пропусков нет.")

        # === ВКЛАДКА 2: СТАТИСТИКА ===
        with tab2:
            st.subheader("Числовые признаки")
            stats = processor.get_numeric_stats()
            if stats is not None:
                st.dataframe(stats.style.background_gradient(cmap="Blues"))
            else:
                st.info("Числовых колонок не найдено.")

            st.subheader("Корреляционная матрица")
            corr = processor.get_correlation()
            if corr is not None:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
                st.pyplot(fig)
            else:
                st.info("Недостаточно данных для корреляции.")

        # === ВКЛАДКА 3: ВИЗУАЛИЗАЦИЯ ===
        with tab3:
            st.subheader("Интерактивный графопостроитель")
            
            # Выбор типа графика
            plot_type = st.selectbox("Выберите тип графика", ["Гистограмма (Распределение)", "Boxplot (Ящик с усами)", "Scatter Plot (Точечная)", "Bar Chart (Столбчатая)"])
            
            if plot_type == "Гистограмма (Распределение)":
                col_to_plot = st.selectbox("Выберите столбец", processor.numeric_cols)
                if col_to_plot:
                    fig, ax = plt.subplots()
                    sns.histplot(df[col_to_plot], kde=True, ax=ax, color="skyblue")
                    st.pyplot(fig)

            elif plot_type == "Boxplot (Ящик с усами)":
                col_to_plot = st.selectbox("Выберите числовой столбец", processor.numeric_cols)
                if col_to_plot:
                    fig, ax = plt.subplots()
                    sns.boxplot(x=df[col_to_plot], ax=ax, color="lightgreen")
                    st.pyplot(fig)

            elif plot_type == "Scatter Plot (Точечная)":
                col_x = st.selectbox("Ось X", processor.numeric_cols)
                col_y = st.selectbox("Ось Y", processor.numeric_cols, index=1 if len(processor.numeric_cols) > 1 else 0)
                if col_x and col_y:
                    fig, ax = plt.subplots()
                    sns.scatterplot(x=df[col_x], y=df[col_y], ax=ax, color="purple")
                    st.pyplot(fig)
            
            elif plot_type == "Bar Chart (Столбчатая)":
                col_cat = st.selectbox("Выберите категориальный столбец", processor.categorical_cols)
                if col_cat:
                    fig, ax = plt.subplots()
                    top_n = st.slider("Сколько категорий показать?", 5, 20, 10)
                    val_counts = df[col_cat].value_counts().head(top_n)
                    sns.barplot(x=val_counts.values, y=val_counts.index, ax=ax, palette="viridis")
                    st.pyplot(fig)

else:
    # Заставка при пустом экране
    st.markdown("""
    ### 👋 Добро пожаловать!
    Этот инструмент разработан в рамках курсовой работы.
    
    **Функционал:**
    *   Автоматический расчет статистик.
    *   Анализ пропусков и типов данных.
    *   Построение графиков для числовых и категориальных данных.
    
    ⬅️ **Загрузите файл CSV в меню слева, чтобы начать.**
    """)