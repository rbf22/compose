# Bounding Box Architecture: The Correct Approach

## The Problem

The current code calculates bounding boxes **after** rendering, trying to reconstruct what the bounds should have been. This is backwards and leads to:

1. **Duplicate calculations** - measuring text twice (once for rendering, once for bounds)
2. **Incorrect bounds** - reconstruction can't capture actual rendered extents
3. **Performance issues** - wasted computation
4. **Maintenance nightmare** - bounds logic scattered throughout rendering code

### Example of WRONG Approach (Current Code)

```python
def _layout_paragraph_simple(self, paragraph: Paragraph):
    """Layout paragraph - WRONG: bounds calculated after rendering"""
    para_start_y = self.current_y
    
    # 1. Render content (mutates state)
    self._render_inline_elements(paragraph.content, ...)
    
    # 2. Add spacing (mutates state more)
    self._add_vertical_space(total_spacing)
    
    # 3. Try to reconstruct bounds (WRONG!)
    bbox_left, bbox_top, bbox_right, bbox_bottom = self._calculate_text_bounding_box(
        "", self.margin_left, para_start_y, "Helvetica", self.current_font_size,
        max_width=..., mode='paragraph'
    )
    
    # 4. Draw box based on reconstruction
    self._draw_bounding_box(bbox_left, bbox_top, bbox_right, bbox_bottom, ...)
```

**Problems:**
- Bounds are **guessed** after the fact
- Can't capture actual text extents (ascenders, descenders)
- Requires complex `mode='paragraph'` logic to reconstruct
- State has already changed (`current_y` moved)

## The Correct Approach

Bounding boxes should be calculated **during layout** and stored in the layout structure. Then they're simply drawn when needed.

### Principle: Layout → Render → Debug

```
┌─────────────────────────────────────┐
│  1. LAYOUT PHASE                    │
│  Calculate ALL bounds               │
│  - Text measurements                │
│  - Line positions                   │
│  - Paragraph extents                │
│  - Complete bounding boxes          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. RENDER PHASE                    │
│  Convert layout to PDF              │
│  - Generate text commands           │
│  - Position elements                │
│  - NO calculation here              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. DEBUG PHASE (optional)          │
│  Draw boxes from layout             │
│  - Use stored bounds                │
│  - No recalculation                 │
└─────────────────────────────────────┘
```

### Example of CORRECT Approach (New Architecture)

```python
def _layout_paragraph_v2(self, paragraph: Paragraph):
    """Layout paragraph - CORRECT: bounds calculated during layout"""
    
    # Phase 1: Calculate layout (includes complete bounds)
    layout = self._calculate_paragraph_layout_v2(paragraph)
    # layout.bounds = (x, y, width, height) - KNOWN and CORRECT
    
    # Phase 2: Render layout
    self._render_paragraph_layout_v2(layout)
    
    # Phase 3: Draw bounding box from layout (if debug enabled)
    if self.debug_bounding_boxes:
        self._draw_bounding_box_from_layout(
            layout.to_layout_box(),
            self.debug_colors['paragraph']
        )
```

**Benefits:**
- Bounds are **calculated once** during layout
- Bounds are **accurate** (based on actual measurements)
- Bounds are **stored** in layout structure
- Drawing is **trivial** (just use stored bounds)

## Implementation Details

### 1. Layout Structures Store Complete Bounds

```python
@dataclass
class TextRun:
    """Atomic text element with COMPLETE bounds"""
    text: str
    font: str
    size: float
    x: float        # Left edge
    y: float        # Baseline position
    width: float    # Measured width
    # Bounds include ascenders and descenders
    
@dataclass
class LineLayout:
    """Line with COMPLETE bounds"""
    runs: List[TextRun]
    x: float
    y: float        # Baseline
    width: float
    height: float   # Includes ascent + descent
    baseline_offset: float  # Distance from top to baseline
    
    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Complete visual bounds"""
        return (self.x, self.y - self.height, self.width, self.height)

@dataclass
class ParagraphLayout:
    """Paragraph with COMPLETE bounds"""
    lines: List[LineLayout]
    x: float
    y: float        # Top of paragraph
    width: float
    height: float   # Total height including all lines
    spacing_after: float
    
    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Complete visual bounds"""
        return (self.x, self.y, self.width, self.height)
```

