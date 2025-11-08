#!/usr/bin/env python3
"""
Demonstration of advanced Compose features:
- Macro system
- Microtypography
- TeX compatibility
"""

def demo_macro_system():
    """Demonstrate the macro system"""
    print("🔧 MACRO SYSTEM DEMONSTRATION")
    print("=" * 50)

    from compose.macro_system import macro_processor, expand_macros

    # Define some macros
    macro_processor.process_newcommand(r"\newcommand{\hello}[1]{Hello, #1!}")
    macro_processor.process_newcommand(r"\newcommand{\vector}[2]{(#1, #2)}")
    macro_processor.process_newcommand(r"\newcommand{\frac}[2]{\frac{#1}{#2}}")

    # Test expansions
    test_cases = [
        r"\hello{World}",
        r"\vector{x}{y}",
        r"\frac{a}{b} + \vector{1}{2}",
    ]

    for test in test_cases:
        result = expand_macros(test)
        print(f"Input:  {test}")
        print(f"Output: {result.expanded}")
        print(f"Macros: {result.macros_used}")
        print()


def demo_microtypography():
    """Demonstrate microtypography features"""
    print("🎨 MICROTYPOGRAPHY DEMONSTRATION")
    print("=" * 50)

    from compose.microtypography import microtypography_engine

    # Test character protrusion
    test_lines = [
        '"Hello, world!"',      # Quotes can protrude
        "Testing (parentheses)", # Parentheses can protrude
        "End of sentence.",     # Period can protrude right
        "Normal text line",     # No protrusion
    ]

    for line in test_lines:
        protrusion = microtypography_engine._calculate_protrusion(line, 12.0)
        left_protrusion, right_protrusion = protrusion
        print(f"Line: {line}")
        print(f"  Left protrusion: {left_protrusion:.2f}pt, Right protrusion: {right_protrusion:.2f}pt")
        print()

    # Test paragraph enhancement
    paragraph = """This is a test paragraph with various punctuation marks.
It contains quotes "like this" and (parentheses) that can protrude.
The microtypography engine will adjust spacing accordingly."""

    enhanced = microtypography_engine.enhance_paragraph(paragraph, 60)
    print("Enhanced paragraph preview:")
    lines = enhanced.split('\n')[:3]  # Show first few lines
    for line in lines:
        if line.strip():
            print(f"  {line}")
    print("  ... (microtypography adjustments applied)")
    print()


def demo_tex_compatibility():
    """Demonstrate TeX compatibility features"""
    print("📐 TEX COMPATIBILITY DEMONSTRATION")
    print("=" * 50)

    from compose.tex_compatibility import tex_compatibility_engine

    # Run compatibility tests
    results = tex_compatibility_engine.run_trip_test_subset()

    print("Trip Test Compatibility Results:")
    print(".1%")
    for test_name, result in results.items():
        if test_name != 'summary':
            status = "✅" if result['passed'] else "❌"
            print(f"  {status} {test_name}: {result['message']}")

    print()

    # Demonstrate TeX-style line breaking
    text = "This is a sample paragraph that demonstrates TeX-style line breaking with proper hyphenation and spacing optimization."
    lines = tex_compatibility_engine.typeset_paragraph_tex_style(text, 40.0)

    print("TeX-style line breaking:")
    for i, line in enumerate(lines[:3], 1):  # Show first few lines
        print(f"{i}d")
    print("  ... (continues)")
    print()


def demo_integration():
    """Demonstrate integrated features working together"""
    print("🚀 INTEGRATED FEATURES DEMONSTRATION")
    print("=" * 50)

    from compose.macro_system import expand_macros
    from compose.microtypography import microtypography_engine

    # Create a sample document with macros
    document = r"""
% Macro definitions
\newcommand{\R}{\mathbb{R}}
\newcommand{\vector}[1]{\mathbf{#1}}

% Document content
Let $\vector{v} \in \R^n$ be a vector.

The equation $E = mc^2$ relates energy and mass.
"""

    print("Original document:")
    print(document.strip())
    print()

    # Process macros
    macro_result = expand_macros(document)
    print("After macro expansion:")
    print(macro_result.expanded.strip())
    print(f"Macros expanded: {macro_result.macros_used}")
    print()

    # Apply microtypography (show preview)
    enhanced = microtypography_engine.enhance_paragraph(macro_result.expanded, 80)
    print("After microtypography enhancement (preview):")
    lines = [line for line in enhanced.split('\n') if line.strip()][:2]
    for line in lines:
        print(f"  {line}")
    print("  ... (spacing adjustments applied)")
    print()


if __name__ == "__main__":
    print("🎉 COMPOSE ADVANCED FEATURES DEMONSTRATION")
    print("=" * 60)
    print()

    try:
        demo_macro_system()
        demo_microtypography()
        demo_tex_compatibility()
        demo_integration()

        print("✨ All advanced features demonstrated successfully!")
        print()
        print("These features provide:")
        print("• LaTeX-style macro expansion with parameter substitution")
        print("• Professional microtypography with character protrusion")
        print("• TeX-compatible box-and-glue layout algorithms")
        print("• Integrated processing pipeline for advanced typesetting")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
