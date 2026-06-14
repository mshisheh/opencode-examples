import os
import json
import re
import pandas as pd
import numpy as np
from backend.analytics import get_stats as analytics_get_stats
from backend.analytics import get_plots as analytics_get_plots
from backend.analytics import get_data_info as analytics_get_data_info

datasets = {}

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")


def get_stats(data_id, column=None):
    if data_id not in datasets:
        return f"Dataset {data_id} not found."
    df = datasets[data_id]["df"]
    stats = analytics_get_stats(df)
    if column:
        if column in stats["numeric"]:
            s = stats["numeric"][column]
            return (
                f"Statistics for {column}: "
                f"mean={s['mean']}, median={s['median']}, std={s['std']}, "
                f"min={s['min']}, max={s['max']}, Q1={s['q1']}, Q3={s['q3']}"
            )
        elif column in stats["categorical"]:
            s = stats["categorical"][column]
            return (
                f"Statistics for {column}: "
                f"{s['unique_values']} unique values, missing={s['missing']}, "
                f"top values: {s['top_values']}"
            )
        else:
            return f"Column '{column}' not found."
    lines = ["Dataset Statistics:"]
    for col, s in stats["numeric"].items():
        lines.append(
            f"  {col}: mean={s['mean']}, median={s['median']}, "
            f"std={s['std']}, range=[{s['min']}, {s['max']}]"
        )
    for col, s in stats["categorical"].items():
        lines.append(
            f"  {col}: {s['unique_values']} unique values, missing={s['missing']}"
        )
    return "\n".join(lines)


def get_plot(data_id, column, plot_type="auto"):
    if data_id not in datasets:
        return None
    df = datasets[data_id]["df"]
    plots, _ = analytics_get_plots(df, columns=[column])
    if plots:
        return plots[0]["image_base64"]
    return None


def get_correlation(data_id, col1, col2):
    if data_id not in datasets:
        return f"Dataset {data_id} not found."
    df = datasets[data_id]["df"]
    if col1 not in df.columns or col2 not in df.columns:
        return f"Columns not found."
    if not (
        pd.api.types.is_numeric_dtype(df[col1])
        and pd.api.types.is_numeric_dtype(df[col2])
    ):
        return f"Both columns must be numeric for correlation."
    corr = df[col1].corr(df[col2])
    return f"The correlation between {col1} and {col2} is {corr:.4f}."


