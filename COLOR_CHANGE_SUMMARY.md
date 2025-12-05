# Terminal Color Change Summary

## Change
Updated the terminal text color from light green (#0f0) to a brighter Kiro purple (#a855ff) for improved contrast.

## Files Modified

### 1. static/css/terminal.css
- Changed body text color from `#0f0` to `#a855ff`
- Updated scrollbar track background from `rgba(0, 255, 0, 0.1)` to `rgba(168, 85, 255, 0.1)`
- Updated success message color from `#0f0` to `#a855ff`

### 2. static/css/themes.css
- Updated default theme name from "Classic Green" to "Kiro Purple"
- Changed CSS variables:
  - `--terminal-fg: #0f0` → `--terminal-fg: #a855ff`
  - `--terminal-glow: #0f0` → `--terminal-glow: #a855ff`

### 3. static/css/pages.css
- Changed body text color from `#0f0` to `#a855ff` for consistency across legal/info pages

## Visual Impact
- All terminal text now displays in bright Kiro purple (#a855ff)
- Improved contrast against black background for better readability
- Glow effects use the purple color
- Success messages use purple
- Scrollbar styling uses purple
- Legal and informational pages (Privacy, Terms, About) also use purple for consistency

## Other Themes
The following alternative themes remain unchanged and can still be selected:
- Amber (#ffb000)
- White (#fff)
- Blue (#00ffff)
- Matrix (Bright Green #00ff41)
- Retro Orange (#ff6600)

## Color Code
**Kiro Purple (Bright)**: #a855ff (RGB: 168, 85, 255)
- Brighter than the original #8e47ff for improved contrast and readability
- Maintains the Kiro brand purple aesthetic while being more visible on black backgrounds
