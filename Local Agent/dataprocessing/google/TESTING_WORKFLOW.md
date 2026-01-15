# Testing Workflow for Google Embeddings

## File Path Structure

```
C:\Users\shine\Testing-2025-01-07\Local Agent\dataprocessing\google\input_images\
└── 25-01-005\                    <- project_key (root folder)
    └── page_001\                 <- page_num = 1 (extracted from folder name)
        └── region_01_red_box.png <- region_number = 1, image_id = "region_01_red_box.png"
```

## Field Extraction

| Field | Source | Example | Notes |
|-------|--------|---------|-------|
| `project_key` | Root folder name | `25-01-005` | From directory structure |
| `page_num` | Folder name `page_XXX` | `page_001` → `1` | Converted with `int()` |
| `region_number` | Filename `region_XX_red_box.png` | `region_01` → `1` | Converted with `int()` |
| `image_id` | Full filename | `region_01_red_box.png` | Entire filename |
| `relative_path` | None/empty | `None` | Can be empty as per user requirement |

## Testing Workflow

### 1. Extract Structured Information

```powershell
python extract_structured_info_google.py 25-01-005
```

**Output:** `structured_json/25-01-005/structured_25-01-005.json`

**Fields extracted:**
- ✅ `project_id` = "25-01-005" (from root folder)
- ✅ `page_number` = 1 (integer from `page_001`)
- ✅ `region_number` = 1 (integer from `region_01`)
- ✅ `image_id` = "region_01_red_box.png" (full filename)
- ✅ `relative_path` = None (empty as requested)
- Plus all structured fields (classification, location, etc.)

### 2. Generate Embeddings

```powershell
python generate_embeddings_gemini.py 25-01-005
```

**What it does:**
- Generates embeddings for `text_verbatim` and `summary`
- Caps embeddings to exactly **1536 dimensions**
- Adds `text_verbatim_embedding` and `summary_embedding` fields

### 3. Test Structure (Optional)

```powershell
python test_table_structure.py
```

**What it does:**
- Validates JSON structure matches table requirements
- Checks field names, data types, embedding dimensions
- Shows converted table format

### 4. Upload to Supabase

```powershell
python upload_to_supabase_test.py 25-01-005
```

**What it does:**
- Converts JSON to table format:
  - `project_id` → `project_key`
  - `page_number` → `page_num`
  - Arrays → comma-separated strings
- Validates all fields (required fields, data types, embedding dimensions)
- Inserts into `test_google_embeddings_table`
- Skips existing records (based on `project_key` + `image_id`)

## Field Mapping (JSON → Supabase)

| JSON Field | Supabase Field | Conversion |
|------------|----------------|------------|
| `project_id` | `project_key` | Direct |
| `page_number` | `page_num` | Direct (must be integer) |
| `region_number` | `region_number` | Direct (integer or null) |
| `image_id` | `image_id` | Direct (full filename) |
| `relative_path` | `relative_path` | Direct (None/empty) |
| `grid_references` (array) | `grid_references` (text) | `", ".join(array)` |
| `section_callouts` (array) | `section_callouts` (text) | `", ".join(array)` |
| `element_callouts` (array) | `element_callouts` (text) | `", ".join(array)` |
| `key_components` (array) | `key_components` (text) | `", ".join(array)` |
| `text_verbatim_embedding` (list) | `text_verbatim_embedding` (vector) | Direct (must be 1536-dim) |
| `summary_embedding` (list) | `summary_embedding` (vector) | Direct (must be 1536-dim) |

## Validation Checks

The upload script validates:

✅ **Required Fields:**
- `project_key` (text, not null)
- `page_num` (integer, not null)
- `image_id` (text, not null)

✅ **Data Types:**
- `page_num` must be integer
- `region_number` must be integer or null
- `text_verbatim_embedding` must be list with 1536 elements
- `summary_embedding` must be list with 1536 elements

✅ **Unique Constraint:**
- Prevents duplicates based on `(project_key, image_id)`

## Troubleshooting

### If embeddings are wrong dimension:
- Check `generate_embeddings_gemini.py` - it should cap to 1536
- Verify `MAX_EMBEDDING_DIM = 1536` in the script

### If page_number or region_number are strings:
- The extraction script uses `int()` to convert
- Check that folder names match pattern: `page_XXX` and `region_XX_red_box.png`

### If upload fails:
- Check Supabase credentials in `.env` file
- Verify table exists: `test_google_embeddings_table`
- Check error messages for specific field validation issues

## Example Output

**JSON Format:**
```json
{
  "images": [{
    "project_id": "25-01-005",
    "page_number": 1,
    "region_number": 1,
    "image_id": "region_01_red_box.png",
    "relative_path": null,
    "classification": "Detail",
    ...
    "text_verbatim_embedding": [0.123, 0.456, ...],  // 1536 dimensions
    "summary_embedding": [0.789, 0.012, ...]         // 1536 dimensions
  }]
}
```

**Supabase Table Format:**
```sql
project_key: "25-01-005"
page_num: 1
region_number: 1
image_id: "region_01_red_box.png"
relative_path: NULL
text_verbatim_embedding: vector(1536)
summary_embedding: vector(1536)
```

