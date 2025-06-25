# Repository Memory for AI Code Reviews

## Quick Review Commands

When asked to "run code review" or "review code", use these prompts:

### Standard Code Review
```
You are a code reviewer. Find any bugs in the code in this repository in the [TARGET_DIRECTORY] directory.
```

### Comprehensive Python Review
```
Search through all Python files and look for:
1. Import errors or missing modules
2. Variable naming inconsistencies 
3. File path issues (hardcoded paths, missing directories)
4. Data type mismatches or conversion errors
5. Index/column name mismatches in pandas operations
6. Division by zero or NaN handling issues
7. Logic errors in conditionals
8. Missing error handling
9. Inefficient or problematic code patterns
```

### Report Generation
Always end reviews with:
```
write the error report to a file AI-Review.md
```

Then add statistics:
```
Add to the report the total numbers of tokens used for the review, and the approximate cost of this session.
```

## Repository Context
- This is a research/academic repository
- Contains Python data analysis code
- Uses MATLAB for modeling
- Focus on data science and financial analysis code patterns