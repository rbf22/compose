# fpdf2 Integration for Compose

## Current Issues fpdf2 Could Fix

### 1. Math Block Margin Violations
**Current Error:** `ERROR: Item 62 (math_block) left 36.0 < margin_left 50.0`
**fpdf2 Solution:** Automatic centering with `pdf.cell(0, 10, text, align='C')`

### 2. Overlap Detection Needed
**Current Error:** `ERROR: Item 67 (list_item) overlaps with item 68 (para_line_A graphic is co)`
**fpdf2 Solution:** Automatic text flow and positioning - no manual Y calculations

### 3. Bottom Margin Violations
**Current Error:** `ERROR: Item 121 (para_line_chartjunk. They) bottom 53.2 < margin_bottom 60.0`
**fpdf2 Solution:** Automatic page breaks with `pdf.add_page()` when needed

### 4. Manual PDF Command Generation
**Current Issue:** Fragile manual PDF command strings
**fpdf2 Solution:** High-level API methods

## Math Rendering Improvements

### Current State
```python
# Just renders placeholder text
math_text = f"[MATH: {content}]"
```

### With fpdf2 + matplotlib
```python
def render_math(self, latex):
    fig, ax = plt.subplots(figsize=(6, 1))
    ax.text(0.5, 0.5, f'${latex}$', fontsize=16,
           ha='center', va='center')
    ax.axis('off')

    # Save and embed as image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, transparent=True)
    self.pdf.image(buf, w=120)
```

## Architecture Benefits

1. **Automatic Layout**: No manual Y coordinate calculations
2. **Robust Positioning**: Built-in margin and page break handling
3. **Better Fonts**: Automatic font embedding and metrics
4. **Error Prevention**: High-level API prevents coordinate errors
5. **Math Integration**: Easy matplotlib integration for equations

## Migration Path

1. **Phase 1**: Add fpdf2 as optional backend alongside current system
2. **Phase 2**: Migrate text rendering (headings, paragraphs, lists)
3. **Phase 3**: Implement proper math rendering
4. **Phase 4**: Add table and image support
5. **Phase 5**: Deprecate manual PDF generation

## Compatibility

- Keep existing `RenderingTracker` for validation
- Maintain same API for document processing
- Gradual migration with feature flags
- Backward compatibility maintained

## Result

Much more robust rendering system that eliminates:
- Manual PDF command generation errors
- Coordinate calculation bugs
- Margin violation issues
- Math rendering placeholders

While providing real mathematical typesetting capabilities.