def query_data(data_id, question):
    if data_id not in datasets:
        return f"Dataset {data_id} not found."
    df = datasets[data_id]["df"]
    q = question.strip()

    avg_match = re.search(
        r'(?:average|mean)\s+(?:of|for|the)?\s*(\w+)', q, re.IGNORECASE
    )
    if avg_match:
        col = avg_match.group(1)
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            cond_match = re.search(
                r'when\s+(\w+)\s+is\s+[\'"]?([^\'",]+?)["\']?(?:\s+and|$|\.)',
                q,
                re.IGNORECASE,
            )
            if cond_match:
                cond_col = cond_match.group(1)
                cond_val = cond_match.group(2).strip()
                if cond_col in df.columns:
                    filtered = df[
                        df[cond_col].astype(str).str.lower() == cond_val.lower()
                    ]
                    if len(filtered) > 0:
                        val = filtered[col].mean()
                        return (
                            f"The average of {col} when {cond_col} is "
                            f"'{cond_val}' is {val:.2f}."
                        )
                    else:
                        return (
                            f"No rows found where {cond_col} is '{cond_val}'."
                        )
            val = df[col].mean()
            return f"The average of {col} is {val:.2f}."
        return f"Column '{col}' is not numeric or not found."

    median_match = re.search(
        r'median\s+(?:of|for|the)\s+(\w+)', q, re.IGNORECASE
    )
    if median_match:
        col = median_match.group(1)
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            val = df[col].median()
            return f"The median of {col} is {val:.2f}."
        return f"Column '{col}' is not numeric or not found."

    for stat_name in ['minimum', 'min', 'maximum', 'max', 'sum', 'std', 'standard deviation']:
        pattern = (
            r'(?:'
            + stat_name
            + r')\s+(?:of|for|the)\s+(\w+)'
        )
        stat_match = re.search(pattern, q, re.IGNORECASE)
        if stat_match:
            col = stat_match.group(1)
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                s = df[col]
                if stat_name in ('minimum', 'min'):
                    val = s.min()
                    return f"The minimum of {col} is {val:.2f}."
                elif stat_name in ('maximum', 'max'):
                    val = s.max()
                    return f"The maximum of {col} is {val:.2f}."
                elif stat_name == 'sum':
                    val = s.sum()
                    return f"The sum of {col} is {val:.2f}."
                elif stat_name in ('std', 'standard deviation'):
                    val = s.std()
                    return f"The standard deviation of {col} is {val:.4f}."
            return f"Column '{col}' is not numeric or not found."

    unique_match = re.search(
        r'unique\s+values?\s+(?:in|of|for)\s+(\w+)', q, re.IGNORECASE
    )
    if unique_match:
        col = unique_match.group(1)
        if col in df.columns:
            vals = df[col].dropna().unique()
            if len(vals) > 20:
                return (
                    f"Column '{col}' has {len(vals)} unique values. "
                    f"First 20: {', '.join(str(v) for v in vals[:20])}"
                )
            return (
                f"Unique values in '{col}': {', '.join(str(v) for v in vals)}"
            )
        return f"Column '{col}' not found."

    show_match = re.search(
        r'show\s+(?:me\s+)?(?:the\s+)?(?:rows?\s+)?where\s+(\w+)\s*([><=!]+)\s*([^\s,]+)',
        q,
        re.IGNORECASE,
    )
    if show_match:
        col = show_match.group(1)
        op = show_match.group(2)
        val_str = show_match.group(3)
        if col in df.columns:
            try:
                val = float(val_str) if '.' in val_str or val_str.isdigit() else val_str
            except ValueError:
                val = val_str.strip("'\"")
            try:
                if pd.api.types.is_numeric_dtype(df[col]) and isinstance(val, (int, float)):
                    if op == '>':
                        filtered = df[df[col] > val]
                    elif op == '<':
                        filtered = df[df[col] < val]
                    elif op == '>=':
                        filtered = df[df[col] >= val]
                    elif op == '<=':
                        filtered = df[df[col] <= val]
                    elif op == '==' or op == '=':
                        filtered = df[df[col] == val]
                    elif op == '!=':
                        filtered = df[df[col] != val]
                    else:
                        filtered = df
                else:
                    filtered = df[df[col].astype(str).str.lower() == str(val).lower()]
                if len(filtered) > 10:
                    return (
                        f"Found {len(filtered)} rows where {col} {op} {val}. "
                        f"First 10 rows:\n{filtered.head(10).to_string(index=False)}"
                    )
                elif len(filtered) > 0:
                    return (
                        f"Found {len(filtered)} rows where {col} {op} {val}:\n"
                        f"{filtered.to_string(index=False)}"
                    )
                else:
                    return f"No rows found where {col} {op} {val}."
            except Exception:
                pass

    count_match = re.search(
        r'how\s+many\s+(?:rows?\s+)?(?:are\s+)?(?:where|with|have)\s+(\w+)\s*([><=!]+)\s*([^\s,?]+)',
        q,
        re.IGNORECASE,
    )
    if count_match:
        col = count_match.group(1)
        op = count_match.group(2)
        val_str = count_match.group(3)
        if col in df.columns:
            try:
                val = float(val_str) if '.' in val_str or val_str.isdigit() else val_str
            except ValueError:
                val = val_str.strip("'\"")
            try:
                if pd.api.types.is_numeric_dtype(df[col]) and isinstance(val, (int, float)):
                    if op == '>':
                        count = (df[col] > val).sum()
                    elif op == '<':
                        count = (df[col] < val).sum()
                    elif op == '>=':
                        count = (df[col] >= val).sum()
                    elif op == '<=':
                        count = (df[col] <= val).sum()
                    elif op in ('==', '='):
                        count = (df[col] == val).sum()
                    elif op == '!=':
                        count = (df[col] != val).sum()
                    else:
                        count = len(df)
                else:
                    count = (df[col].astype(str).str.lower() == str(val).lower()).sum()
                return f"There are {count} rows where {col} {op} {val}."
            except Exception:
                pass

    return None


