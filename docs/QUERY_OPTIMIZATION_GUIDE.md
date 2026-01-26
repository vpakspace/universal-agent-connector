# Query Optimization Guide

Complete guide for using automatic query optimization with EXPLAIN analysis, index recommendations, and query rewrites.

## 🎯 Overview

The Query Optimization feature provides automatic analysis and recommendations to improve query performance:

- **EXPLAIN Analysis**: Detailed query execution plan analysis
- **Index Recommendations**: Automatic suggestions for missing indexes
- **Query Rewrites**: Suggestions for optimizing query structure
- **Before/After Metrics**: Track performance improvements

## 🚀 Quick Start

### Analyze a Query

```bash
POST /api/agents/{agent_id}/query/optimize
Headers: X-API-Key: your-api-key
Body: {
  "query": "SELECT * FROM users WHERE age > 25",
  "track_metrics": true
}
```

### Response

```json
{
  "query": "SELECT * FROM users WHERE age > 25",
  "explain_analysis": {
    "total_cost": 1250.5,
    "execution_time": 45.2,
    "rows_examined": 10000,
    "rows_returned": 150,
    "index_usage": [],
    "sequential_scans": ["users"],
    "warnings": ["Sequential scan on users with filter"]
  },
  "index_recommendations": [
    {
      "table": "users",
      "columns": ["age"],
      "index_type": "btree",
      "reason": "WHERE clause filters on age",
      "estimated_improvement": "50-90% faster",
      "priority": "critical",
      "sql": "CREATE INDEX idx_users_age ON users (age);"
    }
  ],
  "query_rewrites": [
    {
      "original_query": "SELECT * FROM users WHERE age > 25",
      "suggested_query": "SELECT /* specific columns */ FROM users WHERE age > 25",
      "reason": "SELECT * retrieves unnecessary columns",
      "estimated_improvement": "10-30% faster, less data transfer",
      "priority": "info",
      "confidence": 0.7
    }
  ],
  "estimated_improvement": "1 index recommendation(s), 1 rewrite suggestion(s)",
  "generated_at": "2024-01-15T10:30:00Z"
}
```

## 📊 EXPLAIN Analysis

### What It Does

EXPLAIN analysis uses PostgreSQL's EXPLAIN command to analyze query execution plans:

- **Execution Plan**: Shows how the database executes the query
- **Cost Estimation**: Total cost and execution time
- **Row Statistics**: Rows examined vs returned
- **Index Usage**: Which indexes are used
- **Sequential Scans**: Tables scanned without indexes
- **Warnings**: Potential performance issues

### Understanding Results

**Good Signs:**
- Index usage present
- Low execution time
- High selectivity (few rows examined for many returned)

**Warning Signs:**
- Sequential scans on large tables
- High cost/execution time
- Low selectivity (many rows examined for few returned)
- Missing indexes on filtered columns

## 🔍 Index Recommendations

### Automatic Detection

The optimizer automatically detects:

1. **WHERE Clause Filters**: Columns used in WHERE clauses
2. **JOIN Conditions**: Columns used in JOINs
3. **ORDER BY Columns**: Columns used for sorting
4. **Missing Indexes**: Based on sequential scans

### Recommendation Types

**Critical Priority:**
- Sequential scans on filtered columns
- Missing indexes on frequently filtered columns

**Warning Priority:**
- JOIN conditions without indexes
- ORDER BY on large result sets

**Info Priority:**
- Optimization opportunities
- Best practice suggestions

### Applying Recommendations

```sql
-- Example recommendation
CREATE INDEX idx_users_age ON users (age);
```

**Before applying:**
1. Review recommendation reason
2. Check table size
3. Consider write performance impact
4. Test in development first

## 🔄 Query Rewrites

### Common Rewrites

1. **SELECT * → Specific Columns**
   - Reduces data transfer
   - Improves query performance

2. **Add LIMIT to ORDER BY**
   - Prevents sorting entire result set
   - Much faster for large datasets

3. **Subquery → JOIN**
   - Often more efficient
   - Better query plan optimization

4. **Add WHERE Clauses**
   - Reduces rows examined
   - Improves selectivity

### Confidence Levels

