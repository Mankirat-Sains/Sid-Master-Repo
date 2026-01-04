# How to Extract Excel Data for ChatGPT

This guide shows you exactly how to extract the information ChatGPT needs to generate semantic metadata.

## Quick Method: Copy-Paste from Excel

### Step 1: Open Your Excel File

Open your Excel workbook (e.g., "Glulam Column.xlsx")

### Step 2: For Each Key Sheet, Copy This Information

#### A. Sheet Name and Purpose
```
Sheet: Sheet1
Purpose: Main design calculations for glulam column
```

#### B. Sample Data (First 30-50 Rows)
In Excel, select the first 30-50 rows and copy them. Then format like this:

```
Sample Data (Rows 1-30):
Row 1: A1: [value] | B1: [value] | C1: [value] | ...
Row 2: A2: [value] | B2: [value] | C2: [value] | ...
Row 3: A3: [value] | B3: [value] | C3: [value] | ...
...
```

**Tip**: In Excel, you can:
1. Select range (e.g., A1:Z30)
2. Copy (Cmd+C)
3. Paste into a text editor
4. Format as shown above

#### C. Color Legend (If Visible)
If you see a legend explaining colors, describe it:

```
Color Legend:
- Orange/Peach color (cells like N4): INPUT - Cells users should modify
- Gray color (cells like N6): CALCULATION - Cells containing formulas
- Gray color (cells like N7): OUTPUT (CHECK THESE) - Results to review
- Red color (cells like N8): FAIL - Indicates failure
- Green color (cells like P8): PASS - Indicates passing
```

#### D. Key Observations
Note any patterns you see:

```
Key Observations:
- Column A contains parameter labels
- Column B contains input values
- Column C contains units
- Column G contains calculated outputs
- Formulas are in column G (e.g., G12, G13)
```

### Step 3: Format Everything Together

Create a document like this:

```
Workbook: Glulam Column.xlsx

Sheet: Sheet1
Purpose: Main design calculations for glulam column

Sample Data (Rows 1-30):
Row 1: A1: Glulam Column Design | B1: [empty] | C1: [empty]
Row 2: A2: [empty] | B2: [empty] | C2: [empty]
Row 3: A3: Span | B3: 6.0 | C3: m
Row 4: A4: Load | B4: 50.0 | C4: kN
Row 5: A5: [empty] | B5: [empty] | C5: [empty]
Row 6: A6: Moment | B6: =B3*B4 | C6: kN⋅m
Row 7: A7: Shear | B7: =B4/2 | C7: kN
Row 8: A8: [empty] | B8: [empty] | C8: [empty]
...

Color Legend:
- Yellow/Orange cells (B3, B4): Input parameters
- Gray cells (B6, B7): Calculated outputs

Key Observations:
- Column A = Labels
- Column B = Values (inputs) or Formulas (outputs)
- Column C = Units
- Input cells are colored yellow/orange
- Output cells contain formulas and are gray
```

## Alternative: Use Excel's Export

### Method 1: Copy as Text
1. Select range in Excel
2. Copy (Cmd+C)
3. Paste into text editor
4. Format as shown above

### Method 2: Save as CSV (Then Convert)
1. Save sheet as CSV
2. Open CSV in text editor
3. Format for ChatGPT prompt

## Complete Example

Here's a complete example you can use as a template:

```
Workbook: Glulam Column.xlsx

Sheets:
- Sheet1: Main design calculations

Sheet: Sheet1
Purpose: Calculates glulam column design parameters

Sample Data:
Row 1: A1: Glulam Column Design | B1: [empty] | C1: [empty] | D1: [empty]
Row 2: A2: [empty] | B2: [empty] | C2: [empty] | D2: [empty]
Row 3: A3: Span | B3: 6.0 | C3: m | D3: [empty]
Row 4: A4: Load | B4: 50.0 | C4: kN | D4: [empty]
Row 5: A5: [empty] | B5: [empty] | C5: [empty] | D5: [empty]
Row 6: A6: Moment | B6: =B3*B4 | C6: kN⋅m | D6: [empty]
Row 7: A7: Shear | B7: =B4/2 | C7: kN | D7: [empty]
Row 8: A8: [empty] | B8: [empty] | C8: [empty] | D8: [empty]

Color Legend:
- Yellow/Orange (B3, B4): INPUT - User-editable parameters
- Gray (B6, B7): OUTPUT - Calculated results

Key Observations:
- Column A contains parameter labels
- Column B contains values (inputs) or formulas (outputs)
- Column C contains units
- Input cells are colored yellow/orange
- Output cells contain formulas starting with "="
```

## Pro Tips

1. **Focus on Key Sheets**: Usually INFO, Full Building, or main calculation sheets
2. **Include Formulas**: Show formulas in output cells (e.g., `=B3*B4`)
3. **Note Colors**: If colors are used, describe them
4. **Include Headers**: If there are column headers, include them
5. **Show Structure**: Include empty rows if they show structure

## What ChatGPT Needs

Minimum information:
- ✅ Sheet names
- ✅ Sample data (20-30 rows is enough)
- ✅ Color legend (if available)
- ✅ Key patterns you notice

ChatGPT will figure out the rest using AI!