def get_summary(data_id):
    if data_id not in datasets:
        return f"Dataset {data_id} not found."
    df = datasets[data_id]["df"]
    info = analytics_get_data_info(df)
    stats = analytics_get_stats(df)
    lines = [
        f"Dataset: {datasets[data_id]['filename']}",
        f"Rows: {info['rows']}, Columns: {len(info['columns'])}",
    ]
    missing_cols = {k: v for k, v in info['missing'].items() if v > 0}
    if missing_cols:
        lines.append(f"Columns with missing values: {missing_cols}")
    else:
        lines.append("No missing values.")
    if stats['numeric']:
        lines.append(
            f"Numeric columns: {', '.join(stats['numeric'].keys())}"
        )
    if stats['categorical']:
        lines.append(
            f"Categorical columns: {', '.join(stats['categorical'].keys())}"
        )
    if stats['correlations']:
        lines.append(
            f"Correlations found: {len(stats['correlations'])} pairs"
        )
    return "\n".join(lines)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stats",
            "description": "Get statistics for a numeric or categorical column. Returns mean, median, std, min, max, Q1, Q3 for numeric columns, or unique values and top frequencies for categorical columns. If no column is specified, returns stats for all columns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {
                        "type": "string",
                        "description": "Column name to get statistics for. If omitted, returns all column statistics."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_plot",
            "description": "Generate a distribution plot (histogram for numeric, bar chart for categorical) for a specific column.",
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {
                        "type": "string",
                        "description": "Column name to plot."
                    }
                },
                "required": ["column"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_correlation",
            "description": "Get the Pearson correlation coefficient between two numeric columns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "col1": {
                        "type": "string",
                        "description": "First numeric column name."
                    },
                    "col2": {
                        "type": "string",
                        "description": "Second numeric column name."
                    }
                },
                "required": ["col1", "col2"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_data",
            "description": "Query the data to answer questions about averages, medians, filters, counts, unique values, etc. Handles natural language queries like 'average of salary when department is Engineering' or 'show rows where age > 30'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The natural language query about the data."
                    }
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_summary",
            "description": "Get a high-level summary of the dataset including row count, column names, data types, missing values, and correlation info.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
]


def rule_based_chat(message, history, data_id):
    tool_calls = []
    plots = []

    corr_pattern = re.compile(
        r'correlation\s+between\s+(\w+)\s+and\s+(\w+)', re.IGNORECASE
    )
    m = corr_pattern.search(message)
    if m:
        col1, col2 = m.group(1), m.group(2)
        tool_calls.append("get_correlation")
        result = get_correlation(data_id, col1, col2)
        updated_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result},
        ]
        return {
            "response": result,
            "tool_calls": tool_calls,
            "plots": plots,
            "updated_history": updated_history,
        }

    plot_patterns = [
        r'(?:plot|chart|histogram|distribution|graph|visualize)\s+(?:of|for|the)?\s*(\w+)',
        r'(?:show|display)\s+(?:me\s+)?(?:a\s+)?(?:plot|chart|histogram|distribution|graph)\s+(?:of|for|the)?\s*(\w+)',
    ]
    for pat in plot_patterns:
        m = re.search(pat, message, re.IGNORECASE)
        if m:
            col = m.group(1)
            if col in datasets[data_id]["df"].columns:
                tool_calls.append("get_plot")
                plot_b64 = get_plot(data_id, col)
                if plot_b64:
                    plots.append(plot_b64)
                    response_text = f"Here is the distribution plot for {col}:"
                    updated_history = history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": response_text},
                    ]
                    return {
                        "response": response_text,
                        "tool_calls": tool_calls,
                        "plots": plots,
                        "updated_history": updated_history,
                    }

    avg_mean_pattern = re.search(
        r'(?:average|mean)\s+(?:of|for|the)?\s*(\w+)', message, re.IGNORECASE
    )
    if avg_mean_pattern:
        tool_calls.append("query_data")
        result = query_data(data_id, message)
        if result:
            updated_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": result},
            ]
            return {
                "response": result,
                "tool_calls": tool_calls,
                "plots": plots,
                "updated_history": updated_history,
            }

    summary_pattern = re.compile(
        r'^(?:summary|overview|describe|info|information)\s*$', re.IGNORECASE
    )
    if summary_pattern.match(message.strip()):
        tool_calls.append("get_summary")
        result = get_summary(data_id)
        updated_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result},
        ]
        return {
            "response": result,
            "tool_calls": tool_calls,
            "plots": plots,
            "updated_history": updated_history,
        }

    result = query_data(data_id, message)
    if result:
        tool_calls.append("query_data")
        updated_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result},
        ]
        return {
            "response": result,
            "tool_calls": tool_calls,
            "plots": plots,
            "updated_history": updated_history,
        }

    df = datasets[data_id]["df"]
    response_text = (
        f"Dataset has {len(df)} rows and {len(df.columns)} columns. "
        f"You can ask about averages, distributions, correlations, or filters."
    )
    updated_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response_text},
    ]
    return {
        "response": response_text,
        "tool_calls": tool_calls,
        "plots": plots,
        "updated_history": updated_history,
    }


