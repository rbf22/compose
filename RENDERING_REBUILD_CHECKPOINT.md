# Rendering System Rebuild - Checkpoint

## What We Learned

### Coordinate System (CORRECT)
- PDF origin at bottom-left, Y increases upward
- `current_y` = baseline for text rendering
- `text_top = current_y + ascender`
- `text_bottom = current_y - descender`
- Spacing occupies: `[content_bottom - spacing, content_bottom]`
- Next element baseline: `spacing_bottom - ascender`

### The Pipeline (CORRECT)
```
Measure → Update → Render → Check
```

1. **MEASURE**: Calculate exact height needed
2. **UPDATE**: Check fit, handle page breaks, add spacing
3. **RENDER**: Draw at position (no spacing/page logic)
4. **CHECK**: Tracker validates

### Key Insights
- Margin is inviolable - nothing outside it
- Spacing is BETWEEN components, not part of them
- Page breaks happen BEFORE rendering, not after
- Each render method should be simple: take Y, render, return new Y

## Files to Keep
- `/compose/render/layout_measurer.py` - measurement system
- `/compose/render/rendering_tracker.py` - validation
- All tests

## Files to Remove/Refactor
- Old `_layout_document()` - replace with new pipeline
- Old `_layout_*()` methods - replace with clean versions
- `_add_vertical_space()` - logic moves to UPDATE phase
- `use_measurement_pipeline` flag - becomes default

## New Architecture

### LayoutMeasurer
Already implemented. Measures component heights.

### New Render Methods
```python
def _render_heading(self, heading: Heading, y: float) -> float:
    """Render heading at position y, return new y."""
    # Just render, no spacing, no page logic
    # Return: new current_y
    
def _render_paragraph(self, paragraph: Paragraph, y: float) -> float:
    """Render paragraph at position y, return new y."""
    # Just render, no spacing, no page logic
    # Return: new current_y
```

### Main Pipeline
```python
def _layout_document_clean(self, doc: Document):
    """NEW: Clean implementation of Measure → Update → Render → Check."""
    for block in doc.blocks:
        # MEASURE
        measurement = self.measurer.measure(block)
        
        # UPDATE
        available = self.measurer.get_available_height(self.current_y)
        if not fits and not at_top:
            self._new_page()
        
        # Add spacing (UPDATE phase)
        if not at_top:
            self._add_spacing_between_blocks(measurement.spacing_after)
        
        # RENDER
        self.current_y = self._render_block(block, self.current_y)
        
        # CHECK (automatic via tracker)
```

## Status
Ready to implement clean rebuild.
