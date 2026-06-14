import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import base64
from io import BytesIO

plt.style.use('seaborn-v0_8-whitegrid')


def get_data_info(df):
    missing = df.isnull().sum().to_dict()
    missing = {str(k): int(v) for k, v in missing.items()}
    dtypes = {str(k): str(v) for k, v in df.dtypes.to_dict().items()}
    preview = df.head(5).to_dict(orient='records')
    preview = [
        {str(k): (None if pd.isna(v) else v) for k, v in row.items()}
        for row in preview
    ]
    return {
        "columns": list(df.columns),
        "dtypes": dtypes,
        "rows": len(df),
        "missing": missing,
        "preview": preview,
    }


def get_stats(df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns

    numeric_stats = {}
    for col in numeric_cols:
        s = df[col].dropna()
        numeric_stats[str(col)] = {
            "mean": float(s.mean()) if len(s) > 0 else None,
            "median": float(s.median()) if len(s) > 0 else None,
            "std": float(s.std()) if len(s) > 0 and len(s) > 1 else None,
            "min": float(s.min()) if len(s) > 0 else None,
            "max": float(s.max()) if len(s) > 0 else None,
            "q1": float(s.quantile(0.25)) if len(s) > 0 else None,
            "q3": float(s.quantile(0.75)) if len(s) > 0 else None,
        }

    categorical_stats = {}
    for col in categorical_cols:
        s = df[col].dropna()
        value_counts = s.value_counts().head(10).to_dict()
        value_counts = {str(k): int(v) for k, v in value_counts.items()}
        categorical_stats[str(col)] = {
            "unique_values": int(s.nunique()),
            "top_values": value_counts,
            "missing": int(df[col].isnull().sum()),
        }

    correlations = {}
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                col1 = str(corr_matrix.columns[i])
                col2 = str(corr_matrix.columns[j])
                val = corr_matrix.iloc[i, j]
                if not pd.isna(val):
                    correlations[f"{col1}_{col2}"] = round(float(val), 4)

    return {
        "numeric": numeric_stats,
        "categorical": categorical_stats,
        "correlations": correlations,
    }


def get_plots(df, columns=None):
    if columns is not None:
        cols = [c for c in columns if c in df.columns]
    else:
        cols = list(df.columns)

    plots = []

    for col in cols:
        s = df[col].dropna()
        if len(s) == 0:
            continue

        fig, ax = plt.subplots(figsize=(8, 4))

        if pd.api.types.is_numeric_dtype(df[col]):
            ax.hist(
                s,
                bins=min(30, len(s.unique())),
                edgecolor='white',
                alpha=0.7,
                color='steelblue',
            )
            ax.set_xlabel(col)
            ax.set_ylabel('Frequency')
            ax.set_title(f'Distribution of {col}')

            desc = f"Distribution of {col}"
            if len(s) > 0:
                desc += f" - mean={s.mean():.2f}, median={s.median():.2f}"

            plot_type = "histogram"
        else:
            value_counts = s.value_counts().head(20)
            ax.bar(
                range(len(value_counts)),
                value_counts.values,
                color='coral',
                edgecolor='white',
                alpha=0.7,
            )
            ax.set_xticks(range(len(value_counts)))
            ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
            ax.set_xlabel(col)
            ax.set_ylabel('Frequency')
            ax.set_title(f'Frequency of categories in {col}')

            desc = f"Frequency of categories in {col}"
            plot_type = "bar"

        plt.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        plots.append({
            "column": col,
            "type": plot_type,
            "image_base64": img_base64,
            "description": desc,
        })

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) >= 2:
        fig, ax = plt.subplots(
            figsize=(max(6, len(numeric_cols)), max(5, len(numeric_cols) * 0.8))
        )
        corr_matrix = df[numeric_cols].corr()
        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt='.2f',
            cmap='coolwarm',
            ax=ax,
            square=True,
            cbar_kws={"shrink": 0.8},
        )
        ax.set_title('Correlation Matrix')
        plt.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        corr_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
    else:
        corr_base64 = None

    return plots, corr_base64