### 2. Bounds Calculated During Layout

```python
def _calculate_paragraph_layout_v2(self, paragraph: Paragraph) -> ParagraphLayout:
    """Calculate layout with COMPLETE bounds"""
    text = self._extract_text_content(paragraph.content)
    max_width = self.page_width - self.margin_left - self.margin_right
    
    # Text layout engine calculates complete bounds
    line_layouts = self.text_layout_engine.layout_wrapped_text(
        text=text,
        x=self.margin_left,
        y=self.current_y,
        max_width=max_width,
        font=self.current_font,
        size=self.current_font_size,
        line_height_factor=self.line_height_factor
    )
    
    # Each line has complete bounds (including ascent/descent)
    # Total height is sum of all line heights
    total_height = sum(line.height for line in line_layouts)
    
    # Return layout with KNOWN, CORRECT bounds
    return ParagraphLayout(
        lines=line_layouts,
        x=self.margin_left,
        y=self.current_y,
        width=max_width,
        height=total_height,  # Complete height
        spacing_after=self.paragraph_spacing
    )
```

### 3. Drawing Uses Stored Bounds

```python
def _draw_bounding_box_from_layout(self, layout: LayoutBox, 
                                   color: Tuple[float, float, float]):
    """Draw box using STORED bounds - no calculation"""
    if not self.debug_bounding_boxes:
        return
    
    # Extract bounds from layout (already calculated)
    x, y, w, h = layout.bounds
    
    # Draw box - simple, no calculation needed
    self._draw_bounding_box(
        x,       # Left
        y,       # Top  
        x + w,   # Right
        y - h,   # Bottom
        color
    )
```

## Complete Bounds Definition

Following the bounding box design philosophy from the memory:

### Text Element Bounds

```
     ┌─────────────────────────┐ ← Top (baseline + ascent)
     │  Ascender region        │
     │  (e.g., 'h', 'k', 'l')  │
─────┼─────────────────────────┼─── Baseline (y position)
     │  Main body              │
     │  (e.g., 'a', 'e', 'x')  │
     ├─────────────────────────┤
     │  Descender region       │
     │  (e.g., 'g', 'p', 'y')  │
     └─────────────────────────┘ ← Bottom (baseline - descent)
     
     ↑                         ↑
   Left (x)               Right (x + width)
```

### Calculating Complete Bounds

```python
def measure_text(self, text: str, font: str, size: float) -> TextMeasurement:
    """Measure text with COMPLETE bounds"""
    # Get font metrics
    metrics = self.font_metrics[font]
    
    # Calculate width from glyphs
    width = sum(glyph_widths[char] for char in text)
    width = width * (size / units_per_em)
    
    # Calculate height INCLUDING ascenders and descenders
    ascent = metrics['ascent'] * (size / units_per_em)
    descent = abs(metrics['descent']) * (size / units_per_em)
    height = ascent + descent  # COMPLETE height
    
    return TextMeasurement(
        text=text,
        font=font,
        size=size,
        width=width,
        height=height,      # Complete height
        ascent=ascent,      # Above baseline
        descent=descent     # Below baseline
    )
```

## Migration Path

### Step 1: Use New Architecture for New Code

```python
# New code should use layout-first approach
def _layout_new_element(self, element):
    layout = self._calculate_element_layout(element)
    self._render_element_layout(layout)
    
    # Bounding box from layout
    if self.debug_bounding_boxes:
        self._draw_bounding_box_from_layout(
            layout.to_layout_box(),
            self.debug_colors['element']
        )
```

### Step 2: Gradually Migrate Old Code

For each component:

1. **Extract layout calculation** into separate method
2. **Store bounds** in layout structure
3. **Update rendering** to use layout structure
4. **Replace** `_calculate_text_bounding_box()` with stored bounds
5. **Remove** reconstruction logic

### Step 3: Deprecate Old Methods

Once all components migrated:

```python
@deprecated("Use _draw_bounding_box_from_layout instead")
def _calculate_text_bounding_box(self, ...):
    """Old method - reconstructs bounds after rendering"""
    # This should eventually be removed
```

## Benefits of Correct Approach

### 1. Accuracy

Bounds are calculated from actual font metrics:

