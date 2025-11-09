# Bounding Box Calculation: Before vs After

## Visual Comparison

### ❌ WRONG: Current Approach (Reconstruction)

```
Timeline of execution:
═══════════════════════════════════════════════════════════════

Step 1: Start rendering
┌─────────────────────────────────────────────────────────┐
│ para_start_y = self.current_y  # Save position          │
│ # current_y = 720                                       │
└─────────────────────────────────────────────────────────┘

Step 2: Render content (state mutates)
┌─────────────────────────────────────────────────────────┐
│ self._render_inline_elements(...)                       │
│ # Renders: "Hello World"                                │
│ # current_y changes: 720 → 705.6 → 691.2               │
│ # State is MUTATED, original position lost              │
└─────────────────────────────────────────────────────────┘

Step 3: Add spacing (more mutation)
┌─────────────────────────────────────────────────────────┐
│ self._add_vertical_space(18)                            │
│ # current_y changes: 691.2 → 673.2                      │
│ # State mutated AGAIN                                   │
└─────────────────────────────────────────────────────────┘

Step 4: Try to reconstruct bounds (WRONG!)
┌─────────────────────────────────────────────────────────┐
│ bbox = self._calculate_text_bounding_box(               │
│     "", self.margin_left, para_start_y,                 │
│     "Helvetica", 12, mode='paragraph'                   │
│ )                                                       │
│ # Tries to GUESS what the bounds were                   │
│ # Uses empty string "" - can't measure actual text!     │
│ # Uses mode='paragraph' - special case logic            │
│ # Result: APPROXIMATE bounds, not actual                │
└─────────────────────────────────────────────────────────┘

Step 5: Draw box based on guess
┌─────────────────────────────────────────────────────────┐
│ self._draw_bounding_box(bbox_left, bbox_top, ...)      │
│ # Box drawn from RECONSTRUCTED bounds                   │
│ # May not match actual rendered text                    │
└─────────────────────────────────────────────────────────┘

Problems:
• Bounds calculated TWICE (once for render, once for box)
• Reconstruction uses EMPTY STRING - can't be accurate
• State already MUTATED - original info lost
• Special case logic (mode='paragraph') - complex
• APPROXIMATE bounds - not actual measurements
```

### ✅ CORRECT: New Approach (Layout First)

```
Timeline of execution:
═══════════════════════════════════════════════════════════════

Step 1: Calculate complete layout (includes bounds)
┌─────────────────────────────────────────────────────────┐
│ layout = self._calculate_paragraph_layout_v2(paragraph) │
│                                                         │
│ Inside calculation:                                     │
│   text = "Hello World"                                  │
│   measurement = engine.measure_text(text, font, size)   │
│   # width = 66.0 (actual measured width)                │
│   # height = 14.4 (ascent + descent)                    │
│                                                         │
│   lines = engine.layout_wrapped_text(...)               │
│   # Line 1: x=72, y=720, width=66, height=14.4         │
│   # Line 2: x=72, y=705.6, width=60, height=14.4       │
│                                                         │
│   total_height = sum(line.height for line in lines)    │
│   # total_height = 28.8 (actual total)                  │
│                                                         │
│ Return ParagraphLayout(                                 │
│     lines=[line1, line2],                               │
│     x=72, y=720,                                        │
│     width=468,                                          │
│     height=28.8,  # KNOWN, ACCURATE                     │
│     spacing_after=6                                     │
│ )                                                       │
│                                                         │
│ # Layout has COMPLETE, ACCURATE bounds                  │
│ # No guessing, no reconstruction                        │
└─────────────────────────────────────────────────────────┘

Step 2: Render from layout (no calculation)
┌─────────────────────────────────────────────────────────┐
│ self._render_paragraph_layout_v2(layout)                │
│                                                         │
│ for line in layout.lines:                               │
│     for run in line.runs:                               │
│         commands = self._text_run_to_pdf_commands(run)  │
│         self._add_to_current_page(commands)             │
│                                                         │
│ # Pure conversion - no measurement, no calculation      │
│ # Just converts layout data to PDF commands             │
└─────────────────────────────────────────────────────────┘

Step 3: Draw box from known bounds (trivial)
┌─────────────────────────────────────────────────────────┐
│ if self.debug_bounding_boxes:                           │
│     self._draw_bounding_box_from_layout(                │
│         layout.to_layout_box(),                         │
│         self.debug_colors['paragraph']                  │
│     )                                                   │
│                                                         │
│ Inside _draw_bounding_box_from_layout:                  │
│     x, y, w, h = layout.bounds  # Use stored bounds     │
│     self._draw_bounding_box(x, y, x+w, y-h, color)      │
│                                                         │
│ # Bounds are KNOWN from layout                          │
│ # No calculation, no guessing                           │
│ # Just draw using stored values                         │
└─────────────────────────────────────────────────────────┘

Benefits:
✓ Bounds calculated ONCE during layout
✓ Uses ACTUAL TEXT measurements
✓ No state mutation during calculation
✓ No special case logic needed
✓ ACCURATE bounds from measurements
✓ Trivial to draw - just use stored bounds
```