- **High (0.8+)**: Safe, significant improvement expected
- **Medium (0.5-0.8)**: Good improvement, review recommended
- **Low (<0.5)**: Potential improvement, test carefully

## 📈 Metrics Tracking

### Before Metrics

Tracked automatically when `track_metrics: true`:

```json
{
  "before_metrics": {
    "execution_time": 45.2,
    "rows_returned": 150
  }
}
```

### After Metrics

Recorded after applying optimizations:

```json
{
  "after_metrics": {
    "execution_time": 12.5,
    "rows_returned": 150
  },
  "improvement_percentage": 72.3
}
```

### Viewing Metrics

```bash
GET /api/agents/{agent_id}/query/optimize/metrics
Headers: X-API-Key: your-api-key
```

Response:
```json
{
  "metrics": [
    {
      "query_id": "query-123",
      "query": "SELECT * FROM users WHERE age > 25",
      "before_execution_time": 45.2,
      "after_execution_time": 12.5,
      "improvement_percentage": 72.3,
      "indexes_applied": ["idx_users_age"],
      "recorded_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## 🎯 Best Practices

### 1. Regular Analysis

- Analyze slow queries regularly
- Monitor sequential scans
- Review index recommendations

### 2. Apply Indexes Carefully

- Start with critical priority recommendations
- Test in development first
- Monitor write performance impact
- Consider composite indexes for multiple columns

### 3. Review Query Rewrites

- High confidence rewrites are usually safe
- Test medium confidence rewrites
- Review low confidence carefully

### 4. Track Improvements

- Enable metrics tracking
- Compare before/after performance
- Document improvements

### 5. Monitor Over Time

- Review optimization recommendations regularly
- Track which optimizations help most
- Adjust based on actual usage patterns

## 📚 Examples

### Example 1: Missing Index

**Query:**
```sql
SELECT * FROM users WHERE email = 'user@example.com';
```

**Analysis:**
- Sequential scan on users table
- 10,000 rows examined for 1 returned

**Recommendation:**
```sql
CREATE INDEX idx_users_email ON users (email);
```

**Improvement:** 90% faster

### Example 2: ORDER BY Without LIMIT

**Query:**
```sql
SELECT * FROM users ORDER BY created_at DESC;
```

**Analysis:**
- Sorting 10,000 rows
- No LIMIT clause

**Rewrite:**
```sql
SELECT * FROM users ORDER BY created_at DESC LIMIT 100;
```

**Improvement:** 85% faster

### Example 3: SELECT *

**Query:**
```sql
SELECT * FROM users WHERE active = true;
```

**Analysis:**
- Retrieving all columns
- Unnecessary data transfer

**Rewrite:**
```sql
SELECT id, name, email FROM users WHERE active = true;
```

**Improvement:** 25% faster, less data transfer

## 🔗 API Reference

### Optimize Query

```
POST /api/agents/{agent_id}/query/optimize
```

**Request:**
```json
{
  "query": "SELECT * FROM users WHERE age > 25",
  "track_metrics": true
}
```

**Response:** OptimizationReport

### Get Metrics

```
GET /api/agents/{agent_id}/query/optimize/metrics
```

**Response:**
```json
{
  "metrics": [...]
}
```

### Get Recommendations

```
GET /api/agents/{agent_id}/query/optimize/recommendations
```

**Response:**
```json
{
  "recommendations": [...]
}
```

## 🐛 Troubleshooting

### EXPLAIN Fails

**Issue:** EXPLAIN analysis fails
**Solution:** Check query syntax, ensure table exists

### No Recommendations

**Issue:** No index recommendations
**Solution:** Query may already be optimized, or needs manual review

### Metrics Not Tracking

**Issue:** Metrics not recorded
**Solution:** Ensure `track_metrics: true` in request

### Recommendations Not Accurate

**Issue:** Recommendations don't match actual performance
**Solution:** Review EXPLAIN output, consider table statistics

## 📈 Performance Tips

1. **Analyze First**: Always analyze before optimizing
2. **Start Small**: Apply one optimization at a time
3. **Measure Impact**: Track before/after metrics
4. **Review Regularly**: Re-analyze after schema changes
5. **Monitor Production**: Track query performance over time

---

**Questions?** Check [GitHub Discussions](https://github.com/your-repo/ai-agent-connector/discussions) or open an issue!

