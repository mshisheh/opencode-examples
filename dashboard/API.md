# API Contract - Dashboard with Chatbot

## Base URL
Backend runs on `http://localhost:8000`. Frontend served separately on `http://localhost:5500` (or via VS Code Live Server, python -m http.server, etc.)

## CORS
Backend must enable CORS for `http://localhost:5500` (and any other frontend origin).

---

## Endpoints

### 1. Upload CSV
`POST /api/upload`

- Request: `multipart/form-data` with field `file` (the CSV file)
- Response:
```json
{
  "data_id": "uuid-string",
  "filename": "data.csv",
  "rows": 100,
  "columns": ["col1", "col2", "col3"],
  "dtypes": {"col1": "int64", "col2": "object", "col3": "float64"}
}
```

### 2. Get Data Info
`GET /api/data/{data_id}/info`

- Response:
```json
{
  "data_id": "uuid-string",
  "filename": "data.csv",
  "rows": 100,
  "columns": ["col1", "col2", "col3"],
  "dtypes": {"col1": "int64", "col2": "object", "col3": "float64"},
  "missing": {"col1": 0, "col2": 5, "col3": 2},
  "preview": [{"col1": 1, "col2": "a", "col3": 1.5}, ...]
}
```
- `preview` contains first 5 rows

### 3. Get Statistics
`GET /api/data/{data_id}/stats`

- Response:
```json
{
  "data_id": "uuid-string",
  "numeric": {
    "col1": {
      "mean": 50.5,
      "median": 48.0,
      "std": 12.3,
      "min": 10.0,
      "max": 100.0,
      "q1": 35.0,
      "q3": 65.0
    }
  },
  "categorical": {
    "col2": {
      "unique_values": 5,
      "top_values": {"a": 30, "b": 25, "c": 20},
      "missing": 5
    }
  },
  "correlations": {"col1_col3": 0.85}
}
```

### 4. Get Plots
`GET /api/data/{data_id}/plots`

- Query params: `columns` (optional, comma-separated), defaults to all
- Response:
```json
{
  "data_id": "uuid-string",
  "plots": [
    {
      "column": "col1",
      "type": "histogram",
      "image_base64": "iVBOR...",
      "description": "Distribution of col1 - right skewed"
    },
    {
      "column": "col2",
      "type": "bar",
      "image_base64": "iVBOR...",
      "description": "Frequency of categories in col2"
    }
  ],
  "correlation_matrix_base64": "iVBOR..."
}
```

### 5. Chat - Send Message
`POST /api/chat`

- Request:
```json
{
  "data_id": "uuid-string",
  "message": "What is the average of col1?",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```
- Response:
```json
{
  "response": "The average of col1 is 50.5.",
  "tool_calls": ["query_data"],
  "plots": ["base64..."],
  "updated_history": [...]
}
```

### 6. List Uploads
`GET /api/uploads`

- Response:
```json
{
  "uploads": [
    {
      "data_id": "uuid-string",
      "filename": "data.csv",
      "uploaded_at": "2024-01-01T00:00:00"
    }
  ]
}
```

---

## Data Flow

1. User uploads CSV → Backend parses, generates stats + plots, stores in memory
2. Frontend displays stats table + distribution plots automatically
3. User asks question in chat → Backend chatbot interprets → calls tools (query, plot, correlate) → returns response + optional plots
4. Frontend renders chat messages and any returned plots inline

---

## Tool Functions (for Chatbot)

The chatbot agent has access to these Python tools:

1. `get_stats(data_id, column=None)` → Return statistics for all or a specific column
2. `get_plot(data_id, column, plot_type="auto")` → Return base64-encoded plot
3. `get_correlation(data_id, col1, col2)` → Return correlation coefficient
4. `query_data(data_id, sql_like_query)` → Simple query/filter on the data
5. `get_summary(data_id)` → Return a text summary of the dataset