```python
# CORRECT: Uses actual font metrics
ascent = font_metrics['ascent'] * (size / units_per_em)  # e.g., 770/1000 * 12 = 9.24pt
descent = font_metrics['descent'] * (size / units_per_em)  # e.g., 230/1000 * 12 = 2.76pt
height = ascent + descent  # 12pt total

# WRONG: Guesses based on font size
height = font_size * 1.2  # Approximation, not accurate
```

### 2. Performance

No duplicate calculations:

```python
# OLD: Measure twice
width1 = self._measure_text_for_rendering(text)  # First time
width2 = self._measure_text_for_bounds(text)     # Second time (wasted)

# NEW: Measure once
measurement = self.text_layout_engine.measure_text(text)  # Once, cached
width = measurement.width
bounds = (x, y, measurement.width, measurement.height)
```

### 3. Maintainability

Bounds logic in one place:

```python
# OLD: Scattered logic
def _layout_paragraph(self):
    # Some bounds logic here
    pass

def _calculate_text_bounding_box(self, mode='paragraph'):
    # More bounds logic here
    if mode == 'paragraph':
        # Special case logic
    elif mode == 'single':
        # Different logic
    # Complex reconstruction

# NEW: Centralized
class TextLayoutEngine:
    def measure_text(self, text, font, size):
        # ALL bounds calculation here
        # One place, one algorithm
```

### 4. Debuggability

Bounds are visible in layout structure:

```python
# Can inspect layout before rendering
layout = calculate_paragraph_layout(paragraph)
print(f"Paragraph bounds: {layout.bounds}")
print(f"Line 1 bounds: {layout.lines[0].bounds}")
print(f"Text run bounds: {layout.lines[0].runs[0].width}")

# Can visualize layout without rendering
visualize_layout(layout)  # Show boxes without PDF
```

## Testing Strategy

### Test Bounds Calculation

```python
def test_text_bounds_include_ascenders_descenders():
    """Verify bounds include complete text extent"""
    engine = TextLayoutEngine(font_metrics)
    
    # Measure text with ascenders and descenders
    measurement = engine.measure_text("Ayg", "Helvetica", 12)
    
    # Height should include both
    assert measurement.ascent > 0  # Above baseline
    assert measurement.descent > 0  # Below baseline
    assert measurement.height == measurement.ascent + measurement.descent
    
def test_paragraph_bounds_match_content():
    """Verify paragraph bounds match actual content"""
    renderer = ProfessionalPDFRenderer()
    paragraph = Paragraph(content=[Text("Test paragraph")])
    
    layout = renderer._calculate_paragraph_layout_v2(paragraph)
    
    # Bounds should match sum of line bounds
    expected_height = sum(line.height for line in layout.lines)
    assert layout.height == expected_height
```

### Test Bounding Box Drawing

```python
def test_bounding_box_drawn_from_layout():
    """Verify boxes drawn from layout, not recalculated"""
    renderer = ProfessionalPDFRenderer()
    renderer.debug_bounding_boxes = True
    
    # Create layout
    layout = LayoutBox(
        box_type=BoxType.PARAGRAPH,
        x=72, y=720, width=468, height=100
    )
    
    # Draw box
    renderer._draw_bounding_box_from_layout(
        layout,
        renderer.debug_colors['paragraph']
    )
    
    # Verify PDF commands generated
    commands = renderer.pages[0]
    assert any('RG' in cmd for cmd in commands)  # Color set
    assert any('m' in cmd for cmd in commands)   # Move to
    assert any('l' in cmd for cmd in commands)   # Line to
```

## Summary

### ❌ Wrong: Calculate bounds after rendering

```python
render_text()           # Render first
calculate_bounds()      # Try to reconstruct
draw_box()             # Draw reconstructed box
```

### ✅ Correct: Calculate bounds during layout

```python
layout = calculate_layout()  # Bounds included
render_layout()              # Render from layout
draw_box_from_layout()       # Draw known bounds
```

The new architecture ensures bounding boxes are:
- **Accurate** - Based on actual measurements
- **Efficient** - Calculated once
- **Maintainable** - Centralized logic
- **Debuggable** - Visible in layout structures

This aligns with the bounding box design philosophy: calculate complete bounds during layout, use them everywhere.
