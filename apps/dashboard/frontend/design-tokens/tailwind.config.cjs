/**
 * Tailwind token mapping for React UI Material-Style Starter Tokens.
 * Merge this into your existing tailwind.config.cjs.
 */
module.exports = {
  theme: {
    extend: {
      colors: {
        md: {
          primary: "var(--md-sys-color-primary)",
          "on-primary": "var(--md-sys-color-on-primary)",
          "primary-container": "var(--md-sys-color-primary-container)",
          "on-primary-container": "var(--md-sys-color-on-primary-container)",
          secondary: "var(--md-sys-color-secondary)",
          "on-secondary": "var(--md-sys-color-on-secondary)",
          "secondary-container": "var(--md-sys-color-secondary-container)",
          "on-secondary-container": "var(--md-sys-color-on-secondary-container)",
          error: "var(--md-sys-color-error)",
          "on-error": "var(--md-sys-color-on-error)",
          background: "var(--md-sys-color-background)",
          "on-background": "var(--md-sys-color-on-background)",
          surface: "var(--md-sys-color-surface)",
          "on-surface": "var(--md-sys-color-on-surface)",
          "surface-container": "var(--md-sys-color-surface-container)",
          "surface-container-low": "var(--md-sys-color-surface-container-low)",
          "surface-container-high": "var(--md-sys-color-surface-container-high)",
          outline: "var(--md-sys-color-outline)",
          "outline-variant": "var(--md-sys-color-outline-variant)",
        },
      },
      fontFamily: {
        sans: ["var(--md-ref-typeface-plain)"],
        mono: ["var(--md-ref-typeface-mono)"],
      },
      fontSize: {
        "display-large": ["var(--md-sys-typescale-display-large-size)", { lineHeight: "var(--md-sys-typescale-display-large-line-height)", letterSpacing: "var(--md-sys-typescale-display-large-tracking)", fontWeight: "var(--md-sys-typescale-display-large-weight)" }],
        "headline-large": ["var(--md-sys-typescale-headline-large-size)", { lineHeight: "var(--md-sys-typescale-headline-large-line-height)", letterSpacing: "var(--md-sys-typescale-headline-large-tracking)", fontWeight: "var(--md-sys-typescale-headline-large-weight)" }],
        "title-large": ["var(--md-sys-typescale-title-large-size)", { lineHeight: "var(--md-sys-typescale-title-large-line-height)", letterSpacing: "var(--md-sys-typescale-title-large-tracking)", fontWeight: "var(--md-sys-typescale-title-large-weight)" }],
        "body-medium": ["var(--md-sys-typescale-body-medium-size)", { lineHeight: "var(--md-sys-typescale-body-medium-line-height)", letterSpacing: "var(--md-sys-typescale-body-medium-tracking)", fontWeight: "var(--md-sys-typescale-body-medium-weight)" }],
        "label-large": ["var(--md-sys-typescale-label-large-size)", { lineHeight: "var(--md-sys-typescale-label-large-line-height)", letterSpacing: "var(--md-sys-typescale-label-large-tracking)", fontWeight: "var(--md-sys-typescale-label-large-weight)" }],
      },
      spacing: {
        1: "var(--app-space-1)",
        2: "var(--app-space-2)",
        3: "var(--app-space-3)",
        4: "var(--app-space-4)",
        5: "var(--app-space-5)",
        6: "var(--app-space-6)",
        8: "var(--app-space-8)",
        10: "var(--app-space-10)",
        12: "var(--app-space-12)",
        16: "var(--app-space-16)",
        20: "var(--app-space-20)",
        24: "var(--app-space-24)",
      },
      borderRadius: {
        "md-xs": "var(--md-sys-shape-corner-xs)",
        "md-sm": "var(--md-sys-shape-corner-sm)",
        "md-md": "var(--md-sys-shape-corner-md)",
        "md-lg": "var(--md-sys-shape-corner-lg)",
        "md-xl": "var(--md-sys-shape-corner-xl)",
        "md-full": "var(--md-sys-shape-corner-full)",
      },
      boxShadow: {
        "md-1": "var(--md-sys-elevation-level1)",
        "md-2": "var(--md-sys-elevation-level2)",
        "md-3": "var(--md-sys-elevation-level3)",
        "md-4": "var(--md-sys-elevation-level4)",
        "md-5": "var(--md-sys-elevation-level5)",
      },
      screens: {
        compact: "0px",
        medium: "600px",
        expanded: "840px",
        large: "1200px",
        xlarge: "1600px",
      },
    },
  },
};