## Code Comparison

### ❌ WRONG: Reconstruction After Rendering

```python
def _layout_paragraph_simple(self, paragraph: Paragraph):
    # Save starting position
    para_start_y = self.current_y  # 720
    
    # Render (mutates state)
    self._render_inline_elements(paragraph.content, ...)
    # current_y is now 691.2 (mutated)
    
    # Add spacing (mutates more)
    self._add_vertical_space(18)
    # current_y is now 673.2 (mutated again)
    
    # Try to reconstruct bounds (WRONG!)
    bbox_left, bbox_top, bbox_right, bbox_bottom = \
        self._calculate_text_bounding_box(
            "",  # ← EMPTY STRING! Can't measure actual text
            self.margin_left,
            para_start_y,  # ← Old position, state has changed
            "Helvetica",
            self.current_font_size,
            max_width=self.page_width - self.margin_left - self.margin_right,
            mode='paragraph'  # ← Special case logic
        )
    
    # Draw box from reconstructed bounds
    self._draw_bounding_box(
        bbox_left, bbox_top, bbox_right, bbox_bottom,
        self.debug_colors['paragraph']
    )
```

**Problems:**
1. `""` empty string - can't measure actual text width
2. `para_start_y` - state has changed since then
3. `mode='paragraph'` - needs special logic to reconstruct
4. Bounds are **approximate**, not actual

### ✅ CORRECT: Layout First, Then Render

```python
def _layout_paragraph_v2(self, paragraph: Paragraph):
    # Phase 1: Calculate layout (includes complete bounds)
    layout = self._calculate_paragraph_layout_v2(paragraph)
    # layout.bounds = (72, 720, 468, 28.8) - KNOWN and ACCURATE
    
    # Phase 2: Render from layout
    self._render_paragraph_layout_v2(layout)
    
    # Phase 3: Draw box from layout (if debug enabled)
    if self.debug_bounding_boxes:
        self._draw_bounding_box_from_layout(
            layout.to_layout_box(),
            self.debug_colors['paragraph']
        )

def _calculate_paragraph_layout_v2(self, paragraph: Paragraph) -> ParagraphLayout:
    """Calculate layout with COMPLETE bounds"""
    text = self._extract_text_content(paragraph.content)  # "Hello World"
    max_width = self.page_width - self.margin_left - self.margin_right
    
    # Use text layout engine (cached, accurate)
    line_layouts = self.text_layout_engine.layout_wrapped_text(
        text=text,  # ← ACTUAL TEXT, not empty string
        x=self.margin_left,
        y=self.current_y,
        max_width=max_width,
        font=self.current_font,
        size=self.current_font_size,
        line_height_factor=self.line_height_factor
    )
    
    # Calculate total height from actual line heights
    total_height = sum(line.height for line in line_layouts)
    
    # Return layout with KNOWN bounds
    return ParagraphLayout(
        lines=line_layouts,
        x=self.margin_left,
        y=self.current_y,
        width=max_width,
        height=total_height,  # ← ACTUAL height, not guessed
        spacing_after=self.paragraph_spacing
    )

def _draw_bounding_box_from_layout(self, layout: LayoutBox, color):
    """Draw box using STORED bounds - no calculation"""
    if not self.debug_bounding_boxes:
        return
    
    # Extract bounds from layout (already calculated)
    x, y, w, h = layout.bounds  # ← Use stored bounds
    
    # Draw box - trivial, no calculation
    self._draw_bounding_box(x, y, x + w, y - h, color)
```

