# Migration Examples: Old vs New Architecture

This document shows concrete examples of migrating components from the old architecture to the new separated layout/rendering architecture.

## Example 1: Heading Layout

### Old Architecture (Coupled)

```python
def _layout_heading(self, heading: Heading):
    """Layout heading - BOTH calculates AND renders"""
    level = heading.level
    text = self._extract_text_content(heading.content)
    
    # Calculate font size based on level
    if level == 1:
        font_size = 24
    elif level == 2:
        font_size = 20
    else:
        font_size = 16
    
    # Check page break
    if self.current_y < self.margin_bottom + font_size:
        self._new_page()
    
    # Generate PDF commands (tightly coupled)
    commands = [
        "BT",
        "0 0 0 rg",
        f"/Helvetica-Bold {font_size} Tf",
        f"1 0 0 1 {self.margin_left} {self.current_y} Tm",
        f"{self._to_pdf_literal(text)} Tj",
        "ET"
    ]
    self._add_to_current_page(commands)
    
    # Mutate state
    self.current_y -= font_size * 1.5
```

### New Architecture (Separated)

```python
def _calculate_heading_layout_v2(self, heading: Heading) -> LayoutBox:
    """Calculate heading layout - PURE FUNCTION"""
    level = heading.level
    text = self._extract_text_content(heading.content)
    
    # Calculate font size
    font_size = {1: 24, 2: 20, 3: 16}.get(level, 14)
    
    # Use text layout engine
    line = self.text_layout_engine.layout_text_line(
        text=text,
        x=self.margin_left,
        y=self.current_y,
        font="Helvetica-Bold",
        size=font_size
    )
    
    # Return immutable layout structure
    return LayoutBox(
        box_type=BoxType.HEADING,
        x=self.margin_left,
        y=self.current_y,
        width=line.width,
        height=font_size * 1.5,
        content=line,
        metadata={'level': level}
    )

def _render_heading_layout_v2(self, layout: LayoutBox):
    """Render heading layout - PURE CONVERSION"""
    line = layout.content
    
    # Check page break
    if line.y < self.margin_bottom + line.runs[0].size:
        self._new_page()
    
    # Render text run
    for run in line.runs:
        commands = self._text_run_to_pdf_commands(run)
        self._add_to_current_page(commands)
    
    # Update position
    self.current_y -= layout.height
```

## Example 2: List Layout

### Old Architecture (Coupled)

```python
def _layout_list_item(self, item, index, ordered):
    """Layout list item - mixed concerns"""
    # Create bullet/number
    if ordered:
        marker = f"{index}."
    else:
        marker = "•"
    
    # Calculate positions (mixed with rendering)
    marker_x = self.margin_left + 20
    text_x = self.margin_left + 40
    
    # Render marker
    commands = [
        "BT",
        f"/Helvetica {self.current_font_size} Tf",
        f"1 0 0 1 {marker_x} {self.current_y} Tm",
        f"{self._to_pdf_literal(marker)} Tj",
        "ET"
    ]
    self._add_to_current_page(commands)
    
    # Render text (more mixed logic)
    text = self._extract_text_content(item.content)
    lines = self._wrap_text(text, self.page_width - text_x - self.margin_right)
    
    for line in lines:
        commands = [...]
        self._add_to_current_page(commands)
        self.current_y -= self.line_height
```

### New Architecture (Separated)

```python
def _calculate_list_item_layout_v2(self, item, index, ordered) -> LayoutBox:
    """Calculate list item layout - PURE"""
    # Calculate marker
    marker = f"{index}." if ordered else "•"
    marker_x = self.margin_left + 20
    text_x = self.margin_left + 40
    
    # Layout marker
    marker_line = self.text_layout_engine.layout_text_line(
        text=marker,
        x=marker_x,
        y=self.current_y,
        font=self.current_font,
        size=self.current_font_size
    )
    
    # Layout text content
    text = self._extract_text_content(item.content)
    max_width = self.page_width - text_x - self.margin_right
    
    text_lines = self.text_layout_engine.layout_wrapped_text(
        text=text,
        x=text_x,
        y=self.current_y,
        max_width=max_width,
        font=self.current_font,
        size=self.current_font_size
    )
    
    # Calculate total height
    total_height = len(text_lines) * self.text_layout_engine.calculate_line_height(
        self.current_font, self.current_font_size, self.line_height_factor
    )
    
    # Return layout structure
    return LayoutBox(
        box_type=BoxType.LIST_ITEM,
        x=self.margin_left,
        y=self.current_y,
        width=self.page_width - self.margin_left - self.margin_right,
        height=total_height,
        children=[
            LayoutBox(BoxType.TEXT, marker_x, self.current_y, 
                     marker_line.width, marker_line.height, content=marker_line),
            LayoutBox(BoxType.PARAGRAPH, text_x, self.current_y,
                     max_width, total_height, content=text_lines)
        ]
    )

def _render_list_item_layout_v2(self, layout: LayoutBox):
    """Render list item - PURE CONVERSION"""
    for child in layout.children:
        if child.box_type == BoxType.TEXT:
            # Render marker
            line = child.content
            for run in line.runs:
                commands = self._text_run_to_pdf_commands(run)
                self._add_to_current_page(commands)
        elif child.box_type == BoxType.PARAGRAPH:
            # Render text lines
            lines = child.content
            for line in lines:
                for run in line.runs:
                    commands = self._text_run_to_pdf_commands(run)
                    self._add_to_current_page(commands)
    
    self.current_y -= layout.height
```

