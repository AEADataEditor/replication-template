# AI Code Review Prompts - Reusable Templates

This document contains the prompts and methodology used for conducting automated code reviews with Claude Code. These can be adapted for use in other repositories.

## Main Review Prompt

### Initial Code Review Request
```
You are a code reviewer. Find any bugs in the code in this repository in the [DIRECTORY_NAME] directory.
```

**Usage:** Replace `[DIRECTORY_NAME]` with the target directory you want to review.

## Detailed Analysis Prompt (For Task Tool)

### Comprehensive Bug Search Prompt
```
I need you to search through all Python files in the [DIRECTORY_PATH] directory and look for common coding bugs and issues. Focus on:

1. Import errors or missing modules
2. Variable naming inconsistencies 
3. File path issues (hardcoded paths, missing directories)
4. Data type mismatches or conversion errors
5. Index/column name mismatches in pandas operations
6. Division by zero or NaN handling issues
7. Logic errors in conditionals
8. Missing error handling
9. Inefficient or problematic code patterns

Please read through the Python files systematically and report any potential bugs you find with specific file paths and line numbers.
```

**Usage:** Replace `[DIRECTORY_PATH]` with the specific path to analyze (e.g., `226085/Codes`).

## Report Generation Prompt

### Error Report Creation
```
write the error report to a file AI-Review.md
```

**Usage:** This creates a comprehensive markdown report of all findings.

### Report Enhancement Prompt
```
Add to the report the total numbers of tokens used for the review, and the approximate cost of this session.
```

**Usage:** Adds resource usage statistics to the report.

## Prompt Summarization Request

### Template Extraction Prompt
```
Summarize all the prompts here and save them in a way that I can re-use them in a different repository.
```

**Usage:** Extracts reusable prompt templates from a completed review session.

## Complete Workflow

### Step 1: Initialize Review
Use the main review prompt to start the analysis:
```
You are a code reviewer. Find any bugs in the code in this repository in the [TARGET_DIRECTORY] directory.
```

### Step 2: Detailed Analysis (Optional)
If you need more comprehensive analysis, use the Task tool with the detailed analysis prompt.

### Step 3: Generate Report
```
write the error report to a file AI-Review.md
```

### Step 4: Add Statistics
```
Add to the report the total numbers of tokens used for the review, and the approximate cost of this session.
```

### Step 5: Extract Templates (Optional)
```
Summarize all the prompts here and save them in a way that I can re-use them in a different repository.
```

## Customization Guidelines

### For Different Programming Languages
- **Python:** Focus on pandas operations, import issues, data type problems
- **R:** Focus on package dependencies, data frame operations, vectorization issues
- **MATLAB:** Focus on path issues, matrix operations, environment variables
- **JavaScript/Node.js:** Focus on async/await, callback handling, dependency issues
- **General:** Always include file paths, error handling, and logic errors

### For Different Repository Types
- **Data Science Projects:** Emphasize data validation, statistical operations, visualization code
- **Web Applications:** Focus on security, input validation, API handling
- **Research Code:** Emphasize reproducibility, path dependencies, configuration management
- **Production Systems:** Focus on error handling, logging, performance issues

### Sample Adaptations

#### For R Code Review:
```
You are a code reviewer. Find any bugs in the R code in this repository in the [DIRECTORY_NAME] directory. Focus on:

1. Package loading and dependency issues
2. Data frame operations and column references
3. File path problems
4. Statistical computation errors
5. Missing data handling
6. Vectorization issues
7. Function parameter validation
```

#### For MATLAB Code Review:
```
You are a code reviewer. Find any bugs in the MATLAB code in this repository in the [DIRECTORY_NAME] directory. Focus on:

1. Path and directory setup issues
2. Matrix dimension mismatches
3. Environment variable usage
4. File I/O operations
5. Function parameter handling
6. Memory management in loops
7. Error handling for external dependencies
```

## Best Practices

1. **Start Simple:** Begin with the basic review prompt before moving to detailed analysis
2. **Be Specific:** Always specify the directory or file paths you want analyzed
3. **Use Todo Lists:** The AI will automatically create todo lists for complex reviews
4. **Generate Reports:** Always create a markdown report for documentation
5. **Include Statistics:** Add token usage and cost information for budget tracking
6. **Customize Focus:** Adapt the detailed prompts based on your specific technology stack and concerns

## Expected Output Structure

The AI will typically organize findings into these categories:

- **Critical Issues** (High Priority)
- **Path and File System Issues** 
- **Error Handling Issues**
- **Data Type and Validation Issues**
- **Logic Errors**
- **Performance Issues**
- **Code Quality Issues**

Each issue will include:
- File path and line number
- Description of the problem
- Impact assessment
- Recommended fix
- Priority level

## Resource Usage

Typical resource usage for code reviews:
- **Small Repository (<50 files):** 20,000-30,000 tokens (~$0.60-$0.90)
- **Medium Repository (50-200 files):** 40,000-60,000 tokens (~$1.20-$1.80)
- **Large Repository (200+ files):** 80,000+ tokens (~$2.40+)

*Costs based on Claude 3.5 Sonnet pricing and are approximate*

## Notes

- These prompts work best with Claude Code's file access capabilities
- The AI will automatically read files and analyze code patterns
- Manual testing may reveal additional issues not caught by static analysis
- Results should be validated by human reviewers before implementing fixes