TOOL_FUNCTIONS = {
    "get_stats": lambda data_id, **kw: get_stats(data_id, **kw),
    "get_plot": lambda data_id, **kw: get_plot(data_id, **kw),
    "get_correlation": lambda data_id, **kw: get_correlation(data_id, **kw),
    "query_data": lambda data_id, **kw: query_data(data_id, **kw),
    "get_summary": lambda data_id, **kw: get_summary(data_id, **kw),
}

TOOL_SIDE_EFFECTS = {
    "get_plot": True,
}


def llm_chat(message, history, data_id):
    from openai import OpenAI

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    df = datasets[data_id]["df"]
    ds = datasets[data_id]
    info = analytics_get_data_info(df)
    stats = analytics_get_stats(df)

    columns_desc = []
    for col in info["columns"]:
        dtype = info["dtypes"].get(col, "unknown")
        missing = info["missing"].get(col, 0)
        if col in stats["numeric"]:
            s = stats["numeric"][col]
            columns_desc.append(
                f"- {col} ({dtype}): numeric, "
                f"range [{s['min']:.2f}, {s['max']:.2f}], "
                f"mean={s['mean']:.2f}"
            )
        elif col in stats["categorical"]:
            s = stats["categorical"][col]
            top_items = list(s["top_values"].items())[:5]
            top_str = ", ".join(f"{k}:{v}" for k, v in top_items)
            columns_desc.append(
                f"- {col} ({dtype}): categorical, "
                f"{s['unique_values']} unique values, "
                f"top values: {top_str}"
            )
        else:
            columns_desc.append(f"- {col} ({dtype})")

    columns_text = "\n".join(columns_desc)

    system_prompt = (
        f"You are a data analysis assistant helping a user explore their dataset.\n\n"
        f"Dataset: {ds['filename']}\n"
        f"Rows: {info['rows']}, Columns: {len(info['columns'])}\n\n"
        f"Columns:\n{columns_text}\n\n"
        f"You have tools to analyze the data. Use them when needed. "
        f"When the user asks for a plot/chart/distribution, use get_plot. "
        f"Be concise and conversational."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    plots = []
    tool_calls_used = []

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            extra_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "CSV Data Dashboard",
            },
        )

        assistant_msg = response.choices[0].message

        if assistant_msg.tool_calls:
            messages.append(assistant_msg)
            for tc in assistant_msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                tool_calls_used.append(name)

                fn = TOOL_FUNCTIONS.get(name)
                if fn:
                    result = fn(data_id, **args)
                else:
                    result = f"Unknown tool: {name}"

                if TOOL_SIDE_EFFECTS.get(name):
                    if result:
                        plots.append(result)

                result_text = str(result) if result else "No result."

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                })

            second_response = client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=messages,
                extra_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "CSV Data Dashboard",
                },
            )
            final_text = second_response.choices[0].message.content or ""
        else:
            final_text = assistant_msg.content or ""

    except Exception as e:
        final_text = f"Sorry, I encountered an error: {str(e)}"

    response_text = final_text
    updated_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response_text},
    ]

    return {
        "response": response_text,
        "tool_calls": tool_calls_used,
        "plots": plots,
        "updated_history": updated_history,
    }


def chat(message, history, data_id):
    if data_id not in datasets:
        response_text = "Dataset not found. Please upload a CSV file first."
        updated_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response_text},
        ]
        return {
            "response": response_text,
            "tool_calls": [],
            "plots": [],
            "updated_history": updated_history,
        }

    if OPENROUTER_API_KEY:
        try:
            return llm_chat(message, history, data_id)
        except Exception as e:
            return {
                "response": f"LLM error ({str(e)}). Falling back to rule-based mode.",
                "tool_calls": [],
                "plots": [],
                "updated_history": history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": f"LLM error. Falling back to rule-based mode."},
                ],
            }

    return rule_based_chat(message, history, data_id)