## Example 3: Table Cell Layout

### Old Architecture (Coupled)

```python
def _render_table_cell(self, cell_text, x, y, width, height, is_header):
    """Render cell - calculation and rendering mixed"""
    font = "Helvetica-Bold" if is_header else "Helvetica"
    
    # Wrap text
    lines = self._wrap_text(cell_text, width - 4)
    
    # Calculate vertical centering
    total_text_height = len(lines) * self.current_font_size * 1.2
    y_offset = (height - total_text_height) / 2
    
    # Render lines (mixed with calculation)
    current_y = y - y_offset
    for line in lines:
        commands = [
            "BT",
            f"/{font} {self.current_font_size} Tf",
            f"1 0 0 1 {x + 2} {current_y} Tm",
            f"{self._to_pdf_literal(line)} Tj",
            "ET"
        ]
        self._add_to_current_page(commands)
        current_y -= self.current_font_size * 1.2
```

### New Architecture (Separated)

```python
def _calculate_table_cell_layout_v2(self, cell_text, x, y, width, height, 
                                     is_header) -> LayoutBox:
    """Calculate cell layout - PURE"""
    font = "Helvetica-Bold" if is_header else "Helvetica"
    
    # Layout text with padding
    padding = 2
    max_width = width - (padding * 2)
    
    lines = self.text_layout_engine.layout_wrapped_text(
        text=cell_text,
        x=x + padding,
        y=y,
        max_width=max_width,
        font=font,
        size=self.current_font_size,
        alignment="left"
    )
    
    # Calculate vertical centering
    line_height = self.text_layout_engine.calculate_line_height(
        font, self.current_font_size, 1.2
    )
    total_text_height = len(lines) * line_height
    y_offset = (height - total_text_height) / 2
    
    # Adjust line positions for centering
    centered_lines = []
    current_y = y - y_offset
    for line in lines:
        # Create new line with adjusted Y
        adjusted_runs = [
            TextRun(run.text, run.font, run.size, run.x, current_y,
                   run.width, run.color, run.underline, run.strikethrough)
            for run in line.runs
        ]
        centered_lines.append(LineLayout(
            adjusted_runs, line.x, current_y, line.width, line.height
        ))
        current_y -= line_height
    
    return LayoutBox(
        box_type=BoxType.TABLE_CELL,
        x=x,
        y=y,
        width=width,
        height=height,
        content=centered_lines,
        metadata={'is_header': is_header}
    )

def _render_table_cell_layout_v2(self, layout: LayoutBox):
    """Render cell - PURE CONVERSION"""
    lines = layout.content
    
    for line in lines:
        for run in line.runs:
            commands = self._text_run_to_pdf_commands(run)
            self._add_to_current_page(commands)
    
    # Draw cell border
    self._draw_rectangle(layout.x, layout.y, layout.width, layout.height)
```

## Example 4: Code Block Layout

### Old Architecture (Coupled)

```python
def _layout_code_block(self, code_block):
    """Layout code block - mixed concerns"""
    lines = code_block.content.split('\n')
    
    # Add background (rendering mixed with layout)
    self._add_vertical_space(6)
    
    for line in lines:
        if self.current_y < self.margin_bottom + 12:
            self._new_page()
        
        # Render with monospace font
        commands = [
            "BT",
            "0.9 0.9 0.9 rg",  # Light gray background
            f"/Courier {self.current_font_size} Tf",
            f"1 0 0 1 {self.margin_left + 10} {self.current_y} Tm",
            f"{self._to_pdf_literal(line)} Tj",
            "ET"
        ]
        self._add_to_current_page(commands)
        self.current_y -= 14
```

### New Architecture (Separated)