**Benefits:**
1. Uses **actual text** for measurements
2. Bounds calculated **once** during layout
3. No **special case logic** needed
4. Bounds are **accurate** from measurements
5. Drawing is **trivial** - just use stored bounds

## Performance Comparison

### ❌ WRONG: Duplicate Calculations

```python
# Rendering phase
for line in lines:
    width = self._measure_text(line)  # Measurement #1
    # ... render ...

# Bounding box phase
bbox = self._calculate_text_bounding_box(...)
    width = self._measure_text(text)  # Measurement #2 (duplicate!)
    # ... calculate bounds ...
```

**Cost:** 2× text measurements

### ✅ CORRECT: Single Calculation

```python
# Layout phase
measurement = self.text_layout_engine.measure_text(text)  # Once
layout = ParagraphLayout(
    width=measurement.width,
    height=measurement.height
)

# Rendering phase
render_from_layout(layout)  # No measurement

# Bounding box phase
draw_box(layout.bounds)  # No measurement
```

**Cost:** 1× text measurement (cached)

## Accuracy Comparison

### ❌ WRONG: Approximate Bounds

```python
# Reconstruction tries to guess
def _calculate_text_bounding_box(self, text, x, y, font, size, mode='paragraph'):
    if mode == 'paragraph':
        # Guess based on font size
        height = size * 1.2  # ← APPROXIMATION
        # Doesn't account for actual ascenders/descenders
    elif mode == 'single':
        height = size  # ← Different approximation
    # ... more guessing ...
```

**Result:** Bounds may not match actual text extent

### ✅ CORRECT: Measured Bounds

```python
# Measurement uses actual font metrics
def measure_text(self, text, font, size):
    metrics = self.font_metrics[font]
    
    # Actual ascent from font
    ascent = metrics['ascent'] * (size / 1000)  # e.g., 9.24pt
    
    # Actual descent from font
    descent = abs(metrics['descent']) * (size / 1000)  # e.g., 2.76pt
    
    # Complete height
    height = ascent + descent  # e.g., 12pt
    
    return TextMeasurement(
        width=measured_width,
        height=height,  # ← ACTUAL height from font metrics
        ascent=ascent,
        descent=descent
    )
```

**Result:** Bounds match actual rendered text

## State Management Comparison

### ❌ WRONG: State Mutation During Rendering

```python
para_start_y = self.current_y  # 720

# Render line 1
self.current_y -= 14.4  # Now 705.6

# Render line 2
self.current_y -= 14.4  # Now 691.2

# Add spacing
self.current_y -= 18  # Now 673.2

# Try to calculate bounds
# But current_y has changed! Original position lost
# Must use saved para_start_y and guess the rest
```

**Problem:** State mutated, must reconstruct

### ✅ CORRECT: Immutable Layout Structure

```python
# Calculate layout (immutable)
layout = ParagraphLayout(
    lines=[
        LineLayout(x=72, y=720, width=66, height=14.4),
        LineLayout(x=72, y=705.6, width=60, height=14.4)
    ],
    x=72,
    y=720,
    width=468,
    height=28.8
)

# Render from layout (state changes, but layout unchanged)
for line in layout.lines:
    render_line(line)
    self.current_y -= line.height

# Draw box from layout (layout still has original values)
draw_box(layout.bounds)  # Still (72, 720, 468, 28.8)
```

**Benefit:** Layout is immutable, always has correct bounds

## Summary

| Aspect | ❌ Wrong (Current) | ✅ Correct (New) |
|--------|-------------------|------------------|
| **When calculated** | After rendering | During layout |
| **Text used** | Empty string `""` | Actual text |
| **Measurements** | 2× (duplicate) | 1× (cached) |
| **Accuracy** | Approximate | Exact (from metrics) |
| **State** | Mutated, must reconstruct | Immutable, stored |
| **Complexity** | Special cases (`mode=`) | Simple, uniform |
| **Performance** | Slower (duplicate work) | Faster (cached) |
| **Maintainability** | Complex reconstruction | Simple extraction |

The new architecture ensures bounding boxes are calculated correctly: **once, during layout, with complete accuracy**.