```python
def _calculate_code_block_layout_v2(self, code_block) -> LayoutBox:
    """Calculate code block layout - PURE"""
    lines = code_block.content.split('\n')
    
    # Layout each line
    line_layouts = []
    current_y = self.current_y - 6  # Top padding
    
    for line_text in lines:
        line = self.text_layout_engine.layout_text_line(
            text=line_text,
            x=self.margin_left + 10,
            y=current_y,
            font="Courier",
            size=self.current_font_size,
            color=(0.2, 0.2, 0.2)  # Dark gray text
        )
        line_layouts.append(line)
        current_y -= 14
    
    total_height = len(lines) * 14 + 12  # Include padding
    
    return LayoutBox(
        box_type=BoxType.CODE_BLOCK,
        x=self.margin_left,
        y=self.current_y,
        width=self.page_width - self.margin_left - self.margin_right,
        height=total_height,
        content=line_layouts,
        metadata={'background_color': (0.95, 0.95, 0.95)}
    )

def _render_code_block_layout_v2(self, layout: LayoutBox):
    """Render code block - PURE CONVERSION"""
    # Draw background
    bg_color = layout.metadata.get('background_color', (0.95, 0.95, 0.95))
    self._draw_filled_rectangle(
        layout.x, layout.y, layout.width, layout.height,
        fill_color=bg_color
    )
    
    # Render text lines
    lines = layout.content
    for line in lines:
        for run in line.runs:
            commands = self._text_run_to_pdf_commands(run)
            self._add_to_current_page(commands)
    
    self.current_y -= layout.height
```

## Migration Checklist

For each component you migrate:

- [ ] **Extract calculation logic** into `_calculate_X_layout_v2()` method
- [ ] **Return immutable data structure** (LayoutBox, ParagraphLayout, etc.)
- [ ] **Use TextLayoutEngine** for text measurements and wrapping
- [ ] **Create rendering method** `_render_X_layout_v2()` that only converts layout to PDF
- [ ] **Keep rendering pure** - no calculations, only PDF command generation
- [ ] **Write tests** for layout calculation independently
- [ ] **Verify no regressions** by running existing tests
- [ ] **Update call sites** to use new methods
- [ ] **Mark old methods** as deprecated

## Testing Strategy

### Test Layout Calculation

```python
def test_heading_layout():
    """Test heading layout calculation"""
    renderer = ProfessionalPDFRenderer()
    heading = Heading(level=1, content=[Text("Test Heading")])
    
    # Calculate layout
    layout = renderer._calculate_heading_layout_v2(heading)
    
    # Verify layout properties
    assert layout.box_type == BoxType.HEADING
    assert layout.metadata['level'] == 1
    assert layout.height > 0
    assert layout.width > 0
```

### Test Rendering Separately

```python
def test_heading_rendering():
    """Test heading rendering from layout"""
    renderer = ProfessionalPDFRenderer()
    
    # Create mock layout
    line = LineLayout(
        runs=[TextRun("Test", "Helvetica-Bold", 24, 72, 720, 60)],
        x=72, y=720, width=60, height=28.8
    )
    layout = LayoutBox(
        box_type=BoxType.HEADING,
        x=72, y=720, width=60, height=36,
        content=line
    )
    
    # Render
    renderer._render_heading_layout_v2(layout)
    
    # Verify PDF commands were generated
    assert len(renderer.pages[0]) > 0
```

## Performance Tips

1. **Cache layout results** for repeated content
2. **Batch PDF commands** instead of many small appends
3. **Use TextLayoutEngine** for all text measurements (it's cached)
4. **Avoid recalculating** - store layout results
5. **Profile before optimizing** - measure actual bottlenecks

## Common Pitfalls

### ❌ Don't: Mix calculation and rendering

```python
def _layout_element(self, element):
    # Calculate
    width = self._measure_text(...)
    
    # Render (BAD - mixed concerns)
    commands = ["BT", ...]
    self._add_to_current_page(commands)
```

### ✅ Do: Separate phases

```python
def _calculate_element_layout(self, element) -> LayoutBox:
    # Only calculate
    width = self.text_layout_engine.measure_text_width(...)
    return LayoutBox(...)

def _render_element_layout(self, layout: LayoutBox):
    # Only render
    commands = self._layout_to_pdf_commands(layout)
    self._add_to_current_page(commands)
```

### ❌ Don't: Mutate layout structures

```python
layout.x += 10  # BAD - mutating layout
```

### ✅ Do: Create new structures

```python
new_layout = LayoutBox(
    layout.box_type,
    x=layout.x + 10,  # New value
    y=layout.y,
    width=layout.width,
    height=layout.height,
    content=layout.content
)
```

## Summary

The new architecture provides:

- **Clear separation** between layout and rendering
- **Testable components** that can be verified independently
- **Performance improvements** through caching
- **Maintainable code** with single responsibilities
- **Future flexibility** for multiple output formats

Migrate components incrementally, starting with simple ones (headings, paragraphs) and progressing to complex ones (tables, math blocks).